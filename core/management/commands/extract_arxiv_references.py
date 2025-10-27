"""
Django管理命令：提取ArXiv论文的参考文献
从ArXiv论文数据表中读取论文，下载PDF，提取参考文献并存储到数据库
"""
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone
from datetime import datetime, timedelta
import logging
import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

from core.arxiv_models import ArxivPaper, ArxivPaperReference, ArxivReferenceExtractLog
from core.arxiv_reference_extractor import ArxivReferenceExtractor


# 配置日志
logger = logging.getLogger(__name__)


class ThreadSafeStats:
    """线程安全的统计计数器"""
    def __init__(self, total):
        self.total = total
        self.processed = 0
        self.success = 0
        self.failed = 0
        self.skipped = 0
        self.lock = threading.Lock()
    
    def update(self, result):
        """更新统计信息"""
        with self.lock:
            self.processed += 1
            if result == 'success':
                self.success += 1
            elif result == 'failed':
                self.failed += 1
            elif result == 'skipped':
                self.skipped += 1
    
    def get_dict(self):
        """获取统计字典（线程安全）"""
        with self.lock:
            return {
                'total': self.total,
                'processed': self.processed,
                'success': self.success,
                'failed': self.failed,
                'skipped': self.skipped,
            }


class Command(BaseCommand):
    help = '从ArXiv论文PDF中提取参考文献并存储到数据库'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--mode',
            type=str,
            choices=['extract', 'process', 'full'],
            default='full',
            help='处理模式：extract（只提取文本）、process（只LLM处理）、full（完整流程，默认）'
        )
        parser.add_argument(
            '--arxiv-id',
            type=str,
            help='处理指定的arXiv ID'
        )
        parser.add_argument(
            '--limit',
            type=int,
            default=None,
            help='限制处理的论文数量'
        )
        parser.add_argument(
            '--batch-size',
            type=int,
            default=10,
            help='批量处理的大小'
        )
        parser.add_argument(
            '--skip-existing',
            action='store_true',
            help='跳过已经提取过参考文献的论文'
        )
        parser.add_argument(
            '--retry-failed',
            action='store_true',
            help='重试之前失败的论文'
        )
        parser.add_argument(
            '--max-retries',
            type=int,
            default=3,
            help='单篇论文的最大重试次数'
        )
        parser.add_argument(
            '--llm-provider',
            type=str,
            default='qwen',
            help='LLM提供商（默认: qwen）'
        )
        parser.add_argument(
            '--llm-model',
            type=str,
            default='qwen3-max',
            help='LLM模型名称（默认: qwen3-max）'
        )
        parser.add_argument(
            '--llm-timeout',
            type=int,
            default=600,
            help='LLM API超时时间（秒，默认: 600）'
        )
        parser.add_argument(
            '--delay',
            type=float,
            default=1.0,
            help='每篇论文处理之间的延迟（秒）'
        )
        parser.add_argument(
            '--cleanup-pdfs',
            type=int,
            default=None,
            help='清理N天前的PDF文件'
        )
        # Process 模式特有参数
        parser.add_argument(
            '--skip-processed',
            action='store_true',
            help='（process模式）跳过已经LLM处理过的论文'
        )
        parser.add_argument(
            '--max-chars',
            type=int,
            default=50000,
            help='（process模式）最大字符数限制（默认: 50000）'
        )
        parser.add_argument(
            '--clean-old-logs',
            action='store_true',
            help='重跑时清理该论文之前的所有日志记录（避免重复）'
        )
        parser.add_argument(
            '--workers',
            type=int,
            default=1,
            help='并发处理的线程数（默认: 1，建议 extract 模式使用 3-5，process 模式保持 1）'
        )
    
    def handle(self, *args, **options):
        mode = options['mode']
        
        # 根据模式显示不同的标题
        mode_titles = {
            'extract': '【第一阶段】开始提取ArXiv论文参考文献原始文本...',
            'process': '【第二阶段】开始使用LLM处理参考文献...',
            'full': '开始提取ArXiv论文参考文献（完整流程）...'
        }
        self.stdout.write(self.style.SUCCESS(mode_titles[mode]))
        
        # 初始化提取器
        try:
            if mode == 'extract':
                # extract 模式不需要 LLM 配置
                extractor = ArxivReferenceExtractor(
                    max_retries=options['max_retries']
                )
                self.stdout.write('提取器已初始化（无需LLM配置）')
            else:
                # process 和 full 模式需要 LLM
                extractor = ArxivReferenceExtractor(
                    llm_provider=options['llm_provider'],
                    llm_model=options['llm_model'],
                    max_retries=options['max_retries'],
                    llm_timeout=options['llm_timeout']
                )
                self.stdout.write(f'LLM配置: {options["llm_provider"]}/{options["llm_model"]} (超时: {options["llm_timeout"]}秒)')
        except Exception as e:
            raise CommandError(f'初始化提取器失败: {str(e)}')
        
        # 如果指定了清理PDF
        if options['cleanup_pdfs'] is not None:
            self.stdout.write('清理旧的PDF文件...')
            deleted = extractor.cleanup_old_pdfs(days=options['cleanup_pdfs'])
            self.stdout.write(self.style.SUCCESS(f'清理了 {deleted} 个PDF文件'))
            if not options['arxiv_id']:
                return
        
        # 根据模式调用不同的处理方法
        if mode == 'extract':
            self._handle_extract_mode(extractor, options)
        elif mode == 'process':
            self._handle_process_mode(extractor, options)
        else:  # full
            self._handle_full_mode(extractor, options)
    
    def _get_papers_to_process(self, options):
        """获取需要处理的论文列表"""
        queryset = ArxivPaper.objects.all()
        
        # 如果指定了arxiv_id
        if options['arxiv_id']:
            queryset = queryset.filter(arxiv_id=options['arxiv_id'])
        
        # 如果跳过已处理的
        if options['skip_existing']:
            # 性能优化：使用 LEFT JOIN + IS NULL 替代 exclude(id__in=...)
            # 这样可以避免在百万级数据下加载大量 ID 到内存
            from django.db.models import OuterRef, Exists
            
            # 创建子查询：检查是否存在已完成的日志
            completed_logs = ArxivReferenceExtractLog.objects.filter(
                paper_id=OuterRef('id'),
                status='completed'
            )
            
            # 只选择没有已完成日志的论文
            queryset = queryset.filter(~Exists(completed_logs))
        
        # 如果只重试失败的
        if options['retry_failed']:
            from django.db.models import OuterRef, Exists
            
            # 性能优化：使用 Exists 子查询
            failed_logs = ArxivReferenceExtractLog.objects.filter(
                paper_id=OuterRef('id'),
                status='failed'
            )
            
            queryset = queryset.filter(Exists(failed_logs))
        
        # 按发布时间排序
        queryset = queryset.order_by('-published')
        
        # 应用限制
        if options['limit']:
            queryset = queryset[:options['limit']]
        
        return list(queryset)
    
    def _process_single_paper(self, paper, extractor, options):
        """处理单篇论文"""
        arxiv_id = paper.arxiv_id
        
        self.stdout.write(f'\n{"="*70}')
        self.stdout.write(f'处理论文: {arxiv_id}')
        self.stdout.write(f'标题: {paper.title[:60]}...')
        self.stdout.write(f'{"="*70}')
        
        # 检查是否已经有成功的提取记录
        if options['skip_existing']:
            existing_log = ArxivReferenceExtractLog.objects.filter(
                paper=paper,
                status='completed'
            ).first()
            
            if existing_log:
                self.stdout.write(self.style.WARNING(f'  ⊙ 跳过（已处理）'))
                return 'skipped'
        
        # 如果指定了清理旧日志，则删除该论文之前的所有日志
        if options['clean_old_logs']:
            old_logs_count = ArxivReferenceExtractLog.objects.filter(paper=paper).count()
            if old_logs_count > 0:
                ArxivReferenceExtractLog.objects.filter(paper=paper).delete()
                self.stdout.write(f'  🗑️  清理了 {old_logs_count} 条旧日志记录')
        
        # 检查重试次数
        retry_count = ArxivReferenceExtractLog.objects.filter(
            paper=paper
        ).count()
        
        if retry_count >= options['max_retries'] and not options['retry_failed']:
            self.stdout.write(self.style.WARNING(f'  ⊙ 跳过（超过最大重试次数）'))
            return 'skipped'
        
        # 创建提取日志
        log = ArxivReferenceExtractLog.objects.create(
            paper=paper,
            status='pending',
            retry_count=retry_count
        )
        
        start_time = timezone.now()
        
        # 定义进度回调函数
        def progress_callback(step_name, details):
            """打印处理进度"""
            step_icons = {
                'downloading': '📥',
                'downloaded': '✅',
                'download_failed': '❌',
                'extracting_text': '📝',
                'text_extracted': '✅',
                'extraction_failed': '❌',
                'finding_references': '🔍',
                'references_found': '✅',
                'reference_not_found': '⚠️',
                'llm_processing': '🤖',
                'llm_completed': '✅',
                'llm_failed': '❌',
            }
            icon = step_icons.get(step_name, '•')
            self.stdout.write(f'  {icon} {details}')
        
        try:
            # 执行提取
            result = extractor.process_paper(
                paper_id=paper.id,
                arxiv_id=arxiv_id,
                pdf_url=paper.pdf_url,
                progress_callback=progress_callback
            )
            
            # 更新日志
            log.pdf_downloaded = result['pdf_downloaded']
            log.pdf_file_path = result['pdf_path']
            log.pdf_file_size = result['pdf_size']
            log.text_extracted = result['text_extracted']
            log.reference_section_found = result['reference_section_found']
            log.llm_processed = result['llm_processed']
            log.reference_count = result['reference_count']
            log.llm_response = result.get('llm_response')  # 保存LLM原始响应
            
            if result['success']:
                log.status = 'completed'
                
                # 保存参考文献到数据库
                self.stdout.write('  💾 正在保存参考文献到数据库...')
                self._save_references(paper, result['references'], log)
                
                log.completed_at = timezone.now()
                log.duration_seconds = (log.completed_at - start_time).seconds
                log.save()
                
                self.stdout.write(self.style.SUCCESS(
                    f'  ✓ 处理完成！提取 {result["reference_count"]} 条参考文献，耗时 {log.duration_seconds} 秒'
                ))
                return 'success'
            else:
                log.status = 'failed'
                log.error_type = result['error_type']
                log.error_message = result['error_message']
                log.completed_at = timezone.now()
                log.duration_seconds = (log.completed_at - start_time).seconds
                log.save()
                
                self.stdout.write(self.style.ERROR(
                    f'  ✗ 处理失败: {result["error_type"]}'
                ))
                self.stdout.write(self.style.ERROR(
                    f'     错误详情: {result["error_message"][:200]}'
                ))
                return 'failed'
                
        except Exception as e:
            log.status = 'failed'
            log.error_type = 'unexpected_error'
            log.error_message = str(e)
            log.completed_at = timezone.now()
            log.duration_seconds = (log.completed_at - start_time).seconds
            log.save()
            
            self.stdout.write(self.style.ERROR(f'  ✗ 异常: {str(e)}'))
            logger.exception(f'处理论文 {arxiv_id} 时发生异常')
            return 'failed'
    
    def _save_references(self, paper, references, log):
        """保存参考文献到数据库"""
        try:
            with transaction.atomic():
                # 删除旧的参考文献（如果存在）
                ArxivPaperReference.objects.filter(paper=paper).delete()
                
                # 批量创建新的参考文献
                reference_objects = []
                for ref_data in references:
                    reference_objects.append(
                        ArxivPaperReference(
                            paper=paper,
                            reference_number=ref_data.get('reference_number', 0),
                            title=ref_data.get('title'),
                            authors=ref_data.get('authors'),
                            year=ref_data.get('year'),
                            venue=ref_data.get('venue'),
                            venue_type=ref_data.get('venue_type'),
                            volume=ref_data.get('volume'),
                            issue=ref_data.get('issue'),
                            pages=ref_data.get('pages'),
                            doi=ref_data.get('doi'),
                            arxiv_id=ref_data.get('arxiv_id'),
                            url=ref_data.get('url'),
                            raw_text=ref_data.get('raw_text', ''),
                            extraction_method='llm',
                        )
                    )
                
                ArxivPaperReference.objects.bulk_create(reference_objects)
                
        except Exception as e:
            log.error_message = f'保存参考文献失败: {str(e)}'
            log.save()
            raise
    
    def _print_progress(self, stats):
        """打印进度信息"""
        self.stdout.write(
            f"\n进度: {stats['processed']}/{stats['total']} | "
            f"成功: {stats['success']} | "
            f"失败: {stats['failed']} | "
            f"跳过: {stats['skipped']}"
        )
    
    def _print_final_stats(self, stats):
        """打印最终统计信息"""
        # 计算参考文献总数
        total_refs = ArxivPaperReference.objects.count()
        
        self.stdout.write(f'总论文数: {stats["total"]}')
        self.stdout.write(self.style.SUCCESS(f'成功: {stats["success"]}'))
        if stats['failed'] > 0:
            self.stdout.write(self.style.ERROR(f'失败: {stats["failed"]}'))
        if stats['skipped'] > 0:
            self.stdout.write(self.style.WARNING(f'跳过: {stats["skipped"]}'))
        self.stdout.write(f'数据库中参考文献总数: {total_refs}')
        
        # 成功率
        if stats['processed'] > 0:
            success_rate = (stats['success'] / stats['processed']) * 100
            self.stdout.write(f'成功率: {success_rate:.1f}%')
    
    def _handle_extract_mode(self, extractor, options):
        """处理 extract 模式：只提取参考文献原始文本"""
        # 获取需要处理的论文
        papers = self._get_papers_to_process(options)
        
        if not papers:
            self.stdout.write(self.style.WARNING('没有找到需要处理的论文'))
            return
        
        total = len(papers)
        workers = options['workers']
        self.stdout.write(f'找到 {total} 篇论文待处理')
        
        if workers > 1:
            self.stdout.write(f'使用 {workers} 个线程并发处理')
        
        # 线程安全的统计信息
        stats = ThreadSafeStats(total)
        
        # 如果只有 1 个 worker，使用单线程处理
        if workers == 1:
            self._handle_extract_mode_single_thread(papers, extractor, options, stats)
        else:
            self._handle_extract_mode_multi_thread(papers, extractor, options, stats, workers)
        
        # 最终统计
        self.stdout.write('\n' + '=' * 60)
        self.stdout.write(self.style.SUCCESS('【第一阶段】处理完成！'))
        self._print_extract_final_stats(stats.get_dict())
    
    def _handle_extract_mode_single_thread(self, papers, extractor, options, stats):
        """单线程处理 extract 模式"""
        batch_size = options['batch_size']
        delay = options['delay']
        total = len(papers)
        
        for i in range(0, total, batch_size):
            batch = papers[i:i + batch_size]
            self.stdout.write(f'\n处理批次 {i // batch_size + 1} (论文 {i + 1}-{min(i + batch_size, total)})')
            
            for paper in batch:
                result = self._process_paper_extract_only(paper, extractor, options)
                stats.update(result)
                
                # 延迟
                if delay > 0 and stats.processed < total:
                    time.sleep(delay)
            
            # 显示进度
            self._print_progress(stats.get_dict())
    
    def _handle_extract_mode_multi_thread(self, papers, extractor, options, stats, workers):
        """多线程处理 extract 模式"""
        delay = options['delay']
        total = len(papers)
        output_lock = threading.Lock()
        
        def process_paper_with_output(paper):
            """\u5904\u7406\u5355\u7bc7\u8bba\u6587\uff08\u5e26\u8f93\u51fa\u9501\uff09"""
            result = self._process_paper_extract_only(paper, extractor, options)
            stats.update(result)
            
            # 线程安全地打印进度
            with output_lock:
                if stats.processed % 10 == 0 or stats.processed == total:
                    self._print_progress(stats.get_dict())
            
            # 延迟
            if delay > 0:
                time.sleep(delay)
            
            return result
        
        # 使用线程池处理
        with ThreadPoolExecutor(max_workers=workers) as executor:
            futures = {executor.submit(process_paper_with_output, paper): paper for paper in papers}
            
            for future in as_completed(futures):
                try:
                    future.result()
                except Exception as e:
                    paper = futures[future]
                    with output_lock:
                        self.stdout.write(self.style.ERROR(f'处理论文 {paper.arxiv_id} 时发生异常: {str(e)}'))
                        logger.exception(f'多线程处理论文 {paper.arxiv_id} 失败')
    
    def _handle_process_mode(self, extractor, options):
        """处理 process 模式：只使用LLM处理已提取的文本"""
        # 获取需要处理的日志记录
        logs = self._get_logs_to_process(options)
        
        if not logs:
            self.stdout.write(self.style.WARNING('没有找到需要处理的记录'))
            return
        
        total = len(logs)
        self.stdout.write(f'找到 {total} 条记录待处理')
        
        # 统计信息
        stats = {
            'total': total,
            'processed': 0,
            'success': 0,
            'failed': 0,
            'skipped': 0,
        }
        
        # 批量处理
        batch_size = options['batch_size']
        delay = options['delay']
        
        for i in range(0, total, batch_size):
            batch = logs[i:i + batch_size]
            self.stdout.write(f'\n处理批次 {i // batch_size + 1} (记录 {i + 1}-{min(i + batch_size, total)})')
            
            for log in batch:
                result = self._process_log_with_llm(log, extractor, options)
                
                # 更新统计
                stats['processed'] += 1
                if result == 'success':
                    stats['success'] += 1
                elif result == 'failed':
                    stats['failed'] += 1
                elif result == 'skipped':
                    stats['skipped'] += 1
                
                # 延迟
                if delay > 0 and stats['processed'] < total:
                    time.sleep(delay)
            
            # 显示进度
            self._print_progress(stats)
        
        # 最终统计
        self.stdout.write('\n' + '=' * 60)
        self.stdout.write(self.style.SUCCESS('【第二阶段】处理完成！'))
        self._print_process_final_stats(stats)
    
    def _handle_full_mode(self, extractor, options):
        """处理 full 模式：完整流程（提取文本 + LLM处理）"""
        # 获取需要处理的论文
        papers = self._get_papers_to_process(options)
        
        if not papers:
            self.stdout.write(self.style.WARNING('没有找到需要处理的论文'))
            return
        
        total = len(papers)
        workers = options['workers']
        self.stdout.write(f'找到 {total} 篇论文待处理')
        
        if workers > 1:
            self.stdout.write(f'使用 {workers} 个线程并发处理')
            self.stdout.write(self.style.WARNING('注意: full 模式包含 LLM 调用，建议 workers 设置为 2-3 以避免 API 限流'))
        
        # 线程安全的统计信息
        stats = ThreadSafeStats(total)
        
        # 如果只有 1 个 worker，使用单线程处理
        if workers == 1:
            self._handle_full_mode_single_thread(papers, extractor, options, stats)
        else:
            self._handle_full_mode_multi_thread(papers, extractor, options, stats, workers)
        
        # 最终统计
        self.stdout.write('\n' + '=' * 60)
        self.stdout.write(self.style.SUCCESS('处理完成！'))
        self._print_final_stats(stats.get_dict())
    
    def _handle_full_mode_single_thread(self, papers, extractor, options, stats):
        """单线程处理 full 模式"""
        batch_size = options['batch_size']
        delay = options['delay']
        total = len(papers)
        
        for i in range(0, total, batch_size):
            batch = papers[i:i + batch_size]
            self.stdout.write(f'\n处理批次 {i // batch_size + 1} (论文 {i + 1}-{min(i + batch_size, total)})')
            
            for paper in batch:
                result = self._process_single_paper(paper, extractor, options)
                stats.update(result)
                
                # 延迟
                if delay > 0 and stats.processed < total:
                    time.sleep(delay)
            
            # 显示进度
            self._print_progress(stats.get_dict())
    
    def _handle_full_mode_multi_thread(self, papers, extractor, options, stats, workers):
        """多线程处理 full 模式"""
        delay = options['delay']
        total = len(papers)
        output_lock = threading.Lock()
        
        def process_paper_with_output(paper):
            """\u5904\u7406\u5355\u7bc7\u8bba\u6587\uff08\u5e26\u8f93\u51fa\u9501\uff09"""
            result = self._process_single_paper(paper, extractor, options)
            stats.update(result)
            
            # 线程安全地打印进度
            with output_lock:
                if stats.processed % 5 == 0 or stats.processed == total:
                    self._print_progress(stats.get_dict())
            
            # 延迟
            if delay > 0:
                time.sleep(delay)
            
            return result
        
        # 使用线程池处理
        with ThreadPoolExecutor(max_workers=workers) as executor:
            futures = {executor.submit(process_paper_with_output, paper): paper for paper in papers}
            
            for future in as_completed(futures):
                try:
                    future.result()
                except Exception as e:
                    paper = futures[future]
                    with output_lock:
                        self.stdout.write(self.style.ERROR(f'处理论文 {paper.arxiv_id} 时发生异常: {str(e)}'))
                        logger.exception(f'多线程处理论文 {paper.arxiv_id} 失败')
    
    def _get_logs_to_process(self, options):
        """获取需要处理的提取日志列表（用于process模式）"""
        # 基础查询：只选择已提取文本但未LLM处理的记录
        queryset = ArxivReferenceExtractLog.objects.filter(
            reference_section_found=True,
            reference_raw_text__isnull=False
        )
        
        # 如果指定了arxiv_id
        if options['arxiv_id']:
            queryset = queryset.filter(paper__arxiv_id=options['arxiv_id'])
        
        # 如果跳过已处理的
        if options['skip_processed']:
            queryset = queryset.filter(llm_processed=False)
        
        # 如果只重试失败的
        if options['retry_failed']:
            queryset = queryset.filter(
                llm_processed=False,
                status='failed'
            )
        elif not options['skip_processed']:
            # 默认只处理未LLM处理的
            queryset = queryset.filter(llm_processed=False)
        
        # 按时间排序
        queryset = queryset.select_related('paper').order_by('-started_at')
        
        # 应用限制
        if options['limit']:
            queryset = queryset[:options['limit']]
        
        return list(queryset)
    
    def _process_paper_extract_only(self, paper, extractor, options):
        """处理单篇论文（只提取文本，不调用LLM）"""
        arxiv_id = paper.arxiv_id
        
        self.stdout.write(f'\n{"="*70}')
        self.stdout.write(f'处理论文: {arxiv_id}')
        self.stdout.write(f'标题: {paper.title[:60]}...')
        self.stdout.write(f'{"="*70}')
        
        # 检查是否已经有提取记录
        if options['skip_existing']:
            existing_log = ArxivReferenceExtractLog.objects.filter(
                paper=paper,
                reference_section_found=True,
                reference_raw_text__isnull=False
            ).first()
            
            if existing_log:
                self.stdout.write(self.style.WARNING(f'  ⊙ 跳过（已提取文本）'))
                return 'skipped'
        
        # 如果指定了清理旧日志，则删除该论文之前的所有日志
        if options['clean_old_logs']:
            old_logs_count = ArxivReferenceExtractLog.objects.filter(paper=paper).count()
            if old_logs_count > 0:
                ArxivReferenceExtractLog.objects.filter(paper=paper).delete()
                self.stdout.write(f'  🗑️  清理了 {old_logs_count} 条旧日志记录')
        
        # 检查重试次数
        retry_count = ArxivReferenceExtractLog.objects.filter(
            paper=paper
        ).count()
        
        if retry_count >= options['max_retries'] and not options['retry_failed']:
            self.stdout.write(self.style.WARNING(f'  ⊙ 跳过（超过最大重试次数）'))
            return 'skipped'
        
        # 创建提取日志
        log = ArxivReferenceExtractLog.objects.create(
            paper=paper,
            status='extracting',
            retry_count=retry_count
        )
        
        start_time = timezone.now()
        
        # 定义进度回调函数
        def progress_callback(step_name, details):
            """打印处理进度"""
            step_icons = {
                'downloading': '📥',
                'downloaded': '✅',
                'download_failed': '❌',
                'extracting_text': '📝',
                'text_extracted': '✅',
                'extraction_failed': '❌',
                'finding_references': '🔍',
                'references_found': '✅',
                'reference_not_found': '⚠️',
            }
            icon = step_icons.get(step_name, '•')
            self.stdout.write(f'  {icon} {details}')
        
        try:
            # 执行提取（只提取文本，不调用LLM）
            result = extractor.extract_reference_text_only(
                paper_id=paper.id,
                arxiv_id=arxiv_id,
                pdf_url=paper.pdf_url,
                progress_callback=progress_callback
            )
            
            # 更新日志
            log.pdf_downloaded = result['pdf_downloaded']
            log.pdf_file_path = result['pdf_path']
            log.pdf_file_size = result['pdf_size']
            log.text_extracted = result['text_extracted']
            log.reference_section_found = result['reference_section_found']
            
            if result['success']:
                log.status = 'completed'
                log.reference_raw_text = result['reference_text']
                log.reference_text_length = result['reference_text_length']
                log.completed_at = timezone.now()
                log.duration_seconds = (log.completed_at - start_time).seconds
                log.save()
                
                self.stdout.write(self.style.SUCCESS(
                    f'  ✓ 提取完成！参考文献文本长度: {result["reference_text_length"]} 字符，耗时 {log.duration_seconds} 秒'
                ))
                return 'success'
            else:
                log.status = 'failed'
                log.error_type = result['error_type']
                log.error_message = result['error_message']
                log.completed_at = timezone.now()
                log.duration_seconds = (log.completed_at - start_time).seconds
                log.save()
                
                self.stdout.write(self.style.ERROR(
                    f'  ✗ 提取失败: {result["error_type"]}'
                ))
                self.stdout.write(self.style.ERROR(
                    f'     错误详情: {result["error_message"][:200]}'
                ))
                return 'failed'
                
        except Exception as e:
            log.status = 'failed'
            log.error_type = 'unexpected_error'
            log.error_message = str(e)
            log.completed_at = timezone.now()
            log.duration_seconds = (log.completed_at - start_time).seconds
            log.save()
            
            self.stdout.write(self.style.ERROR(f'  ✗ 异常: {str(e)}'))
            logger.exception(f'处理论文 {arxiv_id} 时发生异常')
            return 'failed'
    
    def _process_log_with_llm(self, log, extractor, options):
        """处理单条提取记录（只使用LLM处理）"""
        paper = log.paper
        arxiv_id = paper.arxiv_id
        
        self.stdout.write(f'\n{"="*70}')
        self.stdout.write(f'处理论文: {arxiv_id}')
        self.stdout.write(f'标题: {paper.title[:60]}...')
        self.stdout.write(f'参考文献文本长度: {log.reference_text_length} 字符')
        self.stdout.write(f'{"="*70}')
        
        # 检查是否已经处理过
        if options['skip_processed'] and log.llm_processed:
            self.stdout.write(self.style.WARNING(f'  ⊙ 跳过（已LLM处理）'))
            return 'skipped'
        
        start_time = timezone.now()
        
        try:
            # 使用LLM处理参考文献文本
            self.stdout.write(f'  🤖 正在调用 {options["llm_provider"]}/{options["llm_model"]} 解析参考文献...')
            
            success, references, error, llm_response = extractor.process_reference_text_with_llm(
                reference_text=log.reference_raw_text,
                arxiv_id=arxiv_id,
                max_chars=options['max_chars']
            )
            
            # 保存LLM原始响应
            log.llm_response = llm_response
            
            if success:
                log.llm_processed = True
                log.reference_count = len(references)
                log.status = 'completed'
                
                # 保存参考文献到数据库
                self.stdout.write('  💾 正在保存参考文献到数据库...')
                self._save_references(paper, references, log)
                
                log.completed_at = timezone.now()
                log.duration_seconds = (log.completed_at - start_time).seconds
                log.save()
                
                self.stdout.write(self.style.SUCCESS(
                    f'  ✓ 处理完成！提取 {log.reference_count} 条参考文献，耗时 {log.duration_seconds} 秒'
                ))
                return 'success'
            else:
                log.llm_processed = False
                log.error_type = 'llm_error'
                log.error_message = error
                log.status = 'failed'
                log.completed_at = timezone.now()
                log.duration_seconds = (log.completed_at - start_time).seconds
                log.save()
                
                self.stdout.write(self.style.ERROR(
                    f'  ✗ LLM处理失败'
                ))
                self.stdout.write(self.style.ERROR(
                    f'     错误详情: {error[:200]}'
                ))
                return 'failed'
                
        except Exception as e:
            log.llm_processed = False
            log.error_type = 'unexpected_error'
            log.error_message = str(e)
            log.status = 'failed'
            log.completed_at = timezone.now()
            log.duration_seconds = (log.completed_at - start_time).seconds
            log.save()
            
            self.stdout.write(self.style.ERROR(f'  ✗ 异常: {str(e)}'))
            logger.exception(f'处理论文 {arxiv_id} 时发生异常')
            return 'failed'
    
    def _print_extract_final_stats(self, stats):
        """打印extract模式的最终统计信息"""
        # 计算已提取文本的记录数
        total_extracted = ArxivReferenceExtractLog.objects.filter(
            reference_section_found=True,
            reference_raw_text__isnull=False
        ).count()
        
        self.stdout.write(f'总论文数: {stats["total"]}')
        self.stdout.write(self.style.SUCCESS(f'成功: {stats["success"]}'))
        if stats['failed'] > 0:
            self.stdout.write(self.style.ERROR(f'失败: {stats["failed"]}'))
        if stats['skipped'] > 0:
            self.stdout.write(self.style.WARNING(f'跳过: {stats["skipped"]}'))
        self.stdout.write(f'数据库中已提取参考文献文本的记录数: {total_extracted}')
        
        # 成功率
        if stats['processed'] > 0:
            success_rate = (stats['success'] / stats['processed']) * 100
            self.stdout.write(f'成功率: {success_rate:.1f}%')
    
    def _print_process_final_stats(self, stats):
        """打印process模式的最终统计信息"""
        # 计算参考文献总数
        total_refs = ArxivPaperReference.objects.count()
        
        # 计算已LLM处理的记录数
        total_llm_processed = ArxivReferenceExtractLog.objects.filter(
            llm_processed=True
        ).count()
        
        self.stdout.write(f'总记录数: {stats["total"]}')
        self.stdout.write(self.style.SUCCESS(f'成功: {stats["success"]}'))
        if stats['failed'] > 0:
            self.stdout.write(self.style.ERROR(f'失败: {stats["failed"]}'))
        if stats['skipped'] > 0:
            self.stdout.write(self.style.WARNING(f'跳过: {stats["skipped"]}'))
        self.stdout.write(f'数据库中参考文献总数: {total_refs}')
        self.stdout.write(f'数据库中已LLM处理的记录数: {total_llm_processed}')
        
        # 成功率
        if stats['processed'] > 0:
            success_rate = (stats['success'] / stats['processed']) * 100
            self.stdout.write(f'成功率: {success_rate:.1f}%')

"""
Django管理命令：第一阶段 - 只提取参考文献原始文本
从ArXiv论文PDF中提取参考文献原始文本并存储到数据库，不调用LLM
"""
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone
from datetime import datetime, timedelta
import logging
import time

from core.arxiv_models import ArxivPaper, ArxivReferenceExtractLog
from core.arxiv_reference_extractor import ArxivReferenceExtractor


# 配置日志
logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = '第一阶段：从ArXiv论文PDF中提取参考文献原始文本（不调用LLM）'
    
    def add_arguments(self, parser):
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
            help='跳过已经提取过参考文献文本的论文'
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
            '--delay',
            type=float,
            default=0.5,
            help='每篇论文处理之间的延迟（秒）'
        )
    
    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('【第一阶段】开始提取ArXiv论文参考文献原始文本...'))
        
        # 初始化提取器
        try:
            extractor = ArxivReferenceExtractor(
                max_retries=options['max_retries']
            )
            self.stdout.write('提取器已初始化（无需LLM配置）')
        except Exception as e:
            raise CommandError(f'初始化提取器失败: {str(e)}')
        
        # 获取需要处理的论文
        papers = self._get_papers_to_process(options)
        
        if not papers:
            self.stdout.write(self.style.WARNING('没有找到需要处理的论文'))
            return
        
        total = len(papers)
        self.stdout.write(f'找到 {total} 篇论文待处理')
        
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
            batch = papers[i:i + batch_size]
            self.stdout.write(f'\n处理批次 {i // batch_size + 1} (论文 {i + 1}-{min(i + batch_size, total)})')
            
            for paper in batch:
                result = self._process_single_paper(paper, extractor, options)
                
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
        self.stdout.write(self.style.SUCCESS('【第一阶段】处理完成！'))
        self._print_final_stats(stats)
    
    def _get_papers_to_process(self, options):
        """获取需要处理的论文列表"""
        queryset = ArxivPaper.objects.all()
        
        # 如果指定了arxiv_id
        if options['arxiv_id']:
            queryset = queryset.filter(arxiv_id=options['arxiv_id'])
        
        # 如果跳过已处理的
        if options['skip_existing']:
            # 获取已经提取了参考文献文本的论文ID
            processed_ids = ArxivReferenceExtractLog.objects.filter(
                reference_section_found=True,
                reference_raw_text__isnull=False
            ).values_list('paper_id', flat=True)
            
            queryset = queryset.exclude(id__in=processed_ids)
        
        # 如果只重试失败的
        if options['retry_failed']:
            failed_ids = ArxivReferenceExtractLog.objects.filter(
                status='failed'
            ).values_list('paper_id', flat=True)
            
            queryset = queryset.filter(id__in=failed_ids)
        
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

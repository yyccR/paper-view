"""
Django管理命令：第二阶段 - 使用LLM处理已提取的参考文献文本
从数据库读取已提取的参考文献原始文本，使用LLM进行结构化处理
"""
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone
from datetime import datetime, timedelta
import logging
import time

from core.arxiv_models import ArxivPaper, ArxivPaperReference, ArxivReferenceExtractLog
from core.arxiv_reference_extractor import ArxivReferenceExtractor


# 配置日志
logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = '第二阶段：使用LLM处理已提取的参考文献原始文本'
    
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
            default=5,
            help='批量处理的大小（由于调用LLM，建议设置较小值）'
        )
        parser.add_argument(
            '--skip-processed',
            action='store_true',
            help='跳过已经LLM处理过的论文'
        )
        parser.add_argument(
            '--retry-failed',
            action='store_true',
            help='重试之前LLM处理失败的论文'
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
            default='qwen-max',
            help='LLM模型名称（默认: qwen-max）'
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
            default=2.0,
            help='每篇论文处理之间的延迟（秒）'
        )
        parser.add_argument(
            '--max-chars',
            type=int,
            default=50000,
            help='最大字符数限制（默认: 50000）'
        )
    
    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('【第二阶段】开始使用LLM处理参考文献...'))
        
        # 初始化提取器
        try:
            extractor = ArxivReferenceExtractor(
                llm_provider=options['llm_provider'],
                llm_model=options['llm_model'],
                llm_timeout=options['llm_timeout']
            )
            self.stdout.write(f'LLM配置: {options["llm_provider"]}/{options["llm_model"]} (超时: {options["llm_timeout"]}秒)')
        except Exception as e:
            raise CommandError(f'初始化提取器失败: {str(e)}')
        
        # 获取需要处理的记录
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
            'total_references': 0,
        }
        
        # 批量处理
        batch_size = options['batch_size']
        delay = options['delay']
        
        for i in range(0, total, batch_size):
            batch = logs[i:i + batch_size]
            self.stdout.write(f'\n处理批次 {i // batch_size + 1} (记录 {i + 1}-{min(i + batch_size, total)})')
            
            for log in batch:
                result = self._process_single_log(log, extractor, options)
                
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
        self._print_final_stats(stats)
    
    def _get_logs_to_process(self, options):
        """获取需要处理的提取日志列表"""
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
    
    def _process_single_log(self, log, extractor, options):
        """处理单条提取记录"""
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

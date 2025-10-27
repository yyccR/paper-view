"""
Django管理命令：从arXiv API获取CS领域论文
"""
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from datetime import datetime, date, timedelta
from loguru import logger

from core.arxiv_models import ArxivPaper, ArxivFetchLog
from core.arxiv_client import ArxivAPIClient


class Command(BaseCommand):
    help = '从arXiv API获取CS领域论文元数据（不下载PDF）'
    
    def add_arguments(self, parser):
        """添加命令行参数"""
        parser.add_argument(
            '--days',
            type=int,
            default=1,
            help='获取最近N天的论文（默认1天）'
        )
        
        parser.add_argument(
            '--start-date',
            type=str,
            help='开始日期，格式: YYYY-MM-DD'
        )
        
        parser.add_argument(
            '--end-date',
            type=str,
            help='结束日期，格式: YYYY-MM-DD'
        )
        
        parser.add_argument(
            '--category',
            type=str,
            default='cs.*',
            help='arXiv分类（默认cs.*表示所有CS分类）'
        )
        
        parser.add_argument(
            '--batch-size',
            type=int,
            default=1000,
            help='每批次获取的数量（默认1000，最大2000）'
        )
        
        parser.add_argument(
            '--max-total',
            type=int,
            help='最大获取总数（可选，用于测试）'
        )
        
        parser.add_argument(
            '--delay',
            type=float,
            default=3.0,
            help='请求之间的延迟秒数（默认3秒）'
        )
    
    def handle(self, *args, **options):
        """执行命令"""
        days = options['days']
        start_date_str = options.get('start_date')
        end_date_str = options.get('end_date')
        category = options['category']
        batch_size = options['batch_size']
        max_total = options.get('max_total')
        delay = options['delay']
        
        # 解析日期
        start_date = None
        end_date = None
        
        if start_date_str:
            try:
                start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            except ValueError:
                raise CommandError(f'无效的开始日期格式: {start_date_str}')
        
        if end_date_str:
            try:
                end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
            except ValueError:
                raise CommandError(f'无效的结束日期格式: {end_date_str}')
        
        # 如果没有指定日期范围，使用days参数
        if not start_date and not end_date:
            end_date = date.today()
            start_date = end_date - timedelta(days=days)
        
        self.stdout.write(
            self.style.SUCCESS(
                f'开始获取arXiv论文...\n'
                f'分类: {category}\n'
                f'日期范围: {start_date} 到 {end_date}\n'
                f'批次大小: {batch_size}\n'
                f'请求延迟: {delay}秒'
            )
        )
        
        # 创建获取日志
        fetch_log = ArxivFetchLog.objects.create(
            category=category,
            start_date=start_date,
            end_date=end_date,
            status='running'
        )
        
        start_time = timezone.now()
        
        try:
            # 初始化API客户端
            client = ArxivAPIClient(delay_seconds=delay)
            
            # 获取论文
            papers = client.fetch_all_cs_papers(
                start_date=start_date,
                end_date=end_date,
                batch_size=batch_size,
                max_total=max_total
            )
            
            # 保存到数据库
            new_count = 0
            updated_count = 0
            
            self.stdout.write(f'\n开始保存到数据库...')
            
            for paper_data in papers:
                saved, is_new = self._save_paper(paper_data)
                if saved:
                    if is_new:
                        new_count += 1
                    else:
                        updated_count += 1
                
                # 每100条显示一次进度
                if (new_count + updated_count) % 100 == 0:
                    self.stdout.write(f'已处理: {new_count + updated_count} 条')
            
            # 更新日志
            end_time = timezone.now()
            duration = (end_time - start_time).total_seconds()
            
            fetch_log.status = 'completed'
            fetch_log.total_results = len(papers)
            fetch_log.fetched_count = len(papers)
            fetch_log.new_papers = new_count
            fetch_log.updated_papers = updated_count
            fetch_log.completed_at = end_time
            fetch_log.duration_seconds = int(duration)
            fetch_log.save()
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'\n完成！\n'
                    f'总共获取: {len(papers)} 篇论文\n'
                    f'新增: {new_count} 篇\n'
                    f'更新: {updated_count} 篇\n'
                    f'耗时: {duration:.2f} 秒'
                )
            )
            
        except Exception as e:
            logger.error(f'获取失败: {e}', exc_info=True)
            
            # 更新日志
            fetch_log.status = 'failed'
            fetch_log.error_message = str(e)
            fetch_log.completed_at = timezone.now()
            fetch_log.save()
            
            raise CommandError(f'获取失败: {e}')
    
    def _save_paper(self, paper_data: dict) -> tuple:
        """保存论文到数据库
        
        Args:
            paper_data: 论文数据字典
            
        Returns:
            tuple: (是否保存成功, 是否新增)
        """
        try:
            arxiv_id = paper_data['arxiv_id']
            
            # 提取版本号
            version = 1
            if 'v' in arxiv_id:
                try:
                    version = int(arxiv_id.split('v')[-1])
                except ValueError:
                    pass
            
            # 查找或创建论文记录
            paper, created = ArxivPaper.objects.update_or_create(
                arxiv_id=arxiv_id,
                defaults={
                    'version': version,
                    'title': paper_data['title'],
                    'summary': paper_data['summary'],
                    'authors': paper_data['authors'],
                    'primary_category': paper_data['primary_category'],
                    'categories': paper_data['categories'],
                    'arxiv_url': paper_data['arxiv_url'],
                    'pdf_url': paper_data['pdf_url'],
                    'doi': paper_data.get('doi'),
                    'doi_url': paper_data.get('doi_url'),
                    'published': paper_data['published'],
                    'updated': paper_data['updated'],
                    'comment': paper_data.get('comment'),
                    'journal_ref': paper_data.get('journal_ref'),
                    'fetched_at': timezone.now(),
                }
            )
            
            return True, created
            
        except Exception as e:
            logger.error(f'保存论文失败 {paper_data.get("arxiv_id")}: {e}')
            return False, False

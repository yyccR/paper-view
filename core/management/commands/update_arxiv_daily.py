"""
Django管理命令：每日自动更新arXiv CS论文
适合通过crontab定时执行
"""
from django.core.management.base import BaseCommand
from django.core.management import call_command
from loguru import logger


class Command(BaseCommand):
    help = '每日自动更新arXiv CS论文（获取最近1天的论文）'
    
    def add_arguments(self, parser):
        """添加命令行参数"""
        parser.add_argument(
            '--days',
            type=int,
            default=1,
            help='获取最近N天的论文（默认1天）'
        )
        
        parser.add_argument(
            '--category',
            type=str,
            default='cs.*',
            help='arXiv分类（默认cs.*）'
        )
    
    def handle(self, *args, **options):
        """执行每日更新"""
        days = options['days']
        category = options['category']
        
        logger.info(f'开始每日arXiv更新任务，获取最近{days}天的{category}论文')
        self.stdout.write(
            self.style.SUCCESS(f'开始每日arXiv更新任务，获取最近{days}天的{category}论文')
        )
        
        try:
            # 调用fetch_arxiv_papers命令
            call_command(
                'fetch_arxiv_papers',
                days=days,
                category=category,
                batch_size=1000,
                delay=3.0
            )
            
            logger.info('每日更新任务完成')
            self.stdout.write(self.style.SUCCESS('每日更新任务完成'))
            
        except Exception as e:
            logger.error(f'每日更新任务失败: {e}', exc_info=True)
            self.stdout.write(self.style.ERROR(f'每日更新任务失败: {e}'))
            raise

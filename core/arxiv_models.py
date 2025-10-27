"""
ArXiv论文模型
用于存储从arXiv API获取的论文元数据
"""
from django.db import models
from django.utils import timezone


class ArxivPaper(models.Model):
    """ArXiv论文模型
    
    存储从arXiv API获取的所有论文元数据（不包括PDF文件）
    """
    # 主键
    id = models.AutoField(
        primary_key=True,
        verbose_name='主键ID',
        help_text='自增主键'
    )
    
    # 基本标识信息
    arxiv_id = models.CharField(
        max_length=50, 
        unique=True, 
        db_index=True,
        verbose_name='arXiv ID',
        help_text='论文的arXiv标识符，如2301.12345'
    )
    version = models.IntegerField(
        default=1,
        verbose_name='版本号',
        help_text='论文版本号'
    )
    
    # 基本信息（从API可获取）
    title = models.TextField(
        verbose_name='标题',
        help_text='论文标题'
    )
    summary = models.TextField(
        verbose_name='摘要',
        help_text='论文摘要/简介'
    )
    
    # 作者信息（从API可获取）
    authors = models.JSONField(
        verbose_name='作者列表',
        help_text='作者姓名和机构信息的JSON列表，格式: [{"name": "作者名", "affiliation": "机构"}]'
    )
    
    # 分类信息（从API可获取）
    primary_category = models.CharField(
        max_length=50,
        db_index=True,
        verbose_name='主要分类',
        help_text='论文的主要arXiv分类，如cs.AI'
    )
    categories = models.JSONField(
        verbose_name='所有分类',
        help_text='论文的所有分类列表'
    )
    
    # 链接信息（从API可获取）
    arxiv_url = models.URLField(
        max_length=500,
        verbose_name='arXiv链接',
        help_text='论文的arXiv页面URL'
    )
    pdf_url = models.URLField(
        max_length=500,
        verbose_name='PDF链接',
        help_text='论文PDF的下载URL'
    )
    doi = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        verbose_name='DOI',
        help_text='论文的DOI标识符'
    )
    doi_url = models.URLField(
        max_length=500,
        blank=True,
        null=True,
        verbose_name='DOI链接',
        help_text='DOI解析后的URL'
    )
    
    # 时间信息（从API可获取）
    published = models.DateTimeField(
        db_index=True,
        verbose_name='首次发布时间',
        help_text='论文v1版本的提交时间'
    )
    updated = models.DateTimeField(
        db_index=True,
        verbose_name='更新时间',
        help_text='当前版本的提交时间'
    )
    
    # 附加信息（从API可获取）
    comment = models.TextField(
        blank=True,
        null=True,
        verbose_name='作者评论',
        help_text='作者添加的评论信息'
    )
    journal_ref = models.CharField(
        max_length=500,
        blank=True,
        null=True,
        verbose_name='期刊引用',
        help_text='论文的期刊引用信息'
    )
    
    # 本地管理字段
    fetched_at = models.DateTimeField(
        default=timezone.now,
        verbose_name='获取时间',
        help_text='从API获取数据的时间'
    )
    is_processed = models.BooleanField(
        default=False,
        db_index=True,
        verbose_name='是否已处理',
        help_text='是否已进行后续处理（如AI摘要生成）'
    )
    processing_status = models.CharField(
        max_length=20,
        default='pending',
        choices=[
            ('pending', '待处理'),
            ('processing', '处理中'),
            ('completed', '已完成'),
            ('failed', '失败'),
        ],
        verbose_name='处理状态'
    )
    processing_error = models.TextField(
        blank=True,
        null=True,
        verbose_name='处理错误信息'
    )
    
    class Meta:
        db_table = 'arxiv_paper'
        verbose_name = 'ArXiv论文'
        verbose_name_plural = 'ArXiv论文'
        ordering = ['-published']
        indexes = [
            models.Index(fields=['-published']),
            models.Index(fields=['primary_category', '-published']),
            models.Index(fields=['is_processed', 'processing_status']),
        ]
    
    def __str__(self):
        return f"{self.arxiv_id} - {self.title[:50]}"
    
    @property
    def short_id(self):
        """返回不带版本号的arXiv ID"""
        return self.arxiv_id.split('v')[0] if 'v' in self.arxiv_id else self.arxiv_id
    
    @property
    def author_names(self):
        """返回作者名字列表"""
        if isinstance(self.authors, list):
            return [author.get('name', '') for author in self.authors]
        return []
    
    @property
    def is_cs_paper(self):
        """判断是否为CS领域论文"""
        return self.primary_category.startswith('cs.')


class ArxivFetchLog(models.Model):
    """ArXiv数据获取日志
    
    记录每次从arXiv API获取数据的情况
    """
    # 主键
    id = models.AutoField(
        primary_key=True,
        verbose_name='主键ID',
        help_text='自增主键'
    )
    
    category = models.CharField(
        max_length=50,
        verbose_name='分类',
        help_text='获取的arXiv分类，如cs.AI或cs.*'
    )
    start_date = models.DateField(
        null=True,
        blank=True,
        verbose_name='开始日期',
        help_text='查询的开始日期'
    )
    end_date = models.DateField(
        null=True,
        blank=True,
        verbose_name='结束日期',
        help_text='查询的结束日期'
    )
    total_results = models.IntegerField(
        default=0,
        verbose_name='总结果数',
        help_text='API返回的总结果数'
    )
    fetched_count = models.IntegerField(
        default=0,
        verbose_name='实际获取数',
        help_text='实际获取并保存的论文数'
    )
    new_papers = models.IntegerField(
        default=0,
        verbose_name='新增论文数',
        help_text='新增的论文数（不包括更新）'
    )
    updated_papers = models.IntegerField(
        default=0,
        verbose_name='更新论文数',
        help_text='更新的论文数'
    )
    status = models.CharField(
        max_length=20,
        default='running',
        choices=[
            ('running', '运行中'),
            ('completed', '完成'),
            ('failed', '失败'),
        ],
        verbose_name='状态'
    )
    error_message = models.TextField(
        blank=True,
        null=True,
        verbose_name='错误信息'
    )
    started_at = models.DateTimeField(
        default=timezone.now,
        verbose_name='开始时间'
    )
    completed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='完成时间'
    )
    duration_seconds = models.IntegerField(
        null=True,
        blank=True,
        verbose_name='耗时（秒）'
    )
    
    class Meta:
        db_table = 'arxiv_fetch_log'
        verbose_name = 'ArXiv获取日志'
        verbose_name_plural = 'ArXiv获取日志'
        ordering = ['-started_at']
    
    def __str__(self):
        return f"{self.category} - {self.started_at.strftime('%Y-%m-%d %H:%M')} - {self.status}"


class ArxivPaperReference(models.Model):
    """ArXiv论文参考文献模型
    
    存储从论文PDF中提取的参考文献信息
    """
    # 主键
    id = models.AutoField(
        primary_key=True,
        verbose_name='主键ID',
        help_text='自增主键'
    )
    
    # 关联的论文
    paper = models.ForeignKey(
        ArxivPaper,
        on_delete=models.CASCADE,
        related_name='references',
        verbose_name='所属论文',
        help_text='该参考文献所属的论文',
        db_index=True
    )
    
    # 参考文献在原文中的序号
    reference_number = models.IntegerField(
        verbose_name='序号',
        help_text='参考文献在原文中的序号',
        db_index=True
    )
    
    # 参考文献基本信息
    title = models.TextField(
        blank=True,
        null=True,
        verbose_name='标题',
        help_text='参考文献的标题'
    )
    
    authors = models.JSONField(
        blank=True,
        null=True,
        verbose_name='作者列表',
        help_text='作者姓名列表，格式: ["Author1", "Author2", ...]'
    )
    
    year = models.IntegerField(
        blank=True,
        null=True,
        verbose_name='发表年份',
        help_text='参考文献的发表年份',
        db_index=True
    )
    
    # 出版信息
    venue = models.CharField(
        max_length=500,
        blank=True,
        null=True,
        verbose_name='发表场所',
        help_text='期刊、会议或其他出版场所'
    )
    
    venue_type = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        choices=[
            ('journal', '期刊'),
            ('conference', '会议'),
            ('arxiv', 'arXiv预印本'),
            ('book', '书籍'),
            ('thesis', '学位论文'),
            ('tech_report', '技术报告'),
            ('other', '其他'),
        ],
        verbose_name='场所类型',
        help_text='发表场所的类型'
    )
    
    volume = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name='卷号',
        help_text='期刊或会议的卷号'
    )
    
    issue = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name='期号',
        help_text='期刊的期号'
    )
    
    pages = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name='页码',
        help_text='参考文献的页码范围'
    )
    
    # 标识符
    doi = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        verbose_name='DOI',
        help_text='参考文献的DOI标识符',
        db_index=True
    )
    
    arxiv_id = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name='arXiv ID',
        help_text='如果是arXiv论文，其arXiv标识符',
        db_index=True
    )
    
    url = models.URLField(
        max_length=500,
        blank=True,
        null=True,
        verbose_name='URL',
        help_text='参考文献的在线链接'
    )
    
    # 原始信息
    raw_text = models.TextField(
        verbose_name='原始文本',
        help_text='参考文献的原始文本（从PDF提取）'
    )
    
    # 元数据
    extracted_at = models.DateTimeField(
        default=timezone.now,
        verbose_name='提取时间',
        help_text='从PDF提取的时间'
    )
    
    extraction_method = models.CharField(
        max_length=50,
        default='llm',
        verbose_name='提取方法',
        help_text='提取方法（如llm、regex等）'
    )
    
    confidence_score = models.FloatField(
        blank=True,
        null=True,
        verbose_name='置信度',
        help_text='提取结果的置信度分数（0-1）'
    )
    
    class Meta:
        db_table = 'arxiv_paper_reference'
        verbose_name = 'ArXiv论文参考文献'
        verbose_name_plural = 'ArXiv论文参考文献'
        ordering = ['paper', 'reference_number']
        unique_together = [['paper', 'reference_number']]
        indexes = [
            models.Index(fields=['paper', 'reference_number']),
            models.Index(fields=['year']),
            models.Index(fields=['doi']),
            models.Index(fields=['arxiv_id']),
        ]
    
    def __str__(self):
        return f"{self.paper.arxiv_id} - Ref #{self.reference_number}"
    
    @property
    def author_names_str(self):
        """返回作者名字的字符串表示"""
        if isinstance(self.authors, list) and self.authors:
            return ', '.join(self.authors[:3]) + (' et al.' if len(self.authors) > 3 else '')
        return 'Unknown'


class ArxivReferenceExtractLog(models.Model):
    """ArXiv参考文献提取日志
    
    记录每次从论文PDF提取参考文献的处理情况
    """
    # 主键
    id = models.AutoField(
        primary_key=True,
        verbose_name='主键ID',
        help_text='自增主键'
    )
    
    # 关联的论文
    paper = models.ForeignKey(
        ArxivPaper,
        on_delete=models.CASCADE,
        related_name='extract_logs',
        verbose_name='论文',
        help_text='处理的论文',
        db_index=True
    )
    
    # 处理状态
    status = models.CharField(
        max_length=20,
        default='pending',
        choices=[
            ('pending', '待处理'),
            ('downloading', '下载中'),
            ('extracting', '提取中'),
            ('processing', 'LLM处理中'),
            ('completed', '已完成'),
            ('failed', '失败'),
            ('skipped', '跳过'),
        ],
        verbose_name='状态',
        db_index=True
    )
    
    # 处理结果
    reference_count = models.IntegerField(
        default=0,
        verbose_name='参考文献数量',
        help_text='成功提取的参考文献数量'
    )
    
    pdf_downloaded = models.BooleanField(
        default=False,
        verbose_name='PDF已下载',
        help_text='是否成功下载PDF'
    )
    
    pdf_file_path = models.CharField(
        max_length=500,
        blank=True,
        null=True,
        verbose_name='PDF文件路径',
        help_text='下载的PDF文件路径'
    )
    
    pdf_file_size = models.IntegerField(
        blank=True,
        null=True,
        verbose_name='PDF文件大小',
        help_text='PDF文件大小（字节）'
    )
    
    text_extracted = models.BooleanField(
        default=False,
        verbose_name='文本已提取',
        help_text='是否成功从PDF提取文本'
    )
    
    reference_section_found = models.BooleanField(
        default=False,
        verbose_name='找到参考文献部分',
        help_text='是否找到参考文献部分'
    )
    
    reference_raw_text = models.TextField(
        blank=True,
        null=True,
        verbose_name='参考文献原始文本',
        help_text='从PDF中提取的参考文献部分的原始文本'
    )
    
    reference_text_length = models.IntegerField(
        blank=True,
        null=True,
        verbose_name='参考文献文本长度',
        help_text='参考文献原始文本的字符数'
    )
    
    llm_processed = models.BooleanField(
        default=False,
        verbose_name='LLM已处理',
        help_text='是否成功通过LLM处理'
    )
    
    # 错误信息
    error_message = models.TextField(
        blank=True,
        null=True,
        verbose_name='错误信息',
        help_text='处理失败时的错误信息'
    )
    
    error_type = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name='错误类型',
        help_text='错误类型（如download_error、extraction_error、llm_error等）'
    )
    
    # 处理详情
    processing_details = models.JSONField(
        blank=True,
        null=True,
        verbose_name='处理详情',
        help_text='处理过程中的详细信息（JSON格式）'
    )
    
    llm_response = models.TextField(
        blank=True,
        null=True,
        verbose_name='LLM原始响应',
        help_text='LLM返回的原始响应内容（用于调试）'
    )
    
    # 时间信息
    started_at = models.DateTimeField(
        default=timezone.now,
        verbose_name='开始时间'
    )
    
    completed_at = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name='完成时间'
    )
    
    duration_seconds = models.IntegerField(
        blank=True,
        null=True,
        verbose_name='耗时（秒）',
        help_text='处理耗时'
    )
    
    # 重试信息
    retry_count = models.IntegerField(
        default=0,
        verbose_name='重试次数',
        help_text='处理失败后的重试次数'
    )
    
    class Meta:
        db_table = 'arxiv_reference_extract_log'
        verbose_name = 'ArXiv参考文献提取日志'
        verbose_name_plural = 'ArXiv参考文献提取日志'
        ordering = ['-started_at']
        indexes = [
            models.Index(fields=['paper', '-started_at']),
            models.Index(fields=['status']),
            models.Index(fields=['-started_at']),
        ]
    
    def __str__(self):
        return f"{self.paper.arxiv_id} - {self.status} - {self.started_at.strftime('%Y-%m-%d %H:%M')}"

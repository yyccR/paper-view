from django.db import models
from django.contrib.auth.models import User

# Create your models here.

class AIModelConfig(models.Model):
    """AI模型配置"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name='ai_configs')
    session_id = models.CharField(max_length=255, null=True, blank=True, db_index=True, help_text='匿名用户会话ID')
    
    # 模型提供商
    provider = models.CharField(max_length=50, help_text='模型提供商: gpt, claude, qwen, doubao, gemini')
    # 具体模型
    model_name = models.CharField(max_length=100, help_text='具体模型名称: gpt-4o, claude-3-5-sonnet等')
    # API配置
    api_key = models.CharField(max_length=500, blank=True, help_text='API密钥')
    api_base = models.CharField(max_length=500, blank=True, help_text='API基础URL')
    
    # 是否为当前选中的模型
    is_active = models.BooleanField(default=True, help_text='是否为当前激活的模型')
    
    # 时间戳
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'ai_model_config'
        ordering = ['-updated_at']
        indexes = [
            models.Index(fields=['user', 'is_active']),
            models.Index(fields=['session_id', 'is_active']),
        ]
    
    def __str__(self):
        return f'{self.provider} - {self.model_name}'


class ChatSession(models.Model):
    """聊天会话"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name='chat_sessions')
    session_id = models.CharField(max_length=255, null=True, blank=True, db_index=True, help_text='匿名用户会话ID')
    
    # 会话信息
    title = models.CharField(max_length=500, help_text='会话标题（文章标题或自定义）')
    paper_title = models.CharField(max_length=1000, blank=True, help_text='关联的论文标题')
    paper_url = models.URLField(blank=True, help_text='论文URL')
    
    # 会话类型
    session_type = models.CharField(
        max_length=20, 
        choices=[
            ('translate', '翻译'),
            ('chat', '对话'),
            ('mixed', '混合')
        ],
        default='mixed',
        help_text='会话类型'
    )
    
    # 使用的AI模型信息
    ai_provider = models.CharField(max_length=50, blank=True, help_text='使用的AI提供商')
    ai_model = models.CharField(max_length=100, blank=True, help_text='使用的AI模型')
    
    # 上下文信息
    context_text = models.TextField(blank=True, help_text='选中的上下文文本')
    
    # 统计信息
    message_count = models.IntegerField(default=0, help_text='消息数量')
    last_message_at = models.DateTimeField(null=True, blank=True, help_text='最后消息时间')
    
    # 状态
    is_active = models.BooleanField(default=True, help_text='是否活跃')
    is_pinned = models.BooleanField(default=False, help_text='是否置顶')
    
    # 时间戳
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'chat_session'
        ordering = ['-last_message_at', '-created_at']
        indexes = [
            models.Index(fields=['user', 'is_active']),
            models.Index(fields=['session_id', 'is_active']),
            models.Index(fields=['-last_message_at']),
        ]
    
    def __str__(self):
        return self.title


class ChatMessage(models.Model):
    """聊天消息"""
    session = models.ForeignKey(ChatSession, on_delete=models.CASCADE, related_name='messages')
    
    # 消息角色
    role = models.CharField(
        max_length=20,
        choices=[
            ('user', '用户'),
            ('assistant', 'AI助手'),
            ('system', '系统')
        ],
        help_text='消息角色'
    )
    
    # 消息内容
    content = models.TextField(help_text='消息内容')
    
    # 消息元数据
    metadata = models.JSONField(default=dict, blank=True, help_text='消息元数据（如token数、耗时等）')
    
    # 时间戳
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'chat_message'
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['session', 'created_at']),
        ]
    
    def __str__(self):
        return f'{self.role}: {self.content[:50]}...'

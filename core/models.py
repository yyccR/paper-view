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

"""
LLM 配置管理模块
集中管理所有 LLM 提供商的配置信息
"""
import os
from typing import Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class LLMProviderConfig:
    """LLM 提供商配置"""
    provider: str
    api_key: str
    base_url: Optional[str] = None
    model: Optional[str] = None
    max_tokens: int = 4096
    temperature: float = 0.7
    timeout: int = 60
    extra_params: Optional[Dict[str, Any]] = None


class LLMConfig:
    """LLM 配置管理类"""
    
    # 各个提供商的默认配置
    PROVIDER_CONFIGS = {
        'openai': {
            'base_url': 'https://api.openai.com/v1',
            'default_model': 'gpt-4o-mini',
            'use_openai_lib': True,
        },
        'deepseek': {
            'base_url': 'https://api.deepseek.com/v1',
            'default_model': 'deepseek-chat',
            'use_openai_lib': True,
        },
        'anthropic': {
            'base_url': 'https://api.anthropic.com/v1',
            'default_model': 'claude-3-5-sonnet-20241022',
            'use_openai_lib': False,  # Anthropic 有自己的库
        },
        'qwen': {
            'base_url': 'https://dashscope.aliyuncs.com/compatible-mode/v1',
            'default_model': 'qwen-plus',
            'use_openai_lib': True,
        },
        'moonshot': {
            'base_url': 'https://api.moonshot.cn/v1',
            'default_model': 'moonshot-v1-8k',
            'use_openai_lib': True,
        },
        'zhipu': {
            'base_url': 'https://open.bigmodel.cn/api/paas/v4',
            'default_model': 'glm-4',
            'use_openai_lib': True,
        },
        'doubao': {
            'base_url': 'https://ark.cn-beijing.volces.com/api/v3',
            'default_model': 'doubao-pro-32k',
            'use_openai_lib': True,
        },
    }
    
    @classmethod
    def get_provider_config(cls, provider: str) -> Dict[str, Any]:
        """获取提供商的默认配置"""
        provider = provider.lower()
        if provider not in cls.PROVIDER_CONFIGS:
            raise ValueError(f"不支持的 LLM 提供商: {provider}")
        return cls.PROVIDER_CONFIGS[provider].copy()
    
    @classmethod
    def from_env(cls, provider: str, model: Optional[str] = None) -> LLMProviderConfig:
        """从环境变量创建配置"""
        provider = provider.lower()
        config = cls.get_provider_config(provider)
        
        # 从环境变量获取 API Key
        api_key_env = f"{provider.upper()}_API_KEY"
        api_key = os.getenv(api_key_env)
        
        if not api_key:
            raise ValueError(f"未找到 {api_key_env} 环境变量")
        
        # 允许通过环境变量覆盖 base_url
        base_url_env = f"{provider.upper()}_BASE_URL"
        base_url = os.getenv(base_url_env, config['base_url'])
        
        # 使用指定的模型或默认模型
        model = model or os.getenv(f"{provider.upper()}_MODEL", config['default_model'])
        
        # 其他可选配置
        max_tokens = int(os.getenv(f"{provider.upper()}_MAX_TOKENS", "4096"))
        temperature = float(os.getenv(f"{provider.upper()}_TEMPERATURE", "0.7"))
        timeout = int(os.getenv(f"{provider.upper()}_TIMEOUT", "60"))
        
        return LLMProviderConfig(
            provider=provider,
            api_key=api_key,
            base_url=base_url,
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
            timeout=timeout,
        )
    
    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> LLMProviderConfig:
        """从字典创建配置"""
        provider = config_dict.get('provider', '').lower()
        if not provider:
            raise ValueError("配置中必须指定 provider")
        
        default_config = cls.get_provider_config(provider)
        
        return LLMProviderConfig(
            provider=provider,
            api_key=config_dict['api_key'],
            base_url=config_dict.get('base_url', default_config['base_url']),
            model=config_dict.get('model', default_config['default_model']),
            max_tokens=config_dict.get('max_tokens', 4096),
            temperature=config_dict.get('temperature', 0.7),
            timeout=config_dict.get('timeout', 60),
            extra_params=config_dict.get('extra_params'),
        )
    
    @classmethod
    def get_supported_providers(cls) -> list[str]:
        """获取支持的提供商列表"""
        return list(cls.PROVIDER_CONFIGS.keys())
    
    @classmethod
    def uses_openai_lib(cls, provider: str) -> bool:
        """判断提供商是否使用 OpenAI 库"""
        provider = provider.lower()
        config = cls.get_provider_config(provider)
        return config.get('use_openai_lib', True)

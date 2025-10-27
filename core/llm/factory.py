"""
LLM 工厂类
提供统一的客户端创建接口
"""
from typing import Optional, Dict, Any
from .base import BaseLLMClient
from .config import LLMConfig, LLMProviderConfig
from .openai_client import OpenAIClient
from .anthropic_client import AnthropicClient


class LLMFactory:
    """LLM 客户端工厂类"""
    
    # 注册的客户端类映射
    _CLIENT_REGISTRY = {
        'openai': OpenAIClient,
        'deepseek': OpenAIClient,
        'qwen': OpenAIClient,
        'moonshot': OpenAIClient,
        'zhipu': OpenAIClient,
        'doubao': OpenAIClient,
        'anthropic': AnthropicClient,
    }
    
    @classmethod
    def create(
        cls,
        provider: str,
        model: Optional[str] = None,
        config: Optional[LLMProviderConfig] = None,
        **kwargs
    ) -> BaseLLMClient:
        """
        创建 LLM 客户端
        
        Args:
            provider: LLM 提供商名称 (openai, deepseek, anthropic, qwen 等)
            model: 模型名称（可选，不指定则使用默认模型）
            config: LLM 配置对象（可选，不指定则从环境变量读取）
            **kwargs: 额外的配置参数
            
        Returns:
            LLM 客户端实例
            
        Raises:
            ValueError: 不支持的提供商
            
        Examples:
            # 从环境变量创建
            client = LLMFactory.create('openai')
            
            # 指定模型
            client = LLMFactory.create('openai', model='gpt-4')
            
            # 使用自定义配置
            config = LLMConfig.from_dict({
                'provider': 'deepseek',
                'api_key': 'sk-xxx',
                'model': 'deepseek-chat'
            })
            client = LLMFactory.create('deepseek', config=config)
        """
        provider = provider.lower()
        
        # 检查是否支持该提供商
        if provider not in cls._CLIENT_REGISTRY:
            supported = ', '.join(cls.get_supported_providers())
            raise ValueError(
                f"不支持的 LLM 提供商: {provider}。"
                f"支持的提供商: {supported}"
            )
        
        # 如果没有提供配置，从环境变量创建
        if config is None:
            config = LLMConfig.from_env(provider, model)
        
        # 获取对应的客户端类
        client_class = cls._CLIENT_REGISTRY[provider]
        
        # 创建并返回客户端实例
        return client_class(config)
    
    @classmethod
    def create_from_dict(cls, config_dict: Dict[str, Any]) -> BaseLLMClient:
        """
        从字典配置创建客户端
        
        Args:
            config_dict: 配置字典，必须包含 provider 和 api_key
            
        Returns:
            LLM 客户端实例
            
        Example:
            config = {
                'provider': 'openai',
                'api_key': 'sk-xxx',
                'model': 'gpt-4',
                'temperature': 0.8,
            }
            client = LLMFactory.create_from_dict(config)
        """
        config = LLMConfig.from_dict(config_dict)
        provider = config_dict['provider']
        return cls.create(provider, config=config)
    
    @classmethod
    def register_client(cls, provider: str, client_class: type):
        """
        注册新的客户端类
        
        Args:
            provider: 提供商名称
            client_class: 客户端类（必须继承 BaseLLMClient）
        """
        if not issubclass(client_class, BaseLLMClient):
            raise TypeError(f"{client_class} 必须继承 BaseLLMClient")
        
        cls._CLIENT_REGISTRY[provider.lower()] = client_class
    
    @classmethod
    def get_supported_providers(cls) -> list[str]:
        """获取支持的提供商列表"""
        return list(cls._CLIENT_REGISTRY.keys())
    
    @classmethod
    def is_supported(cls, provider: str) -> bool:
        """检查是否支持指定的提供商"""
        return provider.lower() in cls._CLIENT_REGISTRY

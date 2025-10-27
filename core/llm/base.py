"""
LLM 客户端抽象基类
定义统一的调用接口
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Generator, Union
from .config import LLMProviderConfig


class BaseLLMClient(ABC):
    """LLM 客户端抽象基类"""
    
    def __init__(self, config: LLMProviderConfig):
        """
        初始化 LLM 客户端
        
        Args:
            config: LLM 提供商配置
        """
        self.config = config
        self.provider = config.provider
        self.model = config.model
        self._client = None
    
    @abstractmethod
    def _initialize_client(self):
        """初始化客户端实例（子类实现）"""
        pass
    
    @abstractmethod
    def chat_completion(
        self,
        messages: List[Dict[str, str]],
        **kwargs
    ) -> Dict[str, Any]:
        """
        同步聊天补全
        
        Args:
            messages: 消息列表，格式: [{"role": "user", "content": "..."}]
            **kwargs: 额外参数（temperature, max_tokens 等）
            
        Returns:
            包含响应内容的字典
        """
        pass
    
    @abstractmethod
    def chat_completion_stream(
        self,
        messages: List[Dict[str, str]],
        **kwargs
    ) -> Generator[Dict[str, Any], None, None]:
        """
        流式聊天补全
        
        Args:
            messages: 消息列表
            **kwargs: 额外参数
            
        Yields:
            响应片段字典
        """
        pass
    
    def _merge_params(self, **kwargs) -> Dict[str, Any]:
        """合并配置参数和调用参数"""
        params = {
            'model': self.model,
            'temperature': self.config.temperature,
            'max_tokens': self.config.max_tokens,
        }
        
        # 如果有额外参数，合并进去
        if self.config.extra_params:
            params.update(self.config.extra_params)
        
        # 调用时传入的参数优先级最高
        params.update(kwargs)
        
        return params
    
    def simple_chat(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        **kwargs
    ) -> str:
        """
        简单的单轮对话
        
        Args:
            prompt: 用户提示
            system_prompt: 系统提示（可选）
            **kwargs: 额外参数
            
        Returns:
            AI 回复的文本内容
        """
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        response = self.chat_completion(messages, **kwargs)
        return response.get('content', '')
    
    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} provider={self.provider} model={self.model}>"

"""
基于 OpenAI 库的 LLM 客户端实现
支持 OpenAI 及兼容 OpenAI API 的提供商
"""
from typing import List, Dict, Any, Generator
from openai import OpenAI
from .base import BaseLLMClient
from .config import LLMProviderConfig


class OpenAIClient(BaseLLMClient):
    """
    OpenAI 客户端
    支持所有兼容 OpenAI API 格式的提供商：
    - OpenAI
    - DeepSeek
    - Qwen (通义千问)
    - Moonshot (月之暗面)
    - Zhipu (智谱)
    - Doubao (豆包)
    等
    """
    
    def __init__(self, config: LLMProviderConfig):
        super().__init__(config)
        self._initialize_client()
    
    def _initialize_client(self):
        """初始化 OpenAI 客户端"""
        self._client = OpenAI(
            api_key=self.config.api_key,
            base_url=self.config.base_url,
            timeout=self.config.timeout,
        )
    
    def chat_completion(
        self,
        messages: List[Dict[str, str]],
        **kwargs
    ) -> Dict[str, Any]:
        """
        同步聊天补全
        
        Args:
            messages: 消息列表
            **kwargs: 额外参数
            
        Returns:
            响应字典，格式:
            {
                'content': '回复内容',
                'role': 'assistant',
                'model': '模型名称',
                'usage': {...},
                'finish_reason': 'stop'
            }
        """
        params = self._merge_params(**kwargs)
        
        try:
            response = self._client.chat.completions.create(
                messages=messages,
                **params
            )
            
            message = response.choices[0].message
            
            return {
                'content': message.content,
                'role': message.role,
                'model': response.model,
                'usage': {
                    'prompt_tokens': response.usage.prompt_tokens,
                    'completion_tokens': response.usage.completion_tokens,
                    'total_tokens': response.usage.total_tokens,
                },
                'finish_reason': response.choices[0].finish_reason,
            }
        except Exception as e:
            raise RuntimeError(f"调用 {self.provider} API 失败: {str(e)}") from e
    
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
            响应片段字典，格式:
            {
                'content': '内容片段',
                'role': 'assistant',
                'finish_reason': None or 'stop'
            }
        """
        params = self._merge_params(**kwargs)
        params['stream'] = True
        
        try:
            stream = self._client.chat.completions.create(
                messages=messages,
                **params
            )
            
            for chunk in stream:
                if chunk.choices and len(chunk.choices) > 0:
                    delta = chunk.choices[0].delta
                    finish_reason = chunk.choices[0].finish_reason
                    
                    if delta.content:
                        yield {
                            'content': delta.content,
                            'role': delta.role or 'assistant',
                            'finish_reason': finish_reason,
                        }
                    
                    # 流结束
                    if finish_reason:
                        break
                        
        except Exception as e:
            raise RuntimeError(f"调用 {self.provider} 流式 API 失败: {str(e)}") from e

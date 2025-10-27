"""
Anthropic Claude 客户端实现
"""
from typing import List, Dict, Any, Generator, Optional
from .base import BaseLLMClient
from .config import LLMProviderConfig


class AnthropicClient(BaseLLMClient):
    """
    Anthropic Claude 客户端
    使用官方的 anthropic 库
    """
    
    def __init__(self, config: LLMProviderConfig):
        super().__init__(config)
        self._initialize_client()
    
    def _initialize_client(self):
        """初始化 Anthropic 客户端"""
        try:
            from anthropic import Anthropic
            self._client = Anthropic(
                api_key=self.config.api_key,
                base_url=self.config.base_url,
                timeout=self.config.timeout,
            )
        except ImportError:
            raise ImportError(
                "使用 Anthropic 需要安装 anthropic 库: pip install anthropic"
            )
    
    def _convert_messages(
        self, 
        messages: List[Dict[str, str]]
    ) -> tuple[Optional[str], List[Dict[str, str]]]:
        """
        转换消息格式，提取 system 消息
        Anthropic API 的 system 消息需要单独传递
        """
        system_prompt = None
        converted_messages = []
        
        for msg in messages:
            if msg['role'] == 'system':
                system_prompt = msg['content']
            else:
                converted_messages.append(msg)
        
        return system_prompt, converted_messages
    
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
            响应字典
        """
        params = self._merge_params(**kwargs)
        
        # 移除 max_tokens 并用 Anthropic 的参数名
        max_tokens = params.pop('max_tokens', 4096)
        
        system_prompt, converted_messages = self._convert_messages(messages)
        
        try:
            kwargs_for_api = {
                'model': params['model'],
                'messages': converted_messages,
                'max_tokens': max_tokens,
            }
            
            # 添加 system prompt
            if system_prompt:
                kwargs_for_api['system'] = system_prompt
            
            # 添加其他参数
            if 'temperature' in params:
                kwargs_for_api['temperature'] = params['temperature']
            
            response = self._client.messages.create(**kwargs_for_api)
            
            return {
                'content': response.content[0].text,
                'role': response.role,
                'model': response.model,
                'usage': {
                    'prompt_tokens': response.usage.input_tokens,
                    'completion_tokens': response.usage.output_tokens,
                    'total_tokens': response.usage.input_tokens + response.usage.output_tokens,
                },
                'finish_reason': response.stop_reason,
            }
        except Exception as e:
            raise RuntimeError(f"调用 Anthropic API 失败: {str(e)}") from e
    
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
        params = self._merge_params(**kwargs)
        max_tokens = params.pop('max_tokens', 4096)
        
        system_prompt, converted_messages = self._convert_messages(messages)
        
        try:
            kwargs_for_api = {
                'model': params['model'],
                'messages': converted_messages,
                'max_tokens': max_tokens,
            }
            
            if system_prompt:
                kwargs_for_api['system'] = system_prompt
            
            if 'temperature' in params:
                kwargs_for_api['temperature'] = params['temperature']
            
            with self._client.messages.stream(**kwargs_for_api) as stream:
                for text in stream.text_stream:
                    yield {
                        'content': text,
                        'role': 'assistant',
                        'finish_reason': None,
                    }
                
                # 流结束
                yield {
                    'content': '',
                    'role': 'assistant',
                    'finish_reason': 'stop',
                }
                
        except Exception as e:
            raise RuntimeError(f"调用 Anthropic 流式 API 失败: {str(e)}") from e

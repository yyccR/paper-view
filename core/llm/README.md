# LLM 客户端模块

这是一个统一的 LLM 调用接口模块，支持多个 LLM 提供商，使用工厂设计模式，配置集中管理。

## 特性

- 🏭 **工厂模式**: 统一的客户端创建接口
- 🔌 **多提供商支持**: OpenAI, DeepSeek, Claude, Qwen, Moonshot, Zhipu, Doubao 等
- 📝 **OpenAI 优先**: 优先使用 OpenAI 库，保证兼容性
- ⚙️ **集中配置**: 所有配置统一管理，支持环境变量和字典配置
- 🔄 **流式支持**: 支持同步和流式两种调用方式
- 🎯 **类型安全**: 完整的类型注解

## 支持的提供商

| 提供商 | 使用库 | 默认模型 |
|--------|--------|----------|
| OpenAI | openai | gpt-4o-mini |
| DeepSeek | openai | deepseek-chat |
| Anthropic (Claude) | anthropic | claude-3-5-sonnet-20241022 |
| Qwen (通义千问) | openai | qwen-plus |
| Moonshot (月之暗面) | openai | moonshot-v1-8k |
| Zhipu (智谱) | openai | glm-4 |
| Doubao (豆包) | openai | doubao-pro-32k |

## 安装依赖

```bash
# 基础依赖（OpenAI 及兼容提供商）
pip install openai

# Anthropic Claude 支持
pip install anthropic
```

## 快速开始

### 1. 配置环境变量

在 `.env` 文件中添加：

```bash
# OpenAI
OPENAI_API_KEY=sk-xxx

# DeepSeek
DEEPSEEK_API_KEY=sk-xxx

# Anthropic Claude
ANTHROPIC_API_KEY=sk-ant-xxx

# Qwen (通义千问)
QWEN_API_KEY=sk-xxx

# 可选：自定义 base_url
# OPENAI_BASE_URL=https://api.openai.com/v1
```

### 2. 基本使用

```python
from core.llm import LLMFactory

# 创建客户端（从环境变量自动读取配置）
client = LLMFactory.create('openai')

# 简单对话
response = client.simple_chat("介绍一下 Python")
print(response)

# 完整对话
messages = [
    {"role": "system", "content": "你是一个helpful的助手"},
    {"role": "user", "content": "什么是机器学习？"}
]
result = client.chat_completion(messages)
print(result['content'])

# 流式对话
for chunk in client.chat_completion_stream(messages):
    print(chunk['content'], end='', flush=True)
```

### 3. 使用不同的提供商

```python
# DeepSeek
client = LLMFactory.create('deepseek')

# Claude
client = LLMFactory.create('anthropic', model='claude-3-5-sonnet-20241022')

# 通义千问
client = LLMFactory.create('qwen', model='qwen-max')

# 月之暗面
client = LLMFactory.create('moonshot')

# 智谱 AI
client = LLMFactory.create('zhipu')

# 豆包
client = LLMFactory.create('doubao')
```

### 4. 自定义配置

```python
from core.llm import LLMFactory, LLMConfig

# 方式 1: 从字典创建
config_dict = {
    'provider': 'openai',
    'api_key': 'sk-xxx',
    'model': 'gpt-4',
    'temperature': 0.8,
    'max_tokens': 2000,
}
client = LLMFactory.create_from_dict(config_dict)

# 方式 2: 使用配置对象
config = LLMConfig.from_dict(config_dict)
client = LLMFactory.create('openai', config=config)
```

### 5. 调用参数

```python
# 覆盖默认参数
result = client.chat_completion(
    messages=messages,
    temperature=0.9,
    max_tokens=1000,
    top_p=0.95,
)

# 流式调用
for chunk in client.chat_completion_stream(
    messages=messages,
    temperature=0.7,
):
    print(chunk['content'], end='')
```

## 响应格式

### 同步调用响应

```python
{
    'content': 'AI 回复的内容',
    'role': 'assistant',
    'model': 'gpt-4o-mini',
    'usage': {
        'prompt_tokens': 10,
        'completion_tokens': 20,
        'total_tokens': 30,
    },
    'finish_reason': 'stop'
}
```

### 流式调用响应

```python
# 每个 chunk
{
    'content': '内容片段',
    'role': 'assistant',
    'finish_reason': None  # 最后一个 chunk 为 'stop'
}
```

## 高级用法

### 注册自定义客户端

```python
from core.llm import LLMFactory, BaseLLMClient

class MyCustomClient(BaseLLMClient):
    def _initialize_client(self):
        # 实现初始化逻辑
        pass
    
    def chat_completion(self, messages, **kwargs):
        # 实现同步调用
        pass
    
    def chat_completion_stream(self, messages, **kwargs):
        # 实现流式调用
        pass

# 注册
LLMFactory.register_client('mycustom', MyCustomClient)

# 使用
client = LLMFactory.create('mycustom')
```

### 检查支持的提供商

```python
# 获取所有支持的提供商
providers = LLMFactory.get_supported_providers()
print(providers)  # ['openai', 'deepseek', 'anthropic', ...]

# 检查是否支持
is_supported = LLMFactory.is_supported('openai')  # True
```

## 配置说明

### 环境变量

每个提供商支持以下环境变量：

- `{PROVIDER}_API_KEY`: API 密钥（必需）
- `{PROVIDER}_BASE_URL`: API 地址（可选）
- `{PROVIDER}_MODEL`: 默认模型（可选）
- `{PROVIDER}_MAX_TOKENS`: 最大 token 数（可选，默认 4096）
- `{PROVIDER}_TEMPERATURE`: 温度参数（可选，默认 0.7）
- `{PROVIDER}_TIMEOUT`: 超时时间（可选，默认 60 秒）

例如：
```bash
OPENAI_API_KEY=sk-xxx
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=gpt-4
OPENAI_TEMPERATURE=0.8
```

### 配置优先级

调用参数 > 配置对象 > 环境变量 > 默认配置

## 错误处理

```python
try:
    client = LLMFactory.create('openai')
    result = client.chat_completion(messages)
except ValueError as e:
    print(f"配置错误: {e}")
except RuntimeError as e:
    print(f"API 调用失败: {e}")
except Exception as e:
    print(f"未知错误: {e}")
```

## 实际应用示例

### Django 视图中使用

```python
from django.http import JsonResponse
from core.llm import LLMFactory

def chat_api(request):
    user_message = request.POST.get('message')
    
    client = LLMFactory.create('deepseek')
    response = client.simple_chat(user_message)
    
    return JsonResponse({'reply': response})
```

### 流式响应

```python
from django.http import StreamingHttpResponse
from core.llm import LLMFactory

def chat_stream_api(request):
    messages = [{"role": "user", "content": request.POST.get('message')}]
    
    client = LLMFactory.create('openai')
    
    def generate():
        for chunk in client.chat_completion_stream(messages):
            yield chunk['content']
    
    return StreamingHttpResponse(generate(), content_type='text/plain')
```

### 批量处理

```python
from core.llm import LLMFactory

def batch_summarize(texts: list[str]):
    client = LLMFactory.create('deepseek')
    
    results = []
    for text in texts:
        summary = client.simple_chat(
            f"请总结以下内容：\n\n{text}",
            temperature=0.3
        )
        results.append(summary)
    
    return results
```

## 性能建议

1. **复用客户端**: 客户端对象可以复用，避免频繁创建
2. **合理设置超时**: 根据实际情况调整 timeout 参数
3. **使用流式**: 长文本生成建议使用流式接口
4. **选择合适的模型**: 根据任务复杂度选择模型

## 注意事项

1. 确保环境变量已正确配置
2. Anthropic 需要单独安装 `anthropic` 库
3. 不同提供商的 API 限流策略不同，注意控制请求频率
4. 敏感的 API Key 不要硬编码在代码中

## 扩展开发

如需添加新的提供商：

1. 继承 `BaseLLMClient` 类
2. 实现抽象方法
3. 在 `LLMFactory` 中注册
4. 更新配置文件

详见代码注释和示例。

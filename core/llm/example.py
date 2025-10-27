"""
LLM 客户端使用示例
"""
from core.llm import LLMFactory


def example_basic_usage():
    """基础使用示例"""
    print("=== 基础使用 ===")
    
    # 创建客户端
    client = LLMFactory.create('openai')
    
    # 简单对话
    response = client.simple_chat("你好，请介绍一下自己")
    print(f"回复: {response}\n")


def example_with_system_prompt():
    """带系统提示的示例"""
    print("=== 带系统提示 ===")
    
    client = LLMFactory.create('deepseek')
    
    response = client.simple_chat(
        prompt="什么是机器学习？",
        system_prompt="你是一个专业的AI教师，擅长用简单的语言解释复杂概念。"
    )
    print(f"回复: {response}\n")


def example_chat_completion():
    """完整的对话示例"""
    print("=== 完整对话 ===")
    
    client = LLMFactory.create('openai')
    
    messages = [
        {"role": "system", "content": "你是一个Python编程助手"},
        {"role": "user", "content": "如何读取CSV文件？"},
    ]
    
    result = client.chat_completion(messages, temperature=0.7)
    
    print(f"回复: {result['content']}")
    print(f"模型: {result['model']}")
    print(f"Token使用: {result['usage']}\n")


def example_stream():
    """流式调用示例"""
    print("=== 流式调用 ===")
    
    client = LLMFactory.create('deepseek')
    
    messages = [
        {"role": "user", "content": "写一个Python快速排序算法"}
    ]
    
    print("AI回复: ", end='')
    for chunk in client.chat_completion_stream(messages):
        if chunk['content']:
            print(chunk['content'], end='', flush=True)
    print("\n")


def example_multiple_providers():
    """使用多个提供商"""
    print("=== 多提供商对比 ===")
    
    prompt = "用一句话解释什么是递归"
    
    providers = ['openai', 'deepseek']
    
    for provider in providers:
        try:
            client = LLMFactory.create(provider)
            response = client.simple_chat(prompt, temperature=0.5)
            print(f"{provider}: {response}\n")
        except Exception as e:
            print(f"{provider}: 调用失败 - {e}\n")


def example_custom_config():
    """自定义配置示例"""
    print("=== 自定义配置 ===")
    
    config_dict = {
        'provider': 'openai',
        'api_key': 'your-api-key-here',  # 实际使用时替换
        'model': 'gpt-4o-mini',
        'temperature': 0.8,
        'max_tokens': 500,
    }
    
    # 注意：这只是示例，实际运行需要真实的API key
    try:
        client = LLMFactory.create_from_dict(config_dict)
        print(f"创建客户端成功: {client}")
    except Exception as e:
        print(f"创建失败（预期）: {e}")
    print()


def example_with_parameters():
    """带参数调用示例"""
    print("=== 参数控制 ===")
    
    client = LLMFactory.create('openai')
    
    messages = [{"role": "user", "content": "讲一个笑话"}]
    
    # 高温度，更有创意
    print("高温度 (0.9):")
    result = client.chat_completion(messages, temperature=0.9, max_tokens=200)
    print(f"{result['content']}\n")
    
    # 低温度，更确定
    print("低温度 (0.1):")
    result = client.chat_completion(messages, temperature=0.1, max_tokens=200)
    print(f"{result['content']}\n")


def example_conversation():
    """多轮对话示例"""
    print("=== 多轮对话 ===")
    
    client = LLMFactory.create('deepseek')
    
    messages = [
        {"role": "system", "content": "你是一个友好的助手"},
        {"role": "user", "content": "我想学习Python"},
        {"role": "assistant", "content": "很好！Python是一门非常适合初学者的编程语言。"},
        {"role": "user", "content": "我应该从哪里开始？"},
    ]
    
    result = client.chat_completion(messages)
    print(f"AI: {result['content']}\n")


def main():
    """运行所有示例"""
    print("LLM 客户端使用示例\n")
    print("=" * 50)
    print()
    
    examples = [
        example_basic_usage,
        example_with_system_prompt,
        example_chat_completion,
        example_stream,
        example_multiple_providers,
        example_custom_config,
        example_with_parameters,
        example_conversation,
    ]
    
    for example in examples:
        try:
            example()
        except Exception as e:
            print(f"示例执行错误: {e}\n")
        print("-" * 50)
        print()


if __name__ == '__main__':
    # 运行单个示例
    # example_basic_usage()
    
    # 或运行所有示例
    main()

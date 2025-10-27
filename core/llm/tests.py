"""
LLM 客户端单元测试
"""
import os
from unittest.mock import Mock, patch, MagicMock
from .factory import LLMFactory
from .config import LLMConfig, LLMProviderConfig
from .base import BaseLLMClient


class TestLLMConfig:
    """测试配置类"""
    
    def test_get_supported_providers(self):
        """测试获取支持的提供商列表"""
        providers = LLMConfig.get_supported_providers()
        assert 'openai' in providers
        assert 'deepseek' in providers
        assert 'anthropic' in providers
        assert 'qwen' in providers
        print("✓ 支持的提供商列表正确")
    
    def test_get_provider_config(self):
        """测试获取提供商配置"""
        config = LLMConfig.get_provider_config('openai')
        assert config['default_model'] == 'gpt-4o-mini'
        assert config['use_openai_lib'] == True
        print("✓ OpenAI 配置正确")
        
        config = LLMConfig.get_provider_config('anthropic')
        assert config['use_openai_lib'] == False
        print("✓ Anthropic 配置正确")
    
    def test_from_dict(self):
        """测试从字典创建配置"""
        config_dict = {
            'provider': 'openai',
            'api_key': 'sk-test-key',
            'model': 'gpt-4',
            'temperature': 0.8,
        }
        config = LLMConfig.from_dict(config_dict)
        assert config.provider == 'openai'
        assert config.api_key == 'sk-test-key'
        assert config.model == 'gpt-4'
        assert config.temperature == 0.8
        print("✓ 从字典创建配置成功")


class TestLLMFactory:
    """测试工厂类"""
    
    def test_get_supported_providers(self):
        """测试获取支持的提供商"""
        providers = LLMFactory.get_supported_providers()
        assert len(providers) > 0
        assert 'openai' in providers
        print(f"✓ 工厂支持 {len(providers)} 个提供商")
    
    def test_is_supported(self):
        """测试检查提供商支持"""
        assert LLMFactory.is_supported('openai') == True
        assert LLMFactory.is_supported('unknown') == False
        print("✓ 提供商检查功能正常")
    
    def test_create_from_dict(self):
        """测试从字典创建客户端"""
        config_dict = {
            'provider': 'openai',
            'api_key': 'sk-test-key',
            'model': 'gpt-4o-mini',
        }
        client = LLMFactory.create_from_dict(config_dict)
        assert isinstance(client, BaseLLMClient)
        assert client.provider == 'openai'
        assert client.model == 'gpt-4o-mini'
        print("✓ 从字典创建客户端成功")
    
    def test_unsupported_provider(self):
        """测试不支持的提供商"""
        try:
            LLMFactory.create('unsupported_provider')
            assert False, "应该抛出 ValueError"
        except ValueError as e:
            assert '不支持的 LLM 提供商' in str(e)
            print("✓ 正确处理不支持的提供商")


class TestBaseLLMClient:
    """测试基类功能"""
    
    def test_merge_params(self):
        """测试参数合并"""
        config = LLMProviderConfig(
            provider='test',
            api_key='sk-test',
            model='test-model',
            temperature=0.7,
            max_tokens=2000,
        )
        
        # 创建一个简单的客户端子类用于测试
        class TestClient(BaseLLMClient):
            def _initialize_client(self):
                pass
            def chat_completion(self, messages, **kwargs):
                return {}
            def chat_completion_stream(self, messages, **kwargs):
                yield {}
        
        client = TestClient(config)
        
        # 测试默认参数
        params = client._merge_params()
        assert params['model'] == 'test-model'
        assert params['temperature'] == 0.7
        assert params['max_tokens'] == 2000
        
        # 测试覆盖参数
        params = client._merge_params(temperature=0.9, max_tokens=1000)
        assert params['temperature'] == 0.9
        assert params['max_tokens'] == 1000
        
        print("✓ 参数合并功能正常")


def run_tests():
    """运行所有测试"""
    print("开始运行 LLM 客户端测试...\n")
    print("=" * 50)
    
    # 测试配置类
    print("\n[测试配置类]")
    config_tests = TestLLMConfig()
    config_tests.test_get_supported_providers()
    config_tests.test_get_provider_config()
    config_tests.test_from_dict()
    
    # 测试工厂类
    print("\n[测试工厂类]")
    factory_tests = TestLLMFactory()
    factory_tests.test_get_supported_providers()
    factory_tests.test_is_supported()
    factory_tests.test_create_from_dict()
    factory_tests.test_unsupported_provider()
    
    # 测试基类
    print("\n[测试基类]")
    base_tests = TestBaseLLMClient()
    base_tests.test_merge_params()
    
    print("\n" + "=" * 50)
    print("✓ 所有测试通过！")


if __name__ == '__main__':
    run_tests()

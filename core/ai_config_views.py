from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.views.decorators.csrf import csrf_exempt
from .models import AIModelConfig
import json
import os

# API Base URLs配置
API_BASE_CONFIG = {
    'gpt': 'https://api.openai.com/v1',
    'claude': 'https://api.anthropic.com/v1',
    'gemini': 'https://generativelanguage.googleapis.com/v1',
    'qwen': 'https://dashscope.aliyuncs.com/compatible-mode/v1',
    'grok': 'https://api.x.ai/v1',
    'doubao': 'https://ark.cn-beijing.volces.com/api/v3',
    'deepseek': 'https://api.deepseek.com/v1',
}

# API Key环境变量映射
API_KEY_ENV_MAP = {
    'gpt': 'OPENAI_API_KEY',
    'claude': 'CLAUDE_API_KEY',
    'gemini': 'GEMINI_API_KEY',
    'qwen': 'QWEN_API_KEY',
    'grok': 'GROK_API_KEY',
    'doubao': 'DOUBAO_API_KEY',
    'deepseek': 'DEEPSEEK_API_KEY',
}

# Provider到Logo文件名的映射
PROVIDER_LOGO_MAP = {
    'gpt': 'gpt',
    'claude': 'claude',
    'gemini': 'gemini',
    'qwen': 'qwen',
    'grok': 'grok',
    'doubao': 'doubao',
    'deepseek': 'deepseek',
}

def get_api_key(provider):
    """从环境变量获取API Key"""
    env_var = API_KEY_ENV_MAP.get(provider)
    if env_var:
        return os.getenv(env_var, '')
    return ''

@csrf_exempt
@api_view(['GET', 'POST'])
def ai_model_config(request):
    """AI模型配置API"""
    
    # 获取用户标识（用户ID或会话ID）
    user = request.user if request.user.is_authenticated else None
    session_id = request.session.session_key
    if not session_id and not user:
        # 创建会话
        if not request.session.session_key:
            request.session.create()
        session_id = request.session.session_key
    
    if request.method == 'GET':
        # 获取当前配置
        try:
            if user:
                config = AIModelConfig.objects.filter(user=user, is_active=True).first()
            else:
                config = AIModelConfig.objects.filter(session_id=session_id, is_active=True).first()
            
            if config:
                # 获取logo名称
                logo = PROVIDER_LOGO_MAP.get(config.provider, config.provider)
                
                return Response({
                    'success': True,
                    'data': {
                        'provider': config.provider,
                        'model_name': config.model_name,
                        'api_base': config.api_base,
                        'logo': logo,
                    }
                })
            else:
                return Response({
                    'success': True,
                    'data': None
                })
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    elif request.method == 'POST':
        # 保存配置
        try:
            data = request.data
            provider = data.get('provider')
            model_name = data.get('model_name')
            api_key = data.get('api_key', '')
            api_base = data.get('api_base', '')
            
            if not provider or not model_name:
                return Response({
                    'success': False,
                    'error': 'Provider and model_name are required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # 将之前的活跃配置设为非活跃
            if user:
                AIModelConfig.objects.filter(user=user, is_active=True).update(is_active=False)
            else:
                AIModelConfig.objects.filter(session_id=session_id, is_active=True).update(is_active=False)
            
            # 创建或更新配置
            config, created = AIModelConfig.objects.update_or_create(
                user=user,
                session_id=session_id if not user else None,
                provider=provider,
                model_name=model_name,
                defaults={
                    'api_key': api_key,
                    'api_base': api_base,
                    'is_active': True
                }
            )
            
            # 获取logo名称
            logo = PROVIDER_LOGO_MAP.get(config.provider, config.provider)
            
            return Response({
                'success': True,
                'data': {
                    'provider': config.provider,
                    'model_name': config.model_name,
                    'api_base': config.api_base,
                    'logo': logo,
                }
            })
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@csrf_exempt
@api_view(['GET'])
def ai_model_options(request):
    """获取AI模型选项列表"""
    
    # 定义可用的AI模型 (Updated for 2025)
    model_options = {
        'gpt': {
            'name': 'GPT',
            'logo': 'openai',
            'api_base': API_BASE_CONFIG.get('gpt', ''),
            'api_key': get_api_key('gpt'),
            'models': [
                {'id': 'gpt-5', 'name': 'GPT-5', 'description': 'Latest flagship model (Aug 2025) - Best for complex reasoning'},
                {'id': 'gpt-4o', 'name': 'GPT-4o', 'description': 'Multimodal flagship model with vision capabilities'},
            ]
        },
        'claude': {
            'name': 'Claude',
            'logo': 'claude',
            'api_base': API_BASE_CONFIG.get('claude', ''),
            'api_key': get_api_key('claude'),
            'models': [
                {'id': 'claude-4-5-sonnet-20250929', 'name': 'Claude 4.5 Sonnet', 'description': 'Latest model (Sept 2025) - Best for coding & agents, 1M token context'},
                {'id': 'claude-4-1-opus-20250805', 'name': 'Claude 4.1 Opus', 'description': 'Hybrid reasoning model (Aug 2025) - 200K context'},
            ]
        },
        'gemini': {
            'name': 'Gemini',
            'logo': 'gemini',
            'api_base': API_BASE_CONFIG.get('gemini', ''),
            'api_key': get_api_key('gemini'),
            'models': [
                {'id': 'gemini-2.5-pro', 'name': 'Gemini 2.5 Pro', 'description': 'Latest model (June 2025) - 1M token context, best for research'},
            ]
        },
        'qwen': {
            'name': 'Qwen',
            'logo': 'qwen',
            'api_base': API_BASE_CONFIG.get('qwen', ''),
            'api_key': get_api_key('qwen'),
            'models': [
                {'id': 'qwen3-max', 'name': 'Qwen3-Max', 'description': 'Latest trillion-parameter model (Sept 2025) - Strong coding'},
            ]
        },
        'grok': {
            'name': 'Grok',
            'logo': 'grok',
            'api_base': API_BASE_CONFIG.get('grok', ''),
            'api_key': get_api_key('grok'),
            'models': [
                {'id': 'grok-4', 'name': 'Grok 4', 'description': 'Latest model (July 2025) - Real-time X search & tool use'},
            ]
        },
        'doubao': {
            'name': 'Doubao',
            'logo': 'doubao',
            'api_base': API_BASE_CONFIG.get('doubao', ''),
            'api_key': get_api_key('doubao'),
            'models': [
                {'id': 'doubao-pro-256k', 'name': 'Doubao Pro 256K', 'description': 'Pro version with 256K context'},
                {'id': 'doubao-pro-32k', 'name': 'Doubao Pro 32K', 'description': 'Pro version with 32K context'},
            ]
        },
        'deepseek': {
            'name': 'DeepSeek',
            'logo': 'deepseek',
            'api_base': API_BASE_CONFIG.get('deepseek', ''),
            'api_key': get_api_key('deepseek'),
            'models': [
                {'id': 'deepseek-r1', 'name': 'DeepSeek R1', 'description': 'Cost-effective reasoning model (2025)'},
                {'id': 'deepseek-v3', 'name': 'DeepSeek V3', 'description': 'Latest general-purpose model'},
            ]
        }
    }
    
    return Response({
        'success': True,
        'data': model_options
    })

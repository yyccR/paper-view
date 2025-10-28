from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.views.decorators.csrf import csrf_exempt
from .models import AIModelConfig
import json

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
                return Response({
                    'success': True,
                    'data': {
                        'provider': config.provider,
                        'model_name': config.model_name,
                        'api_base': config.api_base,
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
            
            return Response({
                'success': True,
                'data': {
                    'provider': config.provider,
                    'model_name': config.model_name,
                    'api_base': config.api_base,
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
            'models': [
                {'id': 'gpt-5', 'name': 'GPT-5', 'description': 'Latest flagship model (Aug 2025) - Best for complex reasoning'},
                {'id': 'gpt-4o', 'name': 'GPT-4o', 'description': 'Multimodal flagship model with vision capabilities'},
                {'id': 'gpt-4o-mini', 'name': 'GPT-4o mini', 'description': 'Affordable and intelligent small model'},
                {'id': 'o3', 'name': 'o3', 'description': 'Advanced reasoning model for complex tasks'},
                {'id': 'o1', 'name': 'o1', 'description': 'Reasoning model for problem-solving'},
                {'id': 'o1-mini', 'name': 'o1-mini', 'description': 'Fast reasoning model'},
            ]
        },
        'claude': {
            'name': 'Claude',
            'logo': 'claude',
            'models': [
                {'id': 'claude-4-5-sonnet-20250929', 'name': 'Claude 4.5 Sonnet', 'description': 'Latest model (Sept 2025) - Best for coding & agents, 1M token context'},
                {'id': 'claude-4-1-opus-20250805', 'name': 'Claude 4.1 Opus', 'description': 'Hybrid reasoning model (Aug 2025) - 200K context'},
                {'id': 'claude-3-5-sonnet-20241022', 'name': 'Claude 3.5 Sonnet', 'description': 'Previous generation intelligent model'},
                {'id': 'claude-3-5-haiku-20241022', 'name': 'Claude 3.5 Haiku', 'description': 'Fastest and most compact model'},
            ]
        },
        'gemini': {
            'name': 'Gemini',
            'logo': 'gemini',
            'models': [
                {'id': 'gemini-2.5-pro', 'name': 'Gemini 2.5 Pro', 'description': 'Latest model (June 2025) - 1M token context, best for research'},
                {'id': 'gemini-2.0-flash-exp', 'name': 'Gemini 2.0 Flash', 'description': 'Next generation fast model'},
                {'id': 'gemini-1.5-pro', 'name': 'Gemini 1.5 Pro', 'description': 'Best for complex tasks with long context'},
                {'id': 'gemini-1.5-flash', 'name': 'Gemini 1.5 Flash', 'description': 'Fast and versatile model'},
            ]
        },
        'qwen': {
            'name': 'Qwen',
            'logo': 'qwen',
            'models': [
                {'id': 'qwen3-max', 'name': 'Qwen3-Max', 'description': 'Latest trillion-parameter model (Sept 2025) - Strong coding'},
                {'id': 'qwen3-omni', 'name': 'Qwen3-Omni', 'description': 'Multimodal model with vision and audio'},
                {'id': 'qwen-max', 'name': 'Qwen Max', 'description': 'Most capable previous generation'},
                {'id': 'qwen-plus', 'name': 'Qwen Plus', 'description': 'Balanced performance'},
                {'id': 'qwq-32b-preview', 'name': 'QwQ 32B', 'description': 'Reasoning model'},
            ]
        },
        'grok': {
            'name': 'Grok',
            'logo': 'grok',
            'models': [
                {'id': 'grok-4', 'name': 'Grok 4', 'description': 'Latest model (July 2025) - Real-time X search & tool use'},
                {'id': 'grok-3', 'name': 'Grok 3', 'description': 'Advanced reasoning with real-time data'},
                {'id': 'grok-2', 'name': 'Grok 2', 'description': 'Previous generation model'},
            ]
        },
        'doubao': {
            'name': 'Doubao',
            'logo': 'doubao',
            'models': [
                {'id': 'doubao-pro-256k', 'name': 'Doubao Pro 256K', 'description': 'Pro version with 256K context'},
                {'id': 'doubao-pro-128k', 'name': 'Doubao Pro 128K', 'description': 'Pro version with 128K context'},
                {'id': 'doubao-pro-32k', 'name': 'Doubao Pro 32K', 'description': 'Pro version with 32K context'},
                {'id': 'doubao-lite-32k', 'name': 'Doubao Lite 32K', 'description': 'Lite version with 32K context'},
            ]
        },
        'deepseek': {
            'name': 'DeepSeek',
            'logo': 'deepseek',
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

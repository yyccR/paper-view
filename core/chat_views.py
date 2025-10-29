from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.views.decorators.csrf import csrf_exempt
from django.http import StreamingHttpResponse
from django.utils import timezone
from .models import AIModelConfig, ChatSession, ChatMessage
import json
import os
import requests
import time

# 语言代码映射到完整语言名称
LANGUAGE_NAMES = {
    'zh': '简体中文',
    'en': 'English',
    'ja': '日本語',
    'ko': '한국어',
    'es': 'Español',
    'fr': 'Français',
    'de': 'Deutsch',
    'ru': 'Русский',
}

def get_active_ai_config(request):
    """获取用户当前激活的AI配置"""
    user = request.user if request.user.is_authenticated else None
    session_id = request.session.session_key
    
    if not session_id and not user:
        if not request.session.session_key:
            request.session.create()
        session_id = request.session.session_key
    
    try:
        if user:
            config = AIModelConfig.objects.filter(user=user, is_active=True).first()
        else:
            config = AIModelConfig.objects.filter(session_id=session_id, is_active=True).first()
        return config
    except Exception as e:
        print(f"Error getting AI config: {e}")
        return None


def call_llm_api_stream(config, messages):
    """调用LLM API进行流式响应"""
    if not config:
        raise Exception("No AI model configured")
    
    api_base = config.api_base
    api_key = config.api_key
    model = config.model_name
    provider = config.provider.lower()
    
    # 构建API请求
    headers = {
        'Content-Type': 'application/json',
    }
    
    # 根据不同的provider设置不同的header
    if provider in ['gpt', 'openai', 'qwen', 'deepseek', 'grok', 'doubao']:
        headers['Authorization'] = f'Bearer {api_key}'
    elif provider == 'claude':
        headers['x-api-key'] = api_key
        headers['anthropic-version'] = '2023-06-01'
    elif provider == 'gemini':
        pass
    
    # 构建请求body（启用流式）
    if provider == 'claude':
        request_data = {
            'model': model,
            'messages': messages,
            'max_tokens': 4096,
            'stream': True,
        }
        endpoint = f"{api_base}/messages"
    elif provider == 'gemini':
        # Gemini目前不支持流式，使用普通模式
        request_data = {
            'contents': [
                {
                    'parts': [{'text': msg['content']}],
                    'role': 'user' if msg['role'] == 'user' else 'model'
                } for msg in messages
            ]
        }
        endpoint = f"{api_base}/models/{model}:generateContent?key={api_key}"
    else:
        # OpenAI-compatible format
        request_data = {
            'model': model,
            'messages': messages,
            'temperature': 0.3,
            'max_tokens': 4096,
            'stream': True,
        }
        endpoint = f"{api_base}/chat/completions"
    
    # 发送流式请求
    response = requests.post(endpoint, headers=headers, json=request_data, timeout=60, stream=True)
    
    if response.status_code != 200:
        raise Exception(f"API request failed: {response.status_code} - {response.text}")
    
    # 流式解析
    for line in response.iter_lines():
        if not line:
            continue
        
        line = line.decode('utf-8')
        
        # 跳过非数据行
        if not line.startswith('data: '):
            continue
        
        data_str = line[6:]  # 移除 "data: " 前缀
        
        # 检查流结束标记
        if data_str.strip() == '[DONE]':
            break
        
        try:
            data = json.loads(data_str)
            
            # 解析不同provider的流式响应
            if provider == 'claude':
                if data.get('type') == 'content_block_delta':
                    delta = data.get('delta', {})
                    if delta.get('type') == 'text_delta':
                        text = delta.get('text', '')
                        if text:
                            yield text
            elif provider == 'gemini':
                # Gemini不支持流式，直接返回完整结果
                text = data.get('candidates', [{}])[0].get('content', {}).get('parts', [{}])[0].get('text', '')
                if text:
                    yield text
                    break
            else:
                # OpenAI-compatible format
                choices = data.get('choices', [])
                if choices:
                    delta = choices[0].get('delta', {})
                    content = delta.get('content', '')
                    if content:
                        yield content
        except json.JSONDecodeError:
            continue


def call_llm_api(config, messages):
    """调用LLM API进行翻译（非流式）"""
    if not config:
        raise Exception("No AI model configured")
    
    api_base = config.api_base
    api_key = config.api_key
    model = config.model_name
    
    # 构建API请求
    headers = {
        'Content-Type': 'application/json',
    }
    
    # 根据不同的provider设置不同的header
    provider = config.provider.lower()
    if provider in ['gpt', 'openai', 'qwen', 'deepseek', 'grok', 'doubao']:
        headers['Authorization'] = f'Bearer {api_key}'
    elif provider == 'claude':
        headers['x-api-key'] = api_key
        headers['anthropic-version'] = '2023-06-01'
    elif provider == 'gemini':
        # Gemini uses API key in URL
        pass
    
    # 构建请求body
    if provider == 'claude':
        # Claude API format
        request_data = {
            'model': model,
            'messages': messages,
            'max_tokens': 4096,
        }
        endpoint = f"{api_base}/messages"
    elif provider == 'gemini':
        # Gemini API format
        request_data = {
            'contents': [
                {
                    'parts': [{'text': msg['content']}],
                    'role': 'user' if msg['role'] == 'user' else 'model'
                } for msg in messages
            ]
        }
        endpoint = f"{api_base}/models/{model}:generateContent?key={api_key}"
    else:
        # OpenAI-compatible format (GPT, Qwen, DeepSeek, Grok, Doubao)
        request_data = {
            'model': model,
            'messages': messages,
            'temperature': 0.3,
            'max_tokens': 4096,
        }
        endpoint = f"{api_base}/chat/completions"
    
    # 发送请求
    response = requests.post(endpoint, headers=headers, json=request_data, timeout=30)
    
    if response.status_code != 200:
        raise Exception(f"API request failed: {response.status_code} - {response.text}")
    
    result = response.json()
    
    # 解析响应
    if provider == 'claude':
        translated_text = result.get('content', [{}])[0].get('text', '')
    elif provider == 'gemini':
        translated_text = result.get('candidates', [{}])[0].get('content', {}).get('parts', [{}])[0].get('text', '')
    else:
        # OpenAI-compatible format
        translated_text = result.get('choices', [{}])[0].get('message', {}).get('content', '')
    
    return translated_text


@csrf_exempt
@api_view(['POST'])
def translate_text(request):
    """翻译文本API"""
    try:
        data = request.data
        text = data.get('text', '').strip()
        target_lang = data.get('target_lang', 'zh')
        
        if not text:
            return Response({
                'success': False,
                'error': 'Text is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # 获取用户配置的AI模型
        config = get_active_ai_config(request)
        if not config:
            return Response({
                'success': False,
                'error': 'No AI model configured. Please configure an AI model first.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # 获取目标语言名称
        target_lang_name = LANGUAGE_NAMES.get(target_lang, target_lang)
        
        # 构建翻译prompt
        system_message = f"You are a professional translator. Translate the given text to {target_lang_name}. Only return the translated text, no explanations."
        user_message = f"Translate the following text to {target_lang_name}:\n\n{text}"
        
        messages = [
            {'role': 'system', 'content': system_message},
            {'role': 'user', 'content': user_message}
        ]
        
        # 调用LLM API
        translated_text = call_llm_api(config, messages)
        
        return Response({
            'success': True,
            'data': {
                'original_text': text,
                'translated_text': translated_text,
                'target_lang': target_lang,
                'model_used': f"{config.provider}/{config.model_name}"
            }
        })
        
    except Exception as e:
        print(f"Translation error: {e}")
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@csrf_exempt
@api_view(['POST'])
def chat_with_text(request):
    """与AI聊天API（带上下文）"""
    try:
        data = request.data
        messages = data.get('messages', [])
        context_text = data.get('context_text', '')
        
        if not messages:
            return Response({
                'success': False,
                'error': 'Messages are required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # 获取用户配置的AI模型
        config = get_active_ai_config(request)
        if not config:
            return Response({
                'success': False,
                'error': 'No AI model configured. Please configure an AI model first.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # 如果有上下文文本，在系统消息中添加
        if context_text:
            system_message = f"You are a helpful AI assistant. The user has selected the following text from a document:\n\n{context_text}\n\nPlease help answer questions about this text."
            # 在messages前面插入system message
            full_messages = [{'role': 'system', 'content': system_message}] + messages
        else:
            full_messages = messages
        
        # 调用LLM API
        response_text = call_llm_api(config, full_messages)
        
        return Response({
            'success': True,
            'data': {
                'response': response_text,
                'model_used': f"{config.provider}/{config.model_name}"
            }
        })
        
    except Exception as e:
        print(f"Chat error: {e}")
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@csrf_exempt
def translate_stream(request):
    """流式翻译API"""
    if request.method != 'POST':
        return StreamingHttpResponse('Method not allowed', status=405)
    
    try:
        data = json.loads(request.body)
        text = data.get('text', '').strip()
        target_lang = data.get('target_lang', 'zh')
        session_id_param = data.get('session_id')
        paper_title = data.get('paper_title', '')
        
        if not text:
            return StreamingHttpResponse('{"error": "Text is required"}', status=400)
        
        config = get_active_ai_config(request)
        if not config:
            return StreamingHttpResponse('{"error": "No AI model configured"}', status=400)
        
        target_lang_name = LANGUAGE_NAMES.get(target_lang, target_lang)
        system_message = f"You are a professional translator. Translate the given text to {target_lang_name}. Only return the translated text, no explanations."
        user_message = f"Translate the following text to {target_lang_name}:\n\n{text}"
        
        messages = [
            {'role': 'system', 'content': system_message},
            {'role': 'user', 'content': user_message}
        ]
        
        def event_stream():
            full_response = ""
            try:
                # 发送开始事件
                yield f"data: {json.dumps({'type': 'start', 'model': f'{config.provider}/{config.model_name}'})}\n\n"
                
                # 流式输出翻译结果
                for chunk in call_llm_api_stream(config, messages):
                    full_response += chunk
                    yield f"data: {json.dumps({'type': 'chunk', 'content': chunk})}\n\n"
                
                # 保存会话和消息
                user = request.user if request.user.is_authenticated else None
                sess_id = request.session.session_key
                if not sess_id and not user:
                    if not request.session.session_key:
                        request.session.create()
                    sess_id = request.session.session_key
                
                # 查找或创建会话
                if session_id_param:
                    session = ChatSession.objects.filter(id=session_id_param).first()
                else:
                    session = None
                
                if not session:
                    session = ChatSession.objects.create(
                        user=user,
                        session_id=sess_id if not user else None,
                        title=paper_title[:100] if paper_title else f'翻译: {text[:50]}...',
                        paper_title=paper_title,
                        session_type='translate',
                        ai_provider=config.provider,
                        ai_model=config.model_name,
                        context_text=text
                    )
                
                # 保存消息
                ChatMessage.objects.create(
                    session=session,
                    role='user',
                    content=text
                )
                ChatMessage.objects.create(
                    session=session,
                    role='assistant',
                    content=full_response
                )
                
                # 更新会话统计
                session.message_count = session.messages.count()
                session.last_message_at = timezone.now()
                session.save()
                
                # 发送结束事件
                yield f"data: {json.dumps({'type': 'done', 'session_id': session.id})}\n\n"
                
            except Exception as e:
                yield f"data: {json.dumps({'type': 'error', 'error': str(e)})}\n\n"
        
        response = StreamingHttpResponse(event_stream(), content_type='text/event-stream')
        response['Cache-Control'] = 'no-cache'
        response['X-Accel-Buffering'] = 'no'
        return response
        
    except Exception as e:
        return StreamingHttpResponse(f'{{"error": "{str(e)}"}}', status=500)


@csrf_exempt
def chat_stream(request):
    """流式聊天API"""
    if request.method != 'POST':
        return StreamingHttpResponse('Method not allowed', status=405)
    
    try:
        data = json.loads(request.body)
        messages = data.get('messages', [])
        context_text = data.get('context_text', '')
        session_id_param = data.get('session_id')
        paper_title = data.get('paper_title', '')
        
        if not messages:
            return StreamingHttpResponse('{"error": "Messages are required"}', status=400)
        
        config = get_active_ai_config(request)
        if not config:
            return StreamingHttpResponse('{"error": "No AI model configured"}', status=400)
        
        # 构建完整消息列表
        if context_text:
            system_message = f"You are a helpful AI assistant. The user has selected the following text from a document:\n\n{context_text}\n\nPlease help answer questions about this text."
            full_messages = [{'role': 'system', 'content': system_message}] + messages
        else:
            full_messages = messages
        
        def event_stream():
            full_response = ""
            try:
                yield f"data: {json.dumps({'type': 'start', 'model': f'{config.provider}/{config.model_name}'})}\n\n"
                
                for chunk in call_llm_api_stream(config, full_messages):
                    full_response += chunk
                    yield f"data: {json.dumps({'type': 'chunk', 'content': chunk})}\n\n"
                
                # 保存会话和消息
                user = request.user if request.user.is_authenticated else None
                sess_id = request.session.session_key
                if not sess_id and not user:
                    if not request.session.session_key:
                        request.session.create()
                    sess_id = request.session.session_key
                
                if session_id_param:
                    session = ChatSession.objects.filter(id=session_id_param).first()
                else:
                    session = None
                
                if not session:
                    session = ChatSession.objects.create(
                        user=user,
                        session_id=sess_id if not user else None,
                        title=paper_title[:100] if paper_title else f'对话: {messages[-1]["content"][:50]}...',
                        paper_title=paper_title,
                        session_type='chat',
                        ai_provider=config.provider,
                        ai_model=config.model_name,
                        context_text=context_text
                    )
                
                # 保存用户消息
                for msg in messages:
                    if msg['role'] == 'user':
                        ChatMessage.objects.create(
                            session=session,
                            role='user',
                            content=msg['content']
                        )
                
                # 保存AI回复
                ChatMessage.objects.create(
                    session=session,
                    role='assistant',
                    content=full_response
                )
                
                session.message_count = session.messages.count()
                session.last_message_at = timezone.now()
                session.save()
                
                yield f"data: {json.dumps({'type': 'done', 'session_id': session.id})}\n\n"
                
            except Exception as e:
                yield f"data: {json.dumps({'type': 'error', 'error': str(e)})}\n\n"
        
        response = StreamingHttpResponse(event_stream(), content_type='text/event-stream')
        response['Cache-Control'] = 'no-cache'
        response['X-Accel-Buffering'] = 'no'
        return response
        
    except Exception as e:
        return StreamingHttpResponse(f'{{"error": "{str(e)}"}}', status=500)


@csrf_exempt
@api_view(['GET', 'POST', 'DELETE'])
def session_manage(request, session_id=None):
    """会话管理API"""
    user = request.user if request.user.is_authenticated else None
    sess_id = request.session.session_key
    
    if request.method == 'GET':
        # 获取会话列表或单个会话
        if session_id:
            session = ChatSession.objects.filter(id=session_id).first()
            if not session:
                return Response({'success': False, 'error': 'Session not found'}, status=404)
            
            messages = session.messages.all().values('role', 'content', 'created_at')
            return Response({
                'success': True,
                'data': {
                    'session': {
                        'id': session.id,
                        'title': session.title,
                        'paper_title': session.paper_title,
                        'session_type': session.session_type,
                        'created_at': session.created_at,
                        'message_count': session.message_count
                    },
                    'messages': list(messages)
                }
            })
        else:
            # 获取会话列表
            if user:
                sessions = ChatSession.objects.filter(user=user, is_active=True)
            else:
                sessions = ChatSession.objects.filter(session_id=sess_id, is_active=True)
            
            session_list = sessions.values(
                'id', 'title', 'paper_title', 'session_type', 'message_count', 
                'last_message_at', 'created_at', 'is_pinned'
            )[:20]
            
            return Response({
                'success': True,
                'data': list(session_list)
            })
    
    elif request.method == 'POST':
        # 创建新会话
        data = request.data
        session = ChatSession.objects.create(
            user=user,
            session_id=sess_id if not user else None,
            title=data.get('title', '新对话'),
            paper_title=data.get('paper_title', ''),
            paper_url=data.get('paper_url', ''),
            session_type=data.get('session_type', 'chat'),
            context_text=data.get('context_text', '')
        )
        
        return Response({
            'success': True,
            'data': {
                'session_id': session.id,
                'title': session.title
            }
        })
    
    elif request.method == 'DELETE':
        # 删除会话
        if not session_id:
            return Response({'success': False, 'error': 'Session ID required'}, status=400)
        
        session = ChatSession.objects.filter(id=session_id).first()
        if not session:
            return Response({'success': False, 'error': 'Session not found'}, status=404)
        
        session.is_active = False
        session.save()
        
        return Response({'success': True})

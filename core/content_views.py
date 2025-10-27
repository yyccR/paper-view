"""
内容生成和管理API视图
"""
import json
import shutil
import traceback
from pathlib import Path
from datetime import datetime

from django.conf import settings
from django.http import JsonResponse, FileResponse, HttpResponse, StreamingHttpResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from loguru import logger

from common.download_utils import download_pdf_from_url
import requests
from core.dify_clients import DifyAPIClient
from core.paper_processor import PaperImageProcessor


@csrf_exempt
@api_view(['POST'])
def upload_pdf(request):
    """
    上传PDF文件并生成图文内容
    
    POST /api/generate/upload
    """
    try:
        # 检查是否有文件上传
        if 'file' not in request.FILES:
            return Response({
                'success': False,
                'error': '没有上传文件'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        uploaded_file = request.FILES['file']
        
        # 验证文件类型
        if not uploaded_file.name.endswith('.pdf'):
            return Response({
                'success': False,
                'error': '只支持PDF文件'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        logger.info(f"收到PDF上传请求: {uploaded_file.name}")
        
        # 创建基于日期的输出目录
        today = datetime.now().strftime('%Y-%m-%d')
        base_dir = Path(settings.BASE_DIR) / 'data'
        data_dir = base_dir / today
        data_dir.mkdir(parents=True, exist_ok=True)
        
        # 使用文件名（去掉扩展名）作为子目录名
        file_stem = Path(uploaded_file.name).stem
        output_dir = data_dir / file_stem
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # 保存PDF文件
        pdf_path = output_dir / uploaded_file.name
        with open(pdf_path, 'wb+') as f:
            for chunk in uploaded_file.chunks():
                f.write(chunk)
        
        logger.info(f"PDF文件保存成功: {pdf_path}")
        
        # 处理PDF文件
        result = process_pdf_file(pdf_path)
        
        return Response(result)
        
    except Exception as e:
        logger.error(f"上传PDF处理失败: {traceback.format_exc()}")
        return Response({
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@csrf_exempt
@api_view(['POST'])
def generate_from_url(request):
    """
    通过URL生成图文内容
    
    POST /api/generate/url
    Body: {"url": "https://example.com/file.pdf"}
    """
    try:
        # 获取URL
        url = request.data.get('url', '').strip()
        
        if not url:
            return Response({
                'success': False,
                'error': 'URL不能为空'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        logger.info(f"收到URL生成请求: {url}")
        
        # 下载PDF
        pdf_path = download_pdf_from_url(url)
        logger.info(f"PDF下载成功: {pdf_path}")
        
        # 处理PDF文件
        result = process_pdf_file(pdf_path)
        
        return Response(result)
        
    except Exception as e:
        logger.error(f"URL生成处理失败: {traceback.format_exc()}")
        return Response({
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@csrf_exempt
@api_view(['POST'])
def generate_from_text(request):
    """
    通过文本问题生成图文内容
    
    POST /api/generate/text
    Body: {"question": "你的问题"}
    """
    try:
        # 获取问题文本
        question = request.data.get('question', '').strip()
        
        if not question:
            return Response({
                'success': False,
                'error': '问题不能为空'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        logger.info(f"收到文本生成请求: {question[:100]}...")
        
        # 创建基于日期的输出目录
        today = datetime.now().strftime('%Y-%m-%d')
        base_dir = Path(settings.BASE_DIR) / 'data'
        data_dir = base_dir / today
        data_dir.mkdir(parents=True, exist_ok=True)
        
        # 使用时间戳作为子目录名
        timestamp = datetime.now().strftime('%H%M%S')
        output_dir = data_dir / f"text_{timestamp}"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # 处理文本请求
        result = process_text_question(question, output_dir)
        
        return Response(result)
        
    except Exception as e:
        logger.error(f"文本生成处理失败: {traceback.format_exc()}")
        return Response({
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


def process_text_question(question: str, output_dir: Path):
    """
    处理文本问题并生成图文内容
    
    Args:
        question: 用户问题
        output_dir: 输出目录
        
    Returns:
        dict: 处理结果
    """
    try:
        # 1. 调用Dify生成内容（文本请求）
        dify_client = DifyAPIClient()
        dify_result = dify_client.run_workflow(question=question)
        logger.info(f"Dify文本解析成功: {dify_result.get('title', 'Unknown')}")
        
        # 2. 使用PaperImageProcessor处理（不传pdf_path）
        processor = PaperImageProcessor()
        process_result = processor.process(
            pdf_path=None,  # 文本请求不需要PDF
            dify_result=dify_result,
            output_dir=output_dir
        )
        
        if not process_result['success']:
            return {
                'success': False,
                'error': process_result['error'],
                'traceback': traceback.format_exc()
            }
        
        return {
            'success': True,
            'output_dir': str(output_dir),
            'images': process_result['images'],
            'title': dify_result.get('title', 'Unknown'),
            'dify_result': dify_result
        }
        
    except Exception as e:
        logger.error(f"处理文本请求失败: {traceback.format_exc()}")
        return {
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        }


def process_pdf_file(pdf_path: Path):
    """
    处理PDF文件并生成图文内容
    
    Args:
        pdf_path: PDF文件路径
        
    Returns:
        dict: 处理结果
    """
    try:
        # 1. 调用Dify生成内容
        dify_client = DifyAPIClient()
        dify_result = dify_client.run_workflow(pdf_path=str(pdf_path))
        logger.info(f"Dify解析成功: {dify_result.get('title', 'Unknown')}")
        
        # 2. 使用PaperImageProcessor处理
        processor = PaperImageProcessor()
        process_result = processor.process(pdf_path=str(pdf_path), dify_result=dify_result)
        
        if not process_result['success']:
            return {
                'success': False,
                'error': process_result['error'],
                'traceback': traceback.format_exc()
            }
        
        return {
            'success': True,
            'output_dir': str(pdf_path.parent),
            'images': process_result['images'],
            'title': dify_result.get('title', 'Unknown'),
            'dify_result': dify_result
        }
        
    except Exception as e:
        logger.error(f"处理失败: {traceback.format_exc()}")
        return {
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        }


@api_view(['GET'])
def get_content_list(request):
    """
    获取所有生成的内容列表
    
    GET /api/content/list
    """
    try:
        base_dir = Path(settings.BASE_DIR) / 'data'
        
        if not base_dir.exists():
            return Response({
                'success': True,
                'contents': []
            })
        
        contents = []
        
        # 遍历日期文件夹
        for date_dir in sorted(base_dir.iterdir(), reverse=True):
            if not date_dir.is_dir():
                continue
            
            # 遍历内容文件夹
            for content_dir in date_dir.iterdir():
                if not content_dir.is_dir():
                    continue
                
                # 读取dify_result.json
                json_path = content_dir / "dify_result.json"
                if not json_path.exists():
                    continue
                
                try:
                    with open(json_path, 'r', encoding='utf-8') as f:
                        dify_result = json.load(f)
                    
                    # 获取所有图片
                    images = []
                    for img_file in sorted(content_dir.glob("*.png")):
                        images.append(str(img_file.relative_to(base_dir)))
                    
                    contents.append({
                        'id': f"{date_dir.name}/{content_dir.name}",
                        'title': dify_result.get('title', 'Unknown'),
                        'date': date_dir.name,
                        'folder': content_dir.name,
                        'images': images,
                        'image_count': len(images)
                    })
                    
                except Exception as e:
                    logger.error(f"读取内容失败 {content_dir}: {e}")
                    continue
        
        return Response({
            'success': True,
            'contents': contents
        })
        
    except Exception as e:
        logger.error(f"获取内容列表失败: {traceback.format_exc()}")
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET', 'DELETE'])
def get_content_detail(request, content_id):
    """
    获取单个内容详情或删除内容
    
    GET /api/content/<content_id>
    DELETE /api/content/<content_id>
    content_id格式: yyyy-mm-dd/folder_name
    """
    try:
        base_dir = Path(settings.BASE_DIR) / 'data'
        content_dir = base_dir / content_id
        
        if not content_dir.exists():
            return Response({
                'success': False,
                'error': '内容不存在'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # 处理DELETE请求
        if request.method == 'DELETE':
            shutil.rmtree(content_dir)
            logger.info(f"内容已删除: {content_dir}")
            return Response({
                'success': True,
                'message': '删除成功'
            })
        
        # 处理GET请求
        # 读取dify_result.json
        json_path = content_dir / "dify_result.json"
        if not json_path.exists():
            return Response({
                'success': False,
                'error': 'dify_result.json不存在'
            }, status=status.HTTP_404_NOT_FOUND)
        
        with open(json_path, 'r', encoding='utf-8') as f:
            dify_result = json.load(f)
        
        # 获取所有图片
        images = []
        for img_file in sorted(content_dir.glob("*.png")):
            images.append(str(img_file.relative_to(base_dir)))
        
        return Response({
            'success': True,
            'id': content_id,
            'title': dify_result.get('title', 'Unknown'),
            'summary': dify_result.get('summary', []),
            'mermaid': dify_result.get('mermaid', ''),
            'images': images
        })
        
    except Exception as e:
        logger.error(f"获取内容详情失败: {traceback.format_exc()}")
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
def get_image(request):
    """
    获取图片文件
    
    GET /api/content/image?path=yyyy-mm-dd/folder_name/1.png
    """
    try:
        image_path = request.GET.get('path', '')
        
        if not image_path:
            return Response({
                'success': False,
                'error': '图片路径不能为空'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        base_dir = Path(settings.BASE_DIR) / 'data'
        full_path = base_dir / image_path
        
        if not full_path.exists():
            return Response({
                'success': False,
                'error': '图片不存在'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # 返回图片文件
        return FileResponse(open(full_path, 'rb'), content_type='image/png')
        
    except Exception as e:
        logger.error(f"获取图片失败: {traceback.format_exc()}")
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
def proxy_pdf(request):
    """
    代理下载远程PDF并流式返回，便于前端跟踪下载进度。

    GET /api/proxy/pdf/?url=<pdf_url>
    """
    try:
        url = request.GET.get('url', '').strip()
        if not url:
            return Response({'success': False, 'error': 'url 不能为空'}, status=status.HTTP_400_BAD_REQUEST)

        # 以流方式请求远程PDF
        remote = requests.get(url, stream=True, timeout=30)
        remote.raise_for_status()

        content_length = remote.headers.get('Content-Length')
        content_type = remote.headers.get('Content-Type', 'application/pdf')

        def generate():
            for chunk in remote.iter_content(chunk_size=8192):
                if chunk:
                    yield chunk

        resp = StreamingHttpResponse(generate(), content_type=content_type)
        if content_length:
            resp['Content-Length'] = content_length
        # 建议浏览器内联预览
        resp['Content-Disposition'] = 'inline; filename="preview.pdf"'
        # 允许跨域在开发中通过（可按需调整）
        resp['Access-Control-Expose-Headers'] = 'Content-Length'
        return resp
    except requests.RequestException as e:
        logger.error(f"代理PDF失败: {e}")
        return Response({'success': False, 'error': '下载远程PDF失败'}, status=status.HTTP_502_BAD_GATEWAY)
    except Exception as e:
        logger.error(f"代理PDF异常: {traceback.format_exc()}")
        return Response({'success': False, 'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

"""
首页视图
"""
import os
from pathlib import Path
from django.shortcuts import render
from django.http import JsonResponse
from django.conf import settings


def index(request):
    """
    首页视图
    
    GET /
    """
    return render(request, 'index.html')


def get_index_images(request):
    """
    获取首页背景图片列表
    
    GET /api/index/images/
    返回: {"images": ["image1.png", "image2.jpg", ...]}
    """
    index_images_path = settings.BASE_DIR / 'assets' / 'index_images'
    
    # 支持的图片格式
    image_extensions = {'.png', '.jpg', '.jpeg', '.gif', '.webp', '.svg'}
    
    images = []
    if index_images_path.exists():
        for file in sorted(index_images_path.iterdir(), reverse=True):
            if file.is_file() and file.suffix.lower() in image_extensions:
                images.append(file.name)
    
    return JsonResponse({'images': images})

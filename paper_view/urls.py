"""
URL configuration for paper_view project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

from django.views.generic import TemplateView

from core.content_views import (
    upload_pdf,
    generate_from_url,
    generate_from_text,
    get_content_list,
    get_content_detail,
    get_image,
    proxy_pdf,
)
from core.index_views import get_index_images
from core.workspace_views import search_papers
from core.wordcloud_views import extract_wordcloud_data
from core.ai_config_views import ai_model_config, ai_model_options
from core.chat_views import (
    translate_text, chat_with_text, translate_stream, 
    chat_stream, session_manage
)

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # API endpoints
    path('api/index/images/', get_index_images, name='get_index_images'),
    path('api/search/', search_papers, name='search_papers'),
    path('api/generate/upload/', upload_pdf, name='upload_pdf'),
    path('api/generate/url/', generate_from_url, name='generate_from_url'),
    path('api/generate/text/', generate_from_text, name='generate_from_text'),
    path('api/content/list/', get_content_list, name='get_content_list'),
    path('api/content/<path:content_id>/', get_content_detail, name='get_content_detail'),
    path('api/content/image/', get_image, name='get_image'),
    path('api/proxy/pdf/', proxy_pdf, name='proxy_pdf'),
    path('api/wordcloud/extract/', extract_wordcloud_data, name='extract_wordcloud_data'),
    
    # AI配置相关
    path('api/ai/config/', ai_model_config, name='ai_model_config'),
    path('api/ai/options/', ai_model_options, name='ai_model_options'),
    
    # 翻译和聊天相关
    path('api/translate/', translate_text, name='translate_text'),
    path('api/chat/', chat_with_text, name='chat_with_text'),
    path('api/translate/stream/', translate_stream, name='translate_stream'),
    path('api/chat/stream/', chat_stream, name='chat_stream'),
    
    # 会话管理
    path('api/sessions/', session_manage, name='session_list'),
    path('api/sessions/<int:session_id>/', session_manage, name='session_detail'),
]

# 开发环境下提供media和assets文件访问
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static('/assets/', document_root=settings.BASE_DIR / 'assets')

# Vue前端路由 - 捕获所有其他路由，交给Vue Router处理
# 注意：这必须放在最后，因为它会匹配所有路径
from django.urls import re_path
urlpatterns += [
    re_path(r'^.*$', TemplateView.as_view(template_name='index.html'), name='frontend'),
]

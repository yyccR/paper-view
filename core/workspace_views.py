"""
工作区视图
"""
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.db.models import Q

from .arxiv_models import ArxivPaper


def workspace(request):
    """
    工作区页面
    
    GET /workspace/
    支持URL参数:
    - q: 搜索关键词
    - url: PDF链接
    """
    return render(request, 'workspace.html')


@require_http_methods(["GET"])
def search_papers(request):
    """
    搜索论文
    
    GET /api/search/?q=关键词
    返回: {"results": [{"title": "...", "authors": "...", ...}]}
    """
    query = request.GET.get('q', '')
    
    if not query:
        return JsonResponse({'error': '请提供搜索关键词'}, status=400)
    
    # 在本地数据库中按标题模糊匹配
    qs = (
        ArxivPaper.objects
        .filter(Q(title__icontains=query))
        .order_by('-published')[:100]
    )

    results = []
    for p in qs:
        authors = []
        if isinstance(p.authors, list):
            # 支持 [{"name": "..."}, ...] 或 ["name1", "name2"] 两种格式
            for a in p.authors:
                if isinstance(a, dict):
                    authors.append(a.get('name') or a.get('full_name') or '')
                elif isinstance(a, str):
                    authors.append(a)
        authors_str = ', '.join([x for x in authors if x])

        results.append({
            'title': p.title,
            'authors': authors_str,
            'abstract': p.summary,
            'year': p.published.year if p.published else None,
            'citations': None,
            'url': p.arxiv_url,
            'pdf_url': p.pdf_url,
            'arxiv_id': p.arxiv_id,
            'primary_category': p.primary_category,
        })

    return JsonResponse({'results': results})

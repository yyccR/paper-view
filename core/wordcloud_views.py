"""
词云热力图视图
用于从PDF提取文本并生成词频数据
"""
import re
import json
from collections import Counter
from pathlib import Path
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
import requests
import fitz  # PyMuPDF
from loguru import logger


# 英文停用词列表
ENGLISH_STOPWORDS = {
    'i', 'me', 'my', 'myself', 'we', 'our', 'ours', 'ourselves', 'you', "you're", "you've",
    "you'll", "you'd", 'your', 'yours', 'yourself', 'yourselves', 'he', 'him', 'his',
    'himself', 'she', "she's", 'her', 'hers', 'herself', 'it', "it's", 'its', 'itself',
    'they', 'them', 'their', 'theirs', 'themselves', 'what', 'which', 'who', 'whom', 'this',
    'that', "that'll", 'these', 'those', 'am', 'is', 'are', 'was', 'were', 'be', 'been',
    'being', 'have', 'has', 'had', 'having', 'do', 'does', 'did', 'doing', 'a', 'an', 'the',
    'and', 'but', 'if', 'or', 'because', 'as', 'until', 'while', 'of', 'at', 'by', 'for',
    'with', 'about', 'against', 'between', 'into', 'through', 'during', 'before', 'after',
    'above', 'below', 'to', 'from', 'up', 'down', 'in', 'out', 'on', 'off', 'over', 'under',
    'again', 'further', 'then', 'once', 'here', 'there', 'when', 'where', 'why', 'how', 'all',
    'both', 'each', 'few', 'more', 'most', 'other', 'some', 'such', 'no', 'nor', 'not', 'only',
    'own', 'same', 'so', 'than', 'too', 'very', 's', 't', 'can', 'will', 'just', 'don',
    "don't", 'should', "should've", 'now', 'd', 'll', 'm', 'o', 're', 've', 'y', 'ain',
    'aren', "aren't", 'couldn', "couldn't", 'didn', "didn't", 'doesn', "doesn't", 'hadn',
    "hadn't", 'hasn', "hasn't", 'haven', "haven't", 'isn', "isn't", 'ma', 'mightn', "mightn't",
    'mustn', "mustn't", 'needn', "needn't", 'shan', "shan't", 'shouldn', "shouldn't", 'wasn',
    "wasn't", 'weren', "weren't", 'won', "won't", 'wouldn', "wouldn't", 'et', 'al', 'fig',
    'figure', 'table', 'section', 'eq', 'equation', 'ref', 'references', 'appendix', 'using',
    'used', 'use', 'based', 'two', 'one', 'also', 'may', 'however', 'thus', 'via', 'within',
    'shown', 'show', 'shows', 'result', 'results', 'including', 'different', 'large', 'small',
    'new', 'well', 'given', 'first', 'second', 'third', 'high', 'low', 'many', 'much', 'e.g',
    'i.e', 'etc', 'respectively', 'corresponding', 'obtained', 'observed', 'found', 'see',
}


def extract_text_from_pdf(pdf_path_or_url):
    """
    从PDF文件或URL提取文本
    
    Args:
        pdf_path_or_url: PDF文件路径或URL
        
    Returns:
        str: 提取的文本内容
    """
    try:
        # 判断是URL还是本地文件
        if pdf_path_or_url.startswith('http://') or pdf_path_or_url.startswith('https://'):
            # 下载PDF
            response = requests.get(pdf_path_or_url, timeout=30)
            response.raise_for_status()
            pdf_data = response.content
            doc = fitz.open(stream=pdf_data, filetype="pdf")
        else:
            # 本地文件
            doc = fitz.open(pdf_path_or_url)
        
        text = ""
        for page_num in range(len(doc)):
            page = doc[page_num]
            text += page.get_text()
        
        doc.close()
        return text
    except Exception as e:
        logger.error(f"PDF文本提取失败: {e}")
        raise


def clean_and_tokenize(text):
    """
    清理文本并分词
    
    Args:
        text: 原始文本
        
    Returns:
        list: 词语列表
    """
    # 转小写
    text = text.lower()
    
    # 移除特殊字符，只保留字母和空格
    text = re.sub(r'[^a-z\s]', ' ', text)
    
    # 分词
    words = text.split()
    
    # 过滤停用词和短词
    words = [w for w in words if w not in ENGLISH_STOPWORDS and len(w) > 3]
    
    return words


def calculate_word_frequencies(words, top_n=100):
    """
    计算词频并返回Top N
    
    Args:
        words: 词语列表
        top_n: 返回前N个高频词
        
    Returns:
        list: [(word, frequency), ...]
    """
    counter = Counter(words)
    return counter.most_common(top_n)


def generate_word_clusters(word_freq_list):
    """
    为词语生成聚类（简化版本，基于词频分组）
    
    在实际VOSviewer中，这会使用复杂的NLP算法进行语义聚类
    这里我们简化为按频率范围分组
    
    Args:
        word_freq_list: [(word, frequency), ...]
        
    Returns:
        list: [{'word': str, 'frequency': int, 'cluster': int}, ...]
    """
    if not word_freq_list:
        return []
    
    max_freq = word_freq_list[0][1]
    min_freq = word_freq_list[-1][1]
    
    # 分为5个聚类
    num_clusters = 5
    cluster_size = (max_freq - min_freq) / num_clusters if max_freq > min_freq else 1
    
    result = []
    for word, freq in word_freq_list:
        # 根据频率分配聚类
        if cluster_size > 0:
            cluster = min(num_clusters - 1, int((max_freq - freq) / cluster_size))
        else:
            cluster = 0
        
        result.append({
            'word': word,
            'frequency': freq,
            'cluster': cluster
        })
    
    return result


@csrf_exempt
@require_http_methods(["POST"])
def extract_wordcloud_data(request):
    """
    从PDF提取词云数据
    
    POST /api/wordcloud/extract/
    Body: {"pdf_url": "http://..."}
    
    Returns:
        {
            "success": true,
            "data": [
                {"word": "neural", "frequency": 45, "cluster": 0},
                {"word": "network", "frequency": 38, "cluster": 0},
                ...
            ]
        }
    """
    try:
        data = json.loads(request.body)
        pdf_url = data.get('pdf_url')
        
        if not pdf_url:
            return JsonResponse({
                'success': False,
                'error': '请提供PDF URL'
            }, status=400)
        
        # 1. 提取PDF文本
        logger.info(f"开始提取PDF文本: {pdf_url}")
        text = extract_text_from_pdf(pdf_url)
        
        # 2. 清理和分词
        logger.info("清理和分词中...")
        words = clean_and_tokenize(text)
        
        # 3. 计算词频
        logger.info("计算词频中...")
        word_freq_list = calculate_word_frequencies(words, top_n=100)
        
        # 4. 生成聚类
        logger.info("生成聚类中...")
        word_data = generate_word_clusters(word_freq_list)
        
        logger.info(f"成功提取 {len(word_data)} 个关键词")
        
        return JsonResponse({
            'success': True,
            'data': word_data
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': '无效的JSON格式'
        }, status=400)
    except Exception as e:
        logger.error(f"词云数据提取失败: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

"""
文件下载工具模块
"""
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse
import requests
from loguru import logger
from common.folder_utils import create_daily_folder


def download_pdf_from_url(
    url: str,
    base_dir: str = None,
    date: datetime = None,
    filename: str = None,
    timeout: int = 30
) -> Path:
    """
    从URL下载PDF文件到指定目录结构
    
    目录结构: base_dir/yyyy-mm-dd/url_basename/filename.pdf
    
    Args:
        url: PDF文件的URL地址
        base_dir: 基础目录路径，默认为项目根目录下的 data 文件夹
        date: 日期对象，默认为当前日期
        filename: 保存的文件名，默认使用URL中的文件名
        timeout: 请求超时时间（秒），默认30秒
    
    Returns:
        Path: 下载的PDF文件路径
    
    Raises:
        ValueError: URL无效或不是PDF文件
        requests.RequestException: 下载失败
    
    Example:
        >>> pdf_path = download_pdf_from_url('https://example.com/doc/report.pdf')
        >>> print(pdf_path)  # /path/to/project/data/2025-10-13/doc/report.pdf
        
        >>> pdf_path = download_pdf_from_url(
        ...     'https://example.com/files/report.pdf',
        ...     filename='my_report.pdf'
        ... )
    """
    # 解析URL
    parsed_url = urlparse(url)
    if not parsed_url.scheme or not parsed_url.netloc:
        raise ValueError(f"无效的URL: {url}")
    
    # 获取URL的basename（直接使用URL路径的文件名）
    url_path = parsed_url.path
    from pathlib import PurePosixPath
    url_posix_path = PurePosixPath(url_path)
    
    # 直接使用完整文件名作为basename
    if url_posix_path.name:
        url_basename = url_posix_path.name
    else:
        # 如果没有文件名，使用'pdf'作为默认basename
        url_basename = 'pdf'
    
    # 确定文件名
    if filename is None:
        # 从URL中提取文件名
        filename = url_posix_path.name if url_posix_path.name else 'downloaded.pdf'
    
    # 确保文件名以.pdf结尾
    if not filename.lower().endswith('.pdf'):
        filename += '.pdf'
    
    # 创建每日文件夹
    daily_folder = create_daily_folder(base_dir=base_dir, date=date)
    
    # 创建URL basename文件夹
    url_folder = daily_folder / url_basename
    try:
        url_folder.mkdir(parents=True, exist_ok=True)
        logger.info(f"成功创建/确认URL文件夹: {url_folder}")
    except Exception as e:
        logger.error(f"创建URL文件夹失败: {url_folder}, 错误: {e}")
        raise
    
    # 完整的文件路径
    file_path = url_folder / filename
    
    # 下载文件
    try:
        logger.info(f"开始下载PDF: {url}")
        response = requests.get(url, timeout=timeout, stream=True)
        response.raise_for_status()
        
        # 检查Content-Type是否为PDF
        content_type = response.headers.get('Content-Type', '')
        if 'application/pdf' not in content_type and not url.lower().endswith('.pdf'):
            logger.warning(f"URL可能不是PDF文件，Content-Type: {content_type}")
        
        # 写入文件
        total_size = 0
        with open(file_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    total_size += len(chunk)
        
        logger.info(f"PDF下载成功: {file_path} (大小: {total_size / 1024:.2f} KB)")
        return file_path
        
    except requests.RequestException as e:
        logger.error(f"下载PDF失败: {url}, 错误: {e}")
        # 如果下载失败，删除可能创建的空文件
        if file_path.exists():
            file_path.unlink()
        raise
    except Exception as e:
        logger.error(f"保存PDF文件失败: {file_path}, 错误: {e}")
        if file_path.exists():
            file_path.unlink()
        raise

if __name__ == '__main__':
    download_pdf_from_url(url="https://arxiv.org/abs/1803.10122")
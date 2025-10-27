"""
通用工具函数模块

此模块作为统一入口，导入并重新导出所有工具函数
以保持向后兼容性
"""

# 从 folder_utils 导入文件夹管理相关函数
from .folder_utils import (
    create_daily_folder,
    get_daily_folder_path,
    ensure_daily_folder_exists
)

# 从 download_utils 导入下载相关函数
from .download_utils import (
    download_pdf_from_url
)

# 定义公开的API
__all__ = [
    'create_daily_folder',
    'get_daily_folder_path',
    'ensure_daily_folder_exists',
    'download_pdf_from_url',
]

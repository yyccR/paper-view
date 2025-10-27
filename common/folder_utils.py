"""
文件夹管理工具模块
"""
from datetime import datetime
from pathlib import Path
from loguru import logger


def create_daily_folder(base_dir: str = None, date: datetime = None) -> Path:
    """
    在指定目录下创建每日日期格式的子文件夹
    
    Args:
        base_dir: 基础目录路径，默认为项目根目录下的 data 文件夹
        date: 日期对象，默认为当前日期
    
    Returns:
        Path: 创建的文件夹路径对象
    
    Example:
        >>> folder = create_daily_folder()
        >>> print(folder)  # /path/to/project/data/2025-10-13
        
        >>> folder = create_daily_folder(base_dir='/custom/path')
        >>> print(folder)  # /custom/path/2025-10-13
    """
    # 如果没有指定基础目录，使用项目根目录下的 data 文件夹
    if base_dir is None:
        # 获取项目根目录（manage.py 所在目录）
        current_file = Path(__file__).resolve()
        project_root = current_file.parent.parent
        base_dir = project_root / 'data'
    else:
        base_dir = Path(base_dir)
    
    # 如果没有指定日期，使用当前日期
    if date is None:
        date = datetime.now()
    
    # 格式化日期为 yyyy-mm-dd
    date_str = date.strftime('%Y-%m-%d')
    
    # 创建完整路径
    daily_folder = base_dir / date_str
    
    # 创建文件夹（如果不存在）
    try:
        daily_folder.mkdir(parents=True, exist_ok=True)
        logger.info(f"成功创建/确认文件夹: {daily_folder}")
    except Exception as e:
        logger.error(f"创建文件夹失败: {daily_folder}, 错误: {e}")
        raise
    
    return daily_folder


def get_daily_folder_path(base_dir: str = None, date: datetime = None) -> Path:
    """
    获取每日日期格式的文件夹路径（不创建）
    
    Args:
        base_dir: 基础目录路径，默认为项目根目录下的 data 文件夹
        date: 日期对象，默认为当前日期
    
    Returns:
        Path: 文件夹路径对象
    """
    if base_dir is None:
        current_file = Path(__file__).resolve()
        project_root = current_file.parent.parent
        base_dir = project_root / 'data'
    else:
        base_dir = Path(base_dir)
    
    if date is None:
        date = datetime.now()
    
    date_str = date.strftime('%Y-%m-%d')
    return base_dir / date_str


def ensure_daily_folder_exists(base_dir: str = None, date: datetime = None) -> bool:
    """
    检查每日文件夹是否存在
    
    Args:
        base_dir: 基础目录路径
        date: 日期对象，默认为当前日期
    
    Returns:
        bool: 文件夹是否存在
    """
    folder_path = get_daily_folder_path(base_dir, date)
    return folder_path.exists() and folder_path.is_dir()

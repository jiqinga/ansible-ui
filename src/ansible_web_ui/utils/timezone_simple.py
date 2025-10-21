"""
简化的时区处理 - 直接使用本地时间

如果系统只在中国使用，直接存储和使用本地时间更简单
"""

from datetime import datetime


def now_local() -> datetime:
    """
    获取当前本地时间（不带时区信息）
    
    Returns:
        datetime: 本地时间
    """
    return datetime.now()


def format_datetime(dt: datetime, fmt: str = "%Y-%m-%d %H:%M:%S") -> str:
    """
    格式化时间为字符串
    
    Args:
        dt: 时间对象
        fmt: 格式化字符串
        
    Returns:
        str: 格式化后的时间字符串
    """
    if dt is None:
        return None
    return dt.strftime(fmt)


def to_iso_string(dt: datetime) -> str:
    """
    将时间转换为ISO格式字符串
    
    Args:
        dt: 时间对象
        
    Returns:
        str: ISO格式时间字符串
    """
    if dt is None:
        return None
    return dt.isoformat()

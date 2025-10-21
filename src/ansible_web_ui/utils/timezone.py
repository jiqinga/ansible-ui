"""
时区处理工具

提供统一的时间获取入口。

说明：
- 项目仅在中国使用，直接使用系统时间
- 保留此函数作为统一入口，便于未来扩展
"""

from datetime import datetime


def now() -> datetime:
    """
    获取当前时间（用于数据库默认值和代码中获取时间）
    
    Returns:
        datetime: 当前时间
    """
    return datetime.now()

"""
基础数据模型

提供所有数据模型的基础类和通用字段。
"""

from datetime import datetime
from typing import Any, Dict, Optional
from sqlalchemy import Column, Integer, DateTime
from sqlalchemy.ext.declarative import declared_attr
from ansible_web_ui.core.database import Base
from ansible_web_ui.utils.timezone import now


class BaseModel(Base):
    """
    基础模型类，包含通用字段和方法
    """
    __abstract__ = True

    id = Column(Integer, primary_key=True, index=True, comment="主键ID")
    created_at = Column(
        DateTime, 
        default=now, 
        nullable=False,
        comment="创建时间"
    )
    updated_at = Column(
        DateTime, 
        default=now, 
        onupdate=now,
        nullable=False,
        comment="更新时间"
    )

    @declared_attr
    def __tablename__(cls) -> str:
        """
        自动生成表名（类名转换为下划线格式）
        """
        import re
        # 将驼峰命名转换为下划线命名
        name = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', cls.__name__)
        return re.sub('([a-z0-9])([A-Z])', r'\1_\2', name).lower()

    def to_dict(self) -> Dict[str, Any]:
        """
        将模型转换为字典
        
        Returns:
            Dict[str, Any]: 模型数据字典
        """
        result = {}
        for column in self.__table__.columns:
            value = getattr(self, column.name)
            if isinstance(value, datetime):
                value = value.isoformat()  # 直接使用 isoformat()
            result[column.name] = value
        return result

    def __repr__(self) -> str:
        """
        模型的字符串表示
        """
        return f"<{self.__class__.__name__}(id={self.id})>"
"""
Playbook数据模型

定义Playbook文件的数据库模型。
"""

from datetime import datetime
from typing import Optional, TYPE_CHECKING
from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from ansible_web_ui.models.base import BaseModel
from ansible_web_ui.utils.timezone import now

if TYPE_CHECKING:
    from ansible_web_ui.models.project import Project


class Playbook(BaseModel):
    """
    Playbook模型
    
    存储Playbook文件的元数据信息
    """
    __tablename__ = "playbooks"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey('projects.id'), nullable=True, index=True, comment="所属项目ID")
    filename = Column(String(255), unique=True, nullable=False, index=True, comment="文件名")
    display_name = Column(String(255), nullable=True, comment="显示名称")
    description = Column(Text, nullable=True, comment="描述")
    file_path = Column(String(500), nullable=True, comment="文件路径（缓存路径）")
    file_content = Column(Text, nullable=False, default="", comment="文件内容（存储在数据库）")
    file_size = Column(Integer, nullable=False, default=0, comment="文件大小（字节）")
    file_hash = Column(String(64), nullable=True, comment="文件哈希值")
    is_valid = Column(Boolean, nullable=False, default=True, comment="是否有效")
    validation_error = Column(Text, nullable=True, comment="验证错误信息")
    created_at = Column(DateTime, nullable=False, default=now, comment="创建时间")
    updated_at = Column(DateTime, nullable=False, default=now, onupdate=now, comment="更新时间")
    created_by = Column(Integer, nullable=True, comment="创建用户ID")
    
    # 关系
    project = relationship("Project", back_populates="playbooks")
    
    def __repr__(self) -> str:
        return f"<Playbook(id={self.id}, filename='{self.filename}', is_valid={self.is_valid})>"
    
    def to_dict(self, include_content: bool = False) -> dict:
        """
        转换为字典格式（时间自动转换为本地时区）
        
        Args:
            include_content: 是否包含文件内容（默认不包含以减少数据传输）
        """
        result = {
            "id": self.id,
            "project_id": self.project_id,
            "filename": self.filename,
            "display_name": self.display_name,
            "description": self.description,
            "file_path": self.file_path,
            "file_size": self.file_size,
            "file_hash": self.file_hash,
            "is_valid": self.is_valid,
            "validation_error": self.validation_error,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "created_by": self.created_by
        }
        if include_content:
            result["file_content"] = self.file_content
        return result
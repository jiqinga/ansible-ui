"""
项目文件数据模型

存储项目中的文件内容到数据库。
"""

from datetime import datetime
from typing import Optional, TYPE_CHECKING
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Index
from sqlalchemy.orm import relationship
from ansible_web_ui.models.base import BaseModel
from ansible_web_ui.utils.timezone import now

if TYPE_CHECKING:
    from ansible_web_ui.models.project import Project


class ProjectFile(BaseModel):
    """
    项目文件模型
    
    存储项目中每个文件的内容到数据库。
    """
    __tablename__ = "project_files"
    
    # 添加复合索引以优化查询
    __table_args__ = (
        Index('idx_project_file_path', 'project_id', 'relative_path'),
    )

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey('projects.id', ondelete='CASCADE'), nullable=False, index=True, comment="所属项目ID")
    relative_path = Column(String(500), nullable=False, comment="文件相对路径")
    file_content = Column(Text, nullable=False, default="", comment="文件内容")
    file_size = Column(Integer, nullable=False, default=0, comment="文件大小（字节）")
    file_hash = Column(String(64), nullable=True, comment="文件哈希值")
    is_directory = Column(Integer, nullable=False, default=0, comment="是否为目录（0=文件，1=目录）")
    created_at = Column(DateTime, nullable=False, default=now, comment="创建时间")
    updated_at = Column(DateTime, nullable=False, default=now, onupdate=now, comment="更新时间")
    
    # 关系
    project = relationship("Project", back_populates="files")
    
    def __repr__(self) -> str:
        return f"<ProjectFile(id={self.id}, project_id={self.project_id}, path='{self.relative_path}')>"
    
    def to_dict(self, include_content: bool = False) -> dict:
        """
        转换为字典格式
        
        Args:
            include_content: 是否包含文件内容（默认不包含以减少数据传输）
        """
        result = {
            "id": self.id,
            "project_id": self.project_id,
            "relative_path": self.relative_path,
            "file_size": self.file_size,
            "file_hash": self.file_hash,
            "is_directory": bool(self.is_directory),
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }
        if include_content:
            result["file_content"] = self.file_content
        return result

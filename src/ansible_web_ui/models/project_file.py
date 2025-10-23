"""
项目文件数据模型

存储项目中的文件内容到数据库。
"""

from datetime import datetime
from typing import Optional, TYPE_CHECKING
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Index, Boolean
from sqlalchemy.orm import relationship
from ansible_web_ui.models.base import BaseModel
from ansible_web_ui.utils.timezone import now

if TYPE_CHECKING:
    from ansible_web_ui.models.project import Project


class ProjectFile(BaseModel):
    """
    项目文件模型 - 纯数据库存储
    
    存储项目中每个文件的内容到数据库，支持 UTF-8 编码。
    通过路径前缀匹配构建文件树结构，无需 parent_id 字段。
    """
    __tablename__ = "project_files"
    
    # 添加复合唯一索引以优化查询并确保路径唯一性
    __table_args__ = (
        Index('idx_project_path', 'project_id', 'relative_path', unique=True),
    )

    # 主键和外键
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(
        Integer, 
        ForeignKey('projects.id', ondelete='CASCADE'), 
        nullable=False, 
        index=True, 
        comment="所属项目ID"
    )
    
    # 文件路径和元数据
    relative_path = Column(
        String(500), 
        nullable=False, 
        index=True, 
        comment="文件相对路径（如 'roles/common/tasks/main.yml'）"
    )
    filename = Column(
        String(255), 
        nullable=False, 
        comment="文件名（如 'main.yml'，从 relative_path 提取）"
    )
    
    # 文件内容（核心字段）
    file_content = Column(
        Text, 
        nullable=False, 
        default="", 
        comment="文件内容（UTF-8 编码，存储在数据库）"
    )
    
    # 文件属性
    file_size = Column(
        Integer, 
        nullable=False, 
        default=0, 
        comment="文件大小（字节，最大 10MB）"
    )
    file_hash = Column(
        String(64), 
        nullable=True, 
        comment="文件哈希值（SHA-256，用于完整性验证）"
    )
    is_directory = Column(
        Boolean, 
        nullable=False, 
        default=False, 
        comment="是否为目录"
    )
    
    # 时间戳
    created_at = Column(
        DateTime, 
        nullable=False, 
        default=now, 
        comment="创建时间"
    )
    updated_at = Column(
        DateTime, 
        nullable=False, 
        default=now, 
        onupdate=now, 
        comment="更新时间"
    )
    
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
            "filename": self.filename,
            "file_size": self.file_size,
            "file_hash": self.file_hash,
            "is_directory": self.is_directory,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }
        if include_content:
            result["file_content"] = self.file_content
        return result

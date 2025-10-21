"""
Role数据模型

定义Ansible Role的数据库模型。
"""

from datetime import datetime
from typing import Optional, TYPE_CHECKING
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship
from ansible_web_ui.models.base import BaseModel
from ansible_web_ui.utils.timezone import now

if TYPE_CHECKING:
    from ansible_web_ui.models.project import Project


class Role(BaseModel):
    """
    Ansible Role模型
    
    存储Role的核心元信息。
    实际的目录结构通过RoleService.get_role_structure()动态扫描获取。
    """
    __tablename__ = "roles"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey('projects.id'), nullable=False, index=True, comment="所属项目ID")
    
    name = Column(String(255), nullable=False, index=True, comment="Role名称")
    description = Column(Text, nullable=True, comment="Role描述")
    
    # Role相对路径（相对于项目根目录）
    # 例如: "roles/webserver"
    relative_path = Column(String(500), nullable=False, comment="相对路径")
    
    # 可选：存储结构元数据（JSON格式，灵活扩展）
    # 例如: {"directories": ["tasks", "handlers", "templates"], "custom": ["library"]}
    structure_metadata = Column(JSON, nullable=True, comment="结构元数据")
    
    # 元数据
    created_at = Column(DateTime, nullable=False, default=now, comment="创建时间")
    updated_at = Column(DateTime, nullable=False, default=now, onupdate=now, comment="更新时间")
    
    # 关系
    project = relationship("Project", back_populates="roles")
    
    def __repr__(self) -> str:
        return f"<Role(id={self.id}, name='{self.name}', project_id={self.project_id})>"
    
    def to_dict(self) -> dict:
        """转换为字典格式"""
        return {
            "id": self.id,
            "project_id": self.project_id,
            "name": self.name,
            "description": self.description,
            "relative_path": self.relative_path,
            "structure_metadata": self.structure_metadata,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }

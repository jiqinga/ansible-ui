"""
Project数据模型

定义Ansible项目的数据库模型。
"""

from datetime import datetime
from typing import Optional, TYPE_CHECKING
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from ansible_web_ui.models.base import BaseModel
from ansible_web_ui.utils.timezone import now

if TYPE_CHECKING:
    from ansible_web_ui.models.playbook import Playbook
    from ansible_web_ui.models.role import Role
    from ansible_web_ui.models.project_file import ProjectFile


class Project(BaseModel):
    """
    Ansible项目模型
    
    存储Ansible项目的元数据信息。
    项目的实际文件路径由StorageService统一管理。
    """
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, nullable=False, index=True, comment="项目名称（唯一标识符）")
    display_name = Column(String(255), nullable=True, comment="显示名称")
    description = Column(Text, nullable=True, comment="项目描述")
    
    # 项目类型
    project_type = Column(
        String(50), 
        nullable=False, 
        default='standard',
        comment="项目类型：standard/simple/custom"
    )
    
    # 配置文件相对路径（相对于项目根目录）
    ansible_cfg_relative_path = Column(
        String(500), 
        nullable=False,
        default='ansible.cfg',
        comment="ansible.cfg相对路径"
    )
    
    # 元数据
    created_at = Column(DateTime, nullable=False, default=now, comment="创建时间")
    updated_at = Column(DateTime, nullable=False, default=now, onupdate=now, comment="更新时间")
    created_by = Column(Integer, ForeignKey('users.id'), nullable=True, comment="创建用户ID")
    
    # 关系
    playbooks = relationship("Playbook", back_populates="project", cascade="all, delete-orphan")
    roles = relationship("Role", back_populates="project", cascade="all, delete-orphan")
    files = relationship("ProjectFile", back_populates="project", cascade="all, delete-orphan")
    
    def __repr__(self) -> str:
        return f"<Project(id={self.id}, name='{self.name}', type='{self.project_type}')>"
    
    def to_dict(self) -> dict:
        """转换为字典格式"""
        return {
            "id": self.id,
            "name": self.name,
            "display_name": self.display_name,
            "description": self.description,
            "project_type": self.project_type,
            "ansible_cfg_relative_path": self.ansible_cfg_relative_path,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "created_by": self.created_by
        }

"""
主机组数据模型

定义Ansible inventory中主机组相关的数据结构。
"""

from typing import Any, Dict, List, Optional
from sqlalchemy import Column, String, Text, Boolean, Integer, JSON
from sqlalchemy.orm import relationship
from ansible_web_ui.models.base import BaseModel
import json


class HostGroup(BaseModel):
    """
    主机组模型
    
    存储Ansible inventory中的主机组信息，包括组变量和子组关系。
    """
    __tablename__ = "host_groups"

    # 基本信息
    name = Column(
        String(100), 
        nullable=False, 
        unique=True,
        index=True,
        comment="组名"
    )
    display_name = Column(
        String(255), 
        nullable=True,
        comment="显示名称"
    )
    description = Column(
        Text, 
        nullable=True,
        comment="组描述"
    )
    
    # 层级关系
    parent_group = Column(
        String(100), 
        nullable=True,
        comment="父组名"
    )
    
    # 组变量
    variables = Column(
        JSON, 
        nullable=True,
        comment="组变量（JSON格式）"
    )
    
    # 状态信息
    is_active = Column(
        Boolean, 
        nullable=False, 
        default=True,
        comment="是否激活"
    )
    
    # 排序和显示
    sort_order = Column(
        Integer, 
        nullable=False, 
        default=0,
        comment="排序顺序"
    )
    
    # 标签和元数据
    tags = Column(
        JSON, 
        nullable=True,
        comment="组标签列表"
    )
    extra_data = Column(
        JSON, 
        nullable=True,
        comment="额外元数据"
    )

    def __repr__(self) -> str:
        return f"<HostGroup(name='{self.name}', parent='{self.parent_group}')>"

    def get_variables(self) -> Dict[str, Any]:
        """
        获取组变量
        
        Returns:
            Dict[str, Any]: 组变量字典
        """
        if not self.variables:
            return {}
        if isinstance(self.variables, dict):
            return self.variables
        try:
            return json.loads(self.variables) if isinstance(self.variables, str) else {}
        except (json.JSONDecodeError, TypeError):
            return {}

    def set_variables(self, variables: Dict[str, Any]) -> None:
        """
        设置组变量
        
        Args:
            variables: 组变量字典
        """
        self.variables = variables

    def add_variable(self, key: str, value: Any) -> None:
        """
        添加单个组变量
        
        Args:
            key: 变量名
            value: 变量值
        """
        variables = self.get_variables()
        variables[key] = value
        self.set_variables(variables)

    def remove_variable(self, key: str) -> bool:
        """
        删除组变量
        
        Args:
            key: 变量名
            
        Returns:
            bool: 是否成功删除
        """
        variables = self.get_variables()
        if key in variables:
            del variables[key]
            self.set_variables(variables)
            return True
        return False

    def get_tags(self) -> List[str]:
        """
        获取组标签列表
        
        Returns:
            List[str]: 标签列表
        """
        if not self.tags:
            return []
        if isinstance(self.tags, list):
            return self.tags
        try:
            return json.loads(self.tags) if isinstance(self.tags, str) else []
        except (json.JSONDecodeError, TypeError):
            return []

    def set_tags(self, tags: List[str]) -> None:
        """
        设置组标签
        
        Args:
            tags: 标签列表
        """
        self.tags = tags

    def add_tag(self, tag: str) -> None:
        """
        添加标签
        
        Args:
            tag: 标签名
        """
        tags = self.get_tags()
        if tag not in tags:
            tags.append(tag)
            self.set_tags(tags)

    def remove_tag(self, tag: str) -> bool:
        """
        删除标签
        
        Args:
            tag: 标签名
            
        Returns:
            bool: 是否成功删除
        """
        tags = self.get_tags()
        if tag in tags:
            tags.remove(tag)
            self.set_tags(tags)
            return True
        return False

    def get_ansible_inventory_vars(self) -> Dict[str, Any]:
        """
        获取Ansible inventory格式的组变量
        
        Returns:
            Dict[str, Any]: Ansible inventory格式的变量字典
        """
        return self.get_variables()

    @property
    def is_root_group(self) -> bool:
        """
        检查是否为根组（没有父组）
        
        Returns:
            bool: 是否为根组
        """
        return not self.parent_group

    @property
    def full_path(self) -> str:
        """
        获取组的完整路径
        
        Returns:
            str: 组的完整路径
        """
        if self.is_root_group:
            return self.name
        return f"{self.parent_group}/{self.name}"
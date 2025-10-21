"""
主机数据模型

定义Ansible inventory中主机和主机组相关的数据结构。
"""

from typing import Any, Dict, List, Optional
from sqlalchemy import Column, String, Text, Boolean, Integer, JSON
from ansible_web_ui.models.base import BaseModel
import json


class Host(BaseModel):
    """
    主机模型
    
    存储Ansible inventory中的主机信息，包括连接参数和变量。
    """
    __tablename__ = "hosts"

    # 基本信息
    hostname = Column(
        String(255), 
        nullable=False, 
        index=True,
        comment="主机名"
    )
    display_name = Column(
        String(255), 
        nullable=True,
        comment="显示名称"
    )
    description = Column(
        Text, 
        nullable=True,
        comment="主机描述"
    )
    
    # 分组信息
    group_name = Column(
        String(100), 
        nullable=False, 
        index=True,
        comment="所属主机组"
    )
    
    # 连接参数
    ansible_host = Column(
        String(255), 
        nullable=False,
        comment="Ansible连接地址（IP或域名）"
    )
    ansible_port = Column(
        Integer, 
        nullable=True, 
        default=22,
        comment="SSH连接端口"
    )
    ansible_user = Column(
        String(100), 
        nullable=True,
        comment="SSH连接用户名"
    )
    ansible_ssh_private_key_file = Column(
        String(500), 
        nullable=True,
        comment="SSH私钥文件路径"
    )
    ansible_ssh_pass = Column(
        String(255), 
        nullable=True,
        comment="SSH密码（加密存储）"
    )
    ansible_become = Column(
        Boolean, 
        nullable=False, 
        default=False,
        comment="是否使用sudo提权"
    )
    ansible_become_user = Column(
        String(100), 
        nullable=True, 
        default="root",
        comment="提权用户"
    )
    ansible_become_method = Column(
        String(50), 
        nullable=True, 
        default="sudo",
        comment="提权方法"
    )
    
    # 主机变量
    variables = Column(
        JSON, 
        nullable=True,
        comment="主机变量（JSON格式）"
    )
    
    # 状态信息
    is_active = Column(
        Boolean, 
        nullable=False, 
        default=True,
        comment="是否激活"
    )
    last_ping = Column(
        String(20), 
        nullable=True,
        comment="最后ping时间"
    )
    ping_status = Column(
        String(20), 
        nullable=True, 
        default="unknown",
        comment="ping状态：success/failed/unknown"
    )
    
    # 标签和元数据
    tags = Column(
        JSON, 
        nullable=True,
        comment="主机标签列表"
    )
    extra_data = Column(
        JSON, 
        nullable=True,
        comment="额外元数据"
    )

    def __repr__(self) -> str:
        return f"<Host(hostname='{self.hostname}', group='{self.group_name}')>"

    def get_variables(self) -> Dict[str, Any]:
        """
        获取主机变量
        
        Returns:
            Dict[str, Any]: 主机变量字典
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
        设置主机变量
        
        Args:
            variables: 主机变量字典
        """
        self.variables = variables

    def add_variable(self, key: str, value: Any) -> None:
        """
        添加单个主机变量
        
        Args:
            key: 变量名
            value: 变量值
        """
        variables = self.get_variables()
        variables[key] = value
        self.set_variables(variables)

    def remove_variable(self, key: str) -> bool:
        """
        删除主机变量
        
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
        获取主机标签列表
        
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
        设置主机标签
        
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

    def get_ansible_inventory_dict(self) -> Dict[str, Any]:
        """
        获取Ansible inventory格式的主机信息
        
        Returns:
            Dict[str, Any]: Ansible inventory格式的字典
        """
        result = {
            "ansible_host": self.ansible_host,
        }
        
        # 添加连接参数
        if self.ansible_port and self.ansible_port != 22:
            result["ansible_port"] = self.ansible_port
        if self.ansible_user:
            result["ansible_user"] = self.ansible_user
        if self.ansible_ssh_private_key_file:
            result["ansible_ssh_private_key_file"] = self.ansible_ssh_private_key_file
        if self.ansible_become:
            result["ansible_become"] = self.ansible_become
            if self.ansible_become_user:
                result["ansible_become_user"] = self.ansible_become_user
            if self.ansible_become_method:
                result["ansible_become_method"] = self.ansible_become_method
        
        # 添加自定义变量
        variables = self.get_variables()
        result.update(variables)
        
        return result

    def update_ping_status(self, status: str) -> None:
        """
        更新ping状态
        
        Args:
            status: ping状态 (success/failed/unknown)
        """
        from ansible_web_ui.utils.timezone import now
        self.ping_status = status
        self.last_ping = now().isoformat()

    @property
    def connection_string(self) -> str:
        """
        获取连接字符串用于显示
        
        Returns:
            str: 格式化的连接字符串
        """
        user_part = f"{self.ansible_user}@" if self.ansible_user else ""
        port_part = f":{self.ansible_port}" if self.ansible_port and self.ansible_port != 22 else ""
        return f"{user_part}{self.ansible_host}{port_part}"

    @property
    def is_reachable(self) -> bool:
        """
        检查主机是否可达
        
        Returns:
            bool: 主机是否可达
        """
        return self.ping_status == "success"
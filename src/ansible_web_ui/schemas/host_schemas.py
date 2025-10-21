"""
主机相关的Pydantic模式

定义主机数据的验证、序列化和反序列化规则。
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, field_validator
from datetime import datetime
import re


class HostBase(BaseModel):
    """主机基础模式"""
    hostname: str = Field(..., min_length=1, max_length=255, description="主机名")
    display_name: Optional[str] = Field(None, max_length=255, description="显示名称")
    description: Optional[str] = Field(None, description="主机描述")
    group_name: str = Field(default="ungrouped", max_length=100, description="所属主机组")
    ansible_host: str = Field(..., description="Ansible连接地址（IP或域名）")
    ansible_port: int = Field(default=22, ge=1, le=65535, description="SSH连接端口")
    ansible_user: Optional[str] = Field(None, max_length=100, description="SSH连接用户名")
    ansible_ssh_private_key_file: Optional[str] = Field(None, max_length=500, description="SSH私钥文件路径")
    ansible_ssh_pass: Optional[str] = Field(None, max_length=255, description="SSH密码（用于密码认证）")
    ansible_become: bool = Field(default=False, description="是否使用sudo提权")
    ansible_become_user: str = Field(default="root", max_length=100, description="提权用户")
    ansible_become_method: str = Field(default="sudo", max_length=50, description="提权方法")
    variables: Optional[Dict[str, Any]] = Field(default_factory=dict, description="主机变量")
    tags: Optional[List[str]] = Field(default_factory=list, description="主机标签")
    is_active: bool = Field(default=True, description="是否激活")

    @field_validator('hostname')
    @classmethod
    def validate_hostname(cls, v):
        """验证主机名格式"""
        if not re.match(r'^[a-zA-Z0-9]([a-zA-Z0-9\-\.]*[a-zA-Z0-9])?$', v):
            raise ValueError('主机名格式无效，只能包含字母、数字、连字符和点')
        return v

    @field_validator('ansible_host')
    @classmethod
    def validate_ansible_host(cls, v):
        """验证Ansible主机地址格式"""
        # 简单的IP或域名验证
        ip_pattern = r'^(\d{1,3}\.){3}\d{1,3}$'
        domain_pattern = r'^[a-zA-Z0-9]([a-zA-Z0-9\-\.]*[a-zA-Z0-9])?$'
        
        if not (re.match(ip_pattern, v) or re.match(domain_pattern, v)):
            raise ValueError('Ansible主机地址格式无效')
        return v

    @field_validator('group_name')
    @classmethod
    def validate_group_name(cls, v):
        """验证组名格式"""
        if not re.match(r'^[a-zA-Z0-9_\-]+$', v):
            raise ValueError('组名只能包含字母、数字、下划线和连字符')
        return v

    @field_validator('variables')
    @classmethod
    def validate_variables(cls, v):
        """验证变量格式"""
        if v is None:
            return {}
        
        # 检查变量名是否合法
        for key in v.keys():
            if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', key):
                raise ValueError(f'变量名 "{key}" 格式无效，必须以字母或下划线开头，只能包含字母、数字和下划线')
        
        return v

    @field_validator('tags')
    @classmethod
    def validate_tags(cls, v):
        """验证标签格式"""
        if v is None:
            return []
        
        # 检查标签格式
        for tag in v:
            if not isinstance(tag, str) or not tag.strip():
                raise ValueError('标签必须是非空字符串')
            if not re.match(r'^[a-zA-Z0-9_\-]+$', tag):
                raise ValueError(f'标签 "{tag}" 格式无效，只能包含字母、数字、下划线和连字符')
        
        return list(set(v))  # 去重


class HostCreate(HostBase):
    """创建主机的请求模式"""
    pass


class HostUpdate(BaseModel):
    """更新主机的请求模式"""
    hostname: Optional[str] = Field(None, min_length=1, max_length=255, description="主机名")
    display_name: Optional[str] = Field(None, max_length=255, description="显示名称")
    description: Optional[str] = Field(None, description="主机描述")
    group_name: Optional[str] = Field(None, max_length=100, description="所属主机组")
    ansible_host: Optional[str] = Field(None, description="Ansible连接地址")
    ansible_port: Optional[int] = Field(None, ge=1, le=65535, description="SSH连接端口")
    ansible_user: Optional[str] = Field(None, max_length=100, description="SSH连接用户名")
    ansible_ssh_private_key_file: Optional[str] = Field(None, max_length=500, description="SSH私钥文件路径")
    ansible_ssh_pass: Optional[str] = Field(None, max_length=255, description="SSH密码（用于密码认证）")
    ansible_become: Optional[bool] = Field(None, description="是否使用sudo提权")
    ansible_become_user: Optional[str] = Field(None, max_length=100, description="提权用户")
    ansible_become_method: Optional[str] = Field(None, max_length=50, description="提权方法")
    variables: Optional[Dict[str, Any]] = Field(None, description="主机变量")
    tags: Optional[List[str]] = Field(None, description="主机标签")
    is_active: Optional[bool] = Field(None, description="是否激活")

    # 使用与HostBase相同的验证器
    @field_validator('hostname')
    @classmethod
    def validate_hostname(cls, v):
        return HostBase.validate_hostname(v) if v is not None else v
    
    @field_validator('ansible_host')
    @classmethod
    def validate_ansible_host(cls, v):
        return HostBase.validate_ansible_host(v) if v is not None else v
    
    @field_validator('group_name')
    @classmethod
    def validate_group_name(cls, v):
        return HostBase.validate_group_name(v) if v is not None else v
    
    @field_validator('variables')
    @classmethod
    def validate_variables(cls, v):
        return HostBase.validate_variables(v) if v is not None else v
    
    @field_validator('tags')
    @classmethod
    def validate_tags(cls, v):
        return HostBase.validate_tags(v) if v is not None else v


class HostResponse(HostBase):
    """主机响应模式"""
    id: int = Field(..., description="主机ID")
    ping_status: Optional[str] = Field(None, description="Ping状态")
    last_ping: Optional[str] = Field(None, description="最后Ping时间")
    connection_string: str = Field(..., description="连接字符串")
    is_reachable: bool = Field(..., description="是否可达")
    extra_data: Optional[Dict[str, Any]] = Field(None, description="额外数据（包含系统信息等）")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")

    class Config:
        from_attributes = True


class HostListResponse(BaseModel):
    """主机列表响应模式"""
    hosts: List[HostResponse] = Field(..., description="主机列表")
    total: int = Field(..., description="总数量")
    page: int = Field(default=1, description="当前页码")
    page_size: int = Field(default=20, description="每页数量")
    total_pages: int = Field(..., description="总页数")


class HostVariableUpdate(BaseModel):
    """主机变量更新模式"""
    variables: Dict[str, Any] = Field(..., description="变量字典")

    @field_validator('variables')
    @classmethod
    def validate_variables(cls, v):
        """验证变量格式"""
        for key in v.keys():
            if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', key):
                raise ValueError(f'变量名 "{key}" 格式无效')
        return v


class HostTagUpdate(BaseModel):
    """主机标签更新模式"""
    tags: List[str] = Field(..., description="标签列表")

    @field_validator('tags')
    @classmethod
    def validate_tags(cls, v):
        """验证标签格式"""
        for tag in v:
            if not isinstance(tag, str) or not tag.strip():
                raise ValueError('标签必须是非空字符串')
            if not re.match(r'^[a-zA-Z0-9_\-]+$', tag):
                raise ValueError(f'标签 "{tag}" 格式无效')
        return list(set(v))


class HostPingUpdate(BaseModel):
    """主机Ping状态更新模式"""
    status: str = Field(..., description="Ping状态")

    @field_validator('status')
    @classmethod
    def validate_status(cls, v):
        """验证状态值"""
        if v not in ['success', 'failed', 'unknown']:
            raise ValueError('状态值必须是 success、failed 或 unknown')
        return v


class HostSearchRequest(BaseModel):
    """主机搜索请求模式"""
    query: Optional[str] = Field(None, description="搜索关键词")
    group_name: Optional[str] = Field(None, description="按组筛选")
    tags: Optional[List[str]] = Field(None, description="按标签筛选")
    is_active: Optional[bool] = Field(None, description="按激活状态筛选")
    ping_status: Optional[str] = Field(None, description="按Ping状态筛选")
    page: int = Field(default=1, ge=1, description="页码")
    page_size: int = Field(default=20, ge=1, le=100, description="每页数量")

    @field_validator('ping_status')
    @classmethod
    def validate_ping_status(cls, v):
        """验证Ping状态"""
        if v and v not in ['success', 'failed', 'unknown']:
            raise ValueError('Ping状态必须是 success、failed 或 unknown')
        return v
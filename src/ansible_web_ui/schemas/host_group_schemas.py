"""
主机组相关的Pydantic模式

定义主机组数据的验证、序列化和反序列化规则。
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, field_validator
from datetime import datetime
import re


class HostGroupBase(BaseModel):
    """主机组基础模式"""
    name: str = Field(..., min_length=1, max_length=100, description="组名")
    display_name: Optional[str] = Field(None, max_length=255, description="显示名称")
    description: Optional[str] = Field(None, description="组描述")
    parent_group: Optional[str] = Field(None, max_length=100, description="父组名")
    variables: Optional[Dict[str, Any]] = Field(default_factory=dict, description="组变量")
    tags: Optional[List[str]] = Field(default_factory=list, description="组标签")
    is_active: bool = Field(default=True, description="是否激活")
    sort_order: int = Field(default=0, description="排序顺序")

    @field_validator('name')
    @classmethod
    def validate_name(cls, v):
        """验证组名格式"""
        if not re.match(r'^[a-zA-Z0-9_\-]+$', v):
            raise ValueError('组名只能包含字母、数字、下划线和连字符')
        # 注意：不在这里检查保留字，因为某些系统组（如all）是合法的
        return v

    @field_validator('parent_group')
    @classmethod
    def validate_parent_group(cls, v):
        """验证父组名格式"""
        if v is None:
            return v
        if not re.match(r'^[a-zA-Z0-9_\-]+$', v):
            raise ValueError('父组名只能包含字母、数字、下划线和连字符')
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
                raise ValueError(f'变量名 "{key}" 格式无效，必须以字母或下划线开头')
        
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
                raise ValueError(f'标签 "{tag}" 格式无效')
        
        return list(set(v))  # 去重


class HostGroupCreate(HostGroupBase):
    """创建主机组的请求模式"""
    
    @field_validator('name')
    @classmethod
    def validate_name_create(cls, v):
        """验证组名格式（创建时检查保留字）"""
        if not re.match(r'^[a-zA-Z0-9_\-]+$', v):
            raise ValueError('组名只能包含字母、数字、下划线和连字符')
        if v in ['_meta']:  # 只禁止 _meta，all 是系统组可以存在
            raise ValueError('组名不能使用Ansible保留字 _meta')
        return v


class HostGroupUpdate(BaseModel):
    """更新主机组的请求模式"""
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="组名")
    display_name: Optional[str] = Field(None, max_length=255, description="显示名称")
    description: Optional[str] = Field(None, description="组描述")
    parent_group: Optional[str] = Field(None, max_length=100, description="父组名")
    variables: Optional[Dict[str, Any]] = Field(None, description="组变量")
    tags: Optional[List[str]] = Field(None, description="组标签")
    is_active: Optional[bool] = Field(None, description="是否激活")
    sort_order: Optional[int] = Field(None, description="排序顺序")

    # 使用与HostGroupBase相同的验证器
    @field_validator('name')
    @classmethod
    def validate_name(cls, v):
        return HostGroupBase.validate_name(v) if v is not None else v
    
    @field_validator('parent_group')
    @classmethod
    def validate_parent_group(cls, v):
        return HostGroupBase.validate_parent_group(v) if v is not None else v
    
    @field_validator('variables')
    @classmethod
    def validate_variables(cls, v):
        return HostGroupBase.validate_variables(v) if v is not None else v
    
    @field_validator('tags')
    @classmethod
    def validate_tags(cls, v):
        return HostGroupBase.validate_tags(v) if v is not None else v


class HostGroupResponse(HostGroupBase):
    """主机组响应模式"""
    id: int = Field(..., description="组ID")
    is_root_group: bool = Field(..., description="是否为根组")
    full_path: str = Field(..., description="完整路径")
    host_count: Optional[int] = Field(None, description="主机数量")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")

    class Config:
        from_attributes = True


class HostGroupListResponse(BaseModel):
    """主机组列表响应模式"""
    groups: List[HostGroupResponse] = Field(..., description="主机组列表")
    total: int = Field(..., description="总数量")
    page: int = Field(default=1, description="当前页码")
    page_size: int = Field(default=20, description="每页数量")
    total_pages: int = Field(..., description="总页数")


class HostGroupVariableUpdate(BaseModel):
    """主机组变量更新模式"""
    variables: Dict[str, Any] = Field(..., description="变量字典")

    @field_validator('variables')
    @classmethod
    def validate_variables(cls, v):
        """验证变量格式"""
        for key in v.keys():
            if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', key):
                raise ValueError(f'变量名 "{key}" 格式无效')
        return v


class HostGroupTreeNode(BaseModel):
    """主机组树节点模式"""
    id: int = Field(..., description="组ID")
    name: str = Field(..., description="组名")
    display_name: Optional[str] = Field(None, description="显示名称")
    description: Optional[str] = Field(None, description="组描述")
    host_count: int = Field(default=0, description="主机数量")
    children: List['HostGroupTreeNode'] = Field(default_factory=list, description="子组列表")
    variables: Dict[str, Any] = Field(default_factory=dict, description="组变量")
    tags: List[str] = Field(default_factory=list, description="组标签")
    is_active: bool = Field(default=True, description="是否激活")

    class Config:
        from_attributes = True


# 更新前向引用
HostGroupTreeNode.model_rebuild()


class InventoryResponse(BaseModel):
    """Ansible Inventory响应模式"""
    inventory: Dict[str, Any] = Field(..., description="Ansible inventory格式数据")
    groups: List[HostGroupResponse] = Field(..., description="主机组列表")
    hosts: List[Dict[str, Any]] = Field(..., description="主机列表")
    stats: Dict[str, Any] = Field(..., description="统计信息")


class InventoryStatsResponse(BaseModel):
    """Inventory统计信息响应模式"""
    total_hosts: int = Field(..., description="总主机数")
    active_hosts: int = Field(..., description="激活主机数")
    inactive_hosts: int = Field(..., description="未激活主机数")
    reachable_hosts: int = Field(..., description="可达主机数")
    unreachable_hosts: int = Field(..., description="不可达主机数")
    unknown_status_hosts: int = Field(..., description="状态未知主机数")
    total_groups: int = Field(..., description="总组数")
    group_stats: Dict[str, int] = Field(..., description="各组主机数统计")


class InventoryExportRequest(BaseModel):
    """Inventory导出请求模式"""
    format: str = Field(default="ini", description="导出格式")
    groups: Optional[List[str]] = Field(None, description="指定导出的组")
    include_variables: bool = Field(default=True, description="是否包含变量")
    include_inactive: bool = Field(default=False, description="是否包含未激活主机")

    @field_validator('format')
    @classmethod
    def validate_format(cls, v):
        """验证导出格式"""
        if v not in ['ini', 'yaml', 'json']:
            raise ValueError('导出格式必须是 ini、yaml 或 json')
        return v


class InventoryImportRequest(BaseModel):
    """Inventory导入请求模式"""
    content: str = Field(..., description="导入内容")
    format: str = Field(default="ini", description="导入格式")
    merge_mode: str = Field(default="replace", description="合并模式")
    default_group: str = Field(default="imported", description="默认组名")

    @field_validator('format')
    @classmethod
    def validate_format(cls, v):
        """验证导入格式"""
        if v not in ['ini', 'yaml', 'json']:
            raise ValueError('导入格式必须是 ini、yaml 或 json')
        return v

    @field_validator('merge_mode')
    @classmethod
    def validate_merge_mode(cls, v):
        """验证合并模式"""
        if v not in ['replace', 'merge', 'append']:
            raise ValueError('合并模式必须是 replace、merge 或 append')
        return v
"""
Role相关的Pydantic模式定义
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, validator


class RoleBase(BaseModel):
    """Role基础模式"""
    name: str = Field(..., description="Role名称", min_length=1, max_length=255)
    description: Optional[str] = Field(None, description="Role描述")
    
    @validator('name')
    def validate_name(cls, v):
        """验证Role名称"""
        if '..' in v or '/' in v or '\\' in v:
            raise ValueError('Role名称不能包含路径分隔符')
        return v


class RoleCreate(RoleBase):
    """创建Role的请求模式"""
    project_id: int = Field(..., description="所属项目ID", gt=0)
    template: str = Field(default='basic', description="Role模板：basic/full/minimal")
    
    @validator('template')
    def validate_template(cls, v):
        """验证模板名称"""
        allowed_templates = ['basic', 'full', 'minimal']
        if v not in allowed_templates:
            raise ValueError(f'模板必须是以下之一: {", ".join(allowed_templates)}')
        return v


class RoleUpdate(BaseModel):
    """更新Role的请求模式"""
    description: Optional[str] = Field(None, description="Role描述")
    structure_metadata: Optional[Dict[str, Any]] = Field(None, description="结构元数据")


class RoleResponse(RoleBase):
    """Role响应模式"""
    id: int = Field(..., description="Role ID")
    project_id: int = Field(..., description="所属项目ID")
    relative_path: str = Field(..., description="相对路径")
    structure_metadata: Optional[Dict[str, Any]] = Field(None, description="结构元数据")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    
    class Config:
        from_attributes = True


class RoleListResponse(BaseModel):
    """Role列表响应模式"""
    total: int = Field(..., description="总数")
    items: List[RoleResponse] = Field(..., description="Role列表")


class RoleDirectoryInfo(BaseModel):
    """Role目录信息"""
    exists: bool = Field(..., description="是否存在")
    files: List[str] = Field(default_factory=list, description="文件列表")
    custom: Optional[bool] = Field(None, description="是否为自定义目录")


class RoleStructureResponse(BaseModel):
    """Role结构响应模式"""
    role_name: str = Field(..., description="Role名称")
    directories: Dict[str, RoleDirectoryInfo] = Field(..., description="目录结构")
    exists: bool = Field(..., description="Role是否存在")


class RoleFileInfo(BaseModel):
    """Role文件信息"""
    name: str = Field(..., description="文件名")
    path: str = Field(..., description="相对路径")
    size: int = Field(..., description="文件大小（字节）")


class RoleFilesResponse(BaseModel):
    """Role文件列表响应模式"""
    role_id: int = Field(..., description="Role ID")
    role_name: str = Field(..., description="Role名称")
    files: List[RoleFileInfo] = Field(..., description="文件列表")

"""
项目相关的Pydantic模式定义
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, validator
from .project_file_schemas import FileTreeNode


class ProjectBase(BaseModel):
    """项目基础模式"""
    name: str = Field(..., description="项目名称（唯一标识符）", min_length=1, max_length=255)
    display_name: Optional[str] = Field(None, description="显示名称", max_length=255)
    description: Optional[str] = Field(None, description="项目描述")
    project_type: str = Field(default='standard', description="项目类型：standard/simple/custom")
    ansible_cfg_relative_path: str = Field(default='ansible.cfg', description="ansible.cfg相对路径")
    
    @validator('name')
    def validate_name(cls, v):
        """验证项目名称"""
        if '..' in v or '/' in v or '\\' in v:
            raise ValueError('项目名称不能包含路径分隔符')
        return v
    
    @validator('project_type')
    def validate_project_type(cls, v):
        """验证项目类型"""
        allowed_types = ['standard', 'simple', 'custom', 'role-based']
        if v not in allowed_types:
            raise ValueError(f'项目类型必须是以下之一: {", ".join(allowed_types)}')
        return v


class ProjectCreate(ProjectBase):
    """创建项目的请求模式"""
    template: Optional[str] = Field(None, description="项目模板名称")


class ProjectUpdate(BaseModel):
    """更新项目的请求模式"""
    display_name: Optional[str] = Field(None, description="显示名称", max_length=255)
    description: Optional[str] = Field(None, description="项目描述")
    ansible_cfg_relative_path: Optional[str] = Field(None, description="ansible.cfg相对路径")


class ProjectResponse(ProjectBase):
    """项目响应模式"""
    id: int = Field(..., description="项目ID")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    created_by: Optional[int] = Field(None, description="创建用户ID")
    
    class Config:
        from_attributes = True


class ProjectListResponse(BaseModel):
    """项目列表响应模式"""
    total: int = Field(..., description="总数")
    projects: List[ProjectResponse] = Field(..., description="项目列表")
    skip: int = Field(..., description="跳过数量")
    limit: int = Field(..., description="限制数量")


class ProjectStructureResponse(BaseModel):
    """项目结构响应模式"""
    project: ProjectResponse = Field(..., description="项目信息")
    structure: FileTreeNode = Field(..., description="目录树结构")


class ProjectValidationResponse(BaseModel):
    """项目结构验证响应模式"""
    is_valid: bool = Field(..., description="是否有效")
    project_type: str = Field(..., description="项目类型")
    missing_directories: List[str] = Field(default_factory=list, description="缺失的目录")
    missing_files: List[str] = Field(default_factory=list, description="缺失的文件")
    warnings: List[str] = Field(default_factory=list, description="警告信息")
    structure: Dict[str, Any] = Field(default_factory=dict, description="结构状态")


class CreateDirectoryRequest(BaseModel):
    """创建目录请求模式"""
    path: str = Field(..., description="相对路径", min_length=1)
    
    @validator('path')
    def validate_path(cls, v):
        """验证路径"""
        if '..' in v:
            raise ValueError('路径不能包含".."')
        return v


class MoveFileRequest(BaseModel):
    """移动文件请求模式"""
    source: str = Field(..., description="源路径", min_length=1)
    destination: str = Field(..., description="目标路径", min_length=1)
    
    @validator('source', 'destination')
    def validate_path(cls, v):
        """验证路径"""
        if '..' in v:
            raise ValueError('路径不能包含".."')
        return v


class DeleteFileRequest(BaseModel):
    """删除文件请求模式"""
    path: str = Field(..., description="相对路径", min_length=1)
    
    @validator('path')
    def validate_path(cls, v):
        """验证路径"""
        if '..' in v:
            raise ValueError('路径不能包含".."')
        return v


class FileContentRequest(BaseModel):
    """文件内容写入请求"""
    path: str = Field(..., description="文件相对路径")
    content: str = Field(..., description="文件内容")
    
    @validator('path')
    def validate_path(cls, v):
        """验证路径"""
        if '..' in v:
            raise ValueError('路径不能包含".."')
        return v


class FileContentResponse(BaseModel):
    """文件内容响应"""
    path: str = Field(..., description="文件相对路径")
    content: str = Field(..., description="文件内容")
    size: int = Field(..., description="文件大小（字节）")
    file_hash: Optional[str] = Field(None, description="文件哈希值（SHA-256）")
    hash: Optional[str] = Field(None, description="文件哈希值（SHA-256，已弃用，使用file_hash）")
    last_modified: datetime = Field(..., description="最后修改时间")

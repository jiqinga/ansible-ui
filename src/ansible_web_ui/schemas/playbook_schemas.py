"""
Playbook相关的Pydantic模式定义

定义API请求和响应的数据结构。
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, field_validator


class PlaybookBase(BaseModel):
    """Playbook基础模式"""
    filename: str = Field(..., description="文件名", max_length=255)
    display_name: Optional[str] = Field(None, description="显示名称", max_length=255)
    description: Optional[str] = Field(None, description="描述")


class PlaybookCreate(PlaybookBase):
    """创建Playbook的请求模式"""
    content: Optional[str] = Field(None, description="文件内容")
    path: Optional[str] = Field(None, description="文件路径（可选，用于指定子目录）")
    
    @field_validator('filename')
    @classmethod
    def validate_filename(cls, v):
        """验证文件名格式"""
        if not v.endswith(('.yml', '.yaml')):
            raise ValueError('文件名必须以.yml或.yaml结尾')
        if '/' in v or '\\' in v:
            raise ValueError('文件名不能包含路径分隔符')
        return v


class PlaybookUpdate(BaseModel):
    """更新Playbook的请求模式"""
    display_name: Optional[str] = Field(None, description="显示名称", max_length=255)
    description: Optional[str] = Field(None, description="描述")
    content: Optional[str] = Field(None, description="文件内容")


class PlaybookInfo(PlaybookBase):
    """Playbook信息响应模式"""
    id: int = Field(..., description="ID")
    project_id: Optional[int] = Field(None, description="所属项目ID")
    file_path: Optional[str] = Field(None, description="文件路径（缓存路径）")
    file_size: int = Field(..., description="文件大小（字节）")
    file_hash: Optional[str] = Field(None, description="文件哈希值")
    is_valid: bool = Field(..., description="是否有效")
    validation_error: Optional[str] = Field(None, description="验证错误信息")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    created_by: Optional[int] = Field(None, description="创建用户ID")

    class Config:
        from_attributes = True


class PlaybookContent(BaseModel):
    """Playbook内容响应模式"""
    filename: str = Field(..., description="文件名")
    content: str = Field(..., description="文件内容")
    file_size: int = Field(..., description="文件大小（字节）")
    last_modified: datetime = Field(..., description="最后修改时间")


class ValidationIssue(BaseModel):
    """验证问题详情"""
    line: int = Field(..., description="行号")
    column: int = Field(..., description="列号")
    message: str = Field(..., description="问题描述")
    suggestion: Optional[str] = Field(None, description="修复建议")
    severity: Optional[str] = Field(None, description="严重程度")
    code: Optional[str] = Field(None, description="错误代码")


class PlaybookValidationResult(BaseModel):
    """Playbook验证结果模式"""
    is_valid: bool = Field(..., description="是否有效")
    errors: List[ValidationIssue] = Field(default_factory=list, description="错误列表")
    warnings: List[ValidationIssue] = Field(default_factory=list, description="警告列表")
    syntax_errors: List[Dict[str, Any]] = Field(default_factory=list, description="语法错误详情")


class PlaybookListResponse(BaseModel):
    """Playbook列表响应模式"""
    items: List[PlaybookInfo] = Field(..., description="Playbook列表")
    total: int = Field(..., description="总数量")
    page: int = Field(..., description="当前页码")
    size: int = Field(..., description="每页大小")
    pages: int = Field(..., description="总页数")


class PlaybookUploadResponse(BaseModel):
    """文件上传响应模式"""
    filename: str = Field(..., description="文件名")
    file_size: int = Field(..., description="文件大小")
    upload_path: Optional[str] = Field(None, description="上传路径（缓存路径）")
    is_valid: bool = Field(..., description="是否有效")
    validation_result: Optional[PlaybookValidationResult] = Field(None, description="验证结果")


class PlaybookExecutionConfig(BaseModel):
    """Playbook执行配置模式"""
    playbook_id: int = Field(..., description="Playbook ID")
    inventory_targets: List[str] = Field(..., description="目标主机列表")
    extra_vars: Optional[Dict[str, Any]] = Field(default_factory=dict, description="额外变量")
    tags: Optional[List[str]] = Field(default_factory=list, description="标签列表")
    skip_tags: Optional[List[str]] = Field(default_factory=list, description="跳过的标签列表")
    limit: Optional[str] = Field(None, description="限制主机")
    check_mode: bool = Field(False, description="检查模式")
    diff_mode: bool = Field(False, description="差异模式")
    verbose_level: int = Field(0, description="详细级别", ge=0, le=4)
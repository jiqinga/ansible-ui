"""
配置管理相关的数据模式定义

定义配置管理API的请求和响应数据结构。
"""

from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field, validator
from datetime import datetime


class ConfigValueSchema(BaseModel):
    """配置值模式"""
    value: Any = Field(..., description="配置值")
    description: Optional[str] = Field(None, description="配置描述")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class ConfigItemSchema(BaseModel):
    """配置项模式"""
    key: str = Field(..., description="配置键名")
    value: Any = Field(..., description="配置值")
    description: Optional[str] = Field(None, description="配置描述")
    category: str = Field("general", description="配置分类")
    is_sensitive: bool = Field(False, description="是否为敏感信息")
    is_readonly: bool = Field(False, description="是否只读")
    requires_restart: bool = Field(False, description="修改后是否需要重启")
    validation_rule: Optional[Dict[str, Any]] = Field(None, description="验证规则")
    default_value: Optional[Any] = Field(None, description="默认值")
    created_at: Optional[datetime] = Field(None, description="创建时间")
    updated_at: Optional[datetime] = Field(None, description="更新时间")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class ConfigUpdateSchema(BaseModel):
    """配置更新模式"""
    value: Any = Field(..., description="新的配置值")
    
    @validator('value')
    def validate_value_not_none(cls, v):
        if v is None:
            raise ValueError("配置值不能为None")
        return v


class ConfigBatchUpdateSchema(BaseModel):
    """批量配置更新模式"""
    configs: Dict[str, Any] = Field(..., description="配置更新字典")
    
    @validator('configs')
    def validate_configs_not_empty(cls, v):
        if not v:
            raise ValueError("配置更新不能为空")
        return v


class ConfigCategorySchema(BaseModel):
    """配置分类模式"""
    name: str = Field(..., description="分类名称")
    display_name: str = Field(..., description="显示名称")
    count: int = Field(..., description="配置项数量")
    description: str = Field("", description="分类描述")


class ConfigValidationResultSchema(BaseModel):
    """配置验证结果模式"""
    valid: bool = Field(..., description="是否验证通过")
    errors: Dict[str, str] = Field(default_factory=dict, description="验证错误信息")
    restart_required: List[str] = Field(default_factory=list, description="需要重启的配置项")
    warnings: List[str] = Field(default_factory=list, description="警告信息")


class ConfigUpdateResultSchema(BaseModel):
    """配置更新结果模式"""
    success: bool = Field(..., description="是否更新成功")
    errors: Dict[str, str] = Field(default_factory=dict, description="更新错误信息")
    updated: Dict[str, bool] = Field(default_factory=dict, description="更新结果详情")
    restart_required: List[str] = Field(default_factory=list, description="需要重启的配置项")


class AnsibleConfigFileSchema(BaseModel):
    """Ansible配置文件模式"""
    content: str = Field(..., description="配置文件内容")
    
    @validator('content')
    def validate_content_not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError("配置文件内容不能为空")
        return v


class ConfigExportSchema(BaseModel):
    """配置导出模式"""
    category: Optional[str] = Field(None, description="导出的配置分类")
    include_sensitive: bool = Field(False, description="是否包含敏感配置")


class ConfigImportSchema(BaseModel):
    """配置导入模式"""
    configs: Dict[str, Dict[str, Any]] = Field(..., description="导入的配置数据")
    overwrite: bool = Field(False, description="是否覆盖现有配置")
    
    @validator('configs')
    def validate_configs_format(cls, v):
        if not v:
            raise ValueError("导入配置不能为空")
        
        for key, config_data in v.items():
            if not isinstance(config_data, dict):
                raise ValueError(f"配置项 {key} 的数据格式无效")
            if 'value' not in config_data:
                raise ValueError(f"配置项 {key} 缺少value字段")
        
        return v


class ConfigImportResultSchema(BaseModel):
    """配置导入结果模式"""
    success: bool = Field(..., description="是否导入成功")
    results: Dict[str, str] = Field(..., description="导入结果详情")
    total_count: int = Field(..., description="总配置项数")
    success_count: int = Field(..., description="成功导入数")
    error_count: int = Field(..., description="导入失败数")


class ConfigResetSchema(BaseModel):
    """配置重置模式"""
    keys: List[str] = Field(..., description="要重置的配置键列表")
    
    @validator('keys')
    def validate_keys_not_empty(cls, v):
        if not v:
            raise ValueError("重置配置键列表不能为空")
        return v


class ConfigResetResultSchema(BaseModel):
    """配置重置结果模式"""
    success: bool = Field(..., description="是否重置成功")
    results: Dict[str, bool] = Field(..., description="重置结果详情")
    errors: Dict[str, str] = Field(default_factory=dict, description="重置错误信息")


class SystemStatusSchema(BaseModel):
    """系统状态模式"""
    ansible_config_valid: bool = Field(..., description="Ansible配置是否有效")
    database_connected: bool = Field(..., description="数据库是否连接")
    redis_connected: bool = Field(..., description="Redis是否连接")
    disk_usage_percent: float = Field(..., description="磁盘使用率")
    memory_usage_percent: float = Field(..., description="内存使用率")
    active_tasks: int = Field(..., description="活跃任务数")
    last_check_time: datetime = Field(..., description="最后检查时间")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class ConfigBackupSchema(BaseModel):
    """配置备份模式"""
    backup_name: str = Field(..., description="备份名称")
    description: Optional[str] = Field(None, description="备份描述")
    include_categories: Optional[List[str]] = Field(None, description="包含的配置分类")
    
    @validator('backup_name')
    def validate_backup_name(cls, v):
        if not v or not v.strip():
            raise ValueError("备份名称不能为空")
        
        # 检查备份名称格式
        import re
        if not re.match(r'^[a-zA-Z0-9_\-\u4e00-\u9fff]+$', v):
            raise ValueError("备份名称只能包含字母、数字、下划线、连字符和中文字符")
        
        return v.strip()


class ConfigBackupInfoSchema(BaseModel):
    """配置备份信息模式"""
    name: str = Field(..., description="备份名称")
    description: Optional[str] = Field(None, description="备份描述")
    created_at: datetime = Field(..., description="创建时间")
    size: int = Field(..., description="备份文件大小（字节）")
    config_count: int = Field(..., description="配置项数量")
    categories: List[str] = Field(..., description="包含的配置分类")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class ConfigRestoreSchema(BaseModel):
    """配置恢复模式"""
    backup_name: str = Field(..., description="备份名称")
    overwrite: bool = Field(False, description="是否覆盖现有配置")
    restore_categories: Optional[List[str]] = Field(None, description="要恢复的配置分类")
    
    @validator('backup_name')
    def validate_backup_name_not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError("备份名称不能为空")
        return v.strip()


class ConfigDiffSchema(BaseModel):
    """配置差异模式"""
    key: str = Field(..., description="配置键名")
    current_value: Any = Field(..., description="当前值")
    new_value: Any = Field(..., description="新值")
    action: str = Field(..., description="操作类型：add/update/delete")
    
    @validator('action')
    def validate_action(cls, v):
        if v not in ['add', 'update', 'delete']:
            raise ValueError("操作类型必须是 add、update 或 delete")
        return v


class ConfigCompareResultSchema(BaseModel):
    """配置比较结果模式"""
    differences: List[ConfigDiffSchema] = Field(..., description="配置差异列表")
    total_differences: int = Field(..., description="总差异数")
    additions: int = Field(..., description="新增配置数")
    updates: int = Field(..., description="更新配置数")
    deletions: int = Field(..., description="删除配置数")


# 响应模式
class ConfigListResponseSchema(BaseModel):
    """配置列表响应模式"""
    configs: List[ConfigItemSchema] = Field(..., description="配置项列表")
    total: int = Field(..., description="总数量")
    categories: List[ConfigCategorySchema] = Field(..., description="分类列表")


class ConfigDetailResponseSchema(BaseModel):
    """配置详情响应模式"""
    config: ConfigItemSchema = Field(..., description="配置项详情")


class ConfigCategoriesResponseSchema(BaseModel):
    """配置分类响应模式"""
    categories: List[ConfigCategorySchema] = Field(..., description="分类列表")


class AnsibleConfigResponseSchema(BaseModel):
    """Ansible配置响应模式"""
    content: str = Field(..., description="配置文件内容")
    is_valid: bool = Field(..., description="配置是否有效")
    last_modified: Optional[datetime] = Field(None, description="最后修改时间")
    backup_available: bool = Field(..., description="是否有备份可用")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class ConfigBackupListResponseSchema(BaseModel):
    """配置备份列表响应模式"""
    backups: List[ConfigBackupInfoSchema] = Field(..., description="备份列表")
    total: int = Field(..., description="总数量")


# 错误响应模式
class ConfigErrorResponseSchema(BaseModel):
    """配置错误响应模式"""
    error: str = Field(..., description="错误信息")
    details: Optional[Dict[str, Any]] = Field(None, description="错误详情")
    code: Optional[str] = Field(None, description="错误代码")
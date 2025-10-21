"""
数据模式定义

包含用于API请求和响应的Pydantic模式。
"""

from .host_schemas import *
from .host_group_schemas import *
from .playbook_schemas import *
from .config_schemas import *
from .logging_schemas import *

__all__ = [
    # 主机相关模式
    "HostBase",
    "HostCreate", 
    "HostUpdate",
    "HostResponse",
    "HostListResponse",
    "HostVariableUpdate",
    "HostTagUpdate",
    
    # 主机组相关模式
    "HostGroupBase",
    "HostGroupCreate",
    "HostGroupUpdate", 
    "HostGroupResponse",
    "HostGroupListResponse",
    "HostGroupVariableUpdate",
    
    # Inventory相关模式
    "InventoryResponse",
    "InventoryStatsResponse",
    
    # Playbook相关模式
    "PlaybookBase",
    "PlaybookCreate",
    "PlaybookUpdate",
    "PlaybookInfo",
    "PlaybookContent",
    "PlaybookValidationResult",
    "PlaybookListResponse",
    "PlaybookUploadResponse",
    "PlaybookExecutionConfig",
    
    # 配置管理相关模式
    "ConfigValueSchema",
    "ConfigItemSchema",
    "ConfigUpdateSchema",
    "ConfigBatchUpdateSchema",
    "ConfigCategorySchema",
    "ConfigValidationResultSchema",
    "ConfigUpdateResultSchema",
    "AnsibleConfigFileSchema",
    "ConfigExportSchema",
    "ConfigImportSchema",
    "ConfigImportResultSchema",
    "ConfigResetSchema",
    "ConfigResetResultSchema",
    "SystemStatusSchema",
    "ConfigBackupSchema",
    "ConfigBackupInfoSchema",
    "ConfigRestoreSchema",
    "ConfigDiffSchema",
    "ConfigCompareResultSchema",
    "ConfigListResponseSchema",
    "ConfigDetailResponseSchema",
    "ConfigCategoriesResponseSchema",
    "AnsibleConfigResponseSchema",
    "ConfigBackupListResponseSchema",
    "ConfigErrorResponseSchema"
    ,
    # 日志模块
    "LogEntrySchema",
    "LogQueryFilters",
    "LogQueryResponse"
]

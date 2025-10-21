"""
配置管理API端点

提供系统配置管理的RESTful API接口。
"""

from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from ansible_web_ui.core.database import get_db_session
from ansible_web_ui.auth.dependencies import get_current_active_user, require_permission
from ansible_web_ui.auth.permissions import Permission
from ansible_web_ui.models.user import User
from ansible_web_ui.services.config_management_service import ConfigManagementService
from ansible_web_ui.schemas.config_schemas import (
    ConfigItemSchema,
    ConfigUpdateSchema,
    ConfigBatchUpdateSchema,
    ConfigCategorySchema,
    ConfigValidationResultSchema,
    ConfigUpdateResultSchema,
    AnsibleConfigFileSchema,
    ConfigExportSchema,
    ConfigImportSchema,
    ConfigImportResultSchema,
    ConfigResetSchema,
    ConfigResetResultSchema,
    SystemStatusSchema,
    ConfigBackupSchema,
    ConfigBackupInfoSchema,
    ConfigRestoreSchema,
    ConfigListResponseSchema,
    ConfigDetailResponseSchema,
    ConfigCategoriesResponseSchema,
    AnsibleConfigResponseSchema,
    ConfigBackupListResponseSchema,
    ConfigErrorResponseSchema,
    ConfigCompareResultSchema,
    ConfigDiffSchema
)

router = APIRouter(prefix="/config", tags=["配置管理"])


@router.get(
    "/categories",
    response_model=ConfigCategoriesResponseSchema,
    summary="获取配置分类",
    description="获取所有配置分类及其统计信息"
)
async def get_config_categories(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session)
):
    """获取配置分类列表"""
    service = ConfigManagementService(db)
    
    try:
        categories = await service.get_config_categories()
        return ConfigCategoriesResponseSchema(categories=categories)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取配置分类失败: {str(e)}"
        )


@router.get(
    "/category/{category}",
    response_model=ConfigListResponseSchema,
    summary="获取分类配置",
    description="根据分类获取配置项列表"
)
async def get_configs_by_category(
    category: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session)
):
    """根据分类获取配置项"""
    service = ConfigManagementService(db)
    
    try:
        configs_data = await service.get_configs_by_category(category)
        categories = await service.get_config_categories()
        
        # 转换为ConfigItemSchema格式
        configs = []
        for key, config_data in configs_data.items():
            config_item = ConfigItemSchema(
                key=key,
                value=config_data["value"],
                description=config_data["description"],
                category=category,
                is_sensitive=config_data["is_sensitive"],
                is_readonly=config_data["is_readonly"],
                requires_restart=config_data["requires_restart"],
                validation_rule=config_data["validation_rule"],
                default_value=config_data["default_value"]
            )
            configs.append(config_item)
        
        return ConfigListResponseSchema(
            configs=configs,
            total=len(configs),
            categories=categories
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取配置失败: {str(e)}"
        )


@router.get(
    "/backups",
    response_model=ConfigBackupListResponseSchema,
    summary="获取配置备份列表",
    description="获取所有配置备份的列表"
)
async def list_config_backups(
    current_user: User = Depends(require_permission(Permission.VIEW_SYSTEM_CONFIG)),
    db: AsyncSession = Depends(get_db_session)
):
    """获取配置备份列表"""
    service = ConfigManagementService(db)
    
    try:
        backups_data = await service.list_config_backups()
        
        # 转换为schema格式
        backups = []
        for backup_data in backups_data:
            backup_info = ConfigBackupInfoSchema(
                name=backup_data["name"],
                description=backup_data["description"],
                created_at=backup_data["created_at"],
                size=backup_data["size"],
                config_count=backup_data["config_count"],
                categories=backup_data["categories"]
            )
            backups.append(backup_info)
        
        return ConfigBackupListResponseSchema(
            backups=backups,
            total=len(backups)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取配置备份列表失败: {str(e)}"
        )


@router.get(
    "/{key}",
    response_model=ConfigDetailResponseSchema,
    summary="获取配置详情",
    description="根据配置键获取配置项详情"
)
async def get_config_detail(
    key: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session)
):
    """获取单个配置项详情"""
    service = ConfigManagementService(db)
    
    try:
        # 获取配置值
        value = await service.get_config_value(key)
        if value is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"配置项 '{key}' 不存在"
            )
        
        # 获取配置的完整信息
        system_config_service = service.system_config_service
        config = await system_config_service.get_config_by_key(key)
        
        if not config:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"配置项 '{key}' 不存在"
            )
        
        config_item = ConfigItemSchema(
            key=config.key,
            value=config.get_value(),
            description=config.description,
            category=config.category,
            is_sensitive=config.is_sensitive,
            is_readonly=config.is_readonly,
            requires_restart=config.requires_restart,
            validation_rule=config.get_validation_rule(),
            default_value=config.get_default_value(),
            created_at=config.created_at,
            updated_at=config.updated_at
        )
        
        return ConfigDetailResponseSchema(config=config_item)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取配置详情失败: {str(e)}"
        )


@router.put(
    "/{key}",
    response_model=ConfigUpdateResultSchema,
    summary="更新配置",
    description="更新单个配置项的值"
)
async def update_config(
    key: str,
    config_update: ConfigUpdateSchema,
    current_user: User = Depends(require_permission(Permission.UPDATE_SYSTEM_CONFIG)),
    db: AsyncSession = Depends(get_db_session)
):
    """更新单个配置项"""
    service = ConfigManagementService(db)
    
    try:
        # 验证配置变更
        validation_result = await service.validate_config_changes({key: config_update.value})
        if not validation_result["valid"]:
            return ConfigUpdateResultSchema(
                success=False,
                errors=validation_result["errors"],
                updated={key: False},
                restart_required=validation_result["restart_required"]
            )
        
        # 更新配置
        success, error = await service.set_config_value(key, config_update.value)
        
        return ConfigUpdateResultSchema(
            success=success,
            errors={key: error} if error else {},
            updated={key: success},
            restart_required=validation_result["restart_required"] if success else []
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新配置失败: {str(e)}"
        )


@router.post(
    "/batch-update",
    response_model=ConfigUpdateResultSchema,
    summary="批量更新配置",
    description="批量更新多个配置项"
)
async def batch_update_configs(
    batch_update: ConfigBatchUpdateSchema,
    current_user: User = Depends(require_permission(Permission.UPDATE_SYSTEM_CONFIG)),
    db: AsyncSession = Depends(get_db_session)
):
    """批量更新配置项"""
    service = ConfigManagementService(db)
    
    try:
        result = await service.update_multiple_configs(batch_update.configs)
        
        return ConfigUpdateResultSchema(
            success=result["success"],
            errors=result["errors"],
            updated=result["updated"],
            restart_required=[]  # 需要从验证结果中获取
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"批量更新配置失败: {str(e)}"
        )


@router.post(
    "/validate",
    response_model=ConfigValidationResultSchema,
    summary="验证配置变更",
    description="验证配置变更是否有效"
)
async def validate_config_changes(
    batch_update: ConfigBatchUpdateSchema,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session)
):
    """验证配置变更"""
    service = ConfigManagementService(db)
    
    try:
        result = await service.validate_config_changes(batch_update.configs)
        
        return ConfigValidationResultSchema(
            valid=result["valid"],
            errors=result["errors"],
            restart_required=result["restart_required"],
            warnings=result["warnings"]
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"验证配置变更失败: {str(e)}"
        )


@router.post(
    "/reset",
    response_model=ConfigResetResultSchema,
    summary="重置配置",
    description="将指定配置项重置为默认值"
)
async def reset_configs(
    reset_request: ConfigResetSchema,
    current_user: User = Depends(require_permission(Permission.UPDATE_SYSTEM_CONFIG)),
    db: AsyncSession = Depends(get_db_session)
):
    """重置配置为默认值"""
    service = ConfigManagementService(db)
    
    try:
        results = {}
        errors = {}
        
        for key in reset_request.keys:
            success, error = await service.reset_config_to_default(key)
            results[key] = success
            if error:
                errors[key] = error
        
        return ConfigResetResultSchema(
            success=all(results.values()),
            results=results,
            errors=errors
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"重置配置失败: {str(e)}"
        )


@router.get(
    "/ansible/file",
    response_model=AnsibleConfigResponseSchema,
    summary="获取Ansible配置文件",
    description="获取Ansible配置文件内容"
)
async def get_ansible_config_file(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session)
):
    """获取Ansible配置文件内容"""
    service = ConfigManagementService(db)
    
    try:
        content = await service.get_ansible_config_file_content()
        
        # 检查配置文件是否有效
        is_valid, _ = service._validate_ansible_config_content(content)
        
        # 检查是否有备份文件
        backup_available = service.ansible_config_backup_path.exists()
        
        # 获取文件修改时间
        last_modified = None
        if service.ansible_config_path.exists():
            import os
            from datetime import datetime
            from ansible_web_ui.utils.timezone import now
            timestamp = os.path.getmtime(service.ansible_config_path)
            last_modified = datetime.fromtimestamp(timestamp)
        
        return AnsibleConfigResponseSchema(
            content=content,
            is_valid=is_valid,
            last_modified=last_modified,
            backup_available=backup_available
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取Ansible配置文件失败: {str(e)}"
        )


@router.put(
    "/ansible/file",
    response_model=ConfigUpdateResultSchema,
    summary="更新Ansible配置文件",
    description="更新Ansible配置文件内容"
)
async def update_ansible_config_file(
    config_file: AnsibleConfigFileSchema,
    current_user: User = Depends(require_permission(Permission.MANAGE_ANSIBLE_CONFIG)),
    db: AsyncSession = Depends(get_db_session)
):
    """更新Ansible配置文件"""
    service = ConfigManagementService(db)
    
    try:
        success, error = await service.update_ansible_config_file(config_file.content)
        
        return ConfigUpdateResultSchema(
            success=success,
            errors={"ansible_config": error} if error else {},
            updated={"ansible_config": success},
            restart_required=["ansible_service"] if success else []
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新Ansible配置文件失败: {str(e)}"
        )


@router.post(
    "/ansible/restore-backup",
    response_model=ConfigUpdateResultSchema,
    summary="恢复Ansible配置备份",
    description="从备份文件恢复Ansible配置"
)
async def restore_ansible_config_backup(
    current_user: User = Depends(require_permission(Permission.MANAGE_ANSIBLE_CONFIG)),
    db: AsyncSession = Depends(get_db_session)
):
    """恢复Ansible配置文件备份"""
    service = ConfigManagementService(db)
    
    try:
        success, error = await service.restore_ansible_config_backup()
        
        return ConfigUpdateResultSchema(
            success=success,
            errors={"restore": error} if error else {},
            updated={"ansible_config": success},
            restart_required=["ansible_service"] if success else []
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"恢复Ansible配置备份失败: {str(e)}"
        )


@router.get(
    "/export/{category}",
    summary="导出配置",
    description="导出指定分类的配置"
)
async def export_configs(
    category: str,
    current_user: User = Depends(require_permission(Permission.VIEW_SYSTEM_CONFIG)),
    db: AsyncSession = Depends(get_db_session)
):
    """导出配置"""
    service = ConfigManagementService(db)
    
    try:
        # 导出配置数据
        export_data = await service.system_config_service.export_configs(category)
        
        # 创建临时文件
        import tempfile
        import json
        from pathlib import Path
        
        temp_file = tempfile.NamedTemporaryFile(
            mode='w',
            suffix=f'_{category}_config.json',
            delete=False,
            encoding='utf-8'
        )
        
        json.dump(export_data, temp_file, ensure_ascii=False, indent=2)
        temp_file.close()
        
        return FileResponse(
            path=temp_file.name,
            filename=f"{category}_config.json",
            media_type="application/json"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"导出配置失败: {str(e)}"
        )


@router.post(
    "/import",
    response_model=ConfigImportResultSchema,
    summary="导入配置",
    description="从文件导入配置"
)
async def import_configs(
    file: UploadFile = File(...),
    overwrite: bool = False,
    current_user: User = Depends(require_permission(Permission.UPDATE_SYSTEM_CONFIG)),
    db: AsyncSession = Depends(get_db_session)
):
    """导入配置"""
    service = ConfigManagementService(db)
    
    try:
        # 读取上传的文件
        content = await file.read()
        
        # 解析JSON数据
        import json
        try:
            config_data = json.loads(content.decode('utf-8'))
        except json.JSONDecodeError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"配置文件格式无效: {str(e)}"
            )
        
        # 导入配置
        results = await service.system_config_service.import_configs(config_data, overwrite)
        
        # 统计结果
        total_count = len(results)
        success_count = sum(1 for status in results.values() if "成功" in status)
        error_count = total_count - success_count
        
        return ConfigImportResultSchema(
            success=error_count == 0,
            results=results,
            total_count=total_count,
            success_count=success_count,
            error_count=error_count
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"导入配置失败: {str(e)}"
        )


@router.get(
    "/system/status",
    response_model=SystemStatusSchema,
    summary="获取系统状态",
    description="获取系统运行状态信息"
)
async def get_system_status(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session)
):
    """获取系统状态"""
    service = ConfigManagementService(db)
    
    try:
        from datetime import datetime
        import psutil
        
        # 检查Ansible配置有效性
        ansible_config_content = await service.get_ansible_config_file_content()
        ansible_config_valid, _ = service._validate_ansible_config_content(ansible_config_content)
        
        # 检查数据库连接
        database_connected = True
        try:
            await db.execute("SELECT 1")
        except Exception:
            database_connected = False
        
        # 检查Redis连接（如果配置了）
        redis_connected = True  # 简化实现，实际应该检查Redis连接
        
        # 获取系统资源使用情况
        disk_usage = psutil.disk_usage('/').percent
        memory_usage = psutil.virtual_memory().percent
        
        # 获取活跃任务数（简化实现）
        active_tasks = 0  # 实际应该从任务队列获取
        
        return SystemStatusSchema(
            ansible_config_valid=ansible_config_valid,
            database_connected=database_connected,
            redis_connected=redis_connected,
            disk_usage_percent=disk_usage,
            memory_usage_percent=memory_usage,
            active_tasks=active_tasks,
            last_check_time=now()
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取系统状态失败: {str(e)}"
        )


@router.post(
    "/initialize",
    summary="初始化默认配置",
    description="初始化系统默认配置项"
)
async def initialize_default_configs(
    current_user: User = Depends(require_permission(Permission.SYSTEM_ADMIN)),
    db: AsyncSession = Depends(get_db_session)
):
    """初始化默认配置"""
    service = ConfigManagementService(db)
    
    try:
        await service.initialize_default_configs()
        
        return {"message": "🎯 默认配置初始化成功"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"初始化默认配置失败: {str(e)}"
        )


@router.post(
    "/backup",
    summary="创建配置备份",
    description="创建系统配置备份"
)
async def create_config_backup(
    backup_request: ConfigBackupSchema,
    current_user: User = Depends(require_permission(Permission.UPDATE_SYSTEM_CONFIG)),
    db: AsyncSession = Depends(get_db_session)
):
    """创建配置备份"""
    service = ConfigManagementService(db)
    
    try:
        success, error = await service.create_config_backup(
            backup_name=backup_request.backup_name,
            description=backup_request.description,
            categories=backup_request.include_categories  # Schema中使用include_categories，映射到service的categories参数
        )
        
        if success:
            return {"message": f"🎯 配置备份 '{backup_request.backup_name}' 创建成功"}
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=error
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建配置备份失败: {str(e)}"
        )


@router.post(
    "/restore",
    response_model=ConfigImportResultSchema,
    summary="恢复配置备份",
    description="从备份恢复配置"
)
async def restore_config_backup(
    restore_request: ConfigRestoreSchema,
    current_user: User = Depends(require_permission(Permission.UPDATE_SYSTEM_CONFIG)),
    db: AsyncSession = Depends(get_db_session)
):
    """恢复配置备份"""
    service = ConfigManagementService(db)
    
    try:
        success, error, results = await service.restore_config_backup(
            backup_name=restore_request.backup_name,
            overwrite=restore_request.overwrite,
            categories=restore_request.restore_categories  # Schema中使用restore_categories，映射到service的categories参数
        )
        
        # 统计结果
        total_count = len(results)
        success_count = sum(1 for status in results.values() if "成功" in status)
        error_count = total_count - success_count
        
        return ConfigImportResultSchema(
            success=success,
            results=results,
            total_count=total_count,
            success_count=success_count,
            error_count=error_count
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"恢复配置备份失败: {str(e)}"
        )


@router.delete(
    "/backup/{backup_name}",
    summary="删除配置备份",
    description="删除指定的配置备份"
)
async def delete_config_backup(
    backup_name: str,
    current_user: User = Depends(require_permission(Permission.UPDATE_SYSTEM_CONFIG)),
    db: AsyncSession = Depends(get_db_session)
):
    """删除配置备份"""
    service = ConfigManagementService(db)
    
    try:
        success, error = await service.delete_config_backup(backup_name)
        
        if success:
            return {"message": f"🗑️ 配置备份 '{backup_name}' 删除成功"}
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=error
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除配置备份失败: {str(e)}"
        )


@router.get(
    "/compare/{backup_name}",
    response_model=ConfigCompareResultSchema,
    summary="比较配置差异",
    description="比较当前配置与备份配置的差异"
)
async def compare_config_with_backup(
    backup_name: str,
    current_user: User = Depends(require_permission(Permission.VIEW_SYSTEM_CONFIG)),
    db: AsyncSession = Depends(get_db_session)
):
    """比较配置差异"""
    service = ConfigManagementService(db)
    
    try:
        success, error, differences = await service.compare_configs(backup_name)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=error
            )
        
        # 转换为schema格式
        diff_schemas = []
        for diff in differences:
            diff_schema = ConfigDiffSchema(
                key=diff["key"],
                current_value=diff["current_value"],
                new_value=diff["new_value"],
                action=diff["action"]
            )
            diff_schemas.append(diff_schema)
        
        # 统计差异
        additions = sum(1 for d in differences if d["action"] == "add")
        updates = sum(1 for d in differences if d["action"] == "update")
        deletions = sum(1 for d in differences if d["action"] == "delete")
        
        return ConfigCompareResultSchema(
            differences=diff_schemas,
            total_differences=len(differences),
            additions=additions,
            updates=updates,
            deletions=deletions
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"比较配置差异失败: {str(e)}"
        )
"""
Inventory管理API

提供主机清单管理的RESTful API端点。
"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, status, UploadFile, File
from fastapi.responses import PlainTextResponse
from sqlalchemy.ext.asyncio import AsyncSession

from ansible_web_ui.core.database import get_db_session
from ansible_web_ui.services.inventory_service import InventoryService
from ansible_web_ui.schemas.host_schemas import (
    HostCreate, HostUpdate, HostResponse, HostListResponse,
    HostVariableUpdate, HostTagUpdate, HostPingUpdate, HostSearchRequest
)
from ansible_web_ui.schemas.host_group_schemas import (
    HostGroupCreate, HostGroupUpdate, HostGroupResponse, HostGroupListResponse,
    HostGroupVariableUpdate, HostGroupTreeNode, InventoryResponse,
    InventoryStatsResponse, InventoryExportRequest, InventoryImportRequest
)
from ansible_web_ui.auth.dependencies import get_current_active_user as get_current_user, require_permission
from ansible_web_ui.models.user import User

router = APIRouter(prefix="/inventory", tags=["inventory"])


async def get_inventory_service(db: AsyncSession = Depends(get_db_session)) -> InventoryService:
    """获取Inventory服务实例"""
    service = InventoryService(db)
    await service.initialize()
    return service


# 主机管理API
@router.post("/hosts", response_model=HostResponse, status_code=status.HTTP_201_CREATED)
async def create_host(
    host_data: HostCreate,
    inventory_service: InventoryService = Depends(get_inventory_service),
    current_user: User = Depends(get_current_user)
):
    """
    创建新主机
    
    - **hostname**: 主机名（必需）
    - **ansible_host**: Ansible连接地址（必需）
    - **group_name**: 主机组名（默认为ungrouped）
    - **ansible_port**: SSH端口（默认为22）
    - **ansible_user**: SSH用户名
    - **ansible_ssh_private_key_file**: SSH私钥文件路径
    - **ansible_become**: 是否使用sudo提权
    - **variables**: 主机变量字典
    - **tags**: 主机标签列表
    """
    try:
        host = await inventory_service.add_host(**host_data.dict())
        return HostResponse.from_orm(host)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"创建主机失败: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"服务器内部错误: {str(e)}"
        )


@router.get("/hosts", response_model=HostListResponse)
async def list_hosts(
    group_name: Optional[str] = Query(None, description="按组名筛选"),
    active_only: bool = Query(True, description="是否只返回激活的主机"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=10000, description="每页数量"),
    inventory_service: InventoryService = Depends(get_inventory_service),
    current_user: User = Depends(get_current_user)
):
    """
    获取主机列表
    
    支持按组名筛选和分页。
    """
    try:
        hosts = await inventory_service.list_hosts(
            group_name=group_name,
            active_only=active_only
        )
        
        # 简单分页处理
        total = len(hosts)
        start = (page - 1) * page_size
        end = start + page_size
        paginated_hosts = hosts[start:end]
        
        host_responses = [HostResponse.from_orm(host) for host in paginated_hosts]
        
        return HostListResponse(
            hosts=host_responses,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=(total + page_size - 1) // page_size
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取主机列表失败: {str(e)}"
        )


@router.get("/hosts/count")
async def get_hosts_count(
    group_name: Optional[str] = Query(None, description="按组名筛选"),
    active_only: bool = Query(True, description="是否只统计激活的主机"),
    inventory_service: InventoryService = Depends(get_inventory_service),
    current_user: User = Depends(get_current_user)
):
    """获取主机数量统计（优化：直接count，不查询数据）"""
    try:
        # 🚀 优化：直接count，不查询完整数据
        count = await inventory_service.get_hosts_count_fast(
            group_name=group_name,
            active_only=active_only
        )
        
        return {
            "total_count": count,
            "group_name": group_name,
            "active_only": active_only,
            "timestamp": "2025-10-14T06:41:23.381783+00:00"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取主机数量失败: {str(e)}"
        )



@router.get("/hosts/{host_id}", response_model=HostResponse)
async def get_host(
    host_id: int,
    inventory_service: InventoryService = Depends(get_inventory_service),
    current_user: User = Depends(get_current_user)
):
    """获取指定主机的详细信息"""
    host = await inventory_service.get_host(host_id)
    if not host:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"主机 ID {host_id} 不存在"
        )
    
    return HostResponse.from_orm(host)


@router.put("/hosts/{host_id}", response_model=HostResponse)
async def update_host(
    host_id: int,
    host_data: HostUpdate,
    inventory_service: InventoryService = Depends(get_inventory_service),
    current_user: User = Depends(get_current_user)
):
    """更新主机信息"""
    try:
        # 只更新提供的字段
        update_data = {k: v for k, v in host_data.dict().items() if v is not None}
        
        if not update_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="没有提供要更新的字段"
            )
        
        updated_host = await inventory_service.update_host(host_id, **update_data)
        
        if not updated_host:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"主机 ID {host_id} 不存在"
            )
        
        return HostResponse.from_orm(updated_host)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"更新主机失败: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"服务器内部错误: {str(e)}"
        )


@router.delete("/hosts/{host_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_host(
    host_id: int,
    inventory_service: InventoryService = Depends(get_inventory_service),
    current_user: User = Depends(get_current_user)
):
    """删除主机"""
    success = await inventory_service.remove_host(host_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"主机 ID {host_id} 不存在"
        )


@router.put("/hosts/{host_id}/variables", response_model=HostResponse)
async def update_host_variables(
    host_id: int,
    variables_data: HostVariableUpdate,
    inventory_service: InventoryService = Depends(get_inventory_service),
    current_user: User = Depends(get_current_user)
):
    """更新主机变量"""
    try:
        updated_host = await inventory_service.update_host(
            host_id, 
            variables=variables_data.variables
        )
        
        if not updated_host:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"主机 ID {host_id} 不存在"
            )
        
        return HostResponse.from_orm(updated_host)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"更新主机变量失败: {str(e)}"
        )


@router.put("/hosts/{host_id}/tags", response_model=HostResponse)
async def update_host_tags(
    host_id: int,
    tags_data: HostTagUpdate,
    inventory_service: InventoryService = Depends(get_inventory_service),
    current_user: User = Depends(get_current_user)
):
    """更新主机标签"""
    try:
        updated_host = await inventory_service.update_host(
            host_id,
            tags=tags_data.tags
        )
        
        if not updated_host:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"主机 ID {host_id} 不存在"
            )
        
        return HostResponse.from_orm(updated_host)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"更新主机标签失败: {str(e)}"
        )


@router.post("/hosts/{host_id}/ping")
async def ping_host(
    host_id: int,
    inventory_service: InventoryService = Depends(get_inventory_service),
    current_user: User = Depends(get_current_user)
):
    """
    测试主机SSH连接
    
    返回详细的连接测试结果，包括：
    - success: 是否成功
    - message: 简要信息
    - error_type: 错误类型（如果失败）
    - details: 详细错误信息（如果失败）
    """
    host = await inventory_service.get_host(host_id)
    if not host:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"主机 ID {host_id} 不存在"
        )
    
    try:
        result = await inventory_service.ping_host(host_id)
        
        return {
            "host_id": host_id,
            "hostname": host.hostname,
            "ansible_host": host.ansible_host,
            "ansible_port": host.ansible_port or 22,
            "ansible_user": host.ansible_user or "root",
            "success": result["success"],
            "status": "success" if result["success"] else "failed",
            "message": result["message"],
            "error_type": result.get("error_type"),
            "details": result.get("details")
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"连接测试失败: {str(e)}"
        )


# 主机组管理API
@router.post("/groups", response_model=HostGroupResponse, status_code=status.HTTP_201_CREATED)
async def create_group(
    group_data: HostGroupCreate,
    inventory_service: InventoryService = Depends(get_inventory_service),
    current_user: User = Depends(get_current_user)
):
    """
    创建新主机组
    
    - **name**: 组名（必需）
    - **display_name**: 显示名称
    - **description**: 组描述
    - **parent_group**: 父组名
    - **variables**: 组变量字典
    - **tags**: 组标签列表
    """
    try:
        group = await inventory_service.add_group(**group_data.model_dump())
        return HostGroupResponse.from_orm(group)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"创建主机组失败: {str(e)}"
        )


@router.get("/groups", response_model=HostGroupListResponse)
async def list_groups(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=10000, description="每页数量"),
    inventory_service: InventoryService = Depends(get_inventory_service),
    current_user: User = Depends(get_current_user)
):
    """获取主机组列表"""
    try:
        groups = await inventory_service.list_groups()
        
        # 简单分页处理
        total = len(groups)
        start = (page - 1) * page_size
        end = start + page_size
        paginated_groups = groups[start:end]
        
        group_responses = [HostGroupResponse.from_orm(group) for group in paginated_groups]
        
        return HostGroupListResponse(
            groups=group_responses,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=(total + page_size - 1) // page_size
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取主机组列表失败: {str(e)}"
        )


@router.get("/groups/tree", response_model=List[HostGroupTreeNode])
async def get_group_tree(
    inventory_service: InventoryService = Depends(get_inventory_service),
    current_user: User = Depends(get_current_user)
):
    """获取主机组树形结构"""
    try:
        tree = await inventory_service.get_group_tree()
        return tree
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取组树形结构失败: {str(e)}"
        )


@router.get("/groups/{group_id}", response_model=HostGroupResponse)
async def get_group(
    group_id: int,
    inventory_service: InventoryService = Depends(get_inventory_service),
    current_user: User = Depends(get_current_user)
):
    """获取指定主机组的详细信息"""
    group = await inventory_service.get_group(group_id)
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"主机组 ID {group_id} 不存在"
        )
    
    return HostGroupResponse.from_orm(group)


@router.put("/groups/{group_id}", response_model=HostGroupResponse)
async def update_group(
    group_id: int,
    group_data: HostGroupUpdate,
    inventory_service: InventoryService = Depends(get_inventory_service),
    current_user: User = Depends(get_current_user)
):
    """更新主机组信息"""
    try:
        # 只更新提供的字段
        update_data = {k: v for k, v in group_data.dict().items() if v is not None}
        
        if not update_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="没有提供要更新的字段"
            )
        
        updated_group = await inventory_service.update_group(group_id, **update_data)
        
        if not updated_group:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"主机组 ID {group_id} 不存在"
            )
        
        return HostGroupResponse.from_orm(updated_group)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"更新主机组失败: {str(e)}"
        )


@router.delete("/groups/{group_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_group(
    group_id: int,
    force: bool = Query(False, description="是否强制删除（即使有主机或子组）"),
    inventory_service: InventoryService = Depends(get_inventory_service),
    current_user: User = Depends(get_current_user)
):
    """删除主机组"""
    try:
        success = await inventory_service.remove_group(group_id, force=force)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"主机组 ID {group_id} 不存在"
            )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"删除主机组失败: {str(e)}"
        )


@router.put("/groups/{group_id}/variables", response_model=HostGroupResponse)
async def update_group_variables(
    group_id: int,
    variables_data: HostGroupVariableUpdate,
    inventory_service: InventoryService = Depends(get_inventory_service),
    current_user: User = Depends(get_current_user)
):
    """更新主机组变量"""
    try:
        updated_group = await inventory_service.update_group(
            group_id,
            variables=variables_data.variables
        )
        
        if not updated_group:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"主机组 ID {group_id} 不存在"
            )
        
        return HostGroupResponse.from_orm(updated_group)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"更新主机组变量失败: {str(e)}"
        )


@router.post("/groups/{group_name}/ping")
async def ping_group(
    group_name: str,
    inventory_service: InventoryService = Depends(get_inventory_service),
    current_user: User = Depends(get_current_user)
):
    """测试组中所有主机的连接"""
    group = await inventory_service.get_group_by_name(group_name)
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"主机组 '{group_name}' 不存在"
        )
    
    try:
        results = await inventory_service.ping_group(group_name)
        return {
            "group_name": group_name,
            "results": results,
            "total_hosts": len(results),
            "successful_hosts": sum(1 for success in results.values() if success),
            "failed_hosts": sum(1 for success in results.values() if not success)
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"组连接测试失败: {str(e)}"
        )


# Inventory生成和管理API
@router.get("/generate")
async def generate_inventory(
    format_type: str = Query("json", regex="^(json|yaml|ini)$", description="生成格式"),
    inventory_service: InventoryService = Depends(get_inventory_service),
    current_user: User = Depends(get_current_user)
):
    """
    生成Ansible inventory数据
    
    支持的格式：json, yaml, ini
    """
    try:
        inventory_data = await inventory_service.generate_inventory(format_type)
        
        if format_type == "json":
            return inventory_data
        else:
            # 对于yaml和ini格式，返回纯文本
            return PlainTextResponse(
                content=inventory_data,
                media_type="text/plain"
            )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"生成inventory失败: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"服务器内部错误: {str(e)}"
        )


@router.post("/export")
async def export_inventory(
    export_request: InventoryExportRequest,
    inventory_service: InventoryService = Depends(get_inventory_service),
    current_user: User = Depends(get_current_user)
):
    """
    导出inventory到指定格式
    
    - **format**: 导出格式 (ini/yaml/json)
    - **groups**: 指定导出的组（可选）
    - **include_variables**: 是否包含变量
    - **include_inactive**: 是否包含未激活主机
    """
    try:
        content = await inventory_service.export_inventory(export_request.format)
        
        return PlainTextResponse(
            content=content,
            media_type="text/plain",
            headers={
                "Content-Disposition": f"attachment; filename=inventory.{export_request.format}"
            }
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"导出inventory失败: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"服务器内部错误: {str(e)}"
        )


@router.post("/import")
async def import_inventory(
    import_request: InventoryImportRequest,
    inventory_service: InventoryService = Depends(get_inventory_service),
    current_user: User = Depends(get_current_user)
):
    """
    导入inventory数据
    
    - **content**: inventory内容
    - **format**: 导入格式 (ini/yaml/json)
    - **merge_mode**: 合并模式 (replace/merge/append)
    - **default_group**: 默认组名
    """
    try:
        imported_hosts, imported_groups = await inventory_service.import_inventory(
            content=import_request.content,
            format_type=import_request.format,
            merge_mode=import_request.merge_mode
        )
        
        return {
            "success": True,
            "imported_hosts": imported_hosts,
            "imported_groups": imported_groups,
            "message": f"成功导入 {imported_hosts} 个主机和 {imported_groups} 个组"
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"导入inventory失败: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"服务器内部错误: {str(e)}"
        )


@router.post("/import/file")
async def import_inventory_file(
    file: UploadFile = File(..., description="inventory文件"),
    format_type: str = Query("ini", regex="^(ini|yaml|json)$", description="文件格式"),
    merge_mode: str = Query("replace", regex="^(replace|merge|append)$", description="合并模式"),
    inventory_service: InventoryService = Depends(get_inventory_service),
    current_user: User = Depends(get_current_user)
):
    """
    通过文件上传导入inventory
    
    支持上传ini、yaml、json格式的inventory文件。
    """
    try:
        # 读取文件内容
        content = await file.read()
        content_str = content.decode('utf-8')
        
        imported_hosts, imported_groups = await inventory_service.import_inventory(
            content=content_str,
            format_type=format_type,
            merge_mode=merge_mode
        )
        
        return {
            "success": True,
            "filename": file.filename,
            "imported_hosts": imported_hosts,
            "imported_groups": imported_groups,
            "message": f"成功从文件 {file.filename} 导入 {imported_hosts} 个主机和 {imported_groups} 个组"
        }
    except UnicodeDecodeError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="文件编码错误，请确保文件为UTF-8编码"
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"导入inventory文件失败: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"服务器内部错误: {str(e)}"
        )




@router.get("/stats", response_model=InventoryStatsResponse)
async def get_inventory_stats(
    inventory_service: InventoryService = Depends(get_inventory_service),
    current_user: User = Depends(get_current_user)
):
    """获取inventory统计信息"""
    try:
        stats = await inventory_service.get_inventory_stats()
        return InventoryStatsResponse(**stats)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取统计信息失败: {str(e)}"
        )


# 搜索API
@router.post("/search/hosts", response_model=HostListResponse)
async def search_hosts(
    search_request: HostSearchRequest,
    inventory_service: InventoryService = Depends(get_inventory_service),
    current_user: User = Depends(get_current_user)
):
    """
    搜索主机
    
    支持按关键词、组名、标签、状态等条件搜索主机。
    """
    try:
        # 这里可以实现更复杂的搜索逻辑
        # 暂时使用简单的列表筛选
        hosts = await inventory_service.list_hosts(
            group_name=search_request.group_name,
            active_only=search_request.is_active if search_request.is_active is not None else True
        )
        
        # 按关键词筛选
        if search_request.query:
            hosts = [
                host for host in hosts
                if (search_request.query.lower() in host.hostname.lower() or
                    search_request.query.lower() in (host.display_name or "").lower() or
                    search_request.query.lower() in host.ansible_host.lower())
            ]
        
        # 按ping状态筛选
        if search_request.ping_status:
            hosts = [host for host in hosts if host.ping_status == search_request.ping_status]
        
        # 分页处理
        total = len(hosts)
        start = (search_request.page - 1) * search_request.page_size
        end = start + search_request.page_size
        paginated_hosts = hosts[start:end]
        
        host_responses = [HostResponse.from_orm(host) for host in paginated_hosts]
        
        return HostListResponse(
            hosts=host_responses,
            total=total,
            page=search_request.page,
            page_size=search_request.page_size,
            total_pages=(total + search_request.page_size - 1) // search_request.page_size
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"搜索主机失败: {str(e)}"
        )


@router.post("/hosts/{host_id}/gather-facts")
async def gather_host_facts(
    host_id: int,
    inventory_service: InventoryService = Depends(get_inventory_service),
    current_user: User = Depends(get_current_user)
):
    """
    收集主机系统信息（Ansible Facts）
    
    使用 Ansible setup 模块收集主机的详细系统信息，包括：
    - 操作系统信息
    - 内核版本
    - CPU信息
    - 内存信息
    - 架构信息
    - 网络信息等
    """
    host = await inventory_service.get_host(host_id)
    if not host:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"主机 ID {host_id} 不存在"
        )
    
    try:
        result = await inventory_service.gather_host_facts(host_id)
        
        return {
            "host_id": host_id,
            "hostname": host.hostname,
            "success": result["success"],
            "message": result["message"],
            "facts": result.get("facts"),
            "error": result.get("error")
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"收集系统信息失败: {str(e)}"
        )

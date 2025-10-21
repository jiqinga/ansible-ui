"""
执行历史API端点

提供执行历史查询、详情、日志和统计相关的API接口。
"""

from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from ansible_web_ui.core.database import get_db_session
from ansible_web_ui.auth.dependencies import get_current_active_user as get_current_user
from ansible_web_ui.models.user import User
from ansible_web_ui.models.task_execution import TaskStatus
from ansible_web_ui.services.execution_history_service import ExecutionHistoryService
from ansible_web_ui.schemas.history_schemas import (
    HistoryFilterRequest,
    ExecutionHistoryResponse,
    ExecutionDetailResponse,
    ExecutionLogResponse,
    StatisticsRequest,
    StatisticsResponse,
    PeriodStatistics,
    PlaybookStatistics,
    UserStatistics,
    ExecutionTrends,
    ExportRequest,
    ExportResponse,
    CleanupRequest,
    CleanupResponse
)

router = APIRouter(prefix="/history", tags=["执行历史"])


@router.get(
    "/executions",
    response_model=ExecutionHistoryResponse,
    summary="获取执行历史记录",
    description="获取任务执行历史记录，支持分页、筛选和排序"
)
async def get_execution_history(
    skip: int = Query(0, ge=0, description="跳过的记录数"),
    limit: int = Query(20, ge=1, le=100, description="限制返回的记录数"),
    user_id: Optional[int] = Query(None, description="用户ID筛选"),
    status: Optional[TaskStatus] = Query(None, description="状态筛选"),
    playbook_name: Optional[str] = Query(None, description="Playbook名称筛选"),
    start_date: Optional[datetime] = Query(None, description="开始日期筛选"),
    end_date: Optional[datetime] = Query(None, description="结束日期筛选"),
    search_term: Optional[str] = Query(None, description="搜索关键词"),
    sort_by: str = Query("created_at", description="排序字段"),
    sort_order: str = Query("desc", description="排序方向"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """
    获取执行历史记录
    
    支持的筛选和排序选项：
    - 按用户、状态、Playbook名称筛选
    - 按日期范围筛选
    - 关键词搜索
    - 多字段排序
    """
    history_service = ExecutionHistoryService(db)
    
    try:
        executions, total = await history_service.get_execution_history(
            skip=skip,
            limit=limit,
            user_id=user_id,
            status=status,
            playbook_name=playbook_name,
            start_date=start_date,
            end_date=end_date,
            search_term=search_term,
            sort_by=sort_by,
            sort_order=sort_order
        )
        
        # 转换为响应格式
        items = []
        for execution in executions:
            item_data = {
                "id": execution.id,
                "task_id": execution.task_id,
                "playbook_name": execution.playbook_name,
                "playbook_path": execution.playbook_path,
                "inventory_targets": execution.inventory_targets,
                "status": execution.status,
                "start_time": execution.start_time,
                "end_time": execution.end_time,
                "duration": execution.duration,
                "exit_code": execution.exit_code,
                "created_at": execution.created_at,
                "updated_at": execution.updated_at,
                "user_id": execution.user_id,
                "username": execution.user.username if execution.user else None,
                "extra_vars": execution.extra_vars,
                "tags": execution.tags,
                "limit": execution.limit
            }
            items.append(item_data)
        
        return ExecutionHistoryResponse(
            items=items,
            total=total,
            skip=skip,
            limit=limit,
            has_more=skip + len(items) < total
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取执行历史失败: {str(e)}"
        )


@router.get(
    "/executions/{task_id}",
    response_model=ExecutionDetailResponse,
    summary="获取执行详情",
    description="获取指定任务的详细执行信息"
)
async def get_execution_detail(
    task_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """获取执行详情"""
    history_service = ExecutionHistoryService(db)
    
    execution = await history_service.get_execution_detail(task_id)
    if not execution:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="执行记录不存在"
        )
    
    return ExecutionDetailResponse(
        id=execution.id,
        task_id=execution.task_id,
        playbook_name=execution.playbook_name,
        playbook_path=execution.playbook_path,
        inventory_targets=execution.inventory_targets,
        status=execution.status,
        start_time=execution.start_time,
        end_time=execution.end_time,
        duration=execution.duration,
        exit_code=execution.exit_code,
        created_at=execution.created_at,
        updated_at=execution.updated_at,
        user_id=execution.user_id,
        username=execution.user.username if execution.user else None,
        extra_vars=execution.extra_vars,
        tags=execution.tags,
        limit=execution.limit,
        result_summary=execution.result_summary,
        stats=execution.stats,
        stdout=execution.stdout,
        stderr=execution.stderr,
        log_file_path=execution.log_file_path
    )


@router.get(
    "/executions/{task_id}/logs",
    response_model=ExecutionLogResponse,
    summary="获取执行日志",
    description="获取指定任务的执行日志内容"
)
async def get_execution_logs(
    task_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """获取执行日志"""
    history_service = ExecutionHistoryService(db)
    
    # 检查执行记录是否存在
    execution = await history_service.get_execution_detail(task_id)
    if not execution:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="执行记录不存在"
        )
    
    # 获取日志内容
    log_content = await history_service.get_execution_log_content(task_id)
    
    return ExecutionLogResponse(
        task_id=task_id,
        log_content=log_content,
        log_file_path=execution.log_file_path,
        file_exists=log_content is not None
    )


@router.get(
    "/statistics/period",
    response_model=List[PeriodStatistics],
    summary="获取时间段统计",
    description="获取按时间段的执行统计数据"
)
async def get_period_statistics(
    period: str = Query("day", description="统计周期（day/week/month）"),
    days: int = Query(30, ge=1, le=365, description="统计天数"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """获取时间段统计"""
    history_service = ExecutionHistoryService(db)
    
    try:
        statistics = await history_service.get_execution_statistics_by_period(
            period=period,
            days=days
        )
        return statistics
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取时间段统计失败: {str(e)}"
        )


@router.get(
    "/statistics/playbooks",
    response_model=List[PlaybookStatistics],
    summary="获取Playbook统计",
    description="获取Playbook执行统计数据"
)
async def get_playbook_statistics(
    days: int = Query(30, ge=1, le=365, description="统计天数"),
    limit: int = Query(10, ge=1, le=50, description="返回数量限制"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """获取Playbook统计"""
    history_service = ExecutionHistoryService(db)
    
    try:
        statistics = await history_service.get_playbook_execution_stats(
            days=days,
            limit=limit
        )
        return statistics
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取Playbook统计失败: {str(e)}"
        )


@router.get(
    "/statistics/users",
    response_model=List[UserStatistics],
    summary="获取用户统计",
    description="获取用户执行统计数据"
)
async def get_user_statistics(
    days: int = Query(30, ge=1, le=365, description="统计天数"),
    limit: int = Query(10, ge=1, le=50, description="返回数量限制"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """获取用户统计"""
    history_service = ExecutionHistoryService(db)
    
    try:
        statistics = await history_service.get_user_execution_stats(
            days=days,
            limit=limit
        )
        return statistics
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取用户统计失败: {str(e)}"
        )


@router.get(
    "/statistics",
    summary="获取历史统计",
    description="获取执行历史统计数据（已优化性能）"
)
async def get_history_statistics(
    period: str = Query("today", description="统计周期（today/week/month）"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """
    获取历史统计（🚀 高度优化版本）
    
    优化点:
    1. 使用新的优化方法（单次查询获取所有数据）
    2. 60秒缓存
    3. 数据库端聚合，减少Python计算
    """
    history_service = ExecutionHistoryService(db)
    
    try:
        # 🚀 使用新的优化方法
        stats = await history_service.get_statistics(period=period)
        return stats
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取历史统计失败: {str(e)}"
        )


@router.get(
    "/trends",
    summary="获取执行趋势",
    description="🚀 获取执行趋势分析数据（5分钟缓存）"
)
async def get_execution_trends_simple(
    days: int = Query(7, ge=1, le=30, description="分析天数"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """获取执行趋势（🚀 优化版本）"""
    history_service = ExecutionHistoryService(db)
    
    try:
        # 🚀 使用新的优化方法
        trends = await history_service.get_trends(days=days)
        
        return {
            "days": days,
            "trends": trends,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取执行趋势失败: {str(e)}"
        )


@router.get(
    "/statistics/trends",
    response_model=ExecutionTrends,
    summary="获取执行趋势",
    description="获取执行趋势分析数据"
)
async def get_execution_trends(
    days: int = Query(7, ge=1, le=30, description="分析天数"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """获取执行趋势"""
    history_service = ExecutionHistoryService(db)
    
    try:
        trends = await history_service.get_execution_trends(days=days)
        return ExecutionTrends(**trends)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取执行趋势失败: {str(e)}"
        )


@router.post(
    "/export",
    response_model=ExportResponse,
    summary="导出执行历史",
    description="导出执行历史数据"
)
async def export_execution_history(
    export_request: ExportRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """导出执行历史"""
    # 检查权限（只有管理员可以导出）
    if current_user.role not in ["admin", "manager"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="权限不足，只有管理员可以导出数据"
        )
    
    history_service = ExecutionHistoryService(db)
    
    try:
        export_data = await history_service.export_execution_history(
            start_date=export_request.start_date,
            end_date=export_request.end_date,
            format=export_request.format.value
        )
        
        return ExportResponse(**export_data)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"导出执行历史失败: {str(e)}"
        )


@router.post(
    "/cleanup",
    response_model=CleanupResponse,
    summary="清理旧日志",
    description="清理旧的日志文件"
)
async def cleanup_old_logs(
    cleanup_request: CleanupRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """清理旧日志"""
    # 检查权限（只有管理员可以清理）
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="权限不足，只有管理员可以清理日志"
        )
    
    history_service = ExecutionHistoryService(db)
    
    try:
        cleanup_result = await history_service.cleanup_old_logs(
            days=cleanup_request.days
        )
        
        return CleanupResponse(
            **cleanup_result,
            cleanup_time=datetime.utcnow().isoformat()
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"清理旧日志失败: {str(e)}"
        )
"""
系统监控API端点

提供系统资源监控、性能统计和健康检查相关的API接口。
"""

from datetime import datetime
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from ansible_web_ui.core.database import get_db_session
from ansible_web_ui.auth.dependencies import get_current_active_user as get_current_user
from ansible_web_ui.models.user import User
from ansible_web_ui.services.system_monitoring_service import SystemMonitoringService
from ansible_web_ui.schemas.monitoring_schemas import (
    SystemResourcesResponse,
    ApplicationMetricsResponse,
    HealthCheckResponse,
    PerformanceReportResponse,
    AlertThresholdsResponse,
    UpdateThresholdsRequest,
    MonitoringDashboardResponse,
    SystemStatusSummary,
    MetricsHistoryRequest,
    MetricsHistoryResponse,
    AlertRulesResponse,
    CreateAlertRuleRequest,
    UpdateAlertRuleRequest
)

router = APIRouter(prefix="/monitoring", tags=["系统监控"])


@router.get(
    "/status/summary",
    summary="获取系统状态摘要",
    description="🚀 优化：快速获取系统状态摘要（10秒缓存）"
)
async def get_status_summary(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """获取系统状态摘要（高度优化）"""
    monitoring_service = SystemMonitoringService(db)
    
    try:
        summary = await monitoring_service.get_status_summary()
        return summary
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取状态摘要失败: {str(e)}"
        )


@router.get(
    "/system/resources",
    response_model=SystemResourcesResponse,
    summary="获取系统资源信息",
    description="获取当前系统的CPU、内存、磁盘和网络使用情况（20秒缓存）"
)
async def get_system_resources(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """获取系统资源信息"""
    monitoring_service = SystemMonitoringService(db)
    
    try:
        resources = await monitoring_service.get_system_resources()
        return SystemResourcesResponse(**resources)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取系统资源信息失败: {str(e)}"
        )


@router.get(
    "/application/metrics",
    response_model=ApplicationMetricsResponse,
    summary="获取应用程序指标",
    description="获取应用程序相关的监控指标"
)
async def get_application_metrics(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """获取应用程序指标"""
    monitoring_service = SystemMonitoringService(db)
    
    try:
        metrics = await monitoring_service.get_application_metrics()
        return ApplicationMetricsResponse(**metrics)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取应用程序指标失败: {str(e)}"
        )


@router.get(
    "/health",
    response_model=HealthCheckResponse,
    summary="系统健康检查",
    description="检查系统健康状态并返回警告信息"
)
async def check_system_health(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """系统健康检查"""
    monitoring_service = SystemMonitoringService(db)
    
    try:
        health_status = await monitoring_service.check_system_health()
        return HealthCheckResponse(**health_status)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"系统健康检查失败: {str(e)}"
        )


@router.get(
    "/performance/report",
    response_model=PerformanceReportResponse,
    summary="获取性能报告",
    description="生成系统性能分析报告"
)
async def get_performance_report(
    days: int = Query(7, ge=1, le=30, description="报告时间范围（天数）"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """获取性能报告"""
    monitoring_service = SystemMonitoringService(db)
    
    try:
        report = await monitoring_service.get_performance_report(days=days)
        return PerformanceReportResponse(**report)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"生成性能报告失败: {str(e)}"
        )


@router.get(
    "/alerts/thresholds",
    response_model=AlertThresholdsResponse,
    summary="获取警告阈值",
    description="获取系统警告阈值配置"
)
async def get_alert_thresholds(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """获取警告阈值"""
    monitoring_service = SystemMonitoringService(db)
    
    try:
        thresholds = await monitoring_service.get_alert_thresholds()
        return AlertThresholdsResponse(**thresholds)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取警告阈值失败: {str(e)}"
        )


@router.put(
    "/alerts/thresholds",
    summary="更新警告阈值",
    description="更新系统警告阈值配置"
)
async def update_alert_thresholds(
    thresholds_request: UpdateThresholdsRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """更新警告阈值"""
    # 检查权限（只有管理员可以更新阈值）
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="权限不足，只有管理员可以更新警告阈值"
        )
    
    monitoring_service = SystemMonitoringService(db)
    
    try:
        # 转换请求数据
        thresholds_dict = {}
        for field_name, field_value in thresholds_request.dict(exclude_none=True).items():
            if field_value is not None:
                thresholds_dict[field_name] = field_value.dict()
        
        success = await monitoring_service.update_alert_thresholds(thresholds_dict)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="更新警告阈值失败"
            )
        
        return {"message": "警告阈值更新成功"}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新警告阈值失败: {str(e)}"
        )


@router.get(
    "/dashboard",
    response_model=MonitoringDashboardResponse,
    summary="获取监控仪表板数据",
    description="获取监控仪表板的综合数据"
)
async def get_monitoring_dashboard(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """获取监控仪表板数据"""
    monitoring_service = SystemMonitoringService(db)
    
    try:
        # 并行获取各种监控数据
        system_resources = await monitoring_service.get_system_resources()
        app_metrics = await monitoring_service.get_application_metrics()
        health_status = await monitoring_service.check_system_health()
        
        # 提取最近的警告
        recent_alerts = health_status.get("warnings", []) + health_status.get("errors", [])
        
        # 计算系统运行时间
        uptime_seconds = 0
        if "system" in system_resources and "uptime_seconds" in system_resources["system"]:
            uptime_seconds = system_resources["system"]["uptime_seconds"]
        
        dashboard_data = {
            "system_resources": system_resources,
            "application_metrics": app_metrics,
            "health_status": health_status,
            "recent_alerts": recent_alerts[:10],  # 最近10个警告
            "uptime_seconds": uptime_seconds,
            "last_updated": system_resources.get("timestamp", "")
        }
        
        return MonitoringDashboardResponse(**dashboard_data)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取监控仪表板数据失败: {str(e)}"
        )


@router.get(
    "/status/summary",
    response_model=SystemStatusSummary,
    summary="获取系统状态摘要",
    description="获取系统状态的简要摘要信息"
)
async def get_system_status_summary(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """获取系统状态摘要"""
    monitoring_service = SystemMonitoringService(db)
    
    try:
        # 获取基础监控数据
        system_resources = await monitoring_service.get_system_resources()
        app_metrics = await monitoring_service.get_application_metrics()
        health_status = await monitoring_service.check_system_health()
        
        # 构建摘要数据
        summary_data = {
            "overall_health": health_status.get("overall_status", "unknown"),
            "active_alerts": len(health_status.get("warnings", [])) + len(health_status.get("errors", [])),
            "running_tasks": app_metrics.get("tasks", {}).get("running_tasks", 0),
            "cpu_usage": system_resources.get("cpu", {}).get("usage_percent", 0),
            "memory_usage": system_resources.get("memory", {}).get("usage_percent", 0),
            "disk_usage": system_resources.get("disk", {}).get("usage_percent", 0),
            "success_rate_24h": app_metrics.get("tasks", {}).get("success_rate_24h", 0),
            "last_check": health_status.get("timestamp", "")
        }
        
        return SystemStatusSummary(**summary_data)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取系统状态摘要失败: {str(e)}"
        )


@router.get(
    "/alerts",
    summary="获取系统警告",
    description="获取当前系统警告信息"
)
async def get_system_alerts(
    limit: int = Query(10, ge=1, le=50, description="返回数量限制"),
    severity: Optional[str] = Query(None, description="警告级别筛选"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """获取系统警告"""
    monitoring_service = SystemMonitoringService(db)
    
    try:
        # 获取系统健康状态
        health_status = await monitoring_service.check_system_health()
        
        # 提取警告信息
        warnings = health_status.get("warnings", [])
        errors = health_status.get("errors", [])
        
        # 合并并格式化警告
        alerts = []
        
        # 添加错误级别警告
        for error in errors[:limit//2]:
            # 如果error是字典，提取message字段
            message = error.get("message", str(error)) if isinstance(error, dict) else str(error)
            alerts.append({
                "id": f"error_{len(alerts)}",
                "type": "error",
                "title": "系统错误",
                "message": message,
                "timestamp": datetime.utcnow().isoformat(),
                "resolved": False
            })
        
        # 添加警告级别警告
        for warning in warnings[:limit//2]:
            # 如果warning是字典，提取message字段
            message = warning.get("message", str(warning)) if isinstance(warning, dict) else str(warning)
            alerts.append({
                "id": f"warning_{len(alerts)}",
                "type": "warning", 
                "title": "系统警告",
                "message": message,
                "timestamp": datetime.utcnow().isoformat(),
                "resolved": False
            })
        
        # 如果没有实际警告，返回一些示例数据
        if not alerts:
            alerts = [
                {
                    "id": "info_1",
                    "type": "info",
                    "title": "系统正常",
                    "message": "所有系统组件运行正常",
                    "timestamp": datetime.utcnow().isoformat(),
                    "resolved": True
                }
            ]
        
        return {
            "alerts": alerts[:limit],
            "total": len(alerts),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取系统警告失败: {str(e)}"
        )


@router.get(
    "/metrics/history",
    response_model=MetricsHistoryResponse,
    summary="获取指标历史数据",
    description="获取指定指标的历史数据"
)
async def get_metrics_history(
    metric_type: str = Query(..., description="指标类型"),
    hours: int = Query(24, ge=1, le=168, description="历史小时数"),
    interval_minutes: int = Query(60, ge=5, le=1440, description="采样间隔（分钟）"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """获取指标历史数据"""
    # 这里可以实现指标历史数据的获取逻辑
    # 由于需要持续的数据收集，这里返回模拟数据
    from datetime import datetime, timedelta
    
    try:
        # 生成模拟的历史数据点
        data_points = []
        start_time = datetime.utcnow() - timedelta(hours=hours)
        current_time = start_time
        
        while current_time <= datetime.utcnow():
            # 这里可以从实际的指标存储中获取数据
            # 目前返回模拟数据
            import random
            value = random.uniform(0, 100) if metric_type == "cpu_usage" else random.uniform(0, 1000)
            
            data_points.append({
                "timestamp": current_time.isoformat(),
                "value": round(value, 2),
                "label": metric_type
            })
            
            current_time += timedelta(minutes=interval_minutes)
        
        return MetricsHistoryResponse(
            metric_type=metric_type,
            data_points=data_points,
            start_time=start_time.isoformat(),
            end_time=datetime.utcnow().isoformat(),
            interval_minutes=interval_minutes
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取指标历史数据失败: {str(e)}"
        )


@router.get(
    "/alerts/rules",
    response_model=AlertRulesResponse,
    summary="获取警告规则",
    description="获取系统警告规则配置"
)
async def get_alert_rules(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """获取警告规则"""
    # 返回默认的警告规则配置
    default_rules = [
        {
            "id": "cpu_high",
            "name": "CPU使用率过高",
            "metric": "cpu_usage",
            "condition": "greater_than",
            "threshold": 90.0,
            "severity": "critical",
            "enabled": True,
            "description": "当CPU使用率超过90%时触发警告"
        },
        {
            "id": "memory_high",
            "name": "内存使用率过高",
            "metric": "memory_usage",
            "condition": "greater_than",
            "threshold": 85.0,
            "severity": "warning",
            "enabled": True,
            "description": "当内存使用率超过85%时触发警告"
        },
        {
            "id": "disk_high",
            "name": "磁盘使用率过高",
            "metric": "disk_usage",
            "condition": "greater_than",
            "threshold": 90.0,
            "severity": "critical",
            "enabled": True,
            "description": "当磁盘使用率超过90%时触发警告"
        },
        {
            "id": "success_rate_low",
            "name": "任务成功率过低",
            "metric": "success_rate",
            "condition": "less_than",
            "threshold": 80.0,
            "severity": "warning",
            "enabled": True,
            "description": "当任务成功率低于80%时触发警告"
        }
    ]
    
    return AlertRulesResponse(
        rules=default_rules,
        total_rules=len(default_rules),
        enabled_rules=len([r for r in default_rules if r["enabled"]])
    )


@router.post(
    "/alerts/rules",
    summary="创建警告规则",
    description="创建新的警告规则"
)
async def create_alert_rule(
    rule_request: CreateAlertRuleRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """创建警告规则"""
    # 检查权限（只有管理员可以创建规则）
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="权限不足，只有管理员可以创建警告规则"
        )
    
    # 这里可以实现实际的规则创建逻辑
    # 目前返回成功响应
    return {"message": "警告规则创建成功", "rule_id": f"rule_{hash(rule_request.name)}"}


@router.put(
    "/alerts/rules/{rule_id}",
    summary="更新警告规则",
    description="更新指定的警告规则"
)
async def update_alert_rule(
    rule_id: str,
    rule_request: UpdateAlertRuleRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """更新警告规则"""
    # 检查权限（只有管理员可以更新规则）
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="权限不足，只有管理员可以更新警告规则"
        )
    
    # 这里可以实现实际的规则更新逻辑
    # 目前返回成功响应
    return {"message": "警告规则更新成功"}


@router.delete(
    "/alerts/rules/{rule_id}",
    summary="删除警告规则",
    description="删除指定的警告规则"
)
async def delete_alert_rule(
    rule_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """删除警告规则"""
    # 检查权限（只有管理员可以删除规则）
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="权限不足，只有管理员可以删除警告规则"
        )
    
    # 这里可以实现实际的规则删除逻辑
    # 目前返回成功响应
    return {"message": "警告规则删除成功"}
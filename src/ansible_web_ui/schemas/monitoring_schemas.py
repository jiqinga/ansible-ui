"""
系统监控相关的数据模式

定义系统监控、性能统计和警告相关的Pydantic模型。
"""

from datetime import datetime
from typing import Optional, List, Dict, Any, Union
from pydantic import BaseModel, Field
from enum import Enum


class SystemResourcesResponse(BaseModel):
    """
    系统资源响应模型
    """
    timestamp: str = Field(description="时间戳")
    cpu: Dict[str, Any] = Field(description="CPU信息")
    memory: Dict[str, Any] = Field(description="内存信息")
    disk: Dict[str, Any] = Field(description="磁盘信息")
    network: Dict[str, Any] = Field(description="网络信息")
    system: Dict[str, Any] = Field(description="系统信息")


class ApplicationMetricsResponse(BaseModel):
    """
    应用程序指标响应模型
    """
    timestamp: str = Field(description="时间戳")
    process: Dict[str, Any] = Field(description="进程信息")
    database: Dict[str, Any] = Field(description="数据库信息")
    tasks: Dict[str, Any] = Field(description="任务信息")
    logs: Dict[str, Any] = Field(description="日志信息")


class HealthStatus(str, Enum):
    """
    健康状态枚举
    """
    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    ERROR = "error"


class AlertSeverity(str, Enum):
    """
    警告严重程度枚举
    """
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class HealthAlert(BaseModel):
    """
    健康警告模型
    """
    type: str = Field(description="警告类型")
    message: str = Field(description="警告消息")
    severity: AlertSeverity = Field(description="严重程度")
    value: Optional[Union[int, float]] = Field(description="当前值")
    threshold: Optional[Union[int, float]] = Field(description="阈值")
    timestamp: Optional[str] = Field(description="时间戳")


class HealthCheckResponse(BaseModel):
    """
    健康检查响应模型
    """
    overall_status: HealthStatus = Field(description="总体状态")
    warnings: List[HealthAlert] = Field(description="警告列表")
    errors: List[HealthAlert] = Field(description="错误列表")
    timestamp: str = Field(description="检查时间戳")


class TaskPerformanceMetrics(BaseModel):
    """
    任务性能指标模型
    """
    total_tasks: int = Field(description="总任务数")
    success_tasks: int = Field(description="成功任务数")
    failed_tasks: int = Field(description="失败任务数")
    success_rate: float = Field(description="成功率")
    average_duration: float = Field(description="平均执行时长")
    min_duration: float = Field(description="最短执行时长")
    max_duration: float = Field(description="最长执行时长")


class DailyTrend(BaseModel):
    """
    每日趋势模型
    """
    date: str = Field(description="日期")
    task_count: int = Field(description="任务数量")
    average_duration: float = Field(description="平均执行时长")


class SlowestTask(BaseModel):
    """
    最慢任务模型
    """
    task_id: str = Field(description="任务ID")
    playbook_name: str = Field(description="Playbook名称")
    duration: float = Field(description="执行时长")
    created_at: str = Field(description="创建时间")


class PerformanceReportResponse(BaseModel):
    """
    性能报告响应模型
    """
    report_period_days: int = Field(description="报告周期天数")
    generated_at: str = Field(description="生成时间")
    task_performance: TaskPerformanceMetrics = Field(description="任务性能指标")
    daily_trends: List[DailyTrend] = Field(description="每日趋势")
    slowest_tasks: List[SlowestTask] = Field(description="最慢任务列表")
    current_system_resources: SystemResourcesResponse = Field(description="当前系统资源")


class AlertThreshold(BaseModel):
    """
    警告阈值模型
    """
    warning: Union[int, float] = Field(description="警告阈值")
    critical: Union[int, float] = Field(description="严重阈值")


class AlertThresholdsResponse(BaseModel):
    """
    警告阈值响应模型
    """
    cpu_usage: AlertThreshold = Field(description="CPU使用率阈值")
    memory_usage: AlertThreshold = Field(description="内存使用率阈值")
    disk_usage: AlertThreshold = Field(description="磁盘使用率阈值")
    success_rate: AlertThreshold = Field(description="成功率阈值")
    running_tasks: AlertThreshold = Field(description="运行任务数阈值")
    log_size_mb: AlertThreshold = Field(description="日志大小阈值")


class UpdateThresholdsRequest(BaseModel):
    """
    更新阈值请求模型
    """
    cpu_usage: Optional[AlertThreshold] = Field(description="CPU使用率阈值")
    memory_usage: Optional[AlertThreshold] = Field(description="内存使用率阈值")
    disk_usage: Optional[AlertThreshold] = Field(description="磁盘使用率阈值")
    success_rate: Optional[AlertThreshold] = Field(description="成功率阈值")
    running_tasks: Optional[AlertThreshold] = Field(description="运行任务数阈值")
    log_size_mb: Optional[AlertThreshold] = Field(description="日志大小阈值")


class MonitoringDashboardResponse(BaseModel):
    """
    监控仪表板响应模型
    """
    system_resources: SystemResourcesResponse = Field(description="系统资源")
    application_metrics: ApplicationMetricsResponse = Field(description="应用程序指标")
    health_status: HealthCheckResponse = Field(description="健康状态")
    recent_alerts: List[HealthAlert] = Field(description="最近警告")
    uptime_seconds: int = Field(description="系统运行时间（秒）")
    last_updated: str = Field(description="最后更新时间")


class SystemStatusSummary(BaseModel):
    """
    系统状态摘要模型
    """
    overall_health: HealthStatus = Field(description="总体健康状态")
    active_alerts: int = Field(description="活跃警告数")
    running_tasks: int = Field(description="运行中任务数")
    cpu_usage: float = Field(description="CPU使用率")
    memory_usage: float = Field(description="内存使用率")
    disk_usage: float = Field(description="磁盘使用率")
    success_rate_24h: float = Field(description="24小时成功率")
    last_check: str = Field(description="最后检查时间")


class MetricsHistoryRequest(BaseModel):
    """
    指标历史请求模型
    """
    metric_type: str = Field(description="指标类型")
    hours: int = Field(default=24, ge=1, le=168, description="历史小时数")
    interval_minutes: int = Field(default=60, ge=5, le=1440, description="采样间隔（分钟）")


class MetricDataPoint(BaseModel):
    """
    指标数据点模型
    """
    timestamp: str = Field(description="时间戳")
    value: float = Field(description="指标值")
    label: Optional[str] = Field(description="标签")


class MetricsHistoryResponse(BaseModel):
    """
    指标历史响应模型
    """
    metric_type: str = Field(description="指标类型")
    data_points: List[MetricDataPoint] = Field(description="数据点列表")
    start_time: str = Field(description="开始时间")
    end_time: str = Field(description="结束时间")
    interval_minutes: int = Field(description="采样间隔")


class AlertRule(BaseModel):
    """
    警告规则模型
    """
    id: str = Field(description="规则ID")
    name: str = Field(description="规则名称")
    metric: str = Field(description="监控指标")
    condition: str = Field(description="触发条件")
    threshold: float = Field(description="阈值")
    severity: AlertSeverity = Field(description="严重程度")
    enabled: bool = Field(description="是否启用")
    description: Optional[str] = Field(description="规则描述")


class AlertRulesResponse(BaseModel):
    """
    警告规则响应模型
    """
    rules: List[AlertRule] = Field(description="规则列表")
    total_rules: int = Field(description="总规则数")
    enabled_rules: int = Field(description="启用的规则数")


class CreateAlertRuleRequest(BaseModel):
    """
    创建警告规则请求模型
    """
    name: str = Field(description="规则名称")
    metric: str = Field(description="监控指标")
    condition: str = Field(description="触发条件")
    threshold: float = Field(description="阈值")
    severity: AlertSeverity = Field(description="严重程度")
    description: Optional[str] = Field(description="规则描述")


class UpdateAlertRuleRequest(BaseModel):
    """
    更新警告规则请求模型
    """
    name: Optional[str] = Field(description="规则名称")
    condition: Optional[str] = Field(description="触发条件")
    threshold: Optional[float] = Field(description="阈值")
    severity: Optional[AlertSeverity] = Field(description="严重程度")
    enabled: Optional[bool] = Field(description="是否启用")
    description: Optional[str] = Field(description="规则描述")
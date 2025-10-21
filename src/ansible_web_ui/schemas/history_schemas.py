"""
执行历史相关的数据模式

定义执行历史查询、响应和统计相关的Pydantic模型。
"""

from datetime import datetime
from typing import Optional, List, Dict, Any, Union
from pydantic import BaseModel, Field, validator
from enum import Enum

from ansible_web_ui.models.task_execution import TaskStatus


class HistoryFilterRequest(BaseModel):
    """
    历史记录筛选请求模型
    """
    skip: int = Field(default=0, ge=0, description="跳过的记录数")
    limit: int = Field(default=20, ge=1, le=100, description="限制返回的记录数")
    user_id: Optional[int] = Field(default=None, description="用户ID筛选")
    status: Optional[TaskStatus] = Field(default=None, description="状态筛选")
    playbook_name: Optional[str] = Field(default=None, description="Playbook名称筛选")
    start_date: Optional[datetime] = Field(default=None, description="开始日期筛选")
    end_date: Optional[datetime] = Field(default=None, description="结束日期筛选")
    search_term: Optional[str] = Field(default=None, description="搜索关键词")
    sort_by: str = Field(default="created_at", description="排序字段")
    sort_order: str = Field(default="desc", description="排序方向")
    
    @validator('sort_order')
    def validate_sort_order(cls, v):
        if v.lower() not in ['asc', 'desc']:
            raise ValueError('排序方向必须是 asc 或 desc')
        return v.lower()
    
    @validator('sort_by')
    def validate_sort_by(cls, v):
        allowed_fields = [
            'created_at', 'start_time', 'end_time', 'duration', 
            'status', 'playbook_name', 'user_id'
        ]
        if v not in allowed_fields:
            raise ValueError(f'排序字段必须是以下之一: {", ".join(allowed_fields)}')
        return v


class ExecutionHistoryItem(BaseModel):
    """
    执行历史记录项模型
    """
    id: int = Field(description="记录ID")
    task_id: str = Field(description="任务ID")
    playbook_name: str = Field(description="Playbook名称")
    playbook_path: Optional[str] = Field(description="Playbook路径")
    inventory_targets: str = Field(description="目标主机清单")
    status: TaskStatus = Field(description="执行状态")
    start_time: Optional[datetime] = Field(description="开始时间")
    end_time: Optional[datetime] = Field(description="结束时间")
    duration: Optional[int] = Field(description="执行时长（秒）")
    exit_code: Optional[int] = Field(description="退出代码")
    created_at: datetime = Field(description="创建时间")
    updated_at: datetime = Field(description="更新时间")
    
    # 用户信息
    user_id: int = Field(description="执行用户ID")
    username: Optional[str] = Field(description="执行用户名")
    
    # 执行参数
    extra_vars: Optional[Dict[str, Any]] = Field(description="额外变量")
    tags: Optional[str] = Field(description="执行标签")
    limit: Optional[str] = Field(description="限制执行的主机")
    
    class Config:
        from_attributes = True


class ExecutionHistoryResponse(BaseModel):
    """
    执行历史记录响应模型
    """
    items: List[ExecutionHistoryItem] = Field(description="历史记录列表")
    total: int = Field(description="总记录数")
    skip: int = Field(description="跳过的记录数")
    limit: int = Field(description="限制返回的记录数")
    has_more: bool = Field(description="是否还有更多记录")


class ExecutionDetailResponse(BaseModel):
    """
    执行详情响应模型
    """
    id: int = Field(description="记录ID")
    task_id: str = Field(description="任务ID")
    playbook_name: str = Field(description="Playbook名称")
    playbook_path: Optional[str] = Field(description="Playbook路径")
    inventory_targets: str = Field(description="目标主机清单")
    status: TaskStatus = Field(description="执行状态")
    start_time: Optional[datetime] = Field(description="开始时间")
    end_time: Optional[datetime] = Field(description="结束时间")
    duration: Optional[int] = Field(description="执行时长（秒）")
    exit_code: Optional[int] = Field(description="退出代码")
    created_at: datetime = Field(description="创建时间")
    updated_at: datetime = Field(description="更新时间")
    
    # 用户信息
    user_id: int = Field(description="执行用户ID")
    username: Optional[str] = Field(description="执行用户名")
    
    # 执行参数
    extra_vars: Optional[Dict[str, Any]] = Field(description="额外变量")
    tags: Optional[str] = Field(description="执行标签")
    limit: Optional[str] = Field(description="限制执行的主机")
    
    # 执行结果
    result_summary: Optional[Dict[str, Any]] = Field(description="执行结果摘要")
    stats: Optional[Dict[str, Any]] = Field(description="执行统计信息")
    stdout: Optional[str] = Field(description="标准输出")
    stderr: Optional[str] = Field(description="错误输出")
    log_file_path: Optional[str] = Field(description="日志文件路径")
    
    class Config:
        from_attributes = True


class ExecutionLogResponse(BaseModel):
    """
    执行日志响应模型
    """
    task_id: str = Field(description="任务ID")
    log_content: Optional[str] = Field(description="日志内容")
    log_file_path: Optional[str] = Field(description="日志文件路径")
    file_exists: bool = Field(description="日志文件是否存在")


class StatisticsPeriod(str, Enum):
    """
    统计周期枚举
    """
    DAY = "day"
    WEEK = "week"
    MONTH = "month"


class StatisticsRequest(BaseModel):
    """
    统计请求模型
    """
    period: StatisticsPeriod = Field(default=StatisticsPeriod.DAY, description="统计周期")
    days: int = Field(default=30, ge=1, le=365, description="统计天数")


class PeriodStatistics(BaseModel):
    """
    时间段统计模型
    """
    period: str = Field(description="时间段标识")
    date: str = Field(description="日期ISO格式")
    total_tasks: int = Field(description="总任务数")
    success_tasks: int = Field(description="成功任务数")
    failed_tasks: int = Field(description="失败任务数")
    success_rate: float = Field(description="成功率")
    average_duration: float = Field(description="平均执行时长")


class PlaybookStatistics(BaseModel):
    """
    Playbook统计模型
    """
    playbook_name: str = Field(description="Playbook名称")
    total_executions: int = Field(description="总执行次数")
    success_executions: int = Field(description="成功执行次数")
    failed_executions: int = Field(description="失败执行次数")
    success_rate: float = Field(description="成功率")
    average_duration: float = Field(description="平均执行时长")
    last_execution: Optional[str] = Field(description="最后执行时间")


class UserStatistics(BaseModel):
    """
    用户统计模型
    """
    user_id: int = Field(description="用户ID")
    username: str = Field(description="用户名")
    total_executions: int = Field(description="总执行次数")
    success_executions: int = Field(description="成功执行次数")
    success_rate: float = Field(description="成功率")
    last_execution: Optional[str] = Field(description="最后执行时间")


class ExecutionTrends(BaseModel):
    """
    执行趋势模型
    """
    daily_trends: List[PeriodStatistics] = Field(description="每日趋势")
    status_distribution: Dict[str, int] = Field(description="状态分布")
    duration_distribution: Dict[str, int] = Field(description="执行时长分布")
    analysis_period_days: int = Field(description="分析周期天数")


class StatisticsResponse(BaseModel):
    """
    统计响应模型
    """
    period_statistics: List[PeriodStatistics] = Field(description="时间段统计")
    playbook_statistics: List[PlaybookStatistics] = Field(description="Playbook统计")
    user_statistics: List[UserStatistics] = Field(description="用户统计")
    trends: ExecutionTrends = Field(description="执行趋势")
    generated_at: str = Field(description="生成时间")


class ExportFormat(str, Enum):
    """
    导出格式枚举
    """
    JSON = "json"
    CSV = "csv"


class ExportRequest(BaseModel):
    """
    导出请求模型
    """
    start_date: Optional[datetime] = Field(default=None, description="开始日期")
    end_date: Optional[datetime] = Field(default=None, description="结束日期")
    format: ExportFormat = Field(default=ExportFormat.JSON, description="导出格式")


class ExportResponse(BaseModel):
    """
    导出响应模型
    """
    data: List[Dict[str, Any]] = Field(description="导出数据")
    total_records: int = Field(description="总记录数")
    export_time: str = Field(description="导出时间")
    format: str = Field(description="导出格式")


class CleanupRequest(BaseModel):
    """
    清理请求模型
    """
    days: int = Field(default=90, ge=1, le=365, description="保留天数")


class CleanupResponse(BaseModel):
    """
    清理响应模型
    """
    deleted_files: int = Field(description="删除的文件数")
    deleted_size_bytes: int = Field(description="删除的文件大小（字节）")
    deleted_size_mb: float = Field(description="删除的文件大小（MB）")
    cleanup_time: str = Field(description="清理时间")
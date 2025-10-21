"""
🚀 任务执行相关的数据模型

定义任务执行API的请求和响应数据模型。
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ExecutionOptionsSchema(BaseModel):
    """执行选项配置模型"""
    
    # 基础选项
    limit: Optional[str] = Field(None, description="限制执行的主机")
    tags: Optional[str] = Field(None, description="执行指定标签的任务")
    skip_tags: Optional[str] = Field(None, description="跳过指定标签的任务")
    extra_vars: Optional[Dict[str, Any]] = Field(None, description="额外变量")
    
    # 连接选项
    user: Optional[str] = Field(None, description="SSH用户名")
    private_key_file: Optional[str] = Field(None, description="SSH私钥文件")
    connection: str = Field("ssh", description="连接类型")
    timeout: int = Field(30, description="连接超时时间(秒)")
    
    # 执行选项
    forks: int = Field(5, description="并发执行数")
    verbose: int = Field(0, description="详细输出级别(0-4)")
    check: bool = Field(False, description="检查模式(不实际执行)")
    diff: bool = Field(False, description="显示差异")
    
    # 高级选项
    become: bool = Field(False, description="使用sudo提权")
    become_user: Optional[str] = Field(None, description="提权用户")
    become_method: str = Field("sudo", description="提权方法")


class ExecutePlaybookRequest(BaseModel):
    """执行Playbook请求模型"""
    
    playbook_name: str = Field(..., description="Playbook文件名")
    inventory_targets: List[str] = Field(..., description="目标主机列表")
    execution_options: Optional[ExecutionOptionsSchema] = Field(None, description="执行选项")
    
    class Config:
        json_schema_extra = {
            "example": {
                "playbook_name": "deploy.yml",
                "inventory_targets": ["web-server-1", "web-server-2"],
                "execution_options": {
                    "extra_vars": {"app_version": "1.2.3"},
                    "forks": 10,
                    "verbose": 1,
                    "become": True
                }
            }
        }


class TaskStatusResponse(BaseModel):
    """任务状态响应模型"""
    
    task_id: str = Field(..., description="任务ID")
    task_name: str = Field(..., description="任务名称")
    status: str = Field(..., description="任务状态")
    progress: int = Field(..., description="执行进度(0-100)")
    current_step: Optional[str] = Field(None, description="当前执行步骤")
    start_time: Optional[datetime] = Field(None, description="开始时间")
    end_time: Optional[datetime] = Field(None, description="结束时间")
    duration: Optional[float] = Field(None, description="执行时长(秒)")
    error_message: Optional[str] = Field(None, description="错误信息")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class TaskResultResponse(BaseModel):
    """任务结果响应模型"""
    
    task_id: str = Field(..., description="任务ID")
    playbook_name: str = Field(..., description="Playbook名称")
    status: str = Field(..., description="执行状态")
    exit_code: Optional[int] = Field(None, description="退出代码")
    start_time: Optional[datetime] = Field(None, description="开始时间")
    end_time: Optional[datetime] = Field(None, description="结束时间")
    duration: Optional[float] = Field(None, description="执行时长(秒)")
    
    # 执行统计
    stats: Optional[Dict[str, Any]] = Field(None, description="执行统计信息")
    
    # 输出信息
    log_file_path: Optional[str] = Field(None, description="日志文件路径")
    
    # 错误信息
    error_message: Optional[str] = Field(None, description="错误消息")
    failed_tasks: Optional[List[Dict[str, Any]]] = Field(None, description="失败的任务")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class TaskLogResponse(BaseModel):
    """任务日志响应模型"""
    
    task_id: str = Field(..., description="任务ID")
    logs: List[str] = Field(..., description="日志条目列表")
    total_count: int = Field(..., description="日志总数")
    
    class Config:
        json_schema_extra = {
            "example": {
                "task_id": "abc123-def456-ghi789",
                "logs": [
                    "[10:30:15] INFO: 🚀 开始执行Playbook: deploy.yml",
                    "[10:30:16] INFO: 🎯 目标主机: web-server-1, web-server-2",
                    "[10:30:17] INFO: ⚡ 启动Ansible进程..."
                ],
                "total_count": 25
            }
        }


class TaskListResponse(BaseModel):
    """任务列表响应模型"""
    
    tasks: List[TaskStatusResponse] = Field(..., description="任务列表")
    total_count: int = Field(..., description="任务总数")
    page: int = Field(..., description="当前页码")
    page_size: int = Field(..., description="每页大小")
    
    class Config:
        json_schema_extra = {
            "example": {
                "tasks": [
                    {
                        "task_id": "abc123-def456-ghi789",
                        "task_name": "执行Playbook: deploy.yml",
                        "status": "SUCCESS",
                        "progress": 100,
                        "start_time": "2024-01-01T10:30:15",
                        "end_time": "2024-01-01T10:35:20",
                        "duration": 305.5
                    }
                ],
                "total_count": 1,
                "page": 1,
                "page_size": 20
            }
        }


class CancelTaskRequest(BaseModel):
    """取消任务请求模型"""
    
    reason: Optional[str] = Field(None, description="取消原因")
    
    class Config:
        json_schema_extra = {
            "example": {
                "reason": "用户手动取消执行"
            }
        }


class CancelTaskResponse(BaseModel):
    """取消任务响应模型"""
    
    success: bool = Field(..., description="是否取消成功")
    message: str = Field(..., description="响应消息")
    task_id: str = Field(..., description="任务ID")
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "任务已成功取消",
                "task_id": "abc123-def456-ghi789"
            }
        }


class ValidatePlaybookRequest(BaseModel):
    """验证Playbook请求模型"""
    
    playbook_name: str = Field(..., description="Playbook文件名")
    
    class Config:
        json_schema_extra = {
            "example": {
                "playbook_name": "deploy.yml"
            }
        }


class ValidatePlaybookResponse(BaseModel):
    """验证Playbook响应模型"""
    
    valid: bool = Field(..., description="是否有效")
    errors: List[str] = Field(..., description="错误列表")
    warnings: List[str] = Field(..., description="警告列表")
    message: str = Field(..., description="验证消息")
    
    class Config:
        json_schema_extra = {
            "example": {
                "valid": True,
                "errors": [],
                "warnings": [],
                "message": "Playbook语法验证通过"
            }
        }


class TestConnectionRequest(BaseModel):
    """测试连接请求模型"""
    
    inventory_targets: List[str] = Field(..., description="目标主机列表")
    
    class Config:
        json_schema_extra = {
            "example": {
                "inventory_targets": ["web-server-1", "web-server-2", "db-server-1"]
            }
        }


class TestConnectionResponse(BaseModel):
    """测试连接响应模型"""
    
    total_hosts: int = Field(..., description="总主机数")
    successful_hosts: List[str] = Field(..., description="连接成功的主机")
    failed_hosts: List[str] = Field(..., description="连接失败的主机")
    success_rate: float = Field(..., description="成功率(百分比)")
    message: str = Field(..., description="测试结果消息")
    
    class Config:
        json_schema_extra = {
            "example": {
                "total_hosts": 3,
                "successful_hosts": ["web-server-1", "web-server-2"],
                "failed_hosts": ["db-server-1"],
                "success_rate": 66.67,
                "message": "连接测试完成，成功: 2, 失败: 1"
            }
        }


class WebSocketMessage(BaseModel):
    """WebSocket消息模型"""
    
    type: str = Field(..., description="消息类型")
    task_id: str = Field(..., description="任务ID")
    data: Dict[str, Any] = Field(..., description="消息数据")
    timestamp: datetime = Field(default_factory=datetime.now, description="时间戳")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
        json_schema_extra = {
            "example": {
                "type": "log",
                "task_id": "abc123-def456-ghi789",
                "data": {
                    "message": "[10:30:15] INFO: 🚀 开始执行Playbook: deploy.yml"
                },
                "timestamp": "2024-01-01T10:30:15"
            }
        }
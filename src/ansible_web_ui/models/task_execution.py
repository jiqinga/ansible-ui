"""
任务执行数据模型

定义Ansible任务执行历史和状态相关的数据结构。
"""

from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any
from sqlalchemy import Column, String, DateTime, Enum as SQLEnum, Integer, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship
from ansible_web_ui.models.base import BaseModel


class TaskStatus(str, Enum):
    """
    任务执行状态枚举
    """
    PENDING = "pending"      # 等待执行
    RUNNING = "running"      # 正在执行
    SUCCESS = "success"      # 执行成功
    FAILED = "failed"        # 执行失败
    CANCELLED = "cancelled"  # 已取消
    TIMEOUT = "timeout"      # 执行超时


class TaskExecution(BaseModel):
    """
    任务执行模型
    
    记录每次Ansible任务的执行详情、状态和结果。
    """
    __tablename__ = "task_executions"

    # 任务标识
    task_id = Column(
        String(36), 
        unique=True, 
        nullable=False, 
        index=True,
        comment="任务唯一标识符（UUID）"
    )
    
    # 执行信息
    playbook_name = Column(
        String(255), 
        nullable=False,
        comment="执行的Playbook文件名"
    )
    playbook_path = Column(
        String(500), 
        nullable=True,
        comment="Playbook文件完整路径"
    )
    inventory_targets = Column(
        Text, 
        nullable=False,
        comment="目标主机清单（JSON格式）"
    )
    
    # 执行参数
    extra_vars = Column(
        JSON, 
        nullable=True,
        comment="额外变量（JSON格式）"
    )
    tags = Column(
        String(500), 
        nullable=True,
        comment="执行标签"
    )
    limit = Column(
        String(500), 
        nullable=True,
        comment="限制执行的主机"
    )
    
    # 状态和时间
    status = Column(
        SQLEnum(TaskStatus), 
        nullable=False, 
        default=TaskStatus.PENDING,
        index=True,
        comment="任务执行状态"
    )
    start_time = Column(
        DateTime(timezone=True), 
        nullable=True,
        comment="任务开始时间"
    )
    end_time = Column(
        DateTime(timezone=True), 
        nullable=True,
        comment="任务结束时间"
    )
    duration = Column(
        Integer, 
        nullable=True,
        comment="执行时长（秒）"
    )
    
    # 执行结果
    exit_code = Column(
        Integer, 
        nullable=True,
        comment="退出代码"
    )
    result_summary = Column(
        JSON, 
        nullable=True,
        comment="执行结果摘要（JSON格式）"
    )
    stats = Column(
        JSON, 
        nullable=True,
        comment="执行统计信息（JSON格式）"
    )
    
    # 日志和输出
    log_file_path = Column(
        String(500), 
        nullable=True,
        comment="日志文件路径"
    )
    stdout = Column(
        Text, 
        nullable=True,
        comment="标准输出"
    )
    stderr = Column(
        Text, 
        nullable=True,
        comment="错误输出"
    )
    
    # 关联用户
    user_id = Column(
        Integer, 
        ForeignKey("users.id"), 
        nullable=False,
        index=True,
        comment="执行用户ID"
    )
    
    # 关联关系
    user = relationship("User", back_populates="task_executions")

    def __repr__(self) -> str:
        return f"<TaskExecution(task_id='{self.task_id}', status='{self.status}')>"

    @property
    def is_running(self) -> bool:
        """
        检查任务是否正在运行
        """
        return self.status in [TaskStatus.PENDING, TaskStatus.RUNNING]

    @property
    def is_completed(self) -> bool:
        """
        检查任务是否已完成（成功或失败）
        """
        return self.status in [TaskStatus.SUCCESS, TaskStatus.FAILED, TaskStatus.CANCELLED, TaskStatus.TIMEOUT]

    @property
    def is_successful(self) -> bool:
        """
        检查任务是否执行成功
        """
        return self.status == TaskStatus.SUCCESS

    def calculate_duration(self) -> Optional[int]:
        """
        计算任务执行时长
        
        Returns:
            Optional[int]: 执行时长（秒），如果任务未完成则返回None
        """
        if self.start_time and self.end_time:
            delta = self.end_time - self.start_time
            return int(delta.total_seconds())
        return None

    def update_status(self, status: TaskStatus, end_time: Optional[datetime] = None) -> None:
        """
        更新任务状态
        
        Args:
            status: 新的任务状态
            end_time: 结束时间（可选）
        """
        self.status = status
        if end_time:
            self.end_time = end_time
            self.duration = self.calculate_duration()
        elif status in [TaskStatus.SUCCESS, TaskStatus.FAILED, TaskStatus.CANCELLED, TaskStatus.TIMEOUT]:
            self.end_time = datetime.utcnow()
            self.duration = self.calculate_duration()

    def get_summary_stats(self) -> Dict[str, Any]:
        """
        获取任务执行摘要统计
        
        Returns:
            Dict[str, Any]: 包含基本统计信息的字典
        """
        return {
            "task_id": self.task_id,
            "playbook": self.playbook_name,
            "status": self.status.value,
            "duration": self.duration,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "exit_code": self.exit_code,
            "user": self.user.username if self.user else None
        }
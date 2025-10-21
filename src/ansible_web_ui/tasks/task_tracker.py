"""
任务状态跟踪和结果存储模块

提供任务状态跟踪、结果存储和查询功能，支持实时状态更新和历史记录管理。
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union
from uuid import uuid4

import redis
from celery.result import AsyncResult
from pydantic import BaseModel, Field

from ansible_web_ui.core.config import get_settings
from ansible_web_ui.tasks.celery_app import TaskStatus, get_celery_app
from ansible_web_ui.utils.timezone import now

logger = logging.getLogger(__name__)
settings = get_settings()

class TaskInfo(BaseModel):
    """任务信息模型"""
    task_id: str = Field(..., description="任务ID")
    task_name: str = Field(..., description="任务名称")
    status: str = Field(default=TaskStatus.PENDING, description="任务状态")
    user_id: Optional[int] = Field(None, description="执行用户ID")
    playbook_name: Optional[str] = Field(None, description="Playbook名称")
    inventory_targets: Optional[List[str]] = Field(None, description="目标主机")
    start_time: Optional[datetime] = Field(None, description="开始时间")
    end_time: Optional[datetime] = Field(None, description="结束时间")
    progress: int = Field(default=0, description="执行进度(0-100)")
    current_step: Optional[str] = Field(None, description="当前执行步骤")
    result: Optional[Dict[str, Any]] = Field(None, description="执行结果")
    error_message: Optional[str] = Field(None, description="错误信息")
    log_entries: List[str] = Field(default_factory=list, description="日志条目")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    updated_at: datetime = Field(default_factory=datetime.now, description="更新时间")

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class TaskTracker:
    """任务状态跟踪器"""
    
    def __init__(self):
        """初始化任务跟踪器"""
        self.redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)
        self.celery_app = get_celery_app()
        self.task_prefix = "task:"
        self.log_prefix = "task_log:"
        self.user_tasks_prefix = "user_tasks:"
        self.ws_channel_prefix = "ws:tasks:"
        
    def create_task(
        self,
        task_name: str,
        user_id: Optional[int] = None,
        playbook_name: Optional[str] = None,
        inventory_targets: Optional[List[str]] = None,
        task_id: Optional[str] = None,
        **kwargs
    ) -> str:
        """
        创建新任务记录
        
        参数:
            task_name: 任务名称
            user_id: 执行用户ID
            playbook_name: Playbook名称
            inventory_targets: 目标主机列表
            task_id: 任务ID（如果不提供则自动生成）
            **kwargs: 其他任务参数
            
        返回:
            str: 任务ID
        """
        task_id = task_id or str(uuid4())
        
        # 检查任务是否已存在，如果存在则不重复创建
        existing_task = self.get_task_info(task_id)
        if existing_task:
            logger.info(f"任务已存在，跳过创建: {task_id}")
            return task_id
        
        task_info = TaskInfo(
            task_id=task_id,
            task_name=task_name,
            user_id=user_id,
            playbook_name=playbook_name,
            inventory_targets=inventory_targets or [],
            **kwargs
        )
        
        # 存储任务信息
        self._store_task_info(task_info)
        
        # 添加到用户任务列表
        if user_id:
            self._add_to_user_tasks(user_id, task_id)
            
        logger.info(f"创建任务记录: {task_id}, 任务名称: {task_name}")
        return task_id
    
    def update_task_status(
        self,
        task_id: str,
        status: str,
        progress: Optional[int] = None,
        current_step: Optional[str] = None,
        result: Optional[Dict[str, Any]] = None,
        error_message: Optional[str] = None
    ) -> bool:
        """
        更新任务状态
        
        参数:
            task_id: 任务ID
            status: 新状态
            progress: 执行进度
            current_step: 当前步骤
            result: 执行结果
            error_message: 错误信息
            
        返回:
            bool: 更新是否成功
        """
        try:
            task_info = self.get_task_info(task_id)
            if not task_info:
                logger.error(f"任务不存在: {task_id}")
                return False
            
            # 更新任务信息
            task_info.status = status
            task_info.updated_at = now()
            
            if progress is not None:
                task_info.progress = progress
            if current_step is not None:
                task_info.current_step = current_step
            if result is not None:
                task_info.result = result
            if error_message is not None:
                task_info.error_message = error_message
                
            # 设置开始和结束时间
            if status == TaskStatus.STARTED and not task_info.start_time:
                task_info.start_time = now()
            elif status in [TaskStatus.SUCCESS, TaskStatus.FAILURE, TaskStatus.REVOKED]:
                if not task_info.end_time:
                    task_info.end_time = now()
                if progress is None:
                    task_info.progress = 100 if status == TaskStatus.SUCCESS else task_info.progress
            
            # 存储更新后的任务信息
            self._store_task_info(task_info)
            status_payload = {
                "status": task_info.status,
                "progress": task_info.progress,
                "current_step": task_info.current_step,
                "error_message": task_info.error_message,
                "start_time": task_info.start_time.isoformat() if task_info.start_time else None,
                "end_time": task_info.end_time.isoformat() if task_info.end_time else None,
            }
            if task_info.result is not None:
                status_payload["result"] = task_info.result

            self._publish_websocket_event(task_id, "status", status_payload)

            logger.info(f"更新任务状态: {task_id}, 状态: {status}, 进度: {progress}%")
            return True
            
        except Exception as e:
            logger.error(f"更新任务状态失败: {task_id}, 错误: {str(e)}")
            return False
    
    def add_log_entry(self, task_id: str, log_entry: str) -> bool:
        """
        添加日志条目
        
        参数:
            task_id: 任务ID
            log_entry: 日志内容
            
        返回:
            bool: 添加是否成功
        """
        try:
            # 添加时间戳
            timestamp = now().strftime("%Y-%m-%d %H:%M:%S")
            formatted_entry = f"[{timestamp}] {log_entry}"
            
            # 存储到Redis列表
            log_key = f"{self.log_prefix}{task_id}"
            self.redis_client.lpush(log_key, formatted_entry)
            
            # 设置过期时间（7天）
            self.redis_client.expire(log_key, 7 * 24 * 3600)
            
            # 限制日志条目数量（最多保留1000条）
            self.redis_client.ltrim(log_key, 0, 999)

            self._publish_websocket_event(task_id, "log", {"message": formatted_entry})

            
            logger.debug(f"添加任务日志: {task_id}, 内容: {log_entry[:100]}...")
            return True
            
        except Exception as e:
            logger.error(f"添加任务日志失败: {task_id}, 错误: {str(e)}")
            return False
    
    def get_task_info(self, task_id: str) -> Optional[TaskInfo]:
        """
        获取任务信息
        
        参数:
            task_id: 任务ID
            
        返回:
            Optional[TaskInfo]: 任务信息，不存在时返回None
        """
        try:
            task_key = f"{self.task_prefix}{task_id}"
            task_data = self.redis_client.get(task_key)
            
            if not task_data:
                # 尝试从Celery结果后端获取
                return self._get_task_from_celery(task_id)
            
            task_dict = json.loads(task_data)
            return TaskInfo(**task_dict)
            
        except Exception as e:
            logger.error(f"获取任务信息失败: {task_id}, 错误: {str(e)}")
            return None
    
    def get_task_logs(self, task_id: str, limit: int = 100) -> List[str]:
        """
        获取任务日志
        
        参数:
            task_id: 任务ID
            limit: 日志条目限制
            
        返回:
            List[str]: 日志条目列表
        """
        try:
            log_key = f"{self.log_prefix}{task_id}"
            logs = self.redis_client.lrange(log_key, 0, limit - 1)
            return list(reversed(logs))  # 按时间正序返回
            
        except Exception as e:
            logger.error(f"获取任务日志失败: {task_id}, 错误: {str(e)}")
            return []
    
    def get_user_tasks(
        self,
        user_id: int,
        status_filter: Optional[str] = None,
        limit: int = 50
    ) -> List[TaskInfo]:
        """
        获取用户任务列表
        
        参数:
            user_id: 用户ID
            status_filter: 状态过滤器
            limit: 任务数量限制
            
        返回:
            List[TaskInfo]: 任务信息列表
        """
        try:
            user_tasks_key = f"{self.user_tasks_prefix}{user_id}"
            task_ids = self.redis_client.lrange(user_tasks_key, 0, limit - 1)
            
            tasks = []
            for task_id in task_ids:
                task_info = self.get_task_info(task_id)
                if task_info:
                    if not status_filter or task_info.status == status_filter:
                        tasks.append(task_info)
            
            # 按创建时间倒序排序
            tasks.sort(key=lambda x: x.created_at, reverse=True)
            return tasks
            
        except Exception as e:
            logger.error(f"获取用户任务列表失败: {user_id}, 错误: {str(e)}")
            return []
    
    def cancel_task(self, task_id: str) -> bool:
        """
        取消任务
        
        参数:
            task_id: 任务ID
            
        返回:
            bool: 取消是否成功
        """
        try:
            # 撤销Celery任务
            self.celery_app.control.revoke(task_id, terminate=True)
            
            # 更新任务状态
            self.update_task_status(
                task_id,
                TaskStatus.REVOKED,
                error_message="任务已被用户取消"
            )
            
            logger.info(f"取消任务: {task_id}")
            return True
            
        except Exception as e:
            logger.error(f"取消任务失败: {task_id}, 错误: {str(e)}")
            return False
    
    def cleanup_expired_tasks(self, days: int = 7) -> int:
        """
        清理过期任务
        
        参数:
            days: 保留天数
            
        返回:
            int: 清理的任务数量
        """
        try:
            cutoff_time = now() - timedelta(days=days)
            cleaned_count = 0
            
            # 获取所有任务键
            task_keys = self.redis_client.keys(f"{self.task_prefix}*")
            
            for task_key in task_keys:
                try:
                    task_data = self.redis_client.get(task_key)
                    if task_data:
                        task_dict = json.loads(task_data)
                        created_at = datetime.fromisoformat(task_dict.get("created_at", ""))
                        
                        if created_at < cutoff_time:
                            task_id = task_dict.get("task_id", "")
                            
                            # 删除任务信息
                            self.redis_client.delete(task_key)
                            
                            # 删除任务日志
                            log_key = f"{self.log_prefix}{task_id}"
                            self.redis_client.delete(log_key)
                            
                            cleaned_count += 1
                            
                except Exception as e:
                    logger.error(f"清理任务失败: {task_key}, 错误: {str(e)}")
                    continue
            
            logger.info(f"清理过期任务完成，清理数量: {cleaned_count}")
            return cleaned_count
            
        except Exception as e:
            logger.error(f"清理过期任务失败: {str(e)}")
            return 0
    
    def _publish_websocket_event(self, task_id: str, event_type: str, data: Dict[str, Any]) -> None:
        """Publish task-centric events to the WebSocket channel."""
        if not task_id:
            return

        event = {
            "type": event_type,
            "task_id": task_id,
            "data": data,
            "timestamp": now().isoformat(),
        }

        try:
            channel = f"{self.ws_channel_prefix}{task_id}"
            self.redis_client.publish(channel, json.dumps(event))
        except Exception as exc:  # pragma: no cover - best-effort notification
            logger.debug(f"WebSocket event publish failed: {exc}")

    def _store_task_info(self, task_info: TaskInfo) -> None:
        """存储任务信息到Redis"""
        task_key = f"{self.task_prefix}{task_info.task_id}"
        task_data = task_info.model_dump_json()
        
        # 存储任务信息，设置过期时间（7天）
        self.redis_client.setex(task_key, 7 * 24 * 3600, task_data)
    
    def _add_to_user_tasks(self, user_id: int, task_id: str) -> None:
        """添加任务到用户任务列表"""
        user_tasks_key = f"{self.user_tasks_prefix}{user_id}"
        self.redis_client.lpush(user_tasks_key, task_id)
        
        # 限制用户任务列表长度（最多保留100个）
        self.redis_client.ltrim(user_tasks_key, 0, 99)
        
        # 设置过期时间（30天）
        self.redis_client.expire(user_tasks_key, 30 * 24 * 3600)
    
    def _get_task_from_celery(self, task_id: str) -> Optional[TaskInfo]:
        """从Celery结果后端获取任务信息"""
        try:
            result = AsyncResult(task_id, app=self.celery_app)
            
            if result.state == "PENDING":
                return None
            
            # 构建基础任务信息
            task_info = TaskInfo(
                task_id=task_id,
                task_name="未知任务",
                status=result.state,
                result=result.result if result.successful() else None,
                error_message=str(result.result) if result.failed() else None,
            )
            
            return task_info
            
        except Exception as e:
            logger.error(f"从Celery获取任务信息失败: {task_id}, 错误: {str(e)}")
            return None

# 全局任务跟踪器实例
task_tracker = TaskTracker()

def get_task_tracker() -> TaskTracker:
    """
    获取任务跟踪器实例
    
    返回:
        TaskTracker: 任务跟踪器实例
    """
    return task_tracker

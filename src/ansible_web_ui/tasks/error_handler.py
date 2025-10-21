"""
任务错误处理和超时管理模块

提供任务执行过程中的错误处理、超时管理和重试机制。
"""

import logging
import signal
import traceback
from functools import wraps
from typing import Any, Callable, Dict, Optional, Type, Union

from celery import Task
from celery.exceptions import Retry, SoftTimeLimitExceeded, WorkerLostError
from celery.signals import task_failure, task_retry, task_success

from ansible_web_ui.tasks.task_tracker import TaskStatus, get_task_tracker

logger = logging.getLogger(__name__)

class TaskError(Exception):
    """任务执行错误基类"""
    
    def __init__(self, message: str, error_code: str = "TASK_ERROR", details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        super().__init__(self.message)

class AnsibleExecutionError(TaskError):
    """Ansible执行错误"""
    
    def __init__(self, message: str, playbook: str = "", exit_code: int = 0, details: Optional[Dict[str, Any]] = None):
        self.playbook = playbook
        self.exit_code = exit_code
        super().__init__(message, "ANSIBLE_EXECUTION_ERROR", details)

class TaskTimeoutError(TaskError):
    """任务超时错误"""
    
    def __init__(self, message: str, timeout_seconds: int = 0, details: Optional[Dict[str, Any]] = None):
        self.timeout_seconds = timeout_seconds
        super().__init__(message, "TASK_TIMEOUT_ERROR", details)

class TaskCancelledError(TaskError):
    """任务取消错误"""
    
    def __init__(self, message: str = "任务已被取消", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, "TASK_CANCELLED_ERROR", details)

class ErrorHandler:
    """错误处理器"""
    
    def __init__(self):
        self.task_tracker = get_task_tracker()
        self._setup_signal_handlers()
    
    def _setup_signal_handlers(self):
        """设置信号处理器"""
        def timeout_handler(signum, frame):
            raise TaskTimeoutError("任务执行超时")
        
        # SIGALRM在Windows上不可用，只在Unix系统上设置
        if hasattr(signal, 'SIGALRM'):
            signal.signal(signal.SIGALRM, timeout_handler)
    
    def handle_task_error(
        self,
        task_id: str,
        error: Exception,
        task_name: str = "",
        retry_count: int = 0,
        max_retries: int = 3
    ) -> Dict[str, Any]:
        """
        处理任务错误
        
        参数:
            task_id: 任务ID
            error: 异常对象
            task_name: 任务名称
            retry_count: 当前重试次数
            max_retries: 最大重试次数
            
        返回:
            Dict[str, Any]: 错误处理结果
        """
        error_info = self._extract_error_info(error)
        
        # 记录错误日志
        logger.error(
            f"任务执行失败: {task_id}, 任务名称: {task_name}, "
            f"错误类型: {error_info['error_type']}, "
            f"错误信息: {error_info['message']}, "
            f"重试次数: {retry_count}/{max_retries}"
        )
        
        # 添加错误日志到任务跟踪器
        self.task_tracker.add_log_entry(
            task_id,
            f"❌ 任务执行失败: {error_info['message']}"
        )
        
        # 判断是否需要重试
        should_retry = self._should_retry_error(error, retry_count, max_retries)
        
        if should_retry:
            # 更新任务状态为重试中
            self.task_tracker.update_task_status(
                task_id,
                TaskStatus.RETRY,
                error_message=f"重试中 ({retry_count + 1}/{max_retries}): {error_info['message']}"
            )
            
            self.task_tracker.add_log_entry(
                task_id,
                f"🔄 任务将在 {self._get_retry_delay(retry_count)} 秒后重试"
            )
            
            return {
                "should_retry": True,
                "retry_delay": self._get_retry_delay(retry_count),
                "error_info": error_info
            }
        else:
            # 更新任务状态为失败
            self.task_tracker.update_task_status(
                task_id,
                TaskStatus.FAILURE,
                error_message=error_info['message'],
                result={
                    "error": error_info,
                    "retry_count": retry_count,
                    "final_failure": True
                }
            )
            
            return {
                "should_retry": False,
                "error_info": error_info
            }
    
    def _extract_error_info(self, error: Exception) -> Dict[str, Any]:
        """提取错误信息"""
        error_info = {
            "error_type": type(error).__name__,
            "message": str(error),
            "traceback": traceback.format_exc(),
        }
        
        # 处理特定错误类型（注意顺序，子类要在父类之前）
        if isinstance(error, AnsibleExecutionError):
            error_info.update({
                "playbook": error.playbook,
                "exit_code": error.exit_code,
                "error_code": error.error_code,
                "details": error.details
            })
        elif isinstance(error, TaskError):
            error_info.update({
                "error_code": error.error_code,
                "details": error.details
            })
        elif isinstance(error, SoftTimeLimitExceeded):
            error_info.update({
                "error_code": "SOFT_TIME_LIMIT_EXCEEDED",
                "message": "任务执行时间超过软限制"
            })
        elif isinstance(error, WorkerLostError):
            error_info.update({
                "error_code": "WORKER_LOST_ERROR",
                "message": "Worker进程丢失"
            })
        
        return error_info
    
    def _should_retry_error(self, error: Exception, retry_count: int, max_retries: int) -> bool:
        """判断错误是否应该重试"""
        if retry_count >= max_retries:
            return False
        
        # 不重试的错误类型
        non_retryable_errors = (
            TaskCancelledError,
            SoftTimeLimitExceeded,
            WorkerLostError,
        )
        
        if isinstance(error, non_retryable_errors):
            return False
        
        # Ansible执行错误根据退出码判断
        if isinstance(error, AnsibleExecutionError):
            # 语法错误等不重试
            if error.exit_code in [1, 4]:  # 语法错误、主机不可达
                return False
        
        return True
    
    def _get_retry_delay(self, retry_count: int) -> int:
        """获取重试延迟时间（指数退避）"""
        base_delay = 60  # 基础延迟60秒
        return min(base_delay * (2 ** retry_count), 300)  # 最大延迟5分钟

def with_error_handling(
    task_name: str = "",
    max_retries: int = 3,
    timeout_seconds: Optional[int] = None
):
    """
    任务错误处理装饰器
    
    参数:
        task_name: 任务名称
        max_retries: 最大重试次数
        timeout_seconds: 超时时间（秒）
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            task_id = self.request.id
            error_handler = ErrorHandler()
            
            try:
                # 设置超时（仅在Unix系统上可用）
                if timeout_seconds and hasattr(signal, 'alarm'):
                    signal.alarm(timeout_seconds)
                
                # 执行任务
                result = func(self, *args, **kwargs)
                
                # 清除超时（仅在Unix系统上可用）
                if timeout_seconds and hasattr(signal, 'alarm'):
                    signal.alarm(0)
                
                return result
                
            except Exception as error:
                # 清除超时（仅在Unix系统上可用）
                if timeout_seconds and hasattr(signal, 'alarm'):
                    signal.alarm(0)
                
                # 处理错误
                error_result = error_handler.handle_task_error(
                    task_id,
                    error,
                    task_name or func.__name__,
                    self.request.retries,
                    max_retries
                )
                
                if error_result["should_retry"]:
                    # 抛出重试异常
                    raise self.retry(
                        countdown=error_result["retry_delay"],
                        max_retries=max_retries,
                        exc=error
                    )
                else:
                    # 重新抛出原始异常
                    raise error
        
        return wrapper
    return decorator

# Celery信号处理器
@task_success.connect
def task_success_handler(sender=None, result=None, **kwargs):
    """任务成功处理器"""
    # 从 sender 或 kwargs 中获取 task_id
    task_id = kwargs.get('task_id')
    if not task_id and sender:
        # sender 是 Task 实例，可以从 request 中获取 task_id
        task_id = getattr(sender.request, 'id', None) if hasattr(sender, 'request') else None
    
    if not task_id:
        logger.warning("任务成功处理器收到空的 task_id")
        return
    
    task_tracker = get_task_tracker()
    
    # 更新任务状态
    task_tracker.update_task_status(
        task_id,
        TaskStatus.SUCCESS,
        progress=100,
        result=result
    )
    
    # 添加成功日志
    task_tracker.add_log_entry(task_id, "✅ 任务执行成功")
    
    logger.info(f"任务执行成功: {task_id}")

@task_failure.connect
def task_failure_handler(sender=None, exception=None, traceback=None, einfo=None, **kwargs):
    """任务失败处理器"""
    # 从 kwargs 中获取 task_id
    task_id = kwargs.get('task_id')
    if not task_id and sender:
        task_id = getattr(sender.request, 'id', None) if hasattr(sender, 'request') else None
    
    if not task_id:
        logger.warning("任务失败处理器收到空的 task_id")
        return
    
    task_tracker = get_task_tracker()
    error_handler = ErrorHandler()
    
    # 提取错误信息
    error_info = error_handler._extract_error_info(exception)
    
    # 更新任务状态
    task_tracker.update_task_status(
        task_id,
        TaskStatus.FAILURE,
        error_message=error_info['message'],
        result={"error": error_info}
    )
    
    # 添加失败日志
    task_tracker.add_log_entry(task_id, f"❌ 任务最终失败: {error_info['message']}")
    
    logger.error(f"任务最终失败: {task_id}, 错误: {error_info['message']}")

@task_retry.connect
def task_retry_handler(sender=None, reason=None, einfo=None, **kwargs):
    """任务重试处理器"""
    # 从 kwargs 中获取 task_id
    task_id = kwargs.get('task_id')
    if not task_id and sender:
        task_id = getattr(sender.request, 'id', None) if hasattr(sender, 'request') else None
    
    if not task_id:
        logger.warning("任务重试处理器收到空的 task_id")
        return
    
    task_tracker = get_task_tracker()
    
    # 添加重试日志
    task_tracker.add_log_entry(task_id, f"🔄 任务重试: {reason}")
    
    logger.info(f"任务重试: {task_id}, 原因: {reason}")

# 全局错误处理器实例
error_handler = ErrorHandler()

def get_error_handler() -> ErrorHandler:
    """
    获取错误处理器实例
    
    返回:
        ErrorHandler: 错误处理器实例
    """
    return error_handler
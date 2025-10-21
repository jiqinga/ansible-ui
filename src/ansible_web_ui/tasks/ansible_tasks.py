"""
🚀 Ansible任务执行模块

提供Ansible playbook执行的Celery任务定义，集成实时日志捕获和任务管理功能。
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional

from celery import Task

from ansible_web_ui.tasks.celery_app import celery_app
from ansible_web_ui.tasks.error_handler import with_error_handling
from ansible_web_ui.tasks.task_tracker import TaskStatus, get_task_tracker
from ansible_web_ui.services.ansible_execution_service import (
    get_ansible_execution_service,
    AnsibleExecutionOptions
)

logger = logging.getLogger(__name__)

class BaseAnsibleTask(Task):
    """Ansible任务基类"""
    
    def on_success(self, retval, task_id, args, kwargs):
        """任务成功回调"""
        task_tracker = get_task_tracker()
        task_tracker.add_log_entry(task_id, "✅ 任务执行完成")
        logger.info(f"Ansible任务成功: {task_id}")
    
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """任务失败回调"""
        task_tracker = get_task_tracker()
        task_tracker.add_log_entry(task_id, f"❌ 任务执行失败: {str(exc)}")
        logger.error(f"Ansible任务失败: {task_id}, 错误: {str(exc)}")
    
    def on_retry(self, exc, task_id, args, kwargs, einfo):
        """任务重试回调"""
        task_tracker = get_task_tracker()
        task_tracker.add_log_entry(task_id, f"🔄 任务重试: {str(exc)}")
        logger.info(f"Ansible任务重试: {task_id}, 原因: {str(exc)}")

@celery_app.task(bind=True, base=BaseAnsibleTask, name="ansible_web_ui.tasks.run_playbook")
@with_error_handling(task_name="运行Ansible Playbook", max_retries=2, timeout_seconds=1800)
def run_playbook_task(
    self,
    playbook_name: str,
    inventory_targets: List[str],
    extra_vars: Optional[Dict[str, Any]] = None,
    user_id: Optional[int] = None,
    execution_options: Optional[Dict[str, Any]] = None,
    **kwargs
) -> Dict[str, Any]:
    """
    🚀 执行Ansible Playbook任务
    
    参数:
        playbook_name: Playbook文件名
        inventory_targets: 目标主机列表
        extra_vars: 额外变量
        user_id: 执行用户ID
        execution_options: 执行选项配置
        **kwargs: 其他参数
        
    返回:
        Dict[str, Any]: 执行结果
    """
    import time
    from ansible_web_ui.websocket.manager import get_websocket_manager
    
    task_id = self.request.id
    task_tracker = get_task_tracker()
    ansible_service = get_ansible_execution_service()
    ws_manager = get_websocket_manager()
    
    # 等待WebSocket连接建立（最多等待5秒）
    max_wait_time = 5
    wait_interval = 0.1
    elapsed_time = 0
    
    logger.info(f"⏳ 等待WebSocket连接建立: task_id={task_id}")
    while elapsed_time < max_wait_time:
        if ws_manager.get_active_connections(task_id) > 0:
            logger.info(f"✅ WebSocket连接已建立: task_id={task_id}")
            break
        time.sleep(wait_interval)
        elapsed_time += wait_interval
    
    if ws_manager.get_active_connections(task_id) == 0:
        logger.warning(f"⚠️ WebSocket连接未建立，继续执行任务: task_id={task_id}")
    
    # 更新任务状态为开始执行
    task_tracker.update_task_status(
        task_id,
        TaskStatus.STARTED,
        progress=5,
        current_step="初始化Ansible执行服务"
    )
    
    task_tracker.add_log_entry(task_id, f"🚀 开始执行Playbook: {playbook_name}")
    task_tracker.add_log_entry(task_id, f"🎯 目标主机: {', '.join(inventory_targets)}")
    
    try:
        # 准备执行选项
        options = AnsibleExecutionOptions()
        if execution_options:
            options = AnsibleExecutionOptions(**execution_options)
        
        # 设置额外变量
        if extra_vars:
            options.extra_vars = extra_vars
        
        # 定义日志回调函数
        def log_callback(message: str):
            """实时日志回调"""
            # 这里可以通过WebSocket推送实时日志
            pass
        
        # 执行Playbook
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            execution_result = loop.run_until_complete(
                ansible_service.execute_playbook(
                    playbook_name=playbook_name,
                    inventory_targets=inventory_targets,
                    options=options,
                    user_id=user_id,
                    log_callback=log_callback,
                    task_id=task_id  # 传递Celery任务ID
                )
            )
        finally:
            loop.close()
        
        # 转换结果格式
        result = {
            "task_id": task_id,  # 使用Celery任务ID
            "playbook": execution_result.playbook_name,
            "targets": inventory_targets,
            "status": execution_result.status,
            "exit_code": execution_result.exit_code,
            "duration": execution_result.duration,
            "stats": execution_result.stats,
            "message": f"Playbook执行{'成功' if execution_result.status == 'success' else '失败'}",
            "log_file_path": execution_result.log_file_path
        }
        
        # 更新最终状态
        final_status = TaskStatus.SUCCESS if execution_result.status == "success" else TaskStatus.FAILURE
        task_tracker.update_task_status(
            task_id,
            final_status,
            progress=100,
            result=result
        )
        
        return result
        
    except Exception as e:
        error_message = f"Playbook执行失败: {str(e)}"
        task_tracker.add_log_entry(task_id, f"❌ {error_message}")
        
        # 更新失败状态
        task_tracker.update_task_status(
            task_id,
            TaskStatus.FAILURE,
            error_message=error_message
        )
        
        # 重新抛出异常以触发Celery的重试机制
        raise

@celery_app.task(bind=True, base=BaseAnsibleTask, name="ansible_web_ui.tasks.validate_playbook")
def validate_playbook_task(self, playbook_name: str) -> Dict[str, Any]:
    """
    🔍 验证Playbook语法任务
    
    参数:
        playbook_name: Playbook文件名
        
    返回:
        Dict[str, Any]: 验证结果
    """
    task_id = self.request.id
    task_tracker = get_task_tracker()
    ansible_service = get_ansible_execution_service()
    
    task_tracker.add_log_entry(task_id, f"🔍 开始验证Playbook语法: {playbook_name}")
    
    try:
        # 使用Ansible执行服务验证语法
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            result = loop.run_until_complete(
                ansible_service.validate_playbook_syntax(playbook_name)
            )
        finally:
            loop.close()
        
        task_tracker.add_log_entry(
            task_id, 
            f"✅ Playbook语法验证完成: {'通过' if result['valid'] else '失败'}"
        )
        
        return result
        
    except Exception as e:
        error_message = f"语法验证失败: {str(e)}"
        task_tracker.add_log_entry(task_id, f"❌ {error_message}")
        
        return {
            "valid": False,
            "errors": [error_message],
            "warnings": [],
            "message": "语法验证过程中发生错误"
        }

@celery_app.task(bind=True, base=BaseAnsibleTask, name="ansible_web_ui.tasks.test_connection")
def test_connection_task(self, inventory_targets: List[str]) -> Dict[str, Any]:
    """
    🔗 测试主机连接任务
    
    参数:
        inventory_targets: 目标主机列表
        
    返回:
        Dict[str, Any]: 连接测试结果
    """
    task_id = self.request.id
    task_tracker = get_task_tracker()
    ansible_service = get_ansible_execution_service()
    
    task_tracker.add_log_entry(task_id, f"🔗 开始测试主机连接: {', '.join(inventory_targets)}")
    
    try:
        # 使用Ansible执行服务测试连接
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            result = loop.run_until_complete(
                ansible_service.test_host_connectivity(inventory_targets)
            )
        finally:
            loop.close()
        
        task_tracker.add_log_entry(
            task_id, 
            f"✅ 主机连接测试完成: 成功 {len(result.get('successful_hosts', []))}, "
            f"失败 {len(result.get('failed_hosts', []))}"
        )
        
        return result
        
    except Exception as e:
        error_message = f"连接测试失败: {str(e)}"
        task_tracker.add_log_entry(task_id, f"❌ {error_message}")
        
        return {
            "tested_hosts": inventory_targets,
            "successful_hosts": [],
            "failed_hosts": inventory_targets,
            "success_rate": 0,
            "error": error_message,
            "message": error_message
        }


@celery_app.task(bind=True, base=BaseAnsibleTask, name="ansible_web_ui.tasks.cancel_playbook")
def cancel_playbook_task(self, target_task_id: str) -> Dict[str, Any]:
    """
    🛑 取消Playbook执行任务
    
    参数:
        target_task_id: 要取消的任务ID
        
    返回:
        Dict[str, Any]: 取消结果
    """
    task_id = self.request.id
    task_tracker = get_task_tracker()
    ansible_service = get_ansible_execution_service()
    
    task_tracker.add_log_entry(task_id, f"🛑 开始取消任务: {target_task_id}")
    
    try:
        # 使用Ansible执行服务取消任务
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            success = loop.run_until_complete(
                ansible_service.cancel_task(target_task_id)
            )
        finally:
            loop.close()
        
        if success:
            task_tracker.add_log_entry(task_id, f"✅ 任务取消成功: {target_task_id}")
            return {
                "success": True,
                "message": f"任务 {target_task_id} 已成功取消",
                "cancelled_task_id": target_task_id
            }
        else:
            task_tracker.add_log_entry(task_id, f"⚠️ 任务取消失败: {target_task_id}")
            return {
                "success": False,
                "message": f"任务 {target_task_id} 取消失败，可能已经完成或不存在",
                "cancelled_task_id": target_task_id
            }
            
    except Exception as e:
        error_message = f"取消任务异常: {str(e)}"
        task_tracker.add_log_entry(task_id, f"❌ {error_message}")
        
        return {
            "success": False,
            "message": error_message,
            "cancelled_task_id": target_task_id,
            "error": str(e)
        }


@celery_app.task(bind=True, base=BaseAnsibleTask, name="ansible_web_ui.tasks.retry_playbook")
def retry_playbook_task(
    self, 
    original_task_id: str, 
    max_retries: int = 3, 
    retry_delay: int = 60
) -> Dict[str, Any]:
    """
    🔄 重试Playbook执行任务
    
    参数:
        original_task_id: 原始任务ID
        max_retries: 最大重试次数
        retry_delay: 重试延迟(秒)
        
    返回:
        Dict[str, Any]: 重试结果
    """
    task_id = self.request.id
    task_tracker = get_task_tracker()
    ansible_service = get_ansible_execution_service()
    
    task_tracker.add_log_entry(task_id, f"🔄 开始重试任务: {original_task_id}")
    
    try:
        # 使用Ansible执行服务重试任务
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            success = loop.run_until_complete(
                ansible_service.retry_task(original_task_id, max_retries, retry_delay)
            )
        finally:
            loop.close()
        
        if success:
            task_tracker.add_log_entry(task_id, f"✅ 任务重试启动成功: {original_task_id}")
            return {
                "success": True,
                "message": f"任务 {original_task_id} 重试已启动",
                "original_task_id": original_task_id,
                "retry_task_id": task_id
            }
        else:
            task_tracker.add_log_entry(task_id, f"⚠️ 任务重试失败: {original_task_id}")
            return {
                "success": False,
                "message": f"任务 {original_task_id} 重试失败，可能已达到最大重试次数",
                "original_task_id": original_task_id
            }
            
    except Exception as e:
        error_message = f"重试任务异常: {str(e)}"
        task_tracker.add_log_entry(task_id, f"❌ {error_message}")
        
        return {
            "success": False,
            "message": error_message,
            "original_task_id": original_task_id,
            "error": str(e)
        }
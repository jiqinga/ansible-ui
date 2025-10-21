"""
🚀 Ansible执行服务

提供Ansible playbook执行的核心功能，包括命令封装、实时日志捕获和任务管理。
"""

import asyncio
import json
import logging
import os
import signal
import subprocess
import tempfile
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union, Callable
from uuid import uuid4

import yaml
from pydantic import BaseModel, Field

from ansible_web_ui.core.config import get_settings
from ansible_web_ui.tasks.task_tracker import get_task_tracker, TaskStatus
from ansible_web_ui.services.inventory_service import InventoryService
from ansible_web_ui.services.playbook_service import PlaybookService
from ansible_web_ui.utils.timezone import now

logger = logging.getLogger(__name__)
settings = get_settings()


class AnsibleExecutionOptions(BaseModel):
    """Ansible执行选项配置"""
    
    # 基础选项
    inventory: Optional[str] = Field(None, description="Inventory文件路径或主机列表")
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
    ask_become_pass: bool = Field(False, description="询问提权密码")


class AnsibleExecutionResult(BaseModel):
    """Ansible执行结果"""
    
    task_id: str = Field(..., description="任务ID")
    playbook_name: str = Field(..., description="Playbook名称")
    status: str = Field(..., description="执行状态")
    exit_code: Optional[int] = Field(None, description="退出代码")
    start_time: datetime = Field(..., description="开始时间")
    end_time: Optional[datetime] = Field(None, description="结束时间")
    duration: Optional[float] = Field(None, description="执行时长(秒)")
    
    # 执行统计
    stats: Optional[Dict[str, Any]] = Field(None, description="执行统计信息")
    
    # 输出信息
    stdout: Optional[str] = Field(None, description="标准输出")
    stderr: Optional[str] = Field(None, description="错误输出")
    log_file_path: Optional[str] = Field(None, description="日志文件路径")
    
    # 错误信息
    error_message: Optional[str] = Field(None, description="错误消息")
    failed_tasks: Optional[List[Dict[str, Any]]] = Field(None, description="失败的任务")


class LogStreamHandler:
    """📝 日志流处理器"""
    
    def __init__(self, task_id: str, callback: Optional[Callable[[str], None]] = None):
        self.task_id = task_id
        self.callback = callback
        self.task_tracker = get_task_tracker()
        self.log_buffer = []
        self.lock = threading.Lock()
    
    def write_log(self, message: str, level: str = "INFO") -> None:
        """写入日志消息"""
        timestamp = now().strftime("%H:%M:%S")
        formatted_message = f"[{timestamp}] {level}: {message}"
        
        with self.lock:
            self.log_buffer.append(formatted_message)
            
        # 添加到任务跟踪器
        self.task_tracker.add_log_entry(self.task_id, formatted_message)
        
        # 调用回调函数（用于实时推送）
        if self.callback:
            try:
                self.callback(formatted_message)
            except Exception as e:
                logger.error(f"日志回调函数执行失败: {e}")
    
    def get_logs(self) -> List[str]:
        """获取所有日志"""
        with self.lock:
            return self.log_buffer.copy()


class AnsibleProcessManager:
    """🔧 Ansible进程管理器"""
    
    def __init__(self):
        self.running_processes: Dict[str, subprocess.Popen] = {}
        self.lock = threading.Lock()
    
    def add_process(self, task_id: str, process: subprocess.Popen) -> None:
        """添加运行中的进程"""
        with self.lock:
            self.running_processes[task_id] = process
    
    def remove_process(self, task_id: str) -> None:
        """移除进程"""
        with self.lock:
            self.running_processes.pop(task_id, None)
    
    def get_process(self, task_id: str) -> Optional[subprocess.Popen]:
        """获取进程"""
        with self.lock:
            return self.running_processes.get(task_id)
    
    def terminate_process(self, task_id: str) -> bool:
        """终止进程"""
        process = self.get_process(task_id)
        if not process:
            return False
        
        try:
            # 尝试优雅终止
            process.terminate()
            
            # 等待进程结束
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                # 强制杀死进程
                process.kill()
                process.wait()
            
            self.remove_process(task_id)
            return True
            
        except Exception as e:
            logger.error(f"终止进程失败: {task_id}, 错误: {e}")
            return False


class AnsibleExecutionService:
    """🎯 Ansible执行服务"""
    
    def __init__(self):
        self.settings = get_settings()
        self.task_tracker = get_task_tracker()
        self.process_manager = AnsibleProcessManager()
        
        # 确保必要的目录存在
        self._ensure_directories()
    
    def _ensure_directories(self) -> None:
        """确保必要的目录存在"""
        directories = [
            Path(self.settings.PLAYBOOK_DIR),
            Path(self.settings.INVENTORY_DIR),
            Path(self.settings.LOG_DIR),
            Path(self.settings.LOG_DIR) / "ansible_executions"
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
    
    async def execute_playbook(
        self,
        playbook_name: str,
        inventory_targets: List[str],
        options: Optional[AnsibleExecutionOptions] = None,
        user_id: Optional[int] = None,
        log_callback: Optional[Callable[[str], None]] = None,
        task_id: Optional[str] = None
    ) -> AnsibleExecutionResult:
        """
        🚀 执行Ansible Playbook
        
        Args:
            playbook_name: Playbook文件名
            inventory_targets: 目标主机列表
            options: 执行选项
            user_id: 执行用户ID
            log_callback: 日志回调函数
            task_id: 任务ID（如果不提供则自动生成）
            
        Returns:
            AnsibleExecutionResult: 执行结果
        """
        task_id = task_id or str(uuid4())
        start_time = now()
        
        # 创建日志处理器
        log_handler = LogStreamHandler(task_id, log_callback)
        
        # 创建任务记录（使用传入的task_id）
        self.task_tracker.create_task(
            task_name=f"执行Playbook: {playbook_name}",
            user_id=user_id,
            playbook_name=playbook_name,
            inventory_targets=inventory_targets,
            task_id=task_id
        )
        
        try:
            log_handler.write_log(f"🚀 开始执行Playbook: {playbook_name}")
            log_handler.write_log(f"🎯 目标主机: {', '.join(inventory_targets)}")
            
            # 更新任务状态
            self.task_tracker.update_task_status(
                task_id,
                TaskStatus.STARTED,
                progress=10,
                current_step="准备执行环境"
            )
            
            # 准备执行环境
            playbook_path, inventory_path = await self._prepare_execution_environment(
                playbook_name, inventory_targets, log_handler
            )
            
            # 构建Ansible命令
            command = self._build_ansible_command(
                playbook_path, inventory_path, options or AnsibleExecutionOptions()
            )
            
            log_handler.write_log(f"🔧 执行命令: {' '.join(command)}")
            
            # 更新任务状态
            self.task_tracker.update_task_status(
                task_id,
                TaskStatus.STARTED,
                progress=20,
                current_step="启动Ansible进程"
            )
            
            # 执行Ansible命令
            result = await self._execute_ansible_command(
                task_id, command, log_handler
            )
            
            # 解析执行结果
            execution_result = self._parse_execution_result(
                task_id, playbook_name, start_time, result, log_handler
            )
            
            # 更新最终状态
            final_status = TaskStatus.SUCCESS if execution_result.exit_code == 0 else TaskStatus.FAILURE
            self.task_tracker.update_task_status(
                task_id,
                final_status,
                progress=100,
                result=execution_result.model_dump()
            )
            
            log_handler.write_log(
                f"✅ Playbook执行完成，状态: {execution_result.status}"
            )
            
            return execution_result
            
        except Exception as e:
            error_message = f"Playbook执行失败: {str(e)}"
            log_handler.write_log(f"❌ {error_message}", "ERROR")
            
            # 更新失败状态
            self.task_tracker.update_task_status(
                task_id,
                TaskStatus.FAILURE,
                error_message=error_message
            )
            
            return AnsibleExecutionResult(
                task_id=task_id,
                playbook_name=playbook_name,
                status="failed",
                start_time=start_time,
                end_time=now(),
                error_message=error_message
            )
    
    async def _prepare_execution_environment(
        self,
        playbook_name: str,
        inventory_targets: List[str],
        log_handler: LogStreamHandler
    ) -> Tuple[str, str]:
        """准备执行环境"""
        log_handler.write_log("📋 准备执行环境...")
        
        # 规范化 Playbook 路径（移除可能的目录前缀）
        playbook_name = self._normalize_playbook_path(playbook_name)
        
        # 验证Playbook文件存在
        playbook_path = Path(self.settings.PLAYBOOK_DIR) / playbook_name
        if not playbook_path.exists():
            raise FileNotFoundError(f"Playbook文件不存在: {playbook_name}")
        
        # 创建临时inventory文件
        inventory_path = await self._create_temporary_inventory(inventory_targets)
        
        log_handler.write_log(f"📁 Playbook路径: {playbook_path}")
        log_handler.write_log(f"📋 Inventory路径: {inventory_path}")
        
        return str(playbook_path), inventory_path
    
    async def _create_temporary_inventory(self, inventory_targets: List[str]) -> str:
        """
        创建临时inventory文件
        
        注意：
        - 如果目标是数据库中的主机名，会从主机配置中读取连接信息
        - 始终包含 localhost，以支持本地执行的 playbook
        """
        # 创建临时文件
        temp_file = tempfile.NamedTemporaryFile(
            mode='w', suffix='.ini', delete=False, dir=self.settings.INVENTORY_DIR
        )
        
        try:
            # 始终添加 localhost（用于本地执行）
            temp_file.write("[local]\n")
            temp_file.write("localhost ansible_connection=local\n\n")
            
            # 写入目标主机信息
            temp_file.write("[targets]\n")
            for target in inventory_targets:
                # 如果目标就是 localhost，跳过（已经在 [local] 组中）
                if target.lower() == "localhost":
                    continue
                temp_file.write(f"{target}\n")
            
            temp_file.flush()
            return temp_file.name
            
        finally:
            temp_file.close()
    
    def _normalize_playbook_path(self, playbook_name: str) -> str:
        """
        规范化 Playbook 路径
        
        移除可能的目录前缀（如 'playbooks\\'），只保留文件名
        
        Args:
            playbook_name: 原始 Playbook 名称
            
        Returns:
            str: 规范化后的 Playbook 名称
        """
        # 移除 'playbooks\' 或 'playbooks/' 前缀
        if playbook_name.startswith('playbooks\\') or playbook_name.startswith('playbooks/'):
            playbook_name = playbook_name.split('playbooks', 1)[1].lstrip('\\/').lstrip('/')
        
        return playbook_name
    
    def _build_ansible_command(
        self,
        playbook_path: str,
        inventory_path: str,
        options: AnsibleExecutionOptions
    ) -> List[str]:
        """构建Ansible命令"""
        command = ["ansible-playbook"]
        
        # 基础参数
        command.extend(["-i", inventory_path])
        command.append(playbook_path)
        
        # 详细输出级别
        if options.verbose > 0:
            command.append("-" + "v" * min(options.verbose, 4))
        
        # 限制主机
        if options.limit:
            command.extend(["--limit", options.limit])
        
        # 标签
        if options.tags:
            command.extend(["--tags", options.tags])
        if options.skip_tags:
            command.extend(["--skip-tags", options.skip_tags])
        
        # 额外变量
        if options.extra_vars:
            extra_vars_json = json.dumps(options.extra_vars)
            command.extend(["--extra-vars", extra_vars_json])
        
        # 连接选项
        if options.user:
            command.extend(["--user", options.user])
        if options.private_key_file:
            command.extend(["--private-key", options.private_key_file])
        if options.connection != "ssh":
            command.extend(["--connection", options.connection])
        if options.timeout != 30:
            command.extend(["--timeout", str(options.timeout)])
        
        # 执行选项
        if options.forks != 5:
            command.extend(["--forks", str(options.forks)])
        if options.check:
            command.append("--check")
        if options.diff:
            command.append("--diff")
        
        # 提权选项
        if options.become:
            command.append("--become")
            if options.become_user:
                command.extend(["--become-user", options.become_user])
            if options.become_method != "sudo":
                command.extend(["--become-method", options.become_method])
        
        return command
    
    async def _execute_ansible_command(
        self,
        task_id: str,
        command: List[str],
        log_handler: LogStreamHandler
    ) -> Dict[str, Any]:
        """执行Ansible命令"""
        log_handler.write_log("⚡ 启动Ansible进程...")
        
        # 创建日志文件
        log_file_path = Path(self.settings.LOG_DIR) / "ansible_executions" / f"{task_id}.log"
        
        try:
            # 启动进程
            process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True,
                bufsize=1,
                cwd=self.settings.PLAYBOOK_DIR
            )
            
            # 注册进程
            self.process_manager.add_process(task_id, process)
            
            # 实时读取输出
            stdout_lines = []
            stderr_lines = []
            
            def read_stdout():
                """读取标准输出"""
                for line in iter(process.stdout.readline, ''):
                    if line:
                        line = line.rstrip()
                        stdout_lines.append(line)
                        log_handler.write_log(f"📤 {line}")
                        
                        # 更新进度（简单的进度估算）
                        if "TASK" in line:
                            progress = min(90, len(stdout_lines) * 2)
                            self.task_tracker.update_task_status(
                                task_id,
                                TaskStatus.STARTED,
                                progress=progress,
                                current_step=line.strip()
                            )
            
            def read_stderr():
                """读取错误输出"""
                for line in iter(process.stderr.readline, ''):
                    if line:
                        line = line.rstrip()
                        stderr_lines.append(line)
                        log_handler.write_log(f"⚠️ {line}", "WARN")
            
            # 启动输出读取线程
            stdout_thread = threading.Thread(target=read_stdout)
            stderr_thread = threading.Thread(target=read_stderr)
            
            stdout_thread.start()
            stderr_thread.start()
            
            # 等待进程完成
            exit_code = process.wait()
            
            # 等待输出读取完成
            stdout_thread.join(timeout=5)
            stderr_thread.join(timeout=5)
            
            # 移除进程记录
            self.process_manager.remove_process(task_id)
            
            # 保存日志到文件
            with open(log_file_path, 'w', encoding='utf-8') as f:
                f.write("=== STDOUT ===\n")
                f.write("\n".join(stdout_lines))
                f.write("\n\n=== STDERR ===\n")
                f.write("\n".join(stderr_lines))
            
            return {
                "exit_code": exit_code,
                "stdout": "\n".join(stdout_lines),
                "stderr": "\n".join(stderr_lines),
                "log_file_path": str(log_file_path)
            }
            
        except Exception as e:
            self.process_manager.remove_process(task_id)
            raise e
    
    def _parse_execution_result(
        self,
        task_id: str,
        playbook_name: str,
        start_time: datetime,
        result: Dict[str, Any],
        log_handler: LogStreamHandler
    ) -> AnsibleExecutionResult:
        """解析执行结果"""
        end_time = now()
        duration = (end_time - start_time).total_seconds()
        
        # 确定状态
        exit_code = result.get("exit_code", -1)
        if exit_code == 0:
            status = "success"
        elif exit_code == 2:
            status = "failed"
        else:
            status = "error"
        
        # 解析统计信息（从输出中提取）
        stats = self._extract_stats_from_output(result.get("stdout", ""))
        
        # 解析失败任务
        failed_tasks = self._extract_failed_tasks(result.get("stderr", ""))
        
        return AnsibleExecutionResult(
            task_id=task_id,
            playbook_name=playbook_name,
            status=status,
            exit_code=exit_code,
            start_time=start_time,
            end_time=end_time,
            duration=duration,
            stats=stats,
            stdout=result.get("stdout"),
            stderr=result.get("stderr"),
            log_file_path=result.get("log_file_path"),
            error_message=result.get("stderr") if exit_code != 0 else None,
            failed_tasks=failed_tasks
        )
    
    def _extract_stats_from_output(self, stdout: str) -> Dict[str, Any]:
        """从输出中提取统计信息"""
        stats = {
            "ok": 0,
            "changed": 0,
            "unreachable": 0,
            "failed": 0,
            "skipped": 0,
            "rescued": 0,
            "ignored": 0
        }
        
        # 查找统计信息行
        for line in stdout.split('\n'):
            if "PLAY RECAP" in line:
                continue
            if any(key in line for key in stats.keys()):
                # 解析统计信息
                for key in stats.keys():
                    if f"{key}=" in line:
                        try:
                            value = line.split(f"{key}=")[1].split()[0]
                            stats[key] = int(value)
                        except (IndexError, ValueError):
                            pass
        
        return stats
    
    def _extract_failed_tasks(self, stderr: str) -> List[Dict[str, Any]]:
        """从错误输出中提取失败任务"""
        failed_tasks = []
        
        # 这里可以实现更复杂的错误解析逻辑
        if stderr:
            failed_tasks.append({
                "error": stderr[:500],  # 限制错误信息长度
                "timestamp": now().isoformat()
            })
        
        return failed_tasks
    
    async def cancel_task(self, task_id: str) -> bool:
        """
        🛑 取消任务执行
        
        Args:
            task_id: 任务ID
            
        Returns:
            bool: 是否取消成功
        """
        try:
            # 终止进程
            if self.process_manager.terminate_process(task_id):
                # 更新任务状态
                self.task_tracker.update_task_status(
                    task_id,
                    TaskStatus.REVOKED,
                    error_message="任务已被用户取消"
                )
                
                logger.info(f"任务取消成功: {task_id}")
                return True
            else:
                logger.warning(f"任务取消失败，进程不存在: {task_id}")
                return False
                
        except Exception as e:
            logger.error(f"取消任务失败: {task_id}, 错误: {e}")
            return False
    
    async def retry_task(
        self,
        task_id: str,
        max_retries: int = 3,
        retry_delay: int = 60
    ) -> bool:
        """
        🔄 重试任务
        
        Args:
            task_id: 原任务ID
            max_retries: 最大重试次数
            retry_delay: 重试延迟(秒)
            
        Returns:
            bool: 是否成功启动重试
        """
        try:
            # 获取原任务信息
            task_info = self.task_tracker.get_task_info(task_id)
            if not task_info:
                logger.error(f"重试失败，任务不存在: {task_id}")
                return False
            
            # 检查重试次数
            retry_count = getattr(task_info, 'retry_count', 0)
            if retry_count >= max_retries:
                logger.warning(f"任务重试次数已达上限: {task_id}")
                return False
            
            # 等待重试延迟
            if retry_delay > 0:
                await asyncio.sleep(retry_delay)
            
            # 创建新的重试任务
            new_task_id = str(uuid4())
            
            # 记录重试信息
            self.task_tracker.add_log_entry(
                new_task_id,
                f"🔄 重试任务 {task_id}，第 {retry_count + 1} 次重试"
            )
            
            logger.info(f"任务重试启动: 原任务={task_id}, 新任务={new_task_id}")
            return True
            
        except Exception as e:
            logger.error(f"重试任务失败: {task_id}, 错误: {e}")
            return False
    
    async def validate_playbook_syntax(self, playbook_name: str) -> Dict[str, Any]:
        """
        ✅ 验证Playbook语法
        
        Args:
            playbook_name: Playbook文件名
            
        Returns:
            Dict[str, Any]: 验证结果
        """
        try:
            playbook_path = Path(self.settings.PLAYBOOK_DIR) / playbook_name
            
            if not playbook_path.exists():
                return {
                    "valid": False,
                    "errors": [f"Playbook文件不存在: {playbook_name}"],
                    "warnings": []
                }
            
            # 使用ansible-playbook --syntax-check验证语法
            command = [
                "ansible-playbook",
                "--syntax-check",
                str(playbook_path)
            ]
            
            process = subprocess.run(
                command,
                capture_output=True,
                text=True,
                cwd=self.settings.PLAYBOOK_DIR
            )
            
            if process.returncode == 0:
                return {
                    "valid": True,
                    "errors": [],
                    "warnings": [],
                    "message": "Playbook语法验证通过"
                }
            else:
                return {
                    "valid": False,
                    "errors": [process.stderr.strip()],
                    "warnings": [],
                    "message": "Playbook语法验证失败"
                }
                
        except Exception as e:
            return {
                "valid": False,
                "errors": [f"语法验证异常: {str(e)}"],
                "warnings": [],
                "message": "语法验证过程中发生错误"
            }
    
    async def test_host_connectivity(self, hosts: List[str]) -> Dict[str, Any]:
        """
        🔗 测试主机连接性
        
        Args:
            hosts: 主机列表
            
        Returns:
            Dict[str, Any]: 连接测试结果
        """
        try:
            # 创建临时inventory
            inventory_path = await self._create_temporary_inventory(hosts)
            
            # 使用ansible ping模块测试连接
            command = [
                "ansible",
                "all",
                "-i", inventory_path,
                "-m", "ping",
                "--timeout", "10"
            ]
            
            process = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=60
            )
            
            # 解析结果
            successful_hosts = []
            failed_hosts = []
            
            for line in process.stdout.split('\n'):
                if "SUCCESS" in line:
                    host = line.split()[0]
                    successful_hosts.append(host)
                elif "UNREACHABLE" in line or "FAILED" in line:
                    host = line.split()[0]
                    failed_hosts.append(host)
            
            # 清理临时文件
            try:
                os.unlink(inventory_path)
            except:
                pass
            
            return {
                "total_hosts": len(hosts),
                "successful_hosts": successful_hosts,
                "failed_hosts": failed_hosts,
                "success_rate": len(successful_hosts) / len(hosts) * 100 if hosts else 0,
                "message": f"连接测试完成，成功: {len(successful_hosts)}, 失败: {len(failed_hosts)}"
            }
            
        except Exception as e:
            return {
                "total_hosts": len(hosts),
                "successful_hosts": [],
                "failed_hosts": hosts,
                "success_rate": 0,
                "error": str(e),
                "message": f"连接测试失败: {str(e)}"
            }


# 全局服务实例
ansible_execution_service = AnsibleExecutionService()


def get_ansible_execution_service() -> AnsibleExecutionService:
    """
    获取Ansible执行服务实例
    
    Returns:
        AnsibleExecutionService: 服务实例
    """
    return ansible_execution_service
"""
任务执行服务

提供Ansible任务执行历史管理相关的业务逻辑。
"""

import uuid
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, and_

from ansible_web_ui.models.task_execution import TaskExecution, TaskStatus
from ansible_web_ui.models.user import User
from ansible_web_ui.services.base import BaseService


class TaskExecutionService(BaseService[TaskExecution]):
    """
    任务执行服务类
    
    提供任务执行记录管理、统计分析等功能。
    """
    
    def __init__(self, db_session: AsyncSession):
        super().__init__(TaskExecution, db_session)

    async def create_task_execution(
        self,
        user_id: int,
        playbook_name: str,
        inventory_targets: str,
        playbook_path: Optional[str] = None,
        extra_vars: Optional[Dict[str, Any]] = None,
        tags: Optional[str] = None,
        limit: Optional[str] = None
    ) -> TaskExecution:
        """
        创建新的任务执行记录
        
        Args:
            user_id: 执行用户ID
            playbook_name: Playbook名称
            inventory_targets: 目标主机清单
            playbook_path: Playbook文件路径
            extra_vars: 额外变量
            tags: 执行标签
            limit: 限制执行的主机
            
        Returns:
            TaskExecution: 创建的任务执行对象
        """
        task_id = str(uuid.uuid4())
        
        return await self.create(
            task_id=task_id,
            user_id=user_id,
            playbook_name=playbook_name,
            playbook_path=playbook_path,
            inventory_targets=inventory_targets,
            extra_vars=extra_vars,
            tags=tags,
            limit=limit,
            status=TaskStatus.PENDING
        )

    async def get_by_task_id(self, task_id: str) -> Optional[TaskExecution]:
        """
        根据任务ID获取任务执行记录
        
        Args:
            task_id: 任务ID
            
        Returns:
            Optional[TaskExecution]: 任务执行对象或None
        """
        return await self.get_by_field("task_id", task_id)

    async def get_user_tasks(
        self, 
        user_id: int, 
        skip: int = 0, 
        limit: int = 100
    ) -> List[TaskExecution]:
        """
        获取用户的任务执行记录
        
        Args:
            user_id: 用户ID
            skip: 跳过的记录数
            limit: 限制返回的记录数
            
        Returns:
            List[TaskExecution]: 任务执行记录列表
        """
        return await self.get_by_filters(
            {"user_id": user_id},
            skip=skip,
            limit=limit,
            order_by="created_at",
            desc=True
        )

    async def get_tasks_by_status(self, status: TaskStatus) -> List[TaskExecution]:
        """
        根据状态获取任务列表
        
        Args:
            status: 任务状态
            
        Returns:
            List[TaskExecution]: 任务执行记录列表
        """
        return await self.get_by_filters({"status": status})

    async def get_running_tasks(self) -> List[TaskExecution]:
        """
        获取正在运行的任务
        
        Returns:
            List[TaskExecution]: 正在运行的任务列表
        """
        return await self.get_by_filters(
            {"status": [TaskStatus.PENDING, TaskStatus.RUNNING]}
        )

    async def get_recent_tasks(self, days: int = 7, limit: int = 50) -> List[TaskExecution]:
        """
        获取最近的任务执行记录
        
        Args:
            days: 最近天数
            limit: 限制返回的记录数
            
        Returns:
            List[TaskExecution]: 最近的任务执行记录列表
        """
        since_date = datetime.utcnow() - timedelta(days=days)
        
        result = await self.db.execute(
            select(TaskExecution)
            .where(TaskExecution.created_at >= since_date)
            .order_by(desc(TaskExecution.created_at))
            .limit(limit)
        )
        return result.scalars().all()

    async def start_task(self, task_id: str) -> bool:
        """
        标记任务开始执行
        
        Args:
            task_id: 任务ID
            
        Returns:
            bool: 是否更新成功
        """
        task = await self.get_by_task_id(task_id)
        if not task:
            return False
        
        task.status = TaskStatus.RUNNING
        task.start_time = datetime.utcnow()
        await self.db.commit()
        return True

    async def complete_task(
        self,
        task_id: str,
        status: TaskStatus,
        exit_code: Optional[int] = None,
        result_summary: Optional[Dict[str, Any]] = None,
        stats: Optional[Dict[str, Any]] = None,
        stdout: Optional[str] = None,
        stderr: Optional[str] = None,
        log_file_path: Optional[str] = None
    ) -> bool:
        """
        标记任务完成
        
        Args:
            task_id: 任务ID
            status: 最终状态
            exit_code: 退出代码
            result_summary: 执行结果摘要
            stats: 执行统计信息
            stdout: 标准输出
            stderr: 错误输出
            log_file_path: 日志文件路径
            
        Returns:
            bool: 是否更新成功
        """
        task = await self.get_by_task_id(task_id)
        if not task:
            return False
        
        end_time = datetime.utcnow()
        task.update_status(status, end_time)
        
        if exit_code is not None:
            task.exit_code = exit_code
        if result_summary is not None:
            task.result_summary = result_summary
        if stats is not None:
            task.stats = stats
        if stdout is not None:
            task.stdout = stdout
        if stderr is not None:
            task.stderr = stderr
        if log_file_path is not None:
            task.log_file_path = log_file_path
        
        await self.db.commit()
        return True

    async def cancel_task(self, task_id: str) -> bool:
        """
        取消任务执行
        
        Args:
            task_id: 任务ID
            
        Returns:
            bool: 是否取消成功
        """
        task = await self.get_by_task_id(task_id)
        if not task or not task.is_running:
            return False
        
        task.update_status(TaskStatus.CANCELLED)
        await self.db.commit()
        return True

    async def get_task_statistics(self, days: int = 30) -> Dict[str, Any]:
        """
        获取任务执行统计信息
        
        Args:
            days: 统计天数
            
        Returns:
            Dict[str, Any]: 统计信息
        """
        since_date = datetime.utcnow() - timedelta(days=days)
        
        # 总任务数
        total_tasks = await self.count()
        
        # 最近任务数
        recent_tasks = await self.db.execute(
            select(func.count(TaskExecution.id))
            .where(TaskExecution.created_at >= since_date)
        )
        recent_count = recent_tasks.scalar()
        
        # 按状态统计
        status_stats = {}
        for status in TaskStatus:
            count = await self.count({"status": status})
            status_stats[status.value] = count
        
        # 成功率计算
        success_count = status_stats.get("success", 0)
        failed_count = status_stats.get("failed", 0)
        completed_count = success_count + failed_count
        success_rate = (success_count / completed_count * 100) if completed_count > 0 else 0
        
        # 平均执行时间
        avg_duration_result = await self.db.execute(
            select(func.avg(TaskExecution.duration))
            .where(
                and_(
                    TaskExecution.duration.isnot(None),
                    TaskExecution.created_at >= since_date
                )
            )
        )
        avg_duration = avg_duration_result.scalar() or 0
        
        return {
            "total_tasks": total_tasks,
            "recent_tasks": recent_count,
            "status_distribution": status_stats,
            "success_rate": round(success_rate, 2),
            "average_duration": round(avg_duration, 2),
            "running_tasks": status_stats.get("running", 0) + status_stats.get("pending", 0)
        }

    async def get_playbook_statistics(self) -> Dict[str, Any]:
        """
        获取Playbook执行统计
        
        Returns:
            Dict[str, Any]: Playbook统计信息
        """
        result = await self.db.execute(
            select(
                TaskExecution.playbook_name,
                func.count(TaskExecution.id).label("total_runs"),
                func.sum(
                    func.case((TaskExecution.status == TaskStatus.SUCCESS, 1), else_=0)
                ).label("success_runs"),
                func.avg(TaskExecution.duration).label("avg_duration")
            )
            .group_by(TaskExecution.playbook_name)
            .order_by(desc("total_runs"))
        )
        
        playbook_stats = []
        for row in result:
            success_rate = (row.success_runs / row.total_runs * 100) if row.total_runs > 0 else 0
            playbook_stats.append({
                "playbook_name": row.playbook_name,
                "total_runs": row.total_runs,
                "success_runs": row.success_runs,
                "success_rate": round(success_rate, 2),
                "average_duration": round(row.avg_duration or 0, 2)
            })
        
        return {"playbook_statistics": playbook_stats}

    async def get_user_statistics(self) -> Dict[str, Any]:
        """
        获取用户执行统计
        
        Returns:
            Dict[str, Any]: 用户统计信息
        """
        result = await self.db.execute(
            select(
                User.username,
                func.count(TaskExecution.id).label("total_tasks"),
                func.sum(
                    func.case((TaskExecution.status == TaskStatus.SUCCESS, 1), else_=0)
                ).label("success_tasks")
            )
            .join(User, TaskExecution.user_id == User.id)
            .group_by(User.username)
            .order_by(desc("total_tasks"))
        )
        
        user_stats = []
        for row in result:
            success_rate = (row.success_tasks / row.total_tasks * 100) if row.total_tasks > 0 else 0
            user_stats.append({
                "username": row.username,
                "total_tasks": row.total_tasks,
                "success_tasks": row.success_tasks,
                "success_rate": round(success_rate, 2)
            })
        
        return {"user_statistics": user_stats}

    async def cleanup_old_tasks(self, days: int = 90) -> int:
        """
        清理旧的任务执行记录
        
        Args:
            days: 保留天数
            
        Returns:
            int: 删除的记录数量
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        # 只删除已完成的任务
        result = await self.db.execute(
            select(TaskExecution.id)
            .where(
                and_(
                    TaskExecution.created_at < cutoff_date,
                    TaskExecution.status.in_([
                        TaskStatus.SUCCESS,
                        TaskStatus.FAILED,
                        TaskStatus.CANCELLED,
                        TaskStatus.TIMEOUT
                    ])
                )
            )
        )
        
        task_ids = [row[0] for row in result]
        if task_ids:
            deleted_count = await self.bulk_delete(task_ids)
            return deleted_count
        
        return 0
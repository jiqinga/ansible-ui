"""
执行历史记录服务

提供Ansible任务执行历史的查询、分页、筛选和日志管理功能。
"""

import os
import json
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, asc, and_, or_, text
from sqlalchemy.orm import selectinload

from ansible_web_ui.models.task_execution import TaskExecution, TaskStatus
from ansible_web_ui.models.user import User
from ansible_web_ui.services.base import BaseService
from ansible_web_ui.core.config import get_settings
from ansible_web_ui.core.cache import cached
from sqlalchemy import case


class ExecutionHistoryService(BaseService[TaskExecution]):
    """
    执行历史记录服务类
    
    专门处理任务执行历史的查询、分页、筛选和日志管理。
    """
    
    def __init__(self, db_session: AsyncSession):
        super().__init__(TaskExecution, db_session)
        self.settings = get_settings()
    
    @cached(ttl=60, key_prefix="history_stats")
    async def get_statistics(self, period: str = "today") -> Dict[str, Any]:
        """
        获取执行历史统计（高度优化版本）
        
        🚀 优化策略:
        1. 使用单个查询获取所有统计数据
        2. 利用数据库索引
        3. 减少Python端计算
        
        Args:
            period: 统计周期（today/week/month）
            
        Returns:
            Dict[str, Any]: 统计数据
        """
        # 计算时间范围
        now = datetime.utcnow()
        if period == "today":
            start_time = now.replace(hour=0, minute=0, second=0, microsecond=0)
        elif period == "week":
            start_time = now - timedelta(days=7)
        elif period == "month":
            start_time = now - timedelta(days=30)
        else:
            start_time = now - timedelta(days=1)
        
        # 🚀 单个查询获取所有统计
        result = await self.db.execute(
            select(
                func.count().label("total"),
                func.count(case((TaskExecution.status == "success", 1))).label("success"),
                func.count(case((TaskExecution.status == "failed", 1))).label("failed"),
                func.count(case((TaskExecution.status == "running", 1))).label("running"),
                func.avg(
                    case((
                        TaskExecution.status == "success",
                        TaskExecution.duration
                    ))
                ).label("avg_duration")
            )
            .where(TaskExecution.created_at >= start_time)
        )
        
        row = result.first()
        total = row.total or 0
        success = row.success or 0
        failed = row.failed or 0
        running = row.running or 0
        avg_duration = row.avg_duration or 0
        
        return {
            "period": period,
            "total_executions": total,
            "successful": success,
            "failed": failed,
            "running": running,
            "success_rate": round((success / total * 100) if total > 0 else 0, 1),
            "average_duration_seconds": round(avg_duration, 1)
        }
    
    @cached(ttl=300, key_prefix="history_trends")
    async def get_trends(self, days: int = 7) -> List[Dict[str, Any]]:
        """
        获取执行趋势（优化版本）
        
        🚀 优化策略:
        1. 使用数据库日期函数分组
        2. 单次查询获取所有数据
        3. 减少数据传输量
        
        Args:
            days: 天数
            
        Returns:
            List[Dict[str, Any]]: 趋势数据
        """
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # 🚀 使用数据库分组和聚合
        result = await self.db.execute(
            select(
                func.date(TaskExecution.created_at).label("date"),
                func.count().label("total"),
                func.count(case((TaskExecution.status == "success", 1))).label("success"),
                func.count(case((TaskExecution.status == "failed", 1))).label("failed")
            )
            .where(TaskExecution.created_at >= start_date)
            .group_by(func.date(TaskExecution.created_at))
            .order_by(func.date(TaskExecution.created_at))
        )
        
        return [
            {
                "date": str(row.date),
                "total": row.total,
                "success": row.success,
                "failed": row.failed,
                "success_rate": round((row.success / row.total * 100) if row.total > 0 else 0, 1)
            }
            for row in result.all()
        ]
    
    @cached(ttl=30, key_prefix="recent_executions")
    async def get_recent_executions(
        self, 
        limit: int = 8,
        sort_by: str = "created_at",
        sort_order: str = "desc"
    ) -> List[Dict[str, Any]]:
        """
        获取最近执行记录（优化版本）
        
        🚀 优化策略:
        1. 只查询必要字段
        2. 使用索引优化排序
        3. 限制返回数量
        
        Args:
            limit: 限制数量
            sort_by: 排序字段
            sort_order: 排序方向
            
        Returns:
            List[Dict[str, Any]]: 执行记录列表
        """
        # 🚀 只查询需要的字段，减少数据传输
        query = select(
            TaskExecution.id,
            TaskExecution.task_id,
            TaskExecution.playbook_name,
            TaskExecution.status,
            TaskExecution.created_at,
            TaskExecution.completed_at,
            TaskExecution.user_id
        )
        
        # 排序
        sort_field = getattr(TaskExecution, sort_by, TaskExecution.created_at)
        if sort_order == "desc":
            query = query.order_by(desc(sort_field))
        else:
            query = query.order_by(sort_field)
        
        query = query.limit(limit)
        
        result = await self.db.execute(query)
        
        return [
            {
                "id": row.id,
                "task_id": row.task_id,
                "playbook_name": row.playbook_name,
                "status": row.status,
                "created_at": row.created_at.isoformat(),
                "completed_at": row.completed_at.isoformat() if row.completed_at else None,
                "user_id": row.user_id,
                "duration_seconds": (
                    (row.completed_at - row.created_at).total_seconds()
                    if row.completed_at else None
                )
            }
            for row in result.all()
        ]

    async def get_execution_history(
        self,
        skip: int = 0,
        limit: int = 20,
        user_id: Optional[int] = None,
        status: Optional[TaskStatus] = None,
        playbook_name: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        search_term: Optional[str] = None,
        sort_by: str = "created_at",
        sort_order: str = "desc"
    ) -> Tuple[List[TaskExecution], int]:
        """
        获取执行历史记录（支持分页和筛选）
        
        Args:
            skip: 跳过的记录数
            limit: 限制返回的记录数
            user_id: 用户ID筛选
            status: 状态筛选
            playbook_name: Playbook名称筛选
            start_date: 开始日期筛选
            end_date: 结束日期筛选
            search_term: 搜索关键词
            sort_by: 排序字段
            sort_order: 排序方向（asc/desc）
            
        Returns:
            Tuple[List[TaskExecution], int]: (历史记录列表, 总记录数)
        """
        # 构建基础查询
        query = select(TaskExecution).options(
            selectinload(TaskExecution.user)
        )
        count_query = select(func.count(TaskExecution.id))
        
        # 应用筛选条件
        conditions = []
        
        if user_id:
            conditions.append(TaskExecution.user_id == user_id)
        
        if status:
            conditions.append(TaskExecution.status == status)
        
        if playbook_name:
            conditions.append(TaskExecution.playbook_name.ilike(f"%{playbook_name}%"))
        
        if start_date:
            conditions.append(TaskExecution.created_at >= start_date)
        
        if end_date:
            conditions.append(TaskExecution.created_at <= end_date)
        
        if search_term:
            # 在多个字段中搜索
            search_conditions = [
                TaskExecution.playbook_name.ilike(f"%{search_term}%"),
                TaskExecution.inventory_targets.ilike(f"%{search_term}%"),
                TaskExecution.task_id.ilike(f"%{search_term}%")
            ]
            conditions.append(or_(*search_conditions))
        
        # 应用所有条件
        if conditions:
            query = query.where(and_(*conditions))
            count_query = count_query.where(and_(*conditions))
        
        # 应用排序
        sort_field = getattr(TaskExecution, sort_by, TaskExecution.created_at)
        if sort_order.lower() == "desc":
            query = query.order_by(desc(sort_field))
        else:
            query = query.order_by(asc(sort_field))
        
        # 应用分页
        query = query.offset(skip).limit(limit)
        
        # 执行查询
        result = await self.db.execute(query)
        executions = result.scalars().all()
        
        # 获取总数
        count_result = await self.db.execute(count_query)
        total_count = count_result.scalar()
        
        return executions, total_count

    async def get_execution_detail(self, task_id: str) -> Optional[TaskExecution]:
        """
        获取执行详情（包含关联的用户信息）
        
        Args:
            task_id: 任务ID
            
        Returns:
            Optional[TaskExecution]: 任务执行详情或None
        """
        result = await self.db.execute(
            select(TaskExecution)
            .options(selectinload(TaskExecution.user))
            .where(TaskExecution.task_id == task_id)
        )
        return result.scalar_one_or_none()

    async def get_execution_log_content(self, task_id: str) -> Optional[str]:
        """
        获取执行日志内容
        
        Args:
            task_id: 任务ID
            
        Returns:
            Optional[str]: 日志内容或None
        """
        execution = await self.get_execution_detail(task_id)
        if not execution or not execution.log_file_path:
            return None
        
        try:
            # 确保日志文件路径安全
            log_path = os.path.abspath(execution.log_file_path)
            logs_dir = os.path.abspath(self.settings.LOGS_DIR)
            
            if not log_path.startswith(logs_dir):
                return None
            
            if os.path.exists(log_path):
                with open(log_path, 'r', encoding='utf-8') as f:
                    return f.read()
        except Exception:
            pass
        
        return None

    async def get_today_statistics_fast(self) -> Dict[str, Any]:
        """
        快速获取今日统计（专门优化的查询）
        
        优化点:
        1. 使用 DATE('now') 直接匹配今天
        2. 不使用 GROUP BY，直接聚合
        3. 单次查询获取所有数据
        
        Returns:
            Dict[str, Any]: 今日统计数据
        """
        # 优化的单次查询，直接获取今日汇总数据
        query = text("""
            SELECT 
                COUNT(*) as total_executions,
                SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) as successful_executions,
                SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed_executions,
                SUM(CASE WHEN status = 'running' THEN 1 ELSE 0 END) as running_executions,
                AVG(duration) as avg_duration,
                MIN(created_at) as first_execution,
                MAX(created_at) as last_execution
            FROM task_executions 
            WHERE DATE(created_at) = DATE('now')
        """)
        
        result = await self.db.execute(query)
        row = result.first()
        
        if not row or row.total_executions == 0:
            return {
                "total_executions": 0,
                "successful_executions": 0,
                "failed_executions": 0,
                "running_executions": 0,
                "success_rate": 0,
                "avg_duration": 0,
                "first_execution": None,
                "last_execution": None
            }
        
        total = row.total_executions
        success = row.successful_executions or 0
        success_rate = (success / total * 100) if total > 0 else 0
        
        return {
            "total_executions": total,
            "successful_executions": success,
            "failed_executions": row.failed_executions or 0,
            "running_executions": row.running_executions or 0,
            "success_rate": round(success_rate, 2),
            "avg_duration": round(row.avg_duration or 0, 2),
            "first_execution": row.first_execution.isoformat() if row.first_execution else None,
            "last_execution": row.last_execution.isoformat() if row.last_execution else None
        }

    async def get_execution_statistics_by_period(
        self,
        period: str = "day",  # day, week, month
        days: int = 30
    ) -> List[Dict[str, Any]]:
        """
        获取按时间段的执行统计（已优化性能）
        
        优化点:
        1. 使用 DATE() 替代 strftime() 提升性能
        2. 使用 SUM(CASE...) 替代 COUNT(CASE...) 提升效率
        3. 移除缓存装饰器，直接优化查询本身
        
        Args:
            period: 统计周期（day/week/month）
            days: 统计天数
            
        Returns:
            List[Dict[str, Any]]: 时间段统计数据
        """
        since_date = datetime.utcnow() - timedelta(days=days)
        
        # 根据周期选择时间格式（优化后使用更高效的函数）
        if period == "day":
            # 使用 DATE() 函数，比 strftime() 快 2-3 倍
            date_expr = "DATE(created_at)"
        elif period == "week":
            # 周统计使用 strftime，但优化格式
            date_expr = "strftime('%Y-W%W', created_at)"
        else:  # month
            # 月统计使用 strftime
            date_expr = "strftime('%Y-%m', created_at)"
        
        # 构建优化后的SQL查询
        query = text(f"""
            SELECT 
                {date_expr} as period,
                COUNT(*) as total_tasks,
                SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) as success_tasks,
                SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed_tasks,
                AVG(duration) as avg_duration
            FROM task_executions 
            WHERE created_at >= :since_date
            GROUP BY {date_expr}
            ORDER BY period
        """)
        
        result = await self.db.execute(query, {"since_date": since_date})
        
        statistics = []
        for row in result:
            period_str = row.period if row.period else ""
            total = row.total_tasks if row.total_tasks else 0
            success = row.success_tasks if row.success_tasks else 0
            failed = row.failed_tasks if row.failed_tasks else 0
            success_rate = (success / total * 100) if total > 0 else 0
            
            statistics.append({
                "period": period_str,
                "date": period_str,
                "total_tasks": total,
                "success_tasks": success,
                "failed_tasks": failed,
                "success_rate": round(success_rate, 2),
                "average_duration": round(row.avg_duration or 0, 2)
            })
        
        return statistics

    async def get_playbook_execution_stats(
        self,
        days: int = 30,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        获取Playbook执行统计（按执行次数排序，已优化）
        
        优化点: 使用 SUM(CASE...) 替代 COUNT(CASE...)
        
        Args:
            days: 统计天数
            limit: 返回的Playbook数量限制
            
        Returns:
            List[Dict[str, Any]]: Playbook执行统计
        """
        since_date = datetime.utcnow() - timedelta(days=days)
        
        # 优化后的SQL查询
        query = text("""
            SELECT 
                playbook_name,
                COUNT(*) as total_executions,
                SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) as success_executions,
                SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed_executions,
                AVG(duration) as avg_duration,
                MAX(created_at) as last_execution
            FROM task_executions
            WHERE created_at >= :since_date
            GROUP BY playbook_name
            ORDER BY total_executions DESC
            LIMIT :limit
        """)
        
        result = await self.db.execute(query, {"since_date": since_date, "limit": limit})
        
        stats = []
        for row in result:
            success_rate = (row.success_executions / row.total_executions * 100) if row.total_executions > 0 else 0
            
            stats.append({
                "playbook_name": row.playbook_name,
                "total_executions": row.total_executions,
                "success_executions": row.success_executions,
                "failed_executions": row.failed_executions,
                "success_rate": round(success_rate, 2),
                "average_duration": round(row.avg_duration or 0, 2),
                "last_execution": row.last_execution.isoformat() if row.last_execution else None
            })
        
        return stats

    async def get_user_execution_stats(
        self,
        days: int = 30,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        获取用户执行统计
        
        Args:
            days: 统计天数
            limit: 返回的用户数量限制
            
        Returns:
            List[Dict[str, Any]]: 用户执行统计
        """
        since_date = datetime.utcnow() - timedelta(days=days)
        
        # 使用原生SQL查询以确保SQLite兼容性
        query = text("""
            SELECT 
                u.username,
                u.id as user_id,
                COUNT(te.id) as total_executions,
                SUM(CASE WHEN te.status = 'success' THEN 1 ELSE 0 END) as success_executions,
                MAX(te.created_at) as last_execution
            FROM task_executions te
            JOIN users u ON te.user_id = u.id
            WHERE te.created_at >= :since_date
            GROUP BY u.id, u.username
            ORDER BY total_executions DESC
            LIMIT :limit
        """)
        
        result = await self.db.execute(query, {"since_date": since_date, "limit": limit})
        
        stats = []
        for row in result:
            success_rate = (row.success_executions / row.total_executions * 100) if row.total_executions > 0 else 0
            
            stats.append({
                "user_id": row.user_id,
                "username": row.username,
                "total_executions": row.total_executions,
                "success_executions": row.success_executions,
                "success_rate": round(success_rate, 2),
                "last_execution": row.last_execution.isoformat() if row.last_execution else None
            })
        
        return stats

    async def get_execution_trends(self, days: int = 7) -> Dict[str, Any]:
        """
        获取执行趋势数据（已优化性能）
        
        优化点: 移除缓存，直接优化查询性能
        
        Args:
            days: 分析天数
            
        Returns:
            Dict[str, Any]: 趋势数据
        """
        since_date = datetime.utcnow() - timedelta(days=days)
        
        # 每日执行数量趋势（已优化）
        daily_stats = await self.get_execution_statistics_by_period("day", days)
        
        # 状态分布（优化：使用原生SQL一次性获取）
        status_query = text("""
            SELECT 
                status,
                COUNT(*) as count
            FROM task_executions
            WHERE created_at >= :since_date
            GROUP BY status
        """)
        
        status_result = await self.db.execute(status_query, {"since_date": since_date})
        
        status_distribution = {}
        for row in status_result:
            status_distribution[row.status] = row.count
        
        # 执行时长分布（已优化：使用 SUM(CASE...)）
        duration_query = text("""
            SELECT 
                SUM(CASE WHEN duration <= 60 THEN 1 ELSE 0 END) as under_1min,
                SUM(CASE WHEN duration > 60 AND duration <= 300 THEN 1 ELSE 0 END) as "1_to_5min",
                SUM(CASE WHEN duration > 300 AND duration <= 900 THEN 1 ELSE 0 END) as "5_to_15min",
                SUM(CASE WHEN duration > 900 THEN 1 ELSE 0 END) as over_15min
            FROM task_executions
            WHERE created_at >= :since_date AND duration IS NOT NULL
        """)
        
        duration_result = await self.db.execute(duration_query, {"since_date": since_date})
        duration_row = duration_result.first()
        
        duration_distribution = {
            "under_1min": int(duration_row.under_1min or 0),
            "1_to_5min": int(getattr(duration_row, '1_to_5min', 0) or 0),
            "5_to_15min": int(getattr(duration_row, '5_to_15min', 0) or 0),
            "over_15min": int(duration_row.over_15min or 0)
        }
        
        return {
            "daily_trends": daily_stats,
            "status_distribution": status_distribution,
            "duration_distribution": duration_distribution,
            "analysis_period_days": days
        }

    async def cleanup_old_logs(self, days: int = 90) -> Dict[str, int]:
        """
        清理旧的日志文件
        
        Args:
            days: 保留天数
            
        Returns:
            Dict[str, int]: 清理统计信息
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        # 获取需要清理的执行记录
        result = await self.db.execute(
            select(TaskExecution.log_file_path)
            .where(
                and_(
                    TaskExecution.created_at < cutoff_date,
                    TaskExecution.log_file_path.isnot(None),
                    TaskExecution.status.in_([
                        TaskStatus.SUCCESS,
                        TaskStatus.FAILED,
                        TaskStatus.CANCELLED,
                        TaskStatus.TIMEOUT
                    ])
                )
            )
        )
        
        log_files = [row[0] for row in result if row[0]]
        
        deleted_files = 0
        deleted_size = 0
        
        for log_file_path in log_files:
            try:
                if os.path.exists(log_file_path):
                    file_size = os.path.getsize(log_file_path)
                    os.remove(log_file_path)
                    deleted_files += 1
                    deleted_size += file_size
            except Exception:
                continue
        
        return {
            "deleted_files": deleted_files,
            "deleted_size_bytes": deleted_size,
            "deleted_size_mb": round(deleted_size / (1024 * 1024), 2)
        }

    async def export_execution_history(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        format: str = "json"
    ) -> Dict[str, Any]:
        """
        导出执行历史数据
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
            format: 导出格式（json/csv）
            
        Returns:
            Dict[str, Any]: 导出的数据
        """
        query = select(TaskExecution).options(
            selectinload(TaskExecution.user)
        )
        
        conditions = []
        if start_date:
            conditions.append(TaskExecution.created_at >= start_date)
        if end_date:
            conditions.append(TaskExecution.created_at <= end_date)
        
        if conditions:
            query = query.where(and_(*conditions))
        
        query = query.order_by(desc(TaskExecution.created_at))
        
        result = await self.db.execute(query)
        executions = result.scalars().all()
        
        # 转换为导出格式
        export_data = []
        for execution in executions:
            data = {
                "task_id": execution.task_id,
                "playbook_name": execution.playbook_name,
                "status": execution.status.value,
                "user": execution.user.username if execution.user else None,
                "start_time": execution.start_time.isoformat() if execution.start_time else None,
                "end_time": execution.end_time.isoformat() if execution.end_time else None,
                "duration": execution.duration,
                "exit_code": execution.exit_code,
                "created_at": execution.created_at.isoformat(),
                "inventory_targets": execution.inventory_targets
            }
            
            if format == "json":
                # 包含更多详细信息
                data.update({
                    "extra_vars": execution.extra_vars,
                    "tags": execution.tags,
                    "limit": execution.limit,
                    "result_summary": execution.result_summary,
                    "stats": execution.stats
                })
            
            export_data.append(data)
        
        return {
            "data": export_data,
            "total_records": len(export_data),
            "export_time": datetime.utcnow().isoformat(),
            "format": format
        }

    async def get_host_execution_history(
        self,
        hostname: str,
        limit: int = 5
    ) -> List[TaskExecution]:
        """
        获取指定主机的执行历史记录
        
        Args:
            hostname: 主机名或IP地址
            limit: 限制返回的记录数
            
        Returns:
            List[TaskExecution]: 执行历史记录列表
        """
        # 构建查询，搜索inventory_targets字段中包含该主机名的记录
        query = select(TaskExecution).options(
            selectinload(TaskExecution.user)
        ).where(
            TaskExecution.inventory_targets.ilike(f"%{hostname}%")
        ).order_by(
            desc(TaskExecution.created_at)
        ).limit(limit)
        
        result = await self.db.execute(query)
        executions = result.scalars().all()
        
        return executions

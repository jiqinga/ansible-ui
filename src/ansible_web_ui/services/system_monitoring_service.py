"""
系统监控服务

提供系统资源监控、性能统计和警告功能。
"""

import os
import psutil
import asyncio
from datetime import datetime, timedelta

from ansible_web_ui.utils.timezone import now
from typing import Dict, Any, List, Optional
from concurrent.futures import ThreadPoolExecutor
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, and_, case

from ansible_web_ui.models.task_execution import TaskExecution, TaskStatus
from ansible_web_ui.models.system_config import SystemConfig
from ansible_web_ui.services.base import BaseService
from ansible_web_ui.core.config import get_settings
from ansible_web_ui.core.cache import cached

# 🚀 创建线程池用于 CPU 密集型操作，避免阻塞事件循环
_thread_pool = ThreadPoolExecutor(max_workers=2)


class SystemMonitoringService:
    """
    系统监控服务类
    
    提供系统资源监控、性能分析和警告功能。
    """
    
    def __init__(self, db_session: AsyncSession):
        self.db = db_session
        self.settings = get_settings()
    
    @cached(ttl=10, key_prefix="status_summary")
    async def get_status_summary(self) -> Dict[str, Any]:
        """
        获取系统状态摘要（高度优化版本）
        
        🚀 优化策略:
        1. 并行获取所有数据
        2. 使用更短的缓存时间（10秒）
        3. 简化查询逻辑，只返回必要信息
        
        Returns:
            Dict[str, Any]: 系统状态摘要
        """
        try:
            # 🚀 并行执行所有查询
            results = await asyncio.gather(
                self._get_quick_system_status(),
                self._get_quick_task_stats(),
                return_exceptions=True
            )
            
            system_status = results[0] if not isinstance(results[0], Exception) else {}
            task_stats = results[1] if not isinstance(results[1], Exception) else {}
            
            return {
                "timestamp": datetime.utcnow().isoformat(),
                "system": system_status,
                "tasks": task_stats
            }
        except Exception:
            return {
                "timestamp": datetime.utcnow().isoformat(),
                "system": {},
                "tasks": {}
            }
    
    async def _get_quick_system_status(self) -> Dict[str, Any]:
        """快速获取系统状态（非阻塞）"""
        try:
            loop = asyncio.get_event_loop()
            
            # 🚀 在线程池中执行 psutil 调用
            cpu_percent = await loop.run_in_executor(_thread_pool, psutil.cpu_percent, 0)
            memory = await loop.run_in_executor(_thread_pool, psutil.virtual_memory)
            
            return {
                "cpu_usage": round(cpu_percent, 1),
                "memory_usage": round(memory.percent, 1),
                "status": "healthy" if cpu_percent < 80 and memory.percent < 90 else "warning"
            }
        except Exception:
            return {"cpu_usage": 0, "memory_usage": 0, "status": "unknown"}
    
    async def _get_quick_task_stats(self) -> Dict[str, Any]:
        """快速获取任务统计（优化查询）"""
        try:
            since_24h = datetime.utcnow() - timedelta(hours=24)
            
            # 🚀 使用单个查询获取所有统计
            result = await self.db.execute(
                select(
                    func.count().label("total"),
                    func.count(case((TaskExecution.status == TaskStatus.RUNNING, 1))).label("running"),
                    func.count(case((TaskExecution.status == TaskStatus.SUCCESS, 1))).label("success"),
                    func.count(case((TaskExecution.status == TaskStatus.FAILED, 1))).label("failed")
                ).where(
                    TaskExecution.created_at >= since_24h
                )
            )
            
            row = result.first()
            total = row.total or 0
            success = row.success or 0
            
            return {
                "total_24h": total,
                "running": row.running or 0,
                "success_rate": round((success / total * 100) if total > 0 else 0, 1)
            }
        except Exception:
            return {"total_24h": 0, "running": 0, "success_rate": 0}

    @cached(ttl=20, key_prefix="system_resources")
    async def get_system_resources(self) -> Dict[str, Any]:
        """
        获取当前系统资源使用情况（缓存20秒，快速响应）
        
        🚀 优化点:
        1. 使用线程池执行 psutil 调用，避免阻塞事件循环
        2. 并行获取所有系统信息
        3. 减少数据精度，降低计算开销
        4. 异常处理返回默认值
        5. 获取所有磁盘分区信息（包括文件系统类型）
        
        Returns:
            Dict[str, Any]: 系统资源信息
        """
        try:
            loop = asyncio.get_event_loop()
            
            # 🚀 并行获取所有系统信息，使用线程池避免阻塞
            cpu_task = loop.run_in_executor(_thread_pool, psutil.cpu_percent, 0.1)
            memory_task = loop.run_in_executor(_thread_pool, psutil.virtual_memory)
            disk_task = loop.run_in_executor(_thread_pool, psutil.disk_usage, '/')
            network_task = loop.run_in_executor(_thread_pool, psutil.net_io_counters)
            disk_partitions_task = loop.run_in_executor(_thread_pool, psutil.disk_partitions)
            network_interfaces_task = loop.run_in_executor(_thread_pool, psutil.net_io_counters, True)  # pernic=True
            network_if_addrs_task = loop.run_in_executor(_thread_pool, psutil.net_if_addrs)
            network_if_stats_task = loop.run_in_executor(_thread_pool, psutil.net_if_stats)
            
            cpu_percent, memory, disk_usage, network, disk_partitions, network_interfaces, network_addrs, network_stats = await asyncio.gather(
                cpu_task, memory_task, disk_task, network_task, disk_partitions_task,
                network_interfaces_task, network_if_addrs_task, network_if_stats_task
            )
            
            cpu_count = psutil.cpu_count()
            
            # 系统启动时间（快速获取）
            boot_time = datetime.fromtimestamp(psutil.boot_time())
            uptime = now() - boot_time
            
            # 🔍 获取所有磁盘分区的详细信息
            # 只显示有实际挂载点的分区，过滤掉虚拟文件系统和SWAP分区
            excluded_fstypes = {
                'tmpfs', 'devtmpfs', 'devfs', 'proc', 'sysfs', 
                'cgroup', 'cgroup2', 'overlay', 'squashfs',
                'iso9660', 'udf', 'autofs', 'debugfs', 'tracefs',
                'securityfs', 'pstore', 'binfmt_misc', 'configfs',
                'fusectl', 'mqueue', 'hugetlbfs', 'ramfs',
                'swap'  # 🎯 排除 SWAP 分区
            }
            
            disk_partitions_info = []
            for partition in disk_partitions:
                # 🎯 过滤虚拟文件系统
                if partition.fstype.lower() in excluded_fstypes:
                    continue
                
                # 🎯 必须有挂载点（排除未挂载的分区）
                if not partition.mountpoint or partition.mountpoint.strip() == '':
                    continue
                    
                # 🎯 过滤特殊挂载点（Linux）
                if partition.mountpoint.startswith(('/sys', '/proc', '/dev', '/run', '/snap')):
                    continue
                
                # 🎯 过滤 SWAP 挂载点（通常显示为 [SWAP]）
                if '[SWAP]' in partition.mountpoint.upper():
                    continue
                
                try:
                    usage = await loop.run_in_executor(_thread_pool, psutil.disk_usage, partition.mountpoint)
                    disk_partitions_info.append({
                        "device": partition.device,
                        "mountpoint": partition.mountpoint,
                        "fstype": partition.fstype,  # 文件系统类型
                        "opts": partition.opts,
                        "total_gb": round(usage.total / (1024**3), 2),
                        "used_gb": round(usage.used / (1024**3), 2),
                        "free_gb": round(usage.free / (1024**3), 2),
                        "usage_percent": round(usage.percent, 1)
                    })
                except (PermissionError, OSError):
                    # 跳过无法访问的分区
                    continue
            
            # 🌐 获取所有网络接口的详细信息
            # 过滤掉虚拟网络接口，只保留真实的物理网络接口
            excluded_interface_prefixes = (
                'lo', 'docker', 'br-', 'veth', 'virbr', 'vmnet', 'vboxnet',
                'tun', 'tap', 'zt', 'wg', 'utun', 'awdl', 'llw', 'bridge'
            )
            
            # 包含这些关键词的接口名也要过滤
            excluded_interface_keywords = (
                'vmware', 'virtualbox', 'zerotier', 'tailscale', 'hamachi',
                'virtual', 'loopback', 'tunnel', 'vpn'
            )
            
            network_interfaces_info = []
            for iface_name, iface_stats in network_interfaces.items():
                iface_name_lower = iface_name.lower()
                
                # 🎯 过滤虚拟网络接口（前缀匹配）
                if iface_name_lower.startswith(excluded_interface_prefixes):
                    continue
                
                # 🎯 过滤虚拟网络接口（关键词匹配）
                if any(keyword in iface_name_lower for keyword in excluded_interface_keywords):
                    continue
                
                # 获取接口状态
                stats = network_stats.get(iface_name)
                if not stats:
                    continue
                
                # 获取IP地址
                addrs = network_addrs.get(iface_name, [])
                ipv4_addr = None
                ipv6_addr = None
                mac_addr = None
                
                for addr in addrs:
                    if addr.family == 2:  # AF_INET (IPv4)
                        ipv4_addr = addr.address
                    elif addr.family == 23 or addr.family == 10:  # AF_INET6 (IPv6) - Windows=23, Linux=10
                        ipv6_addr = addr.address
                    elif addr.family == -1 or addr.family == 17:  # AF_LINK (MAC) - Windows=-1, Linux=17
                        mac_addr = addr.address
                
                network_interfaces_info.append({
                    "name": iface_name,
                    "status": "up" if stats.isup else "down",
                    "speed_mbps": stats.speed if stats.speed > 0 else None,
                    "mtu": stats.mtu,
                    "ipv4": ipv4_addr,
                    "ipv6": ipv6_addr,
                    "mac": mac_addr,
                    "bytes_sent": iface_stats.bytes_sent,
                    "bytes_recv": iface_stats.bytes_recv,
                    "packets_sent": iface_stats.packets_sent,
                    "packets_recv": iface_stats.packets_recv,
                    "errors_in": iface_stats.errin,
                    "errors_out": iface_stats.errout,
                    "drops_in": iface_stats.dropin,
                    "drops_out": iface_stats.dropout
                })
            
            # 🚀 降低精度，减少计算开销
            return {
                "timestamp": datetime.utcnow().isoformat(),
                "cpu": {
                    "usage_percent": round(cpu_percent, 1),
                    "count": cpu_count,
                    "frequency_mhz": None,  # 移除不必要的信息
                    "load_average": None
                },
                "memory": {
                    "total_gb": round(memory.total / (1024**3), 1),
                    "available_gb": round(memory.available / (1024**3), 1),
                    "used_gb": round(memory.used / (1024**3), 1),
                    "usage_percent": round(memory.percent, 1),
                    "swap_total_gb": round(memory.swap_memory().total / (1024**3), 1) if hasattr(memory, 'swap_memory') else 0,
                    "swap_used_gb": round(memory.swap_memory().used / (1024**3), 1) if hasattr(memory, 'swap_memory') else 0,
                    "swap_percent": round(memory.swap_memory().percent, 1) if hasattr(memory, 'swap_memory') else 0
                },
                "disk": {
                    "total_gb": round(disk_usage.total / (1024**3), 1),
                    "used_gb": round(disk_usage.used / (1024**3), 1),
                    "free_gb": round(disk_usage.free / (1024**3), 1),
                    "usage_percent": round(disk_usage.percent, 1)
                },
                "disk_partitions": disk_partitions_info,  # 🆕 所有磁盘分区信息
                "network": {
                    "bytes_sent": network.bytes_sent,
                    "bytes_recv": network.bytes_recv,
                    "packets_sent": network.packets_sent,
                    "packets_recv": network.packets_recv
                },
                "network_interfaces": network_interfaces_info,  # 🆕 所有网络接口信息
                "system": {
                    "boot_time": boot_time.isoformat(),
                    "uptime_seconds": int(uptime.total_seconds()),
                    "uptime_days": round(uptime.total_seconds() / 86400, 1)
                }
            }
        except Exception as e:
            # 返回符合schema的默认数据结构
            return {
                "timestamp": datetime.utcnow().isoformat(),
                "cpu": {
                    "usage_percent": 0.0,
                    "count": 1,
                    "frequency_mhz": None,
                    "load_average": None
                },
                "memory": {
                    "total_gb": 0.0,
                    "available_gb": 0.0,
                    "used_gb": 0.0,
                    "usage_percent": 0.0,
                    "swap_total_gb": 0.0,
                    "swap_used_gb": 0.0,
                    "swap_percent": 0.0
                },
                "disk": {
                    "total_gb": 0.0,
                    "used_gb": 0.0,
                    "free_gb": 0.0,
                    "usage_percent": 0.0
                },
                "disk_partitions": [],  # 🆕 空的磁盘分区列表
                "network": {
                    "bytes_sent": 0,
                    "bytes_recv": 0,
                    "packets_sent": 0,
                    "packets_recv": 0
                },
                "network_interfaces": [],  # 🆕 空的网络接口列表
                "system": {
                    "boot_time": datetime.utcnow().isoformat(),
                    "uptime_seconds": 0,
                    "uptime_days": 0.0
                }
            }

    @cached(ttl=60, key_prefix="app_metrics")
    async def get_application_metrics(self) -> Dict[str, Any]:
        """
        获取应用程序相关的监控指标（缓存60秒，优化响应速度）
        
        优化点:
        1. 合并数据库查询，减少查询次数
        2. 限制日志文件遍历数量
        3. 使用缓存避免重复计算
        
        Returns:
            Dict[str, Any]: 应用程序指标
        """
        try:
            # 获取当前进程信息
            current_process = psutil.Process()
            
            # 数据库连接池状态（如果可用）
            db_pool_info = {}
            try:
                if hasattr(self.db.bind, 'pool'):
                    pool = self.db.bind.pool
                    db_pool_info = {
                        "size": pool.size(),
                        "checked_in": pool.checkedin(),
                        "checked_out": pool.checkedout(),
                        "overflow": pool.overflow(),
                        "invalid": pool.invalid()
                    }
            except Exception:
                pass
            
            # 任务执行统计
            task_stats = await self._get_task_execution_metrics()
            
            # 日志文件大小统计
            log_stats = await self._get_log_file_metrics()
            
            return {
                "timestamp": datetime.utcnow().isoformat(),
                "process": {
                    "pid": current_process.pid,
                    "memory_mb": round(current_process.memory_info().rss / (1024**2), 2),
                    "cpu_percent": round(current_process.cpu_percent(), 2),
                    "threads": current_process.num_threads(),
                    "open_files": len(current_process.open_files()),
                    "connections": len(current_process.connections()),
                    "create_time": datetime.fromtimestamp(current_process.create_time()).isoformat()
                },
                "database": {
                    "pool": db_pool_info,
                    "connection_active": True  # 简单的连接检查
                },
                "tasks": task_stats,
                "logs": log_stats
            }
        except Exception as e:
            # 返回符合schema的默认数据结构
            return {
                "timestamp": datetime.utcnow().isoformat(),
                "process": {
                    "pid": 0,
                    "memory_mb": 0.0,
                    "cpu_percent": 0.0,
                    "threads": 0,
                    "open_files": 0,
                    "connections": 0,
                    "create_time": datetime.utcnow().isoformat()
                },
                "database": {
                    "pool": {},
                    "connection_active": False
                },
                "tasks": {
                    "total_tasks": 0,
                    "recent_24h_tasks": 0,
                    "running_tasks": 0,
                    "success_rate_24h": 0.0,
                    "average_duration_24h": 0.0
                },
                "logs": {
                    "total_files": 0,
                    "total_size_mb": 0.0
                }
            }

    async def _get_task_execution_metrics(self) -> Dict[str, Any]:
        """
        获取任务执行相关指标（优化：合并为单次查询）
        
        Returns:
            Dict[str, Any]: 任务执行指标
        """
        try:
            # 最近24小时的任务统计
            since_24h = datetime.utcnow() - timedelta(hours=24)
            
            # 🚀 优化：合并所有统计查询为一次查询
            from sqlalchemy import case
            
            stats_result = await self.db.execute(
                select(
                    func.count(TaskExecution.id).label("total_count"),
                    func.count(case((TaskExecution.created_at >= since_24h, 1))).label("recent_count"),
                    func.count(case((TaskExecution.status.in_([TaskStatus.PENDING, TaskStatus.RUNNING]), 1))).label("running_count"),
                    func.count(case((
                        and_(
                            TaskExecution.created_at >= since_24h,
                            TaskExecution.status == TaskStatus.SUCCESS
                        ), 1
                    ))).label("success_count"),
                    func.avg(case((
                        and_(
                            TaskExecution.created_at >= since_24h,
                            TaskExecution.duration.isnot(None)
                        ), TaskExecution.duration
                    ))).label("avg_duration")
                )
            )
            
            stats = stats_result.first()
            total_count = stats.total_count or 0
            recent_count = stats.recent_count or 0
            running_count = stats.running_count or 0
            success_count = stats.success_count or 0
            avg_duration_value = stats.avg_duration or 0
            
            success_rate = (success_count / recent_count * 100) if recent_count > 0 else 0
            
            return {
                "total_tasks": total_count,
                "recent_24h_tasks": recent_count,
                "running_tasks": running_count,
                "success_rate_24h": round(success_rate, 2),
                "average_duration_24h": round(avg_duration_value, 2)
            }
        except Exception:
            return {
                "total_tasks": 0,
                "recent_24h_tasks": 0,
                "running_tasks": 0,
                "success_rate_24h": 0,
                "average_duration_24h": 0
            }

    @cached(ttl=300, key_prefix="log_metrics")
    async def _get_log_file_metrics(self) -> Dict[str, Any]:
        """
        获取日志文件相关指标（缓存5分钟，避免频繁IO）
        
        Returns:
            Dict[str, Any]: 日志文件指标
        """
        try:
            logs_dir = self.settings.LOGS_DIR
            if not os.path.exists(logs_dir):
                return {"total_files": 0, "total_size_mb": 0}
            
            total_files = 0
            total_size = 0
            
            # 🚀 优化：限制遍历深度和文件数量，避免阻塞
            max_files = 1000  # 最多统计1000个文件
            
            for root, dirs, files in os.walk(logs_dir):
                for file in files:
                    if total_files >= max_files:
                        break
                    if file.endswith('.log'):
                        file_path = os.path.join(root, file)
                        try:
                            total_size += os.path.getsize(file_path)
                            total_files += 1
                        except OSError:
                            continue
                if total_files >= max_files:
                    break
            
            return {
                "total_files": total_files,
                "total_size_mb": round(total_size / (1024**2), 2)
            }
        except Exception:
            return {"total_files": 0, "total_size_mb": 0}

    @cached(ttl=60, key_prefix="system_health")
    async def check_system_health(self) -> Dict[str, Any]:
        """
        检查系统健康状态并生成警告（缓存60秒，快速响应）
        
        优化点:
        1. 复用已缓存的资源和指标数据
        2. 减少重复计算
        3. 快速返回健康状态
        
        Returns:
            Dict[str, Any]: 健康检查结果和警告
        """
        health_status = {
            "overall_status": "healthy",
            "warnings": [],
            "errors": [],
            "timestamp": datetime.utcnow().isoformat()
        }
        
        try:
            # 获取系统资源
            resources = await self.get_system_resources()
            app_metrics = await self.get_application_metrics()
            
            # 当前时间戳
            current_time = datetime.utcnow().isoformat()
            
            # 检查CPU使用率
            cpu_usage = resources.get("cpu", {}).get("usage_percent", 0)
            if cpu_usage > 90:
                health_status["errors"].append({
                    "type": "high_cpu_usage",
                    "message": f"CPU使用率过高: {cpu_usage}%",
                    "severity": "error",
                    "value": cpu_usage,
                    "threshold": 90,
                    "timestamp": current_time
                })
                health_status["overall_status"] = "critical"
            elif cpu_usage > 70:
                health_status["warnings"].append({
                    "type": "moderate_cpu_usage",
                    "message": f"CPU使用率较高: {cpu_usage}%",
                    "severity": "warning",
                    "value": cpu_usage,
                    "threshold": 70,
                    "timestamp": current_time
                })
                if health_status["overall_status"] == "healthy":
                    health_status["overall_status"] = "warning"
            
            # 检查内存使用率
            memory_usage = resources.get("memory", {}).get("usage_percent", 0)
            if memory_usage > 90:
                health_status["errors"].append({
                    "type": "high_memory_usage",
                    "message": f"内存使用率过高: {memory_usage}%",
                    "severity": "error",
                    "value": memory_usage,
                    "threshold": 90,
                    "timestamp": current_time
                })
                health_status["overall_status"] = "critical"
            elif memory_usage > 80:
                health_status["warnings"].append({
                    "type": "moderate_memory_usage",
                    "message": f"内存使用率较高: {memory_usage}%",
                    "severity": "warning",
                    "value": memory_usage,
                    "threshold": 80,
                    "timestamp": current_time
                })
                if health_status["overall_status"] == "healthy":
                    health_status["overall_status"] = "warning"
            
            # 检查磁盘使用率
            disk_usage = resources.get("disk", {}).get("usage_percent", 0)
            if disk_usage > 95:
                health_status["errors"].append({
                    "type": "high_disk_usage",
                    "message": f"磁盘使用率过高: {disk_usage}%",
                    "severity": "error",
                    "value": disk_usage,
                    "threshold": 95,
                    "timestamp": current_time
                })
                health_status["overall_status"] = "critical"
            elif disk_usage > 85:
                health_status["warnings"].append({
                    "type": "moderate_disk_usage",
                    "message": f"磁盘使用率较高: {disk_usage}%",
                    "severity": "warning",
                    "value": disk_usage,
                    "threshold": 85,
                    "timestamp": current_time
                })
                if health_status["overall_status"] == "healthy":
                    health_status["overall_status"] = "warning"
            
            # 检查运行中的任务数量
            running_tasks = app_metrics.get("tasks", {}).get("running_tasks", 0)
            if running_tasks > 10:
                health_status["warnings"].append({
                    "type": "many_running_tasks",
                    "message": f"运行中的任务较多: {running_tasks}个",
                    "severity": "warning",
                    "value": running_tasks,
                    "threshold": 10,
                    "timestamp": current_time
                })
                if health_status["overall_status"] == "healthy":
                    health_status["overall_status"] = "warning"
            
            # 检查日志文件大小
            log_size_mb = app_metrics.get("logs", {}).get("total_size_mb", 0)
            if log_size_mb > 1000:  # 1GB
                health_status["warnings"].append({
                    "type": "large_log_files",
                    "message": f"日志文件占用空间较大: {log_size_mb}MB",
                    "severity": "warning",
                    "value": log_size_mb,
                    "threshold": 1000,
                    "timestamp": current_time
                })
                if health_status["overall_status"] == "healthy":
                    health_status["overall_status"] = "warning"
            
            # 检查最近任务成功率
            success_rate = app_metrics.get("tasks", {}).get("success_rate_24h", 100)
            if success_rate < 50:
                health_status["errors"].append({
                    "type": "low_success_rate",
                    "message": f"最近24小时任务成功率过低: {success_rate}%",
                    "severity": "error",
                    "value": success_rate,
                    "threshold": 50,
                    "timestamp": current_time
                })
                health_status["overall_status"] = "critical"
            elif success_rate < 80:
                health_status["warnings"].append({
                    "type": "moderate_success_rate",
                    "message": f"最近24小时任务成功率较低: {success_rate}%",
                    "severity": "warning",
                    "value": success_rate,
                    "threshold": 80,
                    "timestamp": current_time
                })
                if health_status["overall_status"] == "healthy":
                    health_status["overall_status"] = "warning"
            
        except Exception as e:
            health_status["errors"].append({
                "type": "health_check_error",
                "message": f"健康检查过程中发生错误: {str(e)}",
                "severity": "error",
                "timestamp": datetime.utcnow().isoformat()
            })
            health_status["overall_status"] = "error"
        
        return health_status

    async def get_performance_report(self, days: int = 7) -> Dict[str, Any]:
        """
        生成性能报告
        
        Args:
            days: 报告时间范围（天数）
            
        Returns:
            Dict[str, Any]: 性能报告
        """
        since_date = datetime.utcnow() - timedelta(days=days)
        
        try:
            # 任务执行性能统计
            task_performance = await self.db.execute(
                select(
                    func.count(TaskExecution.id).label("total_tasks"),
                    func.sum(
                        func.case((TaskExecution.status == TaskStatus.SUCCESS, 1), else_=0)
                    ).label("success_tasks"),
                    func.sum(
                        func.case((TaskExecution.status == TaskStatus.FAILED, 1), else_=0)
                    ).label("failed_tasks"),
                    func.avg(TaskExecution.duration).label("avg_duration"),
                    func.min(TaskExecution.duration).label("min_duration"),
                    func.max(TaskExecution.duration).label("max_duration")
                )
                .where(
                    and_(
                        TaskExecution.created_at >= since_date,
                        TaskExecution.duration.isnot(None)
                    )
                )
            )
            
            perf_row = task_performance.first()
            
            # 每日任务数量趋势
            daily_trends = await self.db.execute(
                select(
                    func.date(TaskExecution.created_at).label("date"),
                    func.count(TaskExecution.id).label("task_count"),
                    func.avg(TaskExecution.duration).label("avg_duration")
                )
                .where(TaskExecution.created_at >= since_date)
                .group_by(func.date(TaskExecution.created_at))
                .order_by("date")
            )
            
            trends = []
            for row in daily_trends:
                trends.append({
                    "date": row.date.isoformat(),
                    "task_count": row.task_count,
                    "average_duration": round(row.avg_duration or 0, 2)
                })
            
            # 最慢的任务
            slowest_tasks = await self.db.execute(
                select(
                    TaskExecution.task_id,
                    TaskExecution.playbook_name,
                    TaskExecution.duration,
                    TaskExecution.created_at
                )
                .where(
                    and_(
                        TaskExecution.created_at >= since_date,
                        TaskExecution.duration.isnot(None)
                    )
                )
                .order_by(desc(TaskExecution.duration))
                .limit(10)
            )
            
            slow_tasks = []
            for row in slowest_tasks:
                slow_tasks.append({
                    "task_id": row.task_id,
                    "playbook_name": row.playbook_name,
                    "duration": row.duration,
                    "created_at": row.created_at.isoformat()
                })
            
            # 当前系统资源
            current_resources = await self.get_system_resources()
            
            return {
                "report_period_days": days,
                "generated_at": datetime.utcnow().isoformat(),
                "task_performance": {
                    "total_tasks": perf_row.total_tasks or 0,
                    "success_tasks": perf_row.success_tasks or 0,
                    "failed_tasks": perf_row.failed_tasks or 0,
                    "success_rate": round((perf_row.success_tasks or 0) / (perf_row.total_tasks or 1) * 100, 2),
                    "average_duration": round(perf_row.avg_duration or 0, 2),
                    "min_duration": perf_row.min_duration or 0,
                    "max_duration": perf_row.max_duration or 0
                },
                "daily_trends": trends,
                "slowest_tasks": slow_tasks,
                "current_system_resources": current_resources
            }
            
        except Exception as e:
            # 返回符合schema的默认数据结构
            return {
                "report_period_days": days,
                "generated_at": datetime.utcnow().isoformat(),
                "task_performance": {
                    "total_tasks": 0,
                    "success_tasks": 0,
                    "failed_tasks": 0,
                    "success_rate": 0.0,
                    "average_duration": 0.0,
                    "min_duration": 0.0,
                    "max_duration": 0.0
                },
                "daily_trends": [],
                "slowest_tasks": [],
                "current_system_resources": await self.get_system_resources()
            }

    async def get_alert_thresholds(self) -> Dict[str, Any]:
        """
        获取系统警告阈值配置
        
        Returns:
            Dict[str, Any]: 警告阈值配置
        """
        return {
            "cpu_usage": {
                "warning": 70,
                "critical": 90
            },
            "memory_usage": {
                "warning": 80,
                "critical": 90
            },
            "disk_usage": {
                "warning": 85,
                "critical": 95
            },
            "success_rate": {
                "warning": 80,
                "critical": 50
            },
            "running_tasks": {
                "warning": 10,
                "critical": 20
            },
            "log_size_mb": {
                "warning": 1000,
                "critical": 5000
            }
        }

    async def update_alert_thresholds(self, thresholds: Dict[str, Any]) -> bool:
        """
        更新系统警告阈值配置
        
        Args:
            thresholds: 新的阈值配置
            
        Returns:
            bool: 是否更新成功
        """
        try:
            # 保存阈值到系统配置表
            config_key = "monitoring.alert_thresholds"
            
            # 查询是否已存在配置
            result = await self.db.execute(
                select(SystemConfig).where(SystemConfig.key == config_key)
            )
            config = result.scalar_one_or_none()
            
            if config:
                # 更新现有配置
                config.set_value(thresholds)
            else:
                # 创建新配置
                config = SystemConfig(
                    key=config_key,
                    value="",  # 会被set_value覆盖
                    description="系统监控警告阈值配置",
                    category="monitoring",
                    is_sensitive=False,
                    is_readonly=False,
                    requires_restart=False
                )
                config.set_value(thresholds)
                self.db.add(config)
            
            await self.db.commit()
            return True
            
        except Exception as e:
            await self.db.rollback()
            # 记录错误但不抛出，保持向后兼容
            import logging
            logging.error(f"更新警告阈值失败: {e}")
            return False
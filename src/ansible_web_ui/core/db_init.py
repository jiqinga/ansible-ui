"""
数据库初始化和优化模块

在应用启动时自动创建索引和应用性能优化
"""

import asyncio
from sqlalchemy import text
from ansible_web_ui.core.database import async_engine
from ansible_web_ui.core.logging import get_logger

logger = get_logger(__name__)


async def create_performance_indexes():
    """
    创建性能优化索引
    
    这些索引会在应用启动时自动创建，确保查询性能。
    包含针对以下场景的优化：
    - Count查询优化（hosts, playbooks）
    - 历史统计查询优化（today, week, month）
    - 执行记录列表查询优化
    - 趋势分析查询优化
    """
    logger.info("📊 创建性能优化索引...")
    
    indexes = [
        # 🚀 任务执行表索引（最关键 - 优化历史记录和统计查询）
        ("idx_task_executions_created_at", 
         "CREATE INDEX IF NOT EXISTS idx_task_executions_created_at ON task_executions(created_at)"),
        
        ("idx_task_executions_status", 
         "CREATE INDEX IF NOT EXISTS idx_task_executions_status ON task_executions(status)"),
        
        ("idx_task_executions_status_created", 
         "CREATE INDEX IF NOT EXISTS idx_task_executions_status_created ON task_executions(status, created_at)"),
        
        ("idx_task_executions_user_id", 
         "CREATE INDEX IF NOT EXISTS idx_task_executions_user_id ON task_executions(user_id)"),
        
        ("idx_task_executions_user_created", 
         "CREATE INDEX IF NOT EXISTS idx_task_executions_user_created ON task_executions(user_id, created_at)"),
        
        ("idx_task_executions_playbook", 
         "CREATE INDEX IF NOT EXISTS idx_task_executions_playbook ON task_executions(playbook_name)"),
        
        # 🚀 新增：优化统计查询的复合索引
        ("idx_task_exec_created_status_duration", 
         "CREATE INDEX IF NOT EXISTS idx_task_exec_created_status_duration ON task_executions(created_at, status, duration)"),
        
        # 🚀 主机表索引（优化inventory count查询）
        ("idx_hosts_is_active", 
         "CREATE INDEX IF NOT EXISTS idx_hosts_is_active ON hosts(is_active)"),
        
        ("idx_hosts_hostname", 
         "CREATE INDEX IF NOT EXISTS idx_hosts_hostname ON hosts(hostname)"),
        
        ("idx_hosts_active_group", 
         "CREATE INDEX IF NOT EXISTS idx_hosts_active_group ON hosts(is_active, group_name)"),
        
        # 🚀 Playbook表索引（优化playbook count查询）
        ("idx_playbooks_is_valid", 
         "CREATE INDEX IF NOT EXISTS idx_playbooks_is_valid ON playbooks(is_valid)"),
        
        ("idx_playbooks_filename", 
         "CREATE INDEX IF NOT EXISTS idx_playbooks_filename ON playbooks(filename)"),
        
        ("idx_playbooks_valid_filename", 
         "CREATE INDEX IF NOT EXISTS idx_playbooks_valid_filename ON playbooks(is_valid, filename)"),
        
        # 用户表索引
        ("idx_users_username", 
         "CREATE INDEX IF NOT EXISTS idx_users_username ON users(username)"),
        
        ("idx_users_is_active", 
         "CREATE INDEX IF NOT EXISTS idx_users_is_active ON users(is_active)"),
    ]
    
    created_count = 0
    failed_count = 0
    
    async with async_engine.begin() as conn:
        for idx_name, idx_sql in indexes:
            try:
                await conn.execute(text(idx_sql))
                logger.debug(f"  ✅ {idx_name}")
                created_count += 1
            except Exception as e:
                # 某些索引可能因为表不存在而失败，这是正常的
                logger.debug(f"  ⚠️  {idx_name}: {str(e)}")
                failed_count += 1
    
    if created_count > 0:
        logger.info(f"✅ 成功创建/验证 {created_count} 个索引")
    
    if failed_count > 0:
        logger.debug(f"⚠️  {failed_count} 个索引创建失败（可能是表不存在）")


async def analyze_database():
    """
    分析数据库以优化查询计划
    
    SQLite的ANALYZE命令会收集统计信息，帮助查询优化器选择最佳执行计划
    """
    try:
        async with async_engine.begin() as conn:
            await conn.execute(text("ANALYZE"))
        logger.debug("✅ 数据库分析完成")
    except Exception as e:
        logger.warning(f"⚠️  数据库分析失败: {e}")


async def initialize_database_optimizations():
    """
    初始化数据库优化
    
    在应用启动时调用，自动创建索引和优化数据库
    """
    try:
        logger.info("🚀 初始化数据库性能优化...")
        
        # 创建索引
        await create_performance_indexes()
        
        # 分析数据库
        await analyze_database()
        
        logger.info("✅ 数据库性能优化完成")
        return True
        
    except Exception as e:
        logger.error(f"❌ 数据库优化失败: {e}")
        return False


def sync_initialize_database_optimizations():
    """
    同步版本的数据库优化初始化
    
    用于在非异步环境中调用
    """
    try:
        asyncio.run(initialize_database_optimizations())
        return True
    except Exception as e:
        logger.error(f"❌ 数据库优化失败: {e}")
        return False

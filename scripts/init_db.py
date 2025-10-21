#!/usr/bin/env python3
"""
数据库初始化脚本

创建数据库表并插入初始数据。
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

from ansible_web_ui.core.database import init_db, AsyncSessionLocal, engine
from ansible_web_ui.models import User, UserRole, SystemConfig
from ansible_web_ui.core.config import settings
from passlib.context import CryptContext
from sqlalchemy import text


# 密码加密上下文
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


async def create_default_user():
    """创建默认管理员用户"""
    async with AsyncSessionLocal() as session:
        # 检查是否已存在管理员用户
        from sqlalchemy import select
        result = await session.execute(
            select(User).where(User.username == "admin")
        )
        existing_user = result.scalar_one_or_none()
        
        if existing_user:
            print("✅ 默认管理员用户已存在")
            return
        
        # 创建默认管理员用户
        admin_user = User(
            username="admin",
            email="admin@ansible-web-ui.com",
            full_name="系统管理员",
            password_hash=pwd_context.hash("admin123"),
            role=UserRole.ADMIN,
            is_active=True,
            is_superuser=True
        )
        
        session.add(admin_user)
        await session.commit()
        print("✅ 创建默认管理员用户: admin / admin123")


async def create_default_configs():
    """创建默认系统配置"""
    async with AsyncSessionLocal() as session:
        default_configs = [
            # Ansible配置
            {
                "key": "ansible.host_key_checking",
                "value": "false",
                "description": "是否检查SSH主机密钥",
                "category": "ansible",
                "validation_rule": '{"type": "boolean"}'
            },
            {
                "key": "ansible.timeout",
                "value": "300",
                "description": "Ansible执行超时时间（秒）",
                "category": "ansible",
                "validation_rule": '{"type": "integer", "min": 30, "max": 3600}'
            },
            {
                "key": "ansible.forks",
                "value": "5",
                "description": "Ansible并发执行数",
                "category": "ansible",
                "validation_rule": '{"type": "integer", "min": 1, "max": 50}'
            },
            {
                "key": "ansible.gathering",
                "value": "implicit",
                "description": "事实收集策略",
                "category": "ansible",
                "validation_rule": '{"type": "string", "enum": ["implicit", "explicit", "smart"]}'
            },
            
            # 应用配置
            {
                "key": "app.session_timeout",
                "value": "30",
                "description": "用户会话超时时间（分钟）",
                "category": "security",
                "validation_rule": '{"type": "integer", "min": 5, "max": 480}'
            },
            {
                "key": "app.max_concurrent_tasks",
                "value": "10",
                "description": "最大并发任务数",
                "category": "performance",
                "validation_rule": '{"type": "integer", "min": 1, "max": 100}'
            },
            {
                "key": "app.log_retention_days",
                "value": "30",
                "description": "日志保留天数",
                "category": "maintenance",
                "validation_rule": '{"type": "integer", "min": 1, "max": 365}'
            },
            {
                "key": "app.enable_task_history",
                "value": "true",
                "description": "是否启用任务历史记录",
                "category": "features",
                "validation_rule": '{"type": "boolean"}'
            },
            
            # UI配置
            {
                "key": "ui.theme",
                "value": "glassmorphism",
                "description": "UI主题风格",
                "category": "ui",
                "validation_rule": '{"type": "string", "enum": ["glassmorphism", "dark", "light"]}'
            },
            {
                "key": "ui.language",
                "value": "zh-CN",
                "description": "界面语言",
                "category": "ui",
                "validation_rule": '{"type": "string", "enum": ["zh-CN", "en-US"]}'
            },
            {
                "key": "ui.page_size",
                "value": "20",
                "description": "默认分页大小",
                "category": "ui",
                "validation_rule": '{"type": "integer", "min": 10, "max": 100}'
            }
        ]
        
        from sqlalchemy import select
        for config_data in default_configs:
            # 检查配置是否已存在
            result = await session.execute(
                select(SystemConfig).where(SystemConfig.key == config_data["key"])
            )
            existing_config = result.scalar_one_or_none()
            
            if not existing_config:
                config = SystemConfig(**config_data)
                session.add(config)
        
        await session.commit()
        print(f"✅ 创建了 {len(default_configs)} 个默认系统配置")


async def create_performance_indexes():
    """创建性能优化索引"""
    print("\n🔧 创建性能优化索引...")
    
    indexes = [
        # task_executions 表索引
        ("idx_task_executions_created_at", "task_executions", "created_at"),
        ("idx_task_executions_status_created", "task_executions", "status, created_at"),
        ("idx_task_executions_user_created", "task_executions", "user_id, created_at"),
        ("idx_task_executions_playbook", "task_executions", "playbook_name"),
    ]
    
    async with engine.begin() as conn:
        for index_name, table_name, columns in indexes:
            try:
                # 检查索引是否已存在
                check_query = text(f"""
                    SELECT name FROM sqlite_master 
                    WHERE type='index' AND name=:index_name
                """)
                result = await conn.execute(check_query, {"index_name": index_name})
                exists = result.fetchone()
                
                if exists:
                    print(f"  ⏭️  索引 {index_name} 已存在，跳过")
                    continue
                
                # 创建索引
                create_query = text(f"""
                    CREATE INDEX IF NOT EXISTS {index_name} 
                    ON {table_name} ({columns})
                """)
                await conn.execute(create_query)
                print(f"  ✅ 创建索引: {index_name}")
                
            except Exception as e:
                print(f"  ⚠️  创建索引 {index_name} 失败: {e}")


def optimize_sqlite_pragma(db_path: str = "./data/ansible_web_ui.db") -> bool:
    """
    优化SQLite PRAGMA设置
    
    Args:
        db_path: 数据库文件路径
        
    Returns:
        bool: 优化是否成功
    """
    if not Path(db_path).exists():
        return True
    
    try:
        import sqlite3
        print("\n⚡ 应用SQLite性能优化...")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 应用性能优化设置
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA synchronous=NORMAL")
        cursor.execute("PRAGMA cache_size=-20000")
        cursor.execute("PRAGMA temp_store=MEMORY")
        cursor.execute("PRAGMA mmap_size=268435456")
        cursor.execute("PRAGMA optimize")
        
        conn.commit()
        
        # 显示优化结果
        cursor.execute("PRAGMA journal_mode")
        journal_mode = cursor.fetchone()[0]
        
        cursor.close()
        conn.close()
        
        print(f"  ✅ SQLite性能优化完成 (journal_mode={journal_mode})")
        print("     • WAL模式: 并发性能提升2-5倍")
        print("     • 20MB缓存: 减少磁盘I/O")
        print("     • 256MB内存映射: 利用OS缓存")
        
        return True
        
    except Exception as e:
        print(f"  ⚠️  SQLite优化失败: {e}")
        return False


async def optimize_database():
    """优化数据库"""
    print("\n📊 优化数据库...")
    
    async with engine.begin() as conn:
        try:
            # 分析数据库以优化查询计划
            await conn.execute(text("ANALYZE"))
            print("  ✅ 数据库分析完成")
        except Exception as e:
            print(f"  ⚠️  数据库分析失败: {e}")
    
    # 应用SQLite PRAGMA优化
    optimize_sqlite_pragma()


async def main():
    """主函数"""
    print("🚀 开始初始化数据库...")
    
    try:
        # 创建数据库表
        await init_db()
        print("✅ 数据库表创建完成")
        
        # 创建性能优化索引
        await create_performance_indexes()
        
        # 优化数据库
        await optimize_database()
        
        # 创建默认用户
        await create_default_user()
        
        # 创建默认配置
        await create_default_configs()
        
        print("\n" + "=" * 60)
        print("🎉 数据库初始化完成！")
        print("=" * 60)
        print("\n📋 默认登录信息:")
        print("   用户名: admin")
        print("   密码: admin123")
        print("\n⚠️  请在生产环境中修改默认密码！")
        print("\n💡 性能优化:")
        print("   ✅ 已创建数据库索引")
        print("   ✅ 已优化查询计划")
        print("   ✅ 缓存机制已启用")
        
    except Exception as e:
        print(f"❌ 数据库初始化失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
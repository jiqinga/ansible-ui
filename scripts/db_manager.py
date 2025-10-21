#!/usr/bin/env python3
"""
数据库管理脚本

提供数据库相关的管理功能，如备份、恢复、清理等。
"""

import asyncio
import shutil
import sys
from datetime import datetime
from pathlib import Path

# 添加src目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from ansible_web_ui.core.config import settings
from ansible_web_ui.core.database import init_db, close_db
from ansible_web_ui.core.logging import setup_logging, get_logger


async def backup_database():
    """备份数据库"""
    logger = get_logger(__name__)
    
    try:
        # 解析数据库URL获取文件路径
        if "sqlite" in settings.DATABASE_URL:
            db_path = settings.DATABASE_URL.split("///")[-1]
            db_file = Path(db_path)
            
            if not db_file.exists():
                logger.error("❌ 数据库文件不存在", path=str(db_file))
                return False
            
            # 创建备份文件名
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_dir = Path("data/backups")
            backup_dir.mkdir(exist_ok=True)
            
            backup_file = backup_dir / f"ansible_web_ui_backup_{timestamp}.db"
            
            # 复制数据库文件
            shutil.copy2(db_file, backup_file)
            
            logger.info("✅ 数据库备份成功", 
                       source=str(db_file), 
                       backup=str(backup_file))
            return True
        else:
            logger.error("❌ 当前只支持SQLite数据库备份")
            return False
            
    except Exception as e:
        logger.error("❌ 数据库备份失败", error=str(e))
        return False


async def restore_database(backup_file: str):
    """恢复数据库"""
    logger = get_logger(__name__)
    
    try:
        backup_path = Path(backup_file)
        if not backup_path.exists():
            logger.error("❌ 备份文件不存在", path=backup_file)
            return False
        
        # 解析数据库URL获取文件路径
        if "sqlite" in settings.DATABASE_URL:
            db_path = settings.DATABASE_URL.split("///")[-1]
            db_file = Path(db_path)
            
            # 备份当前数据库
            if db_file.exists():
                current_backup = db_file.with_suffix(f".backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db")
                shutil.copy2(db_file, current_backup)
                logger.info("📦 当前数据库已备份", backup=str(current_backup))
            
            # 恢复数据库
            shutil.copy2(backup_path, db_file)
            
            logger.info("✅ 数据库恢复成功", 
                       backup=backup_file, 
                       target=str(db_file))
            return True
        else:
            logger.error("❌ 当前只支持SQLite数据库恢复")
            return False
            
    except Exception as e:
        logger.error("❌ 数据库恢复失败", error=str(e))
        return False


async def reset_database():
    """重置数据库（删除所有数据）"""
    logger = get_logger(__name__)
    
    try:
        # 先备份
        await backup_database()
        
        # 解析数据库URL获取文件路径
        if "sqlite" in settings.DATABASE_URL:
            db_path = settings.DATABASE_URL.split("///")[-1]
            db_file = Path(db_path)
            
            if db_file.exists():
                db_file.unlink()
                logger.info("🗑️ 数据库文件已删除", path=str(db_file))
            
            # 重新初始化数据库
            await init_db()
            logger.info("✅ 数据库重置完成")
            return True
        else:
            logger.error("❌ 当前只支持SQLite数据库重置")
            return False
            
    except Exception as e:
        logger.error("❌ 数据库重置失败", error=str(e))
        return False
    finally:
        await close_db()


async def check_database():
    """检查数据库状态"""
    logger = get_logger(__name__)
    
    try:
        # 检查数据库文件
        if "sqlite" in settings.DATABASE_URL:
            db_path = settings.DATABASE_URL.split("///")[-1]
            db_file = Path(db_path)
            
            if db_file.exists():
                file_size = db_file.stat().st_size
                logger.info("📊 数据库文件信息", 
                           path=str(db_file),
                           size=f"{file_size / 1024:.2f} KB")
            else:
                logger.warning("⚠️ 数据库文件不存在", path=str(db_file))
        
        # 测试数据库连接
        await init_db()
        logger.info("✅ 数据库连接正常")
        return True
        
    except Exception as e:
        logger.error("❌ 数据库检查失败", error=str(e))
        return False
    finally:
        await close_db()


def list_backups():
    """列出所有备份文件"""
    logger = get_logger(__name__)
    
    backup_dir = Path("data/backups")
    if not backup_dir.exists():
        logger.info("📁 备份目录不存在")
        return []
    
    backups = list(backup_dir.glob("*.db"))
    if not backups:
        logger.info("📁 没有找到备份文件")
        return []
    
    logger.info(f"📋 找到 {len(backups)} 个备份文件:")
    for backup in sorted(backups, reverse=True):
        file_size = backup.stat().st_size
        modified_time = datetime.fromtimestamp(backup.stat().st_mtime)
        logger.info(f"  📄 {backup.name} ({file_size / 1024:.2f} KB, {modified_time.strftime('%Y-%m-%d %H:%M:%S')})")
    
    return backups


async def main():
    """主函数"""
    setup_logging()
    logger = get_logger(__name__)
    
    if len(sys.argv) < 2:
        logger.info("📖 数据库管理工具使用说明:")
        logger.info("  python scripts/db_manager.py backup          - 备份数据库")
        logger.info("  python scripts/db_manager.py restore <file>  - 恢复数据库")
        logger.info("  python scripts/db_manager.py reset           - 重置数据库")
        logger.info("  python scripts/db_manager.py check           - 检查数据库")
        logger.info("  python scripts/db_manager.py list            - 列出备份文件")
        return 1
    
    command = sys.argv[1].lower()
    
    if command == "backup":
        success = await backup_database()
        return 0 if success else 1
    
    elif command == "restore":
        if len(sys.argv) < 3:
            logger.error("❌ 请指定备份文件路径")
            return 1
        success = await restore_database(sys.argv[2])
        return 0 if success else 1
    
    elif command == "reset":
        logger.warning("⚠️ 此操作将删除所有数据，是否继续？(y/N)")
        confirm = input().lower()
        if confirm == 'y':
            success = await reset_database()
            return 0 if success else 1
        else:
            logger.info("❌ 操作已取消")
            return 0
    
    elif command == "check":
        success = await check_database()
        return 0 if success else 1
    
    elif command == "list":
        list_backups()
        return 0
    
    else:
        logger.error(f"❌ 未知命令: {command}")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
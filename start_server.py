#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Ansible Web UI 服务器启动脚本

这个脚本用于启动 Ansible Web UI 应用服务器。
它会自动处理数据库初始化、环境检查等启动前的准备工作。
"""

import os
import sys
import uvicorn
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def check_environment():
    """检查运行环境"""
    print("🔍 检查运行环境...")
    
    # 检查 .env 文件
    env_file = project_root / ".env"
    if not env_file.exists():
        print("⚠️  警告: .env 文件不存在，将使用默认配置")
        print("💡 提示: 可以复制 .env.example 为 .env 并修改配置")
    
    # 检查数据目录
    data_dir = project_root / "data"
    if not data_dir.exists():
        print("📁 创建数据目录...")
        data_dir.mkdir(parents=True, exist_ok=True)
    
    print("✅ 环境检查完成")


def init_database():
    """初始化数据库"""
    print("🗄️  初始化数据库...")
    
    try:
        from src.ansible_web_ui.core.db_init import sync_initialize_database_optimizations
        sync_initialize_database_optimizations()
        print("✅ 数据库初始化完成")
    except Exception as e:
        print(f"⚠️  数据库初始化警告: {e}")
        print("💡 应用启动时会自动进行数据库优化")


def main():
    """主函数"""
    print("=" * 60)
    print("🎯 Ansible Web UI 服务器启动")
    print("=" * 60)
    
    # 环境检查
    check_environment()
    
    # 数据库初始化
    init_database()
    
    # 从环境变量读取配置
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    reload = os.getenv("RELOAD", "true").lower() == "true"
    
    print("\n" + "=" * 60)
    print(f"🚀 启动服务器...")
    print(f"📍 地址: http://{host}:{port}")
    print(f"🔄 热重载: {'启用' if reload else '禁用'}")
    print(f"📚 API文档: http://{host}:{port}/docs")
    print(f"📖 ReDoc文档: http://{host}:{port}/redoc")
    print("=" * 60)
    print("\n💡 按 Ctrl+C 停止服务器\n")
    
    # 启动服务器
    try:
        uvicorn.run(
            "src.ansible_web_ui.main:create_app",
            factory=True,
            host=host,
            port=port,
            reload=reload,
            log_level="info"
        )
    except KeyboardInterrupt:
        print("\n\n👋 服务器已停止")
    except Exception as e:
        print(f"\n❌ 服务器启动失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

"""
Celery Worker启动脚本

提供Celery Worker的启动和管理功能。
"""

import logging
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from ansible_web_ui.tasks.celery_app import celery_app
from ansible_web_ui.core.config import get_settings

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)

def start_worker():
    """启动Celery Worker"""
    settings = get_settings()
    
    logger.info("🚀 启动Celery Worker...")
    logger.info(f"📡 消息代理: {settings.REDIS_URL}")
    logger.info(f"💾 结果后端: {settings.REDIS_URL}")
    
    # 启动worker
    celery_app.worker_main([
        "worker",
        "--loglevel=info",
        "--concurrency=4",
        "--queues=default,ansible_tasks,system_tasks",
        "--hostname=worker@%h",
        "--without-gossip",
        "--without-mingle",
        "--without-heartbeat",
    ])

if __name__ == "__main__":
    start_worker()
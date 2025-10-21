"""
Celery应用配置模块

提供Celery应用实例和基础配置，支持任务队列、结果存储和监控功能。
"""

from celery import Celery
from kombu import Queue
from ansible_web_ui.core.config import get_settings

# 获取应用配置
settings = get_settings()

# 创建Celery应用实例
celery_app = Celery(
    "ansible_web_ui",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=[
        "ansible_web_ui.tasks.ansible_tasks",
    ]
)

# Celery配置
celery_app.conf.update(
    # 任务序列化配置
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Shanghai",
    enable_utc=True,
    
    # 任务路由配置
    task_routes={
        "ansible_web_ui.tasks.ansible_tasks.*": {"queue": "ansible_tasks"},
        "ansible_web_ui.tasks.system_tasks.*": {"queue": "system_tasks"},
    },
    
    # 队列配置
    task_default_queue="default",
    task_queues=(
        Queue("default", routing_key="default"),
        Queue("ansible_tasks", routing_key="ansible_tasks"),
        Queue("system_tasks", routing_key="system_tasks"),
    ),
    
    # 任务执行配置
    task_acks_late=True,  # 任务完成后才确认
    worker_prefetch_multiplier=1,  # 每次只预取一个任务
    task_reject_on_worker_lost=True,  # Worker丢失时拒绝任务
    
    # 任务超时配置
    task_soft_time_limit=1800,  # 软超时30分钟
    task_time_limit=2100,  # 硬超时35分钟
    
    # 任务重试配置
    task_default_retry_delay=60,  # 默认重试延迟60秒
    task_max_retries=3,  # 最大重试次数
    
    # 结果存储配置
    result_expires=3600,  # 结果保存1小时
    result_backend_transport_options={
        "master_name": "mymaster",
        "visibility_timeout": 3600,
    },
    
    # Worker配置
    worker_send_task_events=True,  # 发送任务事件
    task_send_sent_event=True,  # 发送任务发送事件
    
    # 监控配置
    worker_hijack_root_logger=False,  # 不劫持根日志记录器
    worker_log_format="[%(asctime)s: %(levelname)s/%(processName)s] %(message)s",
    worker_task_log_format="[%(asctime)s: %(levelname)s/%(processName)s][%(task_name)s(%(task_id)s)] %(message)s",
    
    # 安全配置
    worker_disable_rate_limits=False,  # 启用速率限制
    task_always_eager=settings.TESTING,  # 测试模式下同步执行任务
)

# 确保任务模块被导入以注册任务
try:
    from ansible_web_ui.tasks import ansible_tasks
except ImportError:
    pass

# 任务状态常量
class TaskStatus:
    """任务状态枚举"""
    PENDING = "PENDING"      # 等待中
    STARTED = "STARTED"      # 已开始
    SUCCESS = "SUCCESS"      # 成功
    FAILURE = "FAILURE"      # 失败
    RETRY = "RETRY"          # 重试中
    REVOKED = "REVOKED"      # 已撤销

# 任务优先级常量
class TaskPriority:
    """任务优先级枚举"""
    LOW = 0      # 低优先级
    NORMAL = 5   # 普通优先级
    HIGH = 10    # 高优先级
    URGENT = 15  # 紧急优先级

def get_celery_app() -> Celery:
    """
    获取Celery应用实例
    
    返回:
        Celery: Celery应用实例
    """
    return celery_app
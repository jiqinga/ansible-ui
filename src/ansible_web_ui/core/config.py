"""
应用配置管理

使用Pydantic Settings管理应用程序配置。
"""

import os
from pathlib import Path
from typing import Optional, List
from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    应用程序设置类
    
    从环境变量和.env文件中读取配置。
    """
    
    # 应用基本信息
    APP_NAME: str = Field(default="Ansible Web UI", description="应用名称")
    APP_VERSION: str = Field(default="0.1.0", description="应用版本")
    DEBUG: bool = Field(default=False, description="调试模式")
    
    # 服务器配置
    HOST: str = Field(default="0.0.0.0", description="服务器监听地址")
    PORT: int = Field(default=8000, description="服务器端口")
    
    # 数据库配置
    DATABASE_URL: str = Field(
        default="sqlite:///./data/ansible_web_ui.db",
        description="数据库连接URL"
    )
    ASYNC_DATABASE_URL: str = Field(
        default="sqlite+aiosqlite:///./data/ansible_web_ui.db",
        description="异步数据库连接URL"
    )
    DATABASE_ECHO: bool = Field(
        default=False,
        description="是否输出SQL查询日志"
    )
    
    # Redis配置（用于Celery）
    REDIS_URL: str = Field(
        default="redis://localhost:6379/0",
        description="Redis连接URL"
    )
    
    # 安全配置
    SECRET_KEY: str = Field(
        default="your-secret-key-change-in-production",
        description="JWT密钥"
    )
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(
        default=30,
        description="访问令牌过期时间（分钟）"
    )
    ALGORITHM: str = Field(default="HS256", description="JWT算法")
    
    # 文件路径配置
    PLAYBOOK_DIR: str = Field(
        default="./playbooks",
        description="Playbook文件目录（用于Ansible执行和临时文件存储，不再用于缓存）"
    )
    PROJECTS_BASE_PATH: str = Field(
        default="./projects",
        description="项目基础存储路径"
    )
    INVENTORY_DIR: str = Field(
        default="./inventory",
        description="Inventory文件目录"
    )
    LOG_DIR: str = Field(
        default="./logs",
        description="日志文件目录"
    )
    UPLOAD_DIR: str = Field(
        default="./uploads",
        description="上传文件目录"
    )
    
    # Ansible配置
    ANSIBLE_CONFIG: str = Field(
        default="./config/ansible.cfg",
        description="Ansible配置文件路径"
    )
    ANSIBLE_HOST_KEY_CHECKING: bool = Field(
        default=False,
        description="是否检查主机密钥"
    )
    ANSIBLE_TIMEOUT: int = Field(
        default=300,
        description="Ansible执行超时时间（秒）"
    )
    
    # Celery配置
    CELERY_BROKER_URL: str = Field(
        default="redis://localhost:6379/0",
        description="Celery消息代理URL"
    )
    CELERY_RESULT_BACKEND: str = Field(
        default="redis://localhost:6379/0",
        description="Celery结果后端URL"
    )
    
    # 日志配置
    LOG_LEVEL: str = Field(default="INFO", description="日志级别")
    LOG_FORMAT: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        description="日志格式"
    )
    LOG_RETENTION_DAYS: int = Field(
        default=30,
        description="日志保留天数",
        ge=1,
        le=365,
    )
    LOG_NO_COLOR: bool = Field(
        default=False,
        description="禁用彩色日志输出"
    )
    
    # 测试配置
    TESTING: bool = Field(default=False, description="测试模式")
    
    # CORS配置
    ALLOWED_ORIGINS: List[str] = Field(
        default=["http://localhost:3000", "http://127.0.0.1:3000"],
        description="允许的跨域源"
    )
    ALLOWED_HOSTS: List[str] = Field(
        default=["*"],
        description="允许的主机"
    )
    
    # 分页配置
    DEFAULT_PAGE_SIZE: int = Field(default=20, description="默认分页大小")
    MAX_PAGE_SIZE: int = Field(default=100, description="最大分页大小")
    
    # 文件上传配置
    MAX_PLAYBOOK_SIZE: int = Field(
        default=10 * 1024 * 1024,  # 10MB
        description="Playbook文件最大大小（字节）"
    )
    ALLOWED_PLAYBOOK_EXTENSIONS: List[str] = Field(
        default=[".yml", ".yaml"],
        description="允许的Playbook文件扩展名"
    )

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True
        extra = "ignore"  # 忽略额外的环境变量

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # 确保必要的目录存在
        self._ensure_directories()

    def _ensure_directories(self) -> None:
        """确保必要的目录存在"""
        directories = [
            Path(self.PLAYBOOK_DIR),
            Path(self.PROJECTS_BASE_PATH),
            Path(self.INVENTORY_DIR),
            Path(self.LOG_DIR),
            Path(self.UPLOAD_DIR),
            Path("./data"),  # 数据库目录
            Path("./config"),  # 配置目录
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)

    @property
    def database_url_sync(self) -> str:
        """获取同步数据库URL"""
        return self.DATABASE_URL

    @property
    def database_url_async(self) -> str:
        """获取异步数据库URL"""
        return self.ASYNC_DATABASE_URL


# 创建全局设置实例
settings = Settings()


def get_settings() -> Settings:
    """获取应用设置实例"""
    return settings

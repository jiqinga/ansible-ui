"""
数据库配置和连接管理

提供SQLAlchemy数据库引擎、会话管理和基础模型类。
"""

from typing import AsyncGenerator, Optional
from sqlalchemy import create_engine, MetaData, event, pool
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
import os
from pathlib import Path

# 数据库配置
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./data/ansible_web_ui.db")
ASYNC_DATABASE_URL = os.getenv("ASYNC_DATABASE_URL", "sqlite+aiosqlite:///./data/ansible_web_ui.db")

# 确保数据目录存在
data_dir = Path("./data")
data_dir.mkdir(exist_ok=True)


def _set_sqlite_pragma(dbapi_conn, connection_record):
    """
    为每个SQLite连接设置性能优化PRAGMA
    
    这些设置将大幅提升SQLite性能：
    - WAL模式：提升并发读写性能
    - NORMAL同步：平衡性能和数据安全
    - 大缓存：减少磁盘I/O
    - 内存临时存储：加速临时表操作
    - 内存映射I/O：利用操作系统缓存
    """
    cursor = dbapi_conn.cursor()
    
    # WAL模式 - 大幅提升并发性能
    cursor.execute("PRAGMA journal_mode=WAL")
    
    # 同步模式 - NORMAL平衡性能和安全性
    cursor.execute("PRAGMA synchronous=NORMAL")
    
    # 增大缓存 - 20MB缓存
    cursor.execute("PRAGMA cache_size=-20000")
    
    # 内存临时存储
    cursor.execute("PRAGMA temp_store=MEMORY")
    
    # 内存映射I/O - 256MB
    cursor.execute("PRAGMA mmap_size=268435456")
    
    # 启用查询优化器
    cursor.execute("PRAGMA optimize")
    
    cursor.close()


# 创建同步数据库引擎（用于Alembic迁移）
engine = create_engine(
    DATABASE_URL,
    connect_args={
        "check_same_thread": False,
        "timeout": 30,  # 增加超时时间
    } if "sqlite" in DATABASE_URL else {},
    echo=False,  # 生产环境设为False
    poolclass=pool.StaticPool if "sqlite" in DATABASE_URL else pool.QueuePool,
    pool_pre_ping=True,  # 连接前检查
)

# 为同步引擎注册PRAGMA设置
if "sqlite" in DATABASE_URL:
    event.listen(engine, "connect", _set_sqlite_pragma)

# 创建异步数据库引擎（用于FastAPI应用）
async_engine = create_async_engine(
    ASYNC_DATABASE_URL,
    echo=False,  # 生产环境设为False
    connect_args={
        "timeout": 30,
    } if "sqlite" in ASYNC_DATABASE_URL else {},
    poolclass=pool.StaticPool if "sqlite" in ASYNC_DATABASE_URL else pool.QueuePool,
    pool_pre_ping=True,
)

# 为异步引擎注册PRAGMA设置
if "sqlite" in ASYNC_DATABASE_URL:
    @event.listens_for(async_engine.sync_engine, "connect")
    def _set_sqlite_pragma_async(dbapi_conn, connection_record):
        _set_sqlite_pragma(dbapi_conn, connection_record)

# 创建会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
AsyncSessionLocal = async_sessionmaker(
    async_engine, class_=AsyncSession, expire_on_commit=False
)

# 创建基础模型类
Base = declarative_base()

# 元数据配置
metadata = MetaData(
    naming_convention={
        "ix": "ix_%(column_0_label)s",
        "uq": "uq_%(table_name)s_%(column_0_name)s",
        "ck": "ck_%(table_name)s_%(constraint_name)s",
        "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
        "pk": "pk_%(table_name)s"
    }
)
Base.metadata = metadata


def get_db() -> Session:
    """
    获取同步数据库会话（用于非异步操作）
    
    Returns:
        Session: SQLAlchemy会话对象
    """
    db = SessionLocal()
    try:
        return db
    finally:
        db.close()


async def get_async_db() -> AsyncGenerator[AsyncSession, None]:
    """
    获取异步数据库会话（用于FastAPI依赖注入）
    
    Yields:
        AsyncSession: SQLAlchemy异步会话对象
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


# 别名，用于FastAPI依赖注入
get_db_session = get_async_db
get_async_db_session = get_async_db


async def init_db() -> None:
    """
    初始化数据库，创建所有表
    """
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def close_db() -> None:
    """
    关闭数据库连接
    """
    await async_engine.dispose()
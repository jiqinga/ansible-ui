"""
缓存管理模块

提供简单的内存缓存功能，用于优化API性能。
"""

import time
from typing import Any, Optional, Dict, Callable
from functools import wraps
import asyncio


class SimpleCache:
    """简单的内存缓存实现"""
    
    def __init__(self):
        self._cache: Dict[str, tuple[Any, float]] = {}
        self._default_ttl = 60  # 默认60秒过期
    
    def get(self, key: str) -> Optional[Any]:
        """获取缓存值"""
        if key in self._cache:
            value, expire_time = self._cache[key]
            if time.time() < expire_time:
                return value
            else:
                # 过期，删除缓存
                del self._cache[key]
        return None
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """设置缓存值"""
        if ttl is None:
            ttl = self._default_ttl
        expire_time = time.time() + ttl
        self._cache[key] = (value, expire_time)
    
    def delete(self, key: str) -> None:
        """删除缓存值"""
        if key in self._cache:
            del self._cache[key]
    
    def clear(self) -> None:
        """清空所有缓存"""
        self._cache.clear()
    
    def cleanup_expired(self) -> int:
        """清理过期缓存，返回清理数量"""
        current_time = time.time()
        expired_keys = [
            key for key, (_, expire_time) in self._cache.items()
            if current_time >= expire_time
        ]
        for key in expired_keys:
            del self._cache[key]
        return len(expired_keys)


# 全局缓存实例
_cache = SimpleCache()


def get_cache() -> SimpleCache:
    """获取全局缓存实例"""
    return _cache


def cached(ttl: int = 60, key_prefix: str = ""):
    """
    缓存装饰器
    
    Args:
        ttl: 缓存过期时间（秒）
        key_prefix: 缓存键前缀
    """
    def decorator(func: Callable):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            # 生成缓存键
            cache_key = f"{key_prefix}:{func.__name__}:{str(args)}:{str(kwargs)}"
            
            # 尝试从缓存获取
            cached_value = _cache.get(cache_key)
            if cached_value is not None:
                return cached_value
            
            # 执行函数
            result = await func(*args, **kwargs)
            
            # 存入缓存
            _cache.set(cache_key, result, ttl)
            
            return result
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            # 生成缓存键
            cache_key = f"{key_prefix}:{func.__name__}:{str(args)}:{str(kwargs)}"
            
            # 尝试从缓存获取
            cached_value = _cache.get(cache_key)
            if cached_value is not None:
                return cached_value
            
            # 执行函数
            result = func(*args, **kwargs)
            
            # 存入缓存
            _cache.set(cache_key, result, ttl)
            
            return result
        
        # 根据函数类型返回对应的包装器
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator

"""
文件缓存服务

提供文件内容的本地缓存功能，优化读取性能。
数据库是主存储，本地文件系统是缓存。
"""

import hashlib
import aiofiles
import aiofiles.os
from pathlib import Path
from typing import Optional, Tuple
from ansible_web_ui.core.config import settings


class FileCacheService:
    """
    文件缓存服务
    
    职责：
    1. 管理文件内容的本地缓存
    2. 使用哈希值验证缓存有效性
    3. 自动清理过期缓存
    """
    
    def __init__(self):
        """初始化缓存服务"""
        # 缓存目录
        self.cache_dir = Path(settings.PLAYBOOK_DIR).resolve()
        self.cache_dir.mkdir(parents=True, exist_ok=True)
    
    def _get_cache_path(self, filename: str) -> Path:
        """
        获取缓存文件路径
        
        Args:
            filename: 文件名
            
        Returns:
            Path: 缓存文件的绝对路径
        """
        # 安全验证：防止路径遍历
        if '..' in filename or '/' in filename or '\\' in filename:
            raise ValueError(f"非法的文件名: {filename}")
        
        return self.cache_dir / filename
    
    @staticmethod
    def calculate_hash(content: str) -> str:
        """
        计算内容的哈希值
        
        Args:
            content: 文件内容
            
        Returns:
            str: SHA256哈希值
        """
        return hashlib.sha256(content.encode('utf-8')).hexdigest()
    
    async def get_from_cache(
        self,
        filename: str,
        expected_hash: Optional[str] = None
    ) -> Optional[str]:
        """
        从缓存读取文件内容
        
        Args:
            filename: 文件名
            expected_hash: 期望的哈希值（用于验证缓存有效性）
            
        Returns:
            Optional[str]: 文件内容，如果缓存无效或不存在则返回None
        """
        try:
            cache_path = self._get_cache_path(filename)
            
            # 检查缓存文件是否存在
            if not cache_path.exists():
                return None
            
            # 读取缓存内容
            async with aiofiles.open(cache_path, 'r', encoding='utf-8') as f:
                content = await f.read()
            
            # 如果提供了期望的哈希值，验证缓存有效性
            if expected_hash:
                actual_hash = self.calculate_hash(content)
                if actual_hash != expected_hash:
                    # 缓存已过期，删除缓存文件
                    await self.remove_from_cache(filename)
                    return None
            
            return content
            
        except Exception:
            # 缓存读取失败，返回None
            return None
    
    async def save_to_cache(
        self,
        filename: str,
        content: str
    ) -> Tuple[str, int]:
        """
        保存内容到缓存
        
        Args:
            filename: 文件名
            content: 文件内容
            
        Returns:
            Tuple[str, int]: (文件哈希值, 文件大小)
        """
        try:
            cache_path = self._get_cache_path(filename)
            
            # 确保父目录存在
            cache_path.parent.mkdir(parents=True, exist_ok=True)
            
            # 写入缓存文件
            async with aiofiles.open(cache_path, 'w', encoding='utf-8') as f:
                await f.write(content)
            
            # 计算哈希值和大小
            file_hash = self.calculate_hash(content)
            file_size = len(content.encode('utf-8'))
            
            return file_hash, file_size
            
        except Exception as e:
            # 缓存写入失败不影响主流程
            raise ValueError(f"缓存写入失败: {str(e)}")
    
    async def remove_from_cache(self, filename: str) -> bool:
        """
        从缓存中删除文件
        
        Args:
            filename: 文件名
            
        Returns:
            bool: 是否删除成功
        """
        try:
            cache_path = self._get_cache_path(filename)
            
            if cache_path.exists():
                await aiofiles.os.remove(cache_path)
                return True
            
            return False
            
        except Exception:
            return False
    
    async def cache_exists(self, filename: str) -> bool:
        """
        检查缓存是否存在
        
        Args:
            filename: 文件名
            
        Returns:
            bool: 缓存是否存在
        """
        try:
            cache_path = self._get_cache_path(filename)
            return cache_path.exists()
        except Exception:
            return False
    
    async def clear_all_cache(self) -> int:
        """
        清空所有缓存
        
        Returns:
            int: 清理的文件数量
        """
        count = 0
        try:
            for cache_file in self.cache_dir.glob('*'):
                if cache_file.is_file():
                    await aiofiles.os.remove(cache_file)
                    count += 1
        except Exception:
            pass
        
        return count
    
    async def get_cache_stats(self) -> dict:
        """
        获取缓存统计信息
        
        Returns:
            dict: 缓存统计信息
        """
        try:
            total_files = 0
            total_size = 0
            
            for cache_file in self.cache_dir.glob('*'):
                if cache_file.is_file():
                    total_files += 1
                    total_size += cache_file.stat().st_size
            
            return {
                'total_files': total_files,
                'total_size_bytes': total_size,
                'total_size_mb': round(total_size / (1024 * 1024), 2),
                'cache_dir': str(self.cache_dir)
            }
            
        except Exception as e:
            return {
                'error': str(e),
                'cache_dir': str(self.cache_dir)
            }

"""
文件管理服务

提供Playbook文件的读写、上传、下载、删除等操作。
"""

import os
import hashlib
import shutil
import aiofiles
from pathlib import Path
from typing import List, Optional, Tuple, Dict, Any
from datetime import datetime

from ansible_web_ui.utils.timezone import now
from fastapi import UploadFile, HTTPException
from ansible_web_ui.core.config import get_settings


class FileService:
    """
    文件管理服务类
    
    负责处理Playbook文件的各种操作，包括安全检查和路径验证。
    """
    
    def __init__(self):
        """初始化文件服务"""
        self.settings = get_settings()
        self.playbook_dir = Path(self.settings.PLAYBOOK_DIR)
        self.upload_dir = Path(self.settings.UPLOAD_DIR)
        self.max_file_size = self.settings.MAX_PLAYBOOK_SIZE
        self.allowed_extensions = {'.yml', '.yaml'}
        
        # 确保目录存在
        self._ensure_directories()
    
    def _ensure_directories(self) -> None:
        """确保必要的目录存在"""
        self.playbook_dir.mkdir(parents=True, exist_ok=True)
        self.upload_dir.mkdir(parents=True, exist_ok=True)
    
    def _validate_filename(self, filename: str) -> None:
        """
        验证文件名的安全性
        
        Args:
            filename: 文件名
            
        Raises:
            HTTPException: 文件名不安全时抛出异常
        """
        # 检查是否为空或仅包含空格
        if not filename.strip():
            raise HTTPException(
                status_code=400,
                detail="文件名不能为空"
            )
        
        # 检查文件名长度
        if len(filename) > 255:
            raise HTTPException(
                status_code=400,
                detail="文件名过长，最大长度为255个字符"
            )
        
        # 检查文件名中的危险字符
        dangerous_chars = ['..', '/', '\\', ':', '*', '?', '"', '<', '>', '|']
        for char in dangerous_chars:
            if char in filename:
                raise HTTPException(
                    status_code=400,
                    detail=f"文件名包含不安全的字符: {char}"
                )
        
        # 检查文件扩展名
        file_path = Path(filename)
        if file_path.suffix.lower() not in self.allowed_extensions:
            raise HTTPException(
                status_code=400,
                detail=f"不支持的文件类型。仅支持: {', '.join(self.allowed_extensions)}"
            )
    
    def _get_safe_path(self, filename: str, base_dir: Path) -> Path:
        """
        获取安全的文件路径
        
        Args:
            filename: 文件名
            base_dir: 基础目录
            
        Returns:
            Path: 安全的文件路径
            
        Raises:
            HTTPException: 路径不安全时抛出异常
        """
        self._validate_filename(filename)
        
        # 构建完整路径
        file_path = base_dir / filename
        
        # 确保路径在基础目录内（防止路径遍历攻击）
        try:
            file_path.resolve().relative_to(base_dir.resolve())
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail="文件路径不安全"
            )
        
        return file_path
    
    async def _calculate_file_hash(self, file_path: Path) -> str:
        """
        计算文件的SHA256哈希值
        
        Args:
            file_path: 文件路径
            
        Returns:
            str: 文件哈希值
        """
        hash_sha256 = hashlib.sha256()
        
        async with aiofiles.open(file_path, 'rb') as f:
            while chunk := await f.read(8192):
                hash_sha256.update(chunk)
        
        return hash_sha256.hexdigest()
    
    async def read_file(self, file_path_str: str) -> str:
        """
        读取文件内容
        
        Args:
            file_path_str: 文件路径（可以是相对路径或绝对路径）
            
        Returns:
            str: 文件内容
            
        Raises:
            HTTPException: 文件不存在或读取失败时抛出异常
        """
        file_path = Path(file_path_str)
        
        if not file_path.exists():
            raise FileNotFoundError(f"文件不存在: {file_path_str}")
        
        if not file_path.is_file():
            raise ValueError(f"不是文件: {file_path_str}")
        
        try:
            # 读取文件内容
            async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
                content = await f.read()
            
            return content
            
        except UnicodeDecodeError:
            raise HTTPException(
                status_code=400,
                detail="文件编码错误，请确保文件为UTF-8编码"
            )
        except PermissionError:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"读取文件失败: {str(e)}"
            )
    
    async def write_file(self, file_path_str: str, content: str) -> Dict[str, Any]:
        """
        写入文件内容
        
        Args:
            file_path_str: 文件路径
            content: 文件内容
            
        Returns:
            Dict[str, Any]: 文件元数据信息
            
        Raises:
            HTTPException: 写入失败时抛出异常
        """
        # 如果是相对路径（只有文件名），使用 playbook_dir
        file_path = Path(file_path_str)
        if not file_path.is_absolute():
            file_path = self.playbook_dir / file_path_str
        
        # 检查内容大小
        content_size = len(content.encode('utf-8'))
        if content_size > self.max_file_size:
            raise HTTPException(
                status_code=413,
                detail=f"文件过大，最大允许大小为 {self.max_file_size} 字节"
            )
        
        try:
            # 确保父目录存在
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            # 如果文件已存在，先备份
            if file_path.exists():
                backup_path = file_path.with_suffix(f"{file_path.suffix}.backup")
                shutil.copy2(file_path, backup_path)
            
            # 写入文件
            async with aiofiles.open(file_path, 'w', encoding='utf-8') as f:
                await f.write(content)
            
            # 获取文件元数据
            stat = file_path.stat()
            file_hash = await self._calculate_file_hash(file_path)
            
            return {
                'file_path': str(file_path),
                'file_size': stat.st_size,
                'file_hash': file_hash
            }
            
        except PermissionError:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"写入文件失败: {str(e)}"
            )
    
    async def upload_file(self, file: UploadFile) -> Dict[str, Any]:
        """
        上传Playbook文件
        
        Args:
            file: 上传的文件对象
            
        Returns:
            Dict[str, Any]: 上传结果信息
            
        Raises:
            HTTPException: 上传失败时抛出异常
        """
        if not file.filename:
            raise HTTPException(
                status_code=400,
                detail="文件名不能为空"
            )
        
        # 验证文件名
        self._validate_filename(file.filename)
        
        # 检查文件大小
        if file.size and file.size > self.max_file_size:
            raise HTTPException(
                status_code=413,
                detail=f"文件过大，最大允许大小为 {self.max_file_size} 字节"
            )
        
        # 生成临时文件路径
        temp_path = self.upload_dir / f"temp_{now().strftime('%Y%m%d_%H%M%S')}_{file.filename}"
        final_path = self._get_safe_path(file.filename, self.playbook_dir)
        
        try:
            # 保存到临时位置
            async with aiofiles.open(temp_path, 'wb') as f:
                content = await file.read()
                
                # 再次检查文件大小
                if len(content) > self.max_file_size:
                    raise HTTPException(
                        status_code=413,
                        detail=f"文件过大，最大允许大小为 {self.max_file_size} 字节"
                    )
                
                await f.write(content)
            
            # 验证文件内容是否为有效的UTF-8编码
            try:
                async with aiofiles.open(temp_path, 'r', encoding='utf-8') as f:
                    await f.read()
            except UnicodeDecodeError:
                raise HTTPException(
                    status_code=400,
                    detail="文件编码错误，请确保文件为UTF-8编码"
                )
            
            # 移动到最终位置
            if final_path.exists():
                # 备份现有文件
                backup_path = final_path.with_suffix(f"{final_path.suffix}.backup")
                shutil.copy2(final_path, backup_path)
            
            shutil.move(temp_path, final_path)
            
            # 获取文件元数据
            stat = final_path.stat()
            metadata = {
                'filename': file.filename,
                'file_path': str(final_path),
                'file_size': stat.st_size,
                'upload_time': now(),
                'file_hash': await self._calculate_file_hash(final_path)
            }
            
            return metadata
            
        except HTTPException:
            # 清理临时文件
            if temp_path.exists():
                temp_path.unlink()
            raise
        except Exception as e:
            # 清理临时文件
            if temp_path.exists():
                temp_path.unlink()
            raise HTTPException(
                status_code=500,
                detail=f"上传文件失败: {str(e)}"
            )
    
    async def delete_file(self, filename: str) -> bool:
        """
        删除Playbook文件
        
        Args:
            filename: 文件名
            
        Returns:
            bool: 是否删除成功
            
        Raises:
            HTTPException: 删除失败时抛出异常
        """
        file_path = self._get_safe_path(filename, self.playbook_dir)
        
        if not file_path.exists():
            raise HTTPException(
                status_code=404,
                detail=f"文件不存在: {filename}"
            )
        
        try:
            # 创建备份
            backup_path = self.upload_dir / f"deleted_{now().strftime('%Y%m%d_%H%M%S')}_{filename}"
            shutil.copy2(file_path, backup_path)
            
            # 删除原文件
            file_path.unlink()
            
            return True
            
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"删除文件失败: {str(e)}"
            )
    
    async def list_files(self, path: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        列出指定路径下的文件和目录
        
        Args:
            path: 相对路径，None或空字符串表示playbooks根目录
        
        Returns:
            List[Dict[str, Any]]: 文件和目录信息列表
        """
        files = []
        
        try:
            # 确定目标目录
            if not path or path == "":
                target_dir = self.playbook_dir
            else:
                # 安全地构建路径
                target_dir = Path(path)
                # 确保路径存在且可访问
                if not target_dir.exists():
                    raise FileNotFoundError(f"路径不存在: {path}")
                if not target_dir.is_dir():
                    raise ValueError(f"不是目录: {path}")
            
            # 遍历目录
            for item_path in target_dir.iterdir():
                stat = item_path.stat()
                
                # 构建文件/目录信息
                file_info = {
                    'name': item_path.name,
                    'path': str(item_path),
                    'is_directory': item_path.is_dir(),
                    'size': stat.st_size if item_path.is_file() else 0,
                    'modified_time': datetime.fromtimestamp(stat.st_mtime).isoformat()
                }
                
                # 只包含目录或允许的文件类型
                if item_path.is_dir() or item_path.suffix.lower() in self.allowed_extensions:
                    files.append(file_info)
            
            # 排序：目录在前，然后按名称排序
            files.sort(key=lambda x: (not x['is_directory'], x['name'].lower()))
            
            return files
            
        except FileNotFoundError:
            raise
        except PermissionError:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"列出文件失败: {str(e)}"
            )
    
    async def file_exists(self, filename: str) -> bool:
        """
        检查文件是否存在
        
        Args:
            filename: 文件名
            
        Returns:
            bool: 文件是否存在
        """
        try:
            file_path = self._get_safe_path(filename, self.playbook_dir)
            return file_path.exists()
        except HTTPException:
            return False
    
    async def get_file_info(self, filename: str) -> Dict[str, Any]:
        """
        获取文件详细信息
        
        Args:
            filename: 文件名
            
        Returns:
            Dict[str, Any]: 文件详细信息
            
        Raises:
            HTTPException: 文件不存在时抛出异常
        """
        file_path = self._get_safe_path(filename, self.playbook_dir)
        
        if not file_path.exists():
            raise HTTPException(
                status_code=404,
                detail=f"文件不存在: {filename}"
            )
        
        try:
            stat = file_path.stat()
            
            file_info = {
                'filename': filename,
                'file_path': str(file_path),
                'file_size': stat.st_size,
                'last_modified': datetime.fromtimestamp(stat.st_mtime),
                'created': datetime.fromtimestamp(stat.st_ctime),
                'file_hash': await self._calculate_file_hash(file_path),
                'is_readable': os.access(file_path, os.R_OK),
                'is_writable': os.access(file_path, os.W_OK)
            }
            
            return file_info
            
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"获取文件信息失败: {str(e)}"
            )
    
    async def copy_file(self, source_filename: str, target_filename: str) -> Dict[str, Any]:
        """
        复制文件
        
        Args:
            source_filename: 源文件名
            target_filename: 目标文件名
            
        Returns:
            Dict[str, Any]: 复制结果信息
            
        Raises:
            HTTPException: 复制失败时抛出异常
        """
        source_path = self._get_safe_path(source_filename, self.playbook_dir)
        target_path = self._get_safe_path(target_filename, self.playbook_dir)
        
        if not source_path.exists():
            raise HTTPException(
                status_code=404,
                detail=f"源文件不存在: {source_filename}"
            )
        
        if target_path.exists():
            raise HTTPException(
                status_code=409,
                detail=f"目标文件已存在: {target_filename}"
            )
        
        try:
            shutil.copy2(source_path, target_path)
            
            # 获取目标文件信息
            stat = target_path.stat()
            result = {
                'source_filename': source_filename,
                'target_filename': target_filename,
                'target_path': str(target_path),
                'file_size': stat.st_size,
                'copy_time': now(),
                'file_hash': await self._calculate_file_hash(target_path)
            }
            
            return result
            
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"复制文件失败: {str(e)}"
            )
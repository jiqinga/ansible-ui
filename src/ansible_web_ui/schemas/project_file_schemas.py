"""
项目文件相关的Pydantic模式定义
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


class ProjectFileBase(BaseModel):
    """项目文件基础模式"""
    relative_path: str = Field(..., description="文件相对路径（相对于项目根目录）")
    filename: str = Field(..., description="文件名（从路径中提取）")
    file_size: int = Field(..., description="文件大小（字节）")
    is_directory: bool = Field(..., description="是否为目录")


class ProjectFileInfo(ProjectFileBase):
    """项目文件信息模式（包含ID和时间戳）"""
    id: int = Field(..., description="文件记录ID")
    project_id: int = Field(..., description="所属项目ID")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    
    class Config:
        from_attributes = True


class ProjectFileContent(ProjectFileInfo):
    """项目文件内容模式（包含完整内容和哈希值）"""
    file_content: str = Field(..., description="文件内容（UTF-8编码）")
    file_hash: Optional[str] = Field(None, description="文件哈希值（SHA-256）")


class FileTreeNode(BaseModel):
    """文件树节点模式"""
    name: str = Field(..., description="文件/目录名称")
    type: str = Field(..., description="类型：file 或 directory")
    path: str = Field(..., description="相对路径")
    size: int = Field(..., description="文件大小（字节，目录为0）")
    children: Optional[List['FileTreeNode']] = Field(None, description="子节点列表（仅目录有）")


# 更新前向引用以支持递归结构
FileTreeNode.model_rebuild()

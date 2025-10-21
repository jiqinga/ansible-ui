"""
基础服务类

提供通用的CRUD操作和数据库会话管理。
"""

from typing import Any, Dict, List, Optional, Type, TypeVar, Generic
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func
from sqlalchemy.orm import selectinload
from ansible_web_ui.models.base import BaseModel

# 泛型类型变量
ModelType = TypeVar("ModelType", bound=BaseModel)


class BaseService(Generic[ModelType]):
    """
    基础服务类，提供通用的CRUD操作
    """
    
    def __init__(self, model: Type[ModelType], db_session: AsyncSession):
        """
        初始化服务
        
        Args:
            model: 数据模型类
            db_session: 数据库会话
        """
        self.model = model
        self.db = db_session

    async def create(self, **kwargs) -> ModelType:
        """
        创建新记录
        
        Args:
            **kwargs: 模型字段值
            
        Returns:
            ModelType: 创建的模型实例
        """
        instance = self.model(**kwargs)
        self.db.add(instance)
        await self.db.commit()
        await self.db.refresh(instance)
        return instance

    async def get_by_id(self, id: int) -> Optional[ModelType]:
        """
        根据ID获取记录
        
        Args:
            id: 记录ID
            
        Returns:
            Optional[ModelType]: 模型实例或None
        """
        result = await self.db.execute(
            select(self.model).where(self.model.id == id)
        )
        return result.scalar_one_or_none()

    async def get_by_field(self, field_name: str, value: Any) -> Optional[ModelType]:
        """
        根据字段值获取记录
        
        Args:
            field_name: 字段名
            value: 字段值
            
        Returns:
            Optional[ModelType]: 模型实例或None
        """
        field = getattr(self.model, field_name)
        result = await self.db.execute(
            select(self.model).where(field == value)
        )
        return result.scalar_one_or_none()

    async def get_all(
        self, 
        skip: int = 0, 
        limit: int = 100,
        order_by: Optional[str] = None,
        desc: bool = False
    ) -> List[ModelType]:
        """
        获取所有记录（分页）
        
        Args:
            skip: 跳过的记录数
            limit: 限制返回的记录数
            order_by: 排序字段名
            desc: 是否降序排列
            
        Returns:
            List[ModelType]: 模型实例列表
        """
        query = select(self.model).offset(skip).limit(limit)
        
        if order_by:
            order_field = getattr(self.model, order_by, None)
            if order_field is not None:
                if desc:
                    query = query.order_by(order_field.desc())
                else:
                    query = query.order_by(order_field)
        
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_by_filters(
        self, 
        filters: Dict[str, Any],
        skip: int = 0,
        limit: int = 100,
        order_by: Optional[str] = None,
        desc: bool = False
    ) -> List[ModelType]:
        """
        根据过滤条件获取记录
        
        Args:
            filters: 过滤条件字典
            skip: 跳过的记录数
            limit: 限制返回的记录数
            order_by: 排序字段名
            desc: 是否降序排列
            
        Returns:
            List[ModelType]: 模型实例列表
        """
        query = select(self.model)
        
        # 应用过滤条件
        for field_name, value in filters.items():
            if hasattr(self.model, field_name):
                field = getattr(self.model, field_name)
                if isinstance(value, list):
                    query = query.where(field.in_(value))
                else:
                    query = query.where(field == value)
        
        # 应用排序
        if order_by and hasattr(self.model, order_by):
            order_field = getattr(self.model, order_by)
            if desc:
                query = query.order_by(order_field.desc())
            else:
                query = query.order_by(order_field)
        
        # 应用分页
        query = query.offset(skip).limit(limit)
        
        result = await self.db.execute(query)
        return result.scalars().all()

    async def update(self, id: int, **kwargs) -> Optional[ModelType]:
        """
        更新记录
        
        Args:
            id: 记录ID
            **kwargs: 要更新的字段值
            
        Returns:
            Optional[ModelType]: 更新后的模型实例或None
        """
        from sqlalchemy.orm import attributes
        
        # 先获取记录
        instance = await self.get_by_id(id)
        if not instance:
            return None
        
        # 更新字段
        for field, value in kwargs.items():
            if hasattr(instance, field):
                setattr(instance, field, value)
                # 对于JSON字段，需要显式标记为已修改
                # 这样SQLAlchemy才会保存更改
                attributes.flag_modified(instance, field)
        
        await self.db.commit()
        await self.db.refresh(instance)
        return instance

    async def delete(self, id: int) -> bool:
        """
        删除记录
        
        Args:
            id: 记录ID
            
        Returns:
            bool: 是否删除成功
        """
        result = await self.db.execute(
            delete(self.model).where(self.model.id == id)
        )
        await self.db.commit()
        return result.rowcount > 0

    async def count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """
        统计记录数量
        
        Args:
            filters: 过滤条件字典
            
        Returns:
            int: 记录数量
        """
        query = select(func.count(self.model.id))
        
        if filters:
            for field_name, value in filters.items():
                if hasattr(self.model, field_name):
                    field = getattr(self.model, field_name)
                    if isinstance(value, list):
                        query = query.where(field.in_(value))
                    else:
                        query = query.where(field == value)
        
        result = await self.db.execute(query)
        return result.scalar()

    async def exists(self, **kwargs) -> bool:
        """
        检查记录是否存在
        
        Args:
            **kwargs: 查询条件
            
        Returns:
            bool: 记录是否存在
        """
        query = select(self.model.id)
        
        for field_name, value in kwargs.items():
            if hasattr(self.model, field_name):
                field = getattr(self.model, field_name)
                query = query.where(field == value)
        
        result = await self.db.execute(query)
        return result.scalar_one_or_none() is not None

    async def bulk_create(self, items: List[Dict[str, Any]]) -> List[ModelType]:
        """
        批量创建记录
        
        Args:
            items: 要创建的记录数据列表
            
        Returns:
            List[ModelType]: 创建的模型实例列表
        """
        instances = [self.model(**item) for item in items]
        self.db.add_all(instances)
        await self.db.commit()
        
        # 刷新所有实例以获取生成的ID
        for instance in instances:
            await self.db.refresh(instance)
        
        return instances

    async def bulk_update(self, updates: List[Dict[str, Any]]) -> int:
        """
        批量更新记录
        
        Args:
            updates: 更新数据列表，每个字典必须包含'id'字段
            
        Returns:
            int: 更新的记录数量
        """
        updated_count = 0
        
        for update_data in updates:
            if 'id' not in update_data:
                continue
            
            record_id = update_data.pop('id')
            result = await self.db.execute(
                update(self.model)
                .where(self.model.id == record_id)
                .values(**update_data)
            )
            updated_count += result.rowcount
        
        await self.db.commit()
        return updated_count

    async def bulk_delete(self, ids: List[int]) -> int:
        """
        批量删除记录
        
        Args:
            ids: 要删除的记录ID列表
            
        Returns:
            int: 删除的记录数量
        """
        result = await self.db.execute(
            delete(self.model).where(self.model.id.in_(ids))
        )
        await self.db.commit()
        return result.rowcount

    async def get_paginated(
        self,
        page: int = 1,
        page_size: int = 20,
        filters: Optional[Dict[str, Any]] = None,
        search_fields: Optional[List[str]] = None,
        search_value: Optional[str] = None,
        order_by: Optional[str] = None,
        desc: bool = False
    ) -> List[ModelType]:
        """
        分页获取记录
        
        Args:
            page: 页码（从1开始）
            page_size: 每页大小
            filters: 过滤条件字典
            search_fields: 搜索字段列表
            search_value: 搜索值
            order_by: 排序字段名
            desc: 是否降序排列
            
        Returns:
            List[ModelType]: 模型实例列表
        """
        from sqlalchemy import or_
        
        query = select(self.model)
        
        # 应用过滤条件
        if filters:
            for field_name, value in filters.items():
                if hasattr(self.model, field_name):
                    field = getattr(self.model, field_name)
                    if isinstance(value, list):
                        query = query.where(field.in_(value))
                    else:
                        query = query.where(field == value)
        
        # 应用搜索条件
        if search_fields and search_value:
            search_conditions = []
            for field_name in search_fields:
                if hasattr(self.model, field_name):
                    field = getattr(self.model, field_name)
                    search_conditions.append(field.like(f"%{search_value}%"))
            
            if search_conditions:
                query = query.where(or_(*search_conditions))
        
        # 应用排序
        if order_by and hasattr(self.model, order_by):
            order_field = getattr(self.model, order_by)
            if desc:
                query = query.order_by(order_field.desc())
            else:
                query = query.order_by(order_field)
        
        # 应用分页
        skip = (page - 1) * page_size
        query = query.offset(skip).limit(page_size)
        
        result = await self.db.execute(query)
        return result.scalars().all()
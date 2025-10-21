"""
主机组服务

提供主机组管理相关的业务逻辑。
"""

import logging
from typing import Optional, List, Dict, Any, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, distinct, and_, or_

from ansible_web_ui.models.host_group import HostGroup
from ansible_web_ui.models.host import Host
from ansible_web_ui.services.base import BaseService

logger = logging.getLogger(__name__)


class HostGroupService(BaseService[HostGroup]):
    """
    主机组服务类
    
    提供主机组管理、层级关系、变量管理等功能。
    """
    
    def __init__(self, db_session: AsyncSession):
        super().__init__(HostGroup, db_session)

    async def create_group(
        self,
        name: str,
        display_name: Optional[str] = None,
        description: Optional[str] = None,
        parent_group: Optional[str] = None,
        variables: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None,
        sort_order: int = 0
    ) -> HostGroup:
        """
        创建新主机组
        
        Args:
            name: 组名
            display_name: 显示名称
            description: 组描述
            parent_group: 父组名
            variables: 组变量
            tags: 组标签
            sort_order: 排序顺序
            
        Returns:
            HostGroup: 创建的主机组对象
        """
        # 检查组名是否已存在
        existing = await self.get_by_name(name)
        if existing:
            raise ValueError(f"组名 '{name}' 已存在")
        
        # 检查父组是否存在
        if parent_group:
            parent = await self.get_by_name(parent_group)
            if not parent:
                raise ValueError(f"父组 '{parent_group}' 不存在")
        
        return await self.create(
            name=name,
            display_name=display_name or name,
            description=description,
            parent_group=parent_group,
            variables=variables or {},
            tags=tags or [],
            sort_order=sort_order
        )

    async def get_by_name(self, name: str) -> Optional[HostGroup]:
        """
        根据组名获取主机组
        
        Args:
            name: 组名
            
        Returns:
            Optional[HostGroup]: 主机组对象或None
        """
        return await self.get_by_field("name", name)

    async def ensure_default_groups(self) -> None:
        """
        确保默认组存在
        
        只创建 ungrouped 组，不创建 all 组
        """
        # 检查 ungrouped 组是否存在
        ungrouped = await self.get_by_name('ungrouped')
        if not ungrouped:
            await self.create_group(
                name='ungrouped',
                display_name='未分组',
                description='未分配到任何组的主机',
                sort_order=999  # 放在最后
            )
            logger.info("✅ 创建默认组: ungrouped")

    async def get_root_groups(self) -> List[HostGroup]:
        """
        获取所有根组（没有父组的组）
        
        Returns:
            List[HostGroup]: 根组列表
        """
        result = await self.db.execute(
            select(HostGroup)
            .where(HostGroup.parent_group.is_(None))
            .order_by(HostGroup.sort_order, HostGroup.name)
        )
        return result.scalars().all()

    async def get_child_groups(self, parent_name: str) -> List[HostGroup]:
        """
        获取指定组的子组
        
        Args:
            parent_name: 父组名
            
        Returns:
            List[HostGroup]: 子组列表
        """
        result = await self.db.execute(
            select(HostGroup)
            .where(HostGroup.parent_group == parent_name)
            .order_by(HostGroup.sort_order, HostGroup.name)
        )
        return result.scalars().all()

    async def get_group_tree(self) -> List[Dict[str, Any]]:
        """
        获取组的树形结构
        
        Returns:
            List[Dict[str, Any]]: 树形结构数据
        """
        # 获取所有组
        all_groups = await self.get_all()
        
        # 构建组映射
        group_map = {group.name: group for group in all_groups}
        
        # 构建树形结构
        async def build_tree(parent_name: Optional[str] = None) -> List[Dict[str, Any]]:
            tree = []
            for group in all_groups:
                if group.parent_group == parent_name:
                    # 获取主机数量
                    host_count = await self._get_group_host_count(group.name)
                    
                    node = {
                        'id': group.id,
                        'name': group.name,
                        'display_name': group.display_name,
                        'description': group.description,
                        'host_count': host_count,
                        'variables': group.get_variables(),
                        'tags': group.get_tags(),
                        'is_active': group.is_active,
                        'children': await build_tree(group.name)
                    }
                    tree.append(node)
            
            # 按排序顺序和名称排序
            tree.sort(key=lambda x: (
                group_map[x['name']].sort_order,
                x['name']
            ))
            
            return tree
        
        return await build_tree()

    async def _get_group_host_count(self, group_name: str) -> int:
        """
        获取组中的主机数量
        
        Args:
            group_name: 组名
            
        Returns:
            int: 主机数量
        """
        result = await self.db.execute(
            select(func.count(Host.id))
            .where(and_(Host.group_name == group_name, Host.is_active == True))
        )
        return result.scalar() or 0

    async def update_group_variables(self, group_id: int, variables: Dict[str, Any]) -> bool:
        """
        更新组变量
        
        Args:
            group_id: 组ID
            variables: 新的变量字典
            
        Returns:
            bool: 是否更新成功
        """
        group = await self.update(group_id, variables=variables)
        return group is not None

    async def add_group_variable(self, group_id: int, key: str, value: Any) -> bool:
        """
        添加组变量
        
        Args:
            group_id: 组ID
            key: 变量名
            value: 变量值
            
        Returns:
            bool: 是否添加成功
        """
        group = await self.get_by_id(group_id)
        if not group:
            return False
        
        group.add_variable(key, value)
        await self.db.commit()
        return True

    async def remove_group_variable(self, group_id: int, key: str) -> bool:
        """
        删除组变量
        
        Args:
            group_id: 组ID
            key: 变量名
            
        Returns:
            bool: 是否删除成功
        """
        group = await self.get_by_id(group_id)
        if not group:
            return False
        
        success = group.remove_variable(key)
        if success:
            await self.db.commit()
        return success

    async def update_group_tags(self, group_id: int, tags: List[str]) -> bool:
        """
        更新组标签
        
        Args:
            group_id: 组ID
            tags: 新的标签列表
            
        Returns:
            bool: 是否更新成功
        """
        group = await self.update(group_id, tags=tags)
        return group is not None

    async def move_group(self, group_id: int, new_parent: Optional[str]) -> bool:
        """
        移动组到新的父组
        
        Args:
            group_id: 组ID
            new_parent: 新父组名，None表示移动到根级别
            
        Returns:
            bool: 是否移动成功
        """
        group = await self.get_by_id(group_id)
        if not group:
            return False
        
        # 检查是否会形成循环引用
        if new_parent and await self._would_create_cycle(group.name, new_parent):
            raise ValueError("移动操作会形成循环引用")
        
        # 检查新父组是否存在
        if new_parent:
            parent = await self.get_by_name(new_parent)
            if not parent:
                raise ValueError(f"父组 '{new_parent}' 不存在")
        
        group.parent_group = new_parent
        await self.db.commit()
        return True

    async def _would_create_cycle(self, group_name: str, new_parent: str) -> bool:
        """
        检查移动操作是否会创建循环引用
        
        Args:
            group_name: 要移动的组名
            new_parent: 新父组名
            
        Returns:
            bool: 是否会创建循环引用
        """
        current = new_parent
        while current:
            if current == group_name:
                return True
            
            parent_group = await self.get_by_name(current)
            if not parent_group:
                break
            
            current = parent_group.parent_group
        
        return False

    async def delete_group(self, group_id: int, force: bool = False) -> bool:
        """
        删除主机组
        
        Args:
            group_id: 组ID
            force: 是否强制删除（即使有主机或子组）
            
        Returns:
            bool: 是否删除成功
        """
        group = await self.get_by_id(group_id)
        if not group:
            return False
        
        # 🔒 保护系统保留组，不允许删除
        PROTECTED_GROUPS = ['ungrouped']
        if group.name in PROTECTED_GROUPS:
            raise ValueError(f"系统保留组 '{group.name}' 不允许删除")
        
        if not force:
            # 检查是否有主机
            host_count = await self._get_group_host_count(group.name)
            if host_count > 0:
                raise ValueError(f"组 '{group.name}' 中还有 {host_count} 个主机，无法删除")
            
            # 检查是否有子组
            child_groups = await self.get_child_groups(group.name)
            if child_groups:
                raise ValueError(f"组 '{group.name}' 还有子组，无法删除")
        else:
            # 强制删除：将子组移动到父组，将主机移动到ungrouped
            child_groups = await self.get_child_groups(group.name)
            for child in child_groups:
                child.parent_group = group.parent_group
            
            # 移动主机到ungrouped组
            result = await self.db.execute(
                select(Host).where(Host.group_name == group.name)
            )
            hosts = result.scalars().all()
            for host in hosts:
                host.group_name = "ungrouped"
            
            await self.db.commit()
        
        return await self.delete(group_id)

    async def get_groups_by_tags(self, tags: List[str]) -> List[HostGroup]:
        """
        根据标签获取组列表
        
        Args:
            tags: 标签列表
            
        Returns:
            List[HostGroup]: 包含任一标签的组列表
        """
        result = await self.db.execute(
            select(HostGroup).where(HostGroup.tags.op("@>")(tags))
        )
        return result.scalars().all()

    async def search_groups(self, query: str) -> List[HostGroup]:
        """
        搜索主机组
        
        Args:
            query: 搜索关键词
            
        Returns:
            List[HostGroup]: 匹配的组列表
        """
        result = await self.db.execute(
            select(HostGroup).where(
                or_(
                    HostGroup.name.contains(query),
                    HostGroup.display_name.contains(query),
                    HostGroup.description.contains(query)
                )
            ).order_by(HostGroup.name)
        )
        return result.scalars().all()

    async def get_group_stats(self) -> Dict[str, Any]:
        """
        获取组统计信息
        
        Returns:
            Dict[str, Any]: 统计信息
        """
        total_groups = await self.count()
        active_groups = await self.count({"is_active": True})
        root_groups = len(await self.get_root_groups())
        
        # 获取各组的主机数量
        result = await self.db.execute(
            select(Host.group_name, func.count(Host.id))
            .where(Host.is_active == True)
            .group_by(Host.group_name)
        )
        host_counts = dict(result.all())
        
        return {
            "total_groups": total_groups,
            "active_groups": active_groups,
            "inactive_groups": total_groups - active_groups,
            "root_groups": root_groups,
            "groups_with_hosts": len([count for count in host_counts.values() if count > 0]),
            "empty_groups": total_groups - len([count for count in host_counts.values() if count > 0]),
            "host_counts_by_group": host_counts
        }

    async def ensure_default_groups(self) -> None:
        """
        确保默认组存在
        """
        default_groups = [
            {
                'name': 'ungrouped',
                'display_name': '未分组',
                'description': '默认的未分组主机组',
                'variables': {}
            }
        ]
        
        for group_data in default_groups:
            existing = await self.get_by_name(group_data['name'])
            if not existing:
                try:
                    await self.create(**group_data)
                except Exception as e:
                    # 如果是唯一约束错误，说明组已存在（并发创建），忽略错误
                    if 'UNIQUE constraint failed' in str(e) or 'already exists' in str(e).lower():
                        logger.debug(f"默认组 {group_data['name']} 已存在，跳过创建")
                        continue
                    # 其他错误则抛出
                    raise

    async def get_group_hierarchy_path(self, group_name: str) -> List[str]:
        """
        获取组的层级路径
        
        Args:
            group_name: 组名
            
        Returns:
            List[str]: 从根到当前组的路径
        """
        path = []
        current = group_name
        
        while current:
            path.insert(0, current)
            group = await self.get_by_name(current)
            if not group:
                break
            current = group.parent_group
        
        return path

    async def get_all_descendant_groups(self, group_name: str) -> List[HostGroup]:
        """
        获取指定组的所有后代组
        
        Args:
            group_name: 组名
            
        Returns:
            List[HostGroup]: 所有后代组列表
        """
        descendants = []
        
        async def collect_descendants(parent_name: str):
            children = await self.get_child_groups(parent_name)
            for child in children:
                descendants.append(child)
                await collect_descendants(child.name)
        
        await collect_descendants(group_name)
        return descendants

    async def get_group_stats(self) -> Dict[str, Any]:
        """
        获取主机组统计信息
        
        Returns:
            Dict[str, Any]: 统计信息
        """
        from sqlalchemy import select, func
        from ansible_web_ui.models.host import Host
        
        # 获取总组数
        total_groups = await self.count()
        
        # 获取活跃组数
        active_groups = await self.count({"is_active": True})
        
        # 获取每个组的主机数量
        query = select(
            Host.group_name,
            func.count(Host.id).label('host_count')
        ).where(
            Host.is_active == True
        ).group_by(Host.group_name)
        
        result = await self.db.execute(query)
        rows = result.all()
        
        group_host_counts = {row.group_name: row.host_count for row in rows}
        
        return {
            "total_groups": total_groups,
            "active_groups": active_groups,
            "inactive_groups": total_groups - active_groups,
            "group_host_counts": group_host_counts
        }

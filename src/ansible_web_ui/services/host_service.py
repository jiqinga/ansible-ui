"""
主机服务

提供主机清单管理相关的业务逻辑。
"""

from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, distinct

from ansible_web_ui.models.host import Host
from ansible_web_ui.services.base import BaseService


class HostService(BaseService[Host]):
    """
    主机服务类
    
    提供主机管理、分组、连接测试等功能。
    """
    
    def __init__(self, db_session: AsyncSession):
        super().__init__(Host, db_session)

    async def create_host(
        self,
        hostname: str,
        ansible_host: str,
        group_name: str = "ungrouped",
        display_name: Optional[str] = None,
        description: Optional[str] = None,
        ansible_port: int = 22,
        ansible_user: Optional[str] = None,
        ansible_ssh_private_key_file: Optional[str] = None,
        ansible_become: bool = False,
        ansible_become_user: str = "root",
        ansible_become_method: str = "sudo",
        is_active: bool = True,
        variables: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None
    ) -> Host:
        """
        创建新主机
        
        Args:
            hostname: 主机名
            ansible_host: Ansible连接地址
            group_name: 主机组名
            display_name: 显示名称
            description: 主机描述
            ansible_port: SSH端口
            ansible_user: SSH用户名
            ansible_ssh_private_key_file: SSH私钥文件路径
            ansible_become: 是否使用sudo提权
            ansible_become_user: 提权用户
            ansible_become_method: 提权方法 (sudo/su/doas)
            is_active: 是否激活主机
            variables: 主机变量
            tags: 主机标签
            
        Returns:
            Host: 创建的主机对象
        """
        return await self.create(
            hostname=hostname,
            display_name=display_name or hostname,
            description=description,
            group_name=group_name,
            ansible_host=ansible_host,
            ansible_port=ansible_port,
            ansible_user=ansible_user,
            ansible_ssh_private_key_file=ansible_ssh_private_key_file,
            ansible_become=ansible_become,
            ansible_become_user=ansible_become_user,
            ansible_become_method=ansible_become_method,
            is_active=is_active,
            variables=variables or {},
            tags=tags or []
        )

    async def get_by_hostname(self, hostname: str) -> Optional[Host]:
        """
        根据主机名获取主机
        
        Args:
            hostname: 主机名
            
        Returns:
            Optional[Host]: 主机对象或None
        """
        return await self.get_by_field("hostname", hostname)

    async def get_hosts_by_group(self, group_name: str) -> List[Host]:
        """
        根据组名获取主机列表
        
        Args:
            group_name: 组名
            
        Returns:
            List[Host]: 主机列表
        """
        return await self.get_by_filters({"group_name": group_name})

    async def get_active_hosts(self) -> List[Host]:
        """
        获取所有激活的主机
        
        Returns:
            List[Host]: 激活的主机列表
        """
        return await self.get_by_filters({"is_active": True})

    async def get_hosts_by_tags(self, tags: List[str]) -> List[Host]:
        """
        根据标签获取主机列表
        
        Args:
            tags: 标签列表
            
        Returns:
            List[Host]: 包含任一标签的主机列表
        """
        result = await self.db.execute(
            select(Host).where(Host.tags.op("@>")(tags))
        )
        return result.scalars().all()

    async def search_hosts(self, query: str) -> List[Host]:
        """
        搜索主机
        
        Args:
            query: 搜索关键词
            
        Returns:
            List[Host]: 匹配的主机列表
        """
        result = await self.db.execute(
            select(Host).where(
                Host.hostname.contains(query) |
                Host.display_name.contains(query) |
                Host.ansible_host.contains(query) |
                Host.description.contains(query)
            )
        )
        return result.scalars().all()

    async def get_all_groups(self) -> List[str]:
        """
        获取所有主机组名
        
        Returns:
            List[str]: 组名列表
        """
        result = await self.db.execute(
            select(distinct(Host.group_name)).order_by(Host.group_name)
        )
        return result.scalars().all()

    async def get_group_stats(self) -> Dict[str, int]:
        """
        获取各组的主机数量统计
        
        Returns:
            Dict[str, int]: 组名到主机数量的映射
        """
        result = await self.db.execute(
            select(Host.group_name, func.count(Host.id))
            .group_by(Host.group_name)
            .order_by(Host.group_name)
        )
        return dict(result.all())

    async def update_host_variables(self, host_id: int, variables: Dict[str, Any]) -> bool:
        """
        更新主机变量
        
        Args:
            host_id: 主机ID
            variables: 新的变量字典
            
        Returns:
            bool: 是否更新成功
        """
        host = await self.update(host_id, variables=variables)
        return host is not None

    async def add_host_variable(self, host_id: int, key: str, value: Any) -> bool:
        """
        添加主机变量
        
        Args:
            host_id: 主机ID
            key: 变量名
            value: 变量值
            
        Returns:
            bool: 是否添加成功
        """
        host = await self.get_by_id(host_id)
        if not host:
            return False
        
        host.add_variable(key, value)
        await self.db.commit()
        return True

    async def remove_host_variable(self, host_id: int, key: str) -> bool:
        """
        删除主机变量
        
        Args:
            host_id: 主机ID
            key: 变量名
            
        Returns:
            bool: 是否删除成功
        """
        host = await self.get_by_id(host_id)
        if not host:
            return False
        
        success = host.remove_variable(key)
        if success:
            await self.db.commit()
        return success

    async def update_host_tags(self, host_id: int, tags: List[str]) -> bool:
        """
        更新主机标签
        
        Args:
            host_id: 主机ID
            tags: 新的标签列表
            
        Returns:
            bool: 是否更新成功
        """
        host = await self.update(host_id, tags=tags)
        return host is not None

    async def add_host_tag(self, host_id: int, tag: str) -> bool:
        """
        添加主机标签
        
        Args:
            host_id: 主机ID
            tag: 标签名
            
        Returns:
            bool: 是否添加成功
        """
        host = await self.get_by_id(host_id)
        if not host:
            return False
        
        host.add_tag(tag)
        await self.db.commit()
        return True

    async def remove_host_tag(self, host_id: int, tag: str) -> bool:
        """
        删除主机标签
        
        Args:
            host_id: 主机ID
            tag: 标签名
            
        Returns:
            bool: 是否删除成功
        """
        host = await self.get_by_id(host_id)
        if not host:
            return False
        
        success = host.remove_tag(tag)
        if success:
            await self.db.commit()
        return success

    async def move_host_to_group(self, host_id: int, new_group: str) -> bool:
        """
        将主机移动到新组
        
        Args:
            host_id: 主机ID
            new_group: 新组名
            
        Returns:
            bool: 是否移动成功
        """
        host = await self.update(host_id, group_name=new_group)
        return host is not None

    async def update_ping_status(self, host_id: int, status: str) -> bool:
        """
        更新主机ping状态
        
        Args:
            host_id: 主机ID
            status: ping状态 (success/failed/unknown)
            
        Returns:
            bool: 是否更新成功
        """
        host = await self.get_by_id(host_id)
        if not host:
            return False
        
        host.update_ping_status(status)
        await self.db.commit()
        return True

    async def get_reachable_hosts(self) -> List[Host]:
        """
        获取可达的主机列表
        
        Returns:
            List[Host]: 可达的主机列表
        """
        return await self.get_by_filters({"ping_status": "success"})

    async def get_unreachable_hosts(self) -> List[Host]:
        """
        获取不可达的主机列表
        
        Returns:
            List[Host]: 不可达的主机列表
        """
        return await self.get_by_filters({"ping_status": "failed"})

    async def generate_ansible_inventory(self, group_name: Optional[str] = None) -> Dict[str, Any]:
        """
        生成Ansible inventory格式的数据
        
        Args:
            group_name: 可选的组名，如果指定则只返回该组的主机
            
        Returns:
            Dict[str, Any]: Ansible inventory格式的字典
        """
        if group_name:
            hosts = await self.get_hosts_by_group(group_name)
        else:
            hosts = await self.get_active_hosts()
        
        inventory = {"_meta": {"hostvars": {}}}
        
        # 按组组织主机
        groups = {}
        for host in hosts:
            group = host.group_name
            if group not in groups:
                groups[group] = {"hosts": []}
            
            groups[group]["hosts"].append(host.hostname)
            inventory["_meta"]["hostvars"][host.hostname] = host.get_ansible_inventory_dict()
        
        # 添加组信息到inventory
        inventory.update(groups)
        
        return inventory

    async def get_host_stats(self) -> Dict[str, Any]:
        """
        获取主机统计信息
        
        Returns:
            Dict[str, Any]: 统计信息
        """
        total_hosts = await self.count()
        active_hosts = await self.count({"is_active": True})
        reachable_hosts = await self.count({"ping_status": "success"})
        unreachable_hosts = await self.count({"ping_status": "failed"})
        
        group_stats = await self.get_group_stats()
        
        return {
            "total_hosts": total_hosts,
            "active_hosts": active_hosts,
            "inactive_hosts": total_hosts - active_hosts,
            "reachable_hosts": reachable_hosts,
            "unreachable_hosts": unreachable_hosts,
            "unknown_status_hosts": total_hosts - reachable_hosts - unreachable_hosts,
            "total_groups": len(group_stats),
            "group_stats": group_stats
        }

    async def get_group_stats(self) -> Dict[str, int]:
        """
        获取各组的主机数量统计
        
        Returns:
            Dict[str, int]: 组名到主机数量的映射
        """
        from sqlalchemy import select, func
        
        # 查询每个组的主机数量
        query = select(
            Host.group_name,
            func.count(Host.id).label('count')
        ).where(
            Host.is_active == True
        ).group_by(Host.group_name)
        
        result = await self.db.execute(query)
        rows = result.all()
        
        # 转换为字典
        group_stats = {row.group_name: row.count for row in rows}
        
        return group_stats

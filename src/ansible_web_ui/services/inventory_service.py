"""
Inventory服务

提供完整的Ansible inventory管理功能，整合主机和主机组管理。
"""

import os
import json
from typing import Optional, List, Dict, Any, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from pathlib import Path

from ansible_web_ui.models.host import Host
from ansible_web_ui.models.host_group import HostGroup
from ansible_web_ui.services.host_service import HostService
from ansible_web_ui.services.host_group_service import HostGroupService
from ansible_web_ui.utils.serialization import (
    generate_ansible_inventory_ini,
    generate_ansible_inventory_yaml,
    generate_ansible_inventory_json,
    parse_ansible_inventory_ini,
    import_inventory_from_content,
    export_inventory_to_file
)
from ansible_web_ui.utils.validation import (
    validate_hostname,
    validate_ansible_host,
    validate_group_name,
    validate_ansible_variables
)


class InventoryService:
    """
    Inventory服务类
    
    提供完整的Ansible inventory管理功能。
    """
    
    def __init__(self, db_session: AsyncSession, inventory_dir: str = "./inventory"):
        self.db = db_session
        self.host_service = HostService(db_session)
        self.group_service = HostGroupService(db_session)
        self.inventory_dir = Path(inventory_dir)
        self.inventory_dir.mkdir(exist_ok=True)

    async def initialize(self) -> None:
        """
        初始化inventory服务，创建默认组等
        """
        await self.group_service.ensure_default_groups()

    # 主机管理方法
    async def add_host(
        self,
        hostname: str,
        ansible_host: str,
        group_name: str = "ungrouped",
        **kwargs
    ) -> Host:
        """
        添加主机到inventory
        
        Args:
            hostname: 主机名
            ansible_host: Ansible连接地址
            group_name: 主机组名
            **kwargs: 其他主机参数
            
        Returns:
            Host: 创建的主机对象
        """
        # 验证输入
        is_valid, error = validate_hostname(hostname)
        if not is_valid:
            raise ValueError(f"主机名无效: {error}")
        
        is_valid, error = validate_ansible_host(ansible_host)
        if not is_valid:
            raise ValueError(f"Ansible主机地址无效: {error}")
        
        is_valid, error = validate_group_name(group_name)
        if not is_valid:
            raise ValueError(f"组名无效: {error}")
        
        # 确保组存在
        await self._ensure_group_exists(group_name)
        
        # 创建主机
        host = await self.host_service.create_host(
            hostname=hostname,
            ansible_host=ansible_host,
            group_name=group_name,
            **kwargs
        )
        
        # 生成inventory文件
        await self._generate_inventory_files()
        
        return host

    async def update_host(self, host_id: int, **kwargs) -> Optional[Host]:
        """
        更新主机信息
        
        Args:
            host_id: 主机ID
            **kwargs: 更新的字段
            
        Returns:
            Optional[Host]: 更新后的主机对象
        """
        # 验证组名（如果有更新）
        if 'group_name' in kwargs:
            is_valid, error = validate_group_name(kwargs['group_name'])
            if not is_valid:
                raise ValueError(f"组名无效: {error}")
            await self._ensure_group_exists(kwargs['group_name'])
        
        # 验证变量（如果有更新）
        if 'variables' in kwargs:
            is_valid, errors = validate_ansible_variables(kwargs['variables'])
            if not is_valid:
                raise ValueError(f"变量无效: {'; '.join(errors)}")
        
        host = await self.host_service.update(host_id, **kwargs)
        
        if host:
            await self._generate_inventory_files()
        
        return host

    async def remove_host(self, host_id: int) -> bool:
        """
        从inventory中删除主机
        
        Args:
            host_id: 主机ID
            
        Returns:
            bool: 是否删除成功
        """
        success = await self.host_service.delete(host_id)
        
        if success:
            await self._generate_inventory_files()
        
        return success

    async def get_host(self, host_id: int) -> Optional[Host]:
        """
        获取主机信息
        
        Args:
            host_id: 主机ID
            
        Returns:
            Optional[Host]: 主机对象
        """
        return await self.host_service.get_by_id(host_id)

    async def get_host_by_name(self, hostname: str) -> Optional[Host]:
        """
        根据主机名获取主机
        
        Args:
            hostname: 主机名
            
        Returns:
            Optional[Host]: 主机对象
        """
        return await self.host_service.get_by_hostname(hostname)

    async def get_hosts_count_fast(
        self,
        group_name: Optional[str] = None,
        active_only: bool = True
    ) -> int:
        """
        快速获取主机数量（优化：只count，不查询数据）
        
        Args:
            group_name: 可选的组名筛选
            active_only: 是否只统计激活的主机
            
        Returns:
            int: 主机数量
        """
        from sqlalchemy import select, func
        from ansible_web_ui.models.host import Host
        from ansible_web_ui.core.cache import get_cache
        
        # 生成缓存key
        cache_key = f"hosts_count:{group_name}:{active_only}"
        
        # 尝试从缓存获取
        cache = get_cache()
        cached_count = cache.get(cache_key)
        if cached_count is not None:
            return cached_count
        
        # 构建count查询
        count_query = select(func.count(Host.id))
        
        if group_name:
            count_query = count_query.where(Host.group_name == group_name)
        
        if active_only:
            count_query = count_query.where(Host.is_active == True)
        
        result = await self.db.execute(count_query)
        count = result.scalar() or 0
        
        # 缓存结果
        cache.set(cache_key, count, ttl=60)
        
        return count
    
    async def list_hosts(
        self,
        group_name: Optional[str] = None,
        active_only: bool = True
    ) -> List[Host]:
        """
        列出主机
        
        Args:
            group_name: 可选的组名筛选
            active_only: 是否只返回激活的主机
            
        Returns:
            List[Host]: 主机列表
        """
        if group_name:
            hosts = await self.host_service.get_hosts_by_group(group_name)
        elif active_only:
            hosts = await self.host_service.get_active_hosts()
        else:
            hosts = await self.host_service.get_all()
        
        return hosts

    # 主机组管理方法
    async def add_group(
        self,
        name: str,
        display_name: Optional[str] = None,
        description: Optional[str] = None,
        parent_group: Optional[str] = None,
        variables: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None,
        **kwargs
    ) -> HostGroup:
        """
        添加主机组
        
        Args:
            name: 组名
            display_name: 显示名称
            description: 描述
            parent_group: 父组名
            variables: 组变量
            tags: 组标签
            **kwargs: 其他参数
            
        Returns:
            HostGroup: 创建的主机组对象
        """
        # 验证输入
        is_valid, error = validate_group_name(name)
        if not is_valid:
            raise ValueError(f"组名无效: {error}")
        
        if variables:
            is_valid, errors = validate_ansible_variables(variables)
            if not is_valid:
                raise ValueError(f"变量无效: {'; '.join(errors)}")
        
        group = await self.group_service.create_group(
            name=name,
            display_name=display_name,
            description=description,
            parent_group=parent_group,
            variables=variables,
            tags=tags
        )
        
        await self._generate_inventory_files()
        
        return group

    async def update_group(self, group_id: int, **kwargs) -> Optional[HostGroup]:
        """
        更新主机组
        
        Args:
            group_id: 组ID
            **kwargs: 更新的字段
            
        Returns:
            Optional[HostGroup]: 更新后的组对象
        """
        # 验证变量（如果有更新）
        if 'variables' in kwargs:
            is_valid, errors = validate_ansible_variables(kwargs['variables'])
            if not is_valid:
                raise ValueError(f"变量无效: {'; '.join(errors)}")
        
        group = await self.group_service.update(group_id, **kwargs)
        
        if group:
            await self._generate_inventory_files()
        
        return group

    async def remove_group(self, group_id: int, force: bool = False) -> bool:
        """
        删除主机组
        
        Args:
            group_id: 组ID
            force: 是否强制删除
            
        Returns:
            bool: 是否删除成功
        """
        success = await self.group_service.delete_group(group_id, force=force)
        
        if success:
            await self._generate_inventory_files()
        
        return success

    async def get_group(self, group_id: int) -> Optional[HostGroup]:
        """
        获取主机组信息
        
        Args:
            group_id: 组ID
            
        Returns:
            Optional[HostGroup]: 主机组对象
        """
        return await self.group_service.get_by_id(group_id)

    async def get_group_by_name(self, name: str) -> Optional[HostGroup]:
        """
        根据组名获取主机组
        
        Args:
            name: 组名
            
        Returns:
            Optional[HostGroup]: 主机组对象
        """
        return await self.group_service.get_by_name(name)

    async def list_groups(self) -> List[HostGroup]:
        """
        列出所有主机组
        
        Returns:
            List[HostGroup]: 主机组列表
        """
        return await self.group_service.get_all()

    async def get_group_tree(self) -> List[Dict[str, Any]]:
        """
        获取主机组树形结构
        
        Returns:
            List[Dict[str, Any]]: 树形结构数据
        """
        return await self.group_service.get_group_tree()

    # Inventory生成和管理方法
    async def generate_inventory(self, format_type: str = "json") -> Dict[str, Any]:
        """
        生成Ansible inventory数据
        
        Args:
            format_type: 格式类型 (json/yaml/ini)
            
        Returns:
            Dict[str, Any]: inventory数据
        """
        hosts = await self.list_hosts(active_only=True)
        groups = await self.list_groups()
        
        # 转换为字典格式
        hosts_data = []
        for host in hosts:
            host_dict = {
                'hostname': host.hostname,
                'group_name': host.group_name,
                'ansible_host': host.ansible_host,
                'ansible_port': host.ansible_port,
                'ansible_user': host.ansible_user,
                'ansible_ssh_private_key_file': host.ansible_ssh_private_key_file,
                'ansible_become': host.ansible_become,
                'ansible_become_user': host.ansible_become_user,
                'ansible_become_method': host.ansible_become_method,
                'variables': host.get_variables(),
                'is_active': host.is_active
            }
            hosts_data.append(host_dict)
        
        groups_data = []
        for group in groups:
            group_dict = {
                'name': group.name,
                'variables': group.get_variables()
            }
            groups_data.append(group_dict)
        
        if format_type.lower() == "json":
            inventory_content = generate_ansible_inventory_json(hosts_data, groups_data)
            return json.loads(inventory_content)
        elif format_type.lower() == "yaml":
            return generate_ansible_inventory_yaml(hosts_data, groups_data)
        elif format_type.lower() == "ini":
            return generate_ansible_inventory_ini(hosts_data, groups_data)
        else:
            raise ValueError(f"不支持的格式类型: {format_type}")

    async def export_inventory(self, format_type: str = "ini") -> str:
        """
        导出inventory到指定格式
        
        Args:
            format_type: 导出格式 (ini/yaml/json)
            
        Returns:
            str: 导出的内容
        """
        hosts = await self.list_hosts(active_only=True)
        groups = await self.list_groups()
        
        # 转换为字典格式
        hosts_data = []
        for host in hosts:
            host_dict = {
                'hostname': host.hostname,
                'group_name': host.group_name,
                'ansible_host': host.ansible_host,
                'ansible_port': host.ansible_port,
                'ansible_user': host.ansible_user,
                'ansible_ssh_private_key_file': host.ansible_ssh_private_key_file,
                'ansible_become': host.ansible_become,
                'ansible_become_user': host.ansible_become_user,
                'ansible_become_method': host.ansible_become_method,
                'variables': host.get_variables(),
                'is_active': host.is_active
            }
            hosts_data.append(host_dict)
        
        groups_data = []
        for group in groups:
            group_dict = {
                'name': group.name,
                'variables': group.get_variables()
            }
            groups_data.append(group_dict)
        
        return export_inventory_to_file(hosts_data, groups_data, format_type)

    async def import_inventory(
        self,
        content: str,
        format_type: str = "ini",
        merge_mode: str = "replace"
    ) -> Tuple[int, int]:
        """
        导入inventory数据
        
        Args:
            content: inventory内容
            format_type: 格式类型 (ini/yaml/json)
            merge_mode: 合并模式 (replace/merge/append)
            
        Returns:
            Tuple[int, int]: (导入的主机数, 导入的组数)
        """
        # 解析导入内容
        hosts_data, groups_data = import_inventory_from_content(content, format_type)
        
        imported_hosts = 0
        imported_groups = 0
        
        if merge_mode == "replace":
            # 清空现有数据
            await self._clear_inventory()
        
        # 导入组
        for group_data in groups_data:
            try:
                existing_group = await self.get_group_by_name(group_data['name'])
                
                if existing_group:
                    if merge_mode == "merge":
                        # 合并变量
                        existing_vars = existing_group.get_variables()
                        new_vars = group_data.get('variables', {})
                        existing_vars.update(new_vars)
                        await self.group_service.update_group_variables(
                            existing_group.id, existing_vars
                        )
                else:
                    await self.add_group(
                        name=group_data['name'],
                        variables=group_data.get('variables', {})
                    )
                    imported_groups += 1
            except Exception as e:
                # 记录错误但继续处理
                print(f"导入组 {group_data['name']} 失败: {str(e)}")
        
        # 导入主机
        for host_data in hosts_data:
            try:
                existing_host = await self.get_host_by_name(host_data['hostname'])
                
                if existing_host:
                    if merge_mode == "merge":
                        # 合并变量
                        existing_vars = existing_host.get_variables()
                        new_vars = host_data.get('variables', {})
                        existing_vars.update(new_vars)
                        
                        # 更新主机信息
                        update_data = {
                            'ansible_host': host_data.get('ansible_host', existing_host.ansible_host),
                            'group_name': host_data.get('group_name', existing_host.group_name),
                            'variables': existing_vars
                        }
                        await self.update_host(existing_host.id, **update_data)
                else:
                    await self.add_host(
                        hostname=host_data['hostname'],
                        ansible_host=host_data.get('ansible_host', host_data['hostname']),
                        group_name=host_data.get('group_name', 'ungrouped'),
                        ansible_port=host_data.get('ansible_port', 22),
                        ansible_user=host_data.get('ansible_user'),
                        ansible_ssh_private_key_file=host_data.get('ansible_ssh_private_key_file'),
                        ansible_become=host_data.get('ansible_become', False),
                        ansible_become_user=host_data.get('ansible_become_user', 'root'),
                        ansible_become_method=host_data.get('ansible_become_method', 'sudo'),
                        variables=host_data.get('variables', {})
                    )
                    imported_hosts += 1
            except Exception as e:
                # 记录错误但继续处理
                print(f"导入主机 {host_data['hostname']} 失败: {str(e)}")
        
        return imported_hosts, imported_groups

    async def get_inventory_stats(self) -> Dict[str, Any]:
        """
        获取inventory统计信息
        
        Returns:
            Dict[str, Any]: 统计信息
        """
        host_stats = await self.host_service.get_host_stats()
        group_stats = await self.group_service.get_group_stats()
        
        return {
            **host_stats,
            **group_stats,
            "inventory_files": self._get_inventory_files_info()
        }

    # 私有辅助方法
    async def _ensure_group_exists(self, group_name: str) -> None:
        """
        确保组存在，如果不存在则创建
        
        Args:
            group_name: 组名
        """
        existing = await self.get_group_by_name(group_name)
        if not existing:
            await self.group_service.create_group(
                name=group_name,
                display_name=group_name,
                description=f"自动创建的组: {group_name}"
            )

    async def _generate_inventory_files(self) -> None:
        """
        生成inventory文件到磁盘
        """
        try:
            # 生成不同格式的inventory文件
            formats = ["ini", "yaml", "json"]
            
            for format_type in formats:
                content = await self.export_inventory(format_type)
                
                if format_type == "ini":
                    file_path = self.inventory_dir / "hosts.ini"
                elif format_type == "yaml":
                    file_path = self.inventory_dir / "hosts.yml"
                else:  # json
                    file_path = self.inventory_dir / "hosts.json"
                
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
        
        except Exception as e:
            # 记录错误但不中断操作
            print(f"生成inventory文件失败: {str(e)}")

    async def _clear_inventory(self) -> None:
        """
        清空inventory数据
        """
        # 删除所有主机
        hosts = await self.list_hosts(active_only=False)
        for host in hosts:
            await self.host_service.delete(host.id)
        
        # 删除非默认组
        groups = await self.list_groups()
        for group in groups:
            if group.name not in ['ungrouped', 'all']:
                await self.group_service.delete(group.id)

    def _get_inventory_files_info(self) -> Dict[str, Any]:
        """
        获取inventory文件信息
        
        Returns:
            Dict[str, Any]: 文件信息
        """
        files_info = {}
        
        for file_name in ["hosts.ini", "hosts.yml", "hosts.json"]:
            file_path = self.inventory_dir / file_name
            if file_path.exists():
                stat = file_path.stat()
                files_info[file_name] = {
                    "exists": True,
                    "size": stat.st_size,
                    "modified": stat.st_mtime
                }
            else:
                files_info[file_name] = {"exists": False}
        
        return files_info

    # 主机连接测试方法
    async def ping_host(self, host_id: int) -> Dict[str, Any]:
        """
        测试主机SSH连接（使用paramiko库）
        
        Args:
            host_id: 主机ID
            
        Returns:
            Dict[str, Any]: 包含连接测试结果和详细信息的字典
                - success: bool - 是否成功
                - message: str - 详细信息
                - error_type: str - 错误类型（如果失败）
                - details: str - 详细错误信息（如果失败）
        """
        import paramiko
        import socket
        from pathlib import Path
        
        host = await self.get_host(host_id)
        if not host:
            return {
                "success": False,
                "message": "主机不存在",
                "error_type": "host_not_found",
                "details": f"主机ID {host_id} 不存在于数据库中"
            }
        
        # 判断认证方式
        use_password_auth = bool(host.ansible_ssh_pass and not host.ansible_ssh_private_key_file)
        
        # 获取连接参数
        port = host.ansible_port or 22
        user = host.ansible_user or "root"
        hostname = host.ansible_host
        
        # 创建SSH客户端
        ssh_client = paramiko.SSHClient()
        ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        try:
            # 根据认证方式连接
            if use_password_auth:
                # 密码认证
                ssh_client.connect(
                    hostname=hostname,
                    port=port,
                    username=user,
                    password=host.ansible_ssh_pass,
                    timeout=10,
                    allow_agent=False,
                    look_for_keys=False
                )
            else:
                # 密钥认证
                key_file = host.ansible_ssh_private_key_file
                if key_file:
                    # 展开用户目录路径
                    key_path = Path(key_file).expanduser()
                    
                    if not key_path.exists():
                        await self.host_service.update_ping_status(host_id, "failed")
                        return {
                            "success": False,
                            "message": "SSH密钥文件不存在",
                            "error_type": "key_file_not_found",
                            "details": f"私钥文件不存在: {key_file}\n请检查文件路径是否正确"
                        }
                    
                    try:
                        ssh_client.connect(
                            hostname=hostname,
                            port=port,
                            username=user,
                            key_filename=str(key_path),
                            timeout=10,
                            allow_agent=False,
                            look_for_keys=False
                        )
                    except paramiko.ssh_exception.PasswordRequiredException:
                        await self.host_service.update_ping_status(host_id, "failed")
                        return {
                            "success": False,
                            "message": "SSH密钥需要密码短语",
                            "error_type": "key_passphrase_required",
                            "details": f"私钥文件 {key_file} 受密码保护\n请使用无密码的私钥或在系统中配置密钥代理"
                        }
                else:
                    # 没有指定私钥，尝试使用默认密钥
                    ssh_client.connect(
                        hostname=hostname,
                        port=port,
                        username=user,
                        timeout=10,
                        allow_agent=True,
                        look_for_keys=True
                    )
            
            # 执行测试命令
            stdin, stdout, stderr = ssh_client.exec_command("echo 'SSH_CONNECTION_TEST_OK'", timeout=5)
            output = stdout.read().decode('utf-8').strip()
            
            # 关闭连接
            ssh_client.close()
            
            # 检查命令执行结果
            if "SSH_CONNECTION_TEST_OK" in output:
                await self.host_service.update_ping_status(host_id, "success")
                auth_method = "密码认证" if use_password_auth else "密钥认证"
                return {
                    "success": True,
                    "message": f"SSH连接成功 ({user}@{hostname}:{port}) - {auth_method}",
                    "error_type": None,
                    "details": None
                }
            else:
                await self.host_service.update_ping_status(host_id, "failed")
                return {
                    "success": False,
                    "message": "命令执行失败",
                    "error_type": "command_execution_failed",
                    "details": f"SSH连接成功但命令执行失败\n输出: {output}"
                }
                
        except paramiko.AuthenticationException as e:
            # 认证失败
            await self.host_service.update_ping_status(host_id, "failed")
            if use_password_auth:
                return {
                    "success": False,
                    "message": "SSH密码认证失败",
                    "error_type": "password_authentication_failed",
                    "details": f"SSH密码认证失败，可能原因：\n1. 密码错误\n2. 用户名错误（当前: {user}）\n3. 用户不存在或被禁用\n4. SSH服务器禁用了密码认证\n5. 用户无SSH登录权限"
                }
            else:
                return {
                    "success": False,
                    "message": "SSH密钥认证失败",
                    "error_type": "key_authentication_failed",
                    "details": f"SSH密钥认证失败，可能原因：\n1. 私钥文件不存在或路径错误\n2. 私钥权限不正确（应为 600 或 400）\n3. 公钥未添加到目标主机的 ~/.ssh/authorized_keys\n4. 私钥与公钥不匹配\n5. 用户名错误（当前: {user}）"
                }
                
        except socket.timeout:
            # 连接超时
            await self.host_service.update_ping_status(host_id, "failed")
            return {
                "success": False,
                "message": "连接超时",
                "error_type": "connection_timeout",
                "details": f"连接到 {hostname}:{port} 超时，可能原因：\n1. 主机不在线\n2. 防火墙阻止\n3. 网络延迟过高\n4. 端口号错误"
            }
            
        except socket.gaierror as e:
            # 主机名解析失败
            await self.host_service.update_ping_status(host_id, "failed")
            return {
                "success": False,
                "message": "主机名解析失败",
                "error_type": "hostname_resolution_failed",
                "details": f"无法解析主机名 {hostname}\n请检查主机名或IP地址是否正确\n错误: {str(e)}"
            }
            
        except ConnectionRefusedError:
            # 连接被拒绝
            await self.host_service.update_ping_status(host_id, "failed")
            return {
                "success": False,
                "message": "连接被拒绝",
                "error_type": "connection_refused",
                "details": f"主机 {hostname}:{port} 拒绝连接，可能原因：\n1. SSH服务未运行\n2. 端口号错误（当前: {port}）\n3. 防火墙阻止连接"
            }
            
        except paramiko.SSHException as e:
            # SSH协议错误
            await self.host_service.update_ping_status(host_id, "failed")
            error_msg = str(e).lower()
            
            if "no hostkey" in error_msg or "host key" in error_msg:
                return {
                    "success": False,
                    "message": "主机密钥验证失败",
                    "error_type": "host_key_verification_failed",
                    "details": f"主机密钥验证失败\n错误: {str(e)}"
                }
            else:
                return {
                    "success": False,
                    "message": "SSH协议错误",
                    "error_type": "ssh_protocol_error",
                    "details": f"SSH连接过程中发生协议错误\n错误: {str(e)}"
                }
                
        except Exception as e:
            # 其他异常
            await self.host_service.update_ping_status(host_id, "failed")
            return {
                "success": False,
                "message": f"连接测试异常: {type(e).__name__}",
                "error_type": "exception",
                "details": f"发生未预期的错误\n错误类型: {type(e).__name__}\n错误信息: {str(e)}"
            }
        finally:
            # 确保SSH连接被关闭
            try:
                ssh_client.close()
            except:
                pass
    
    def _analyze_ssh_error(
        self, 
        return_code: int, 
        stderr: str, 
        host: str, 
        port: int, 
        user: str,
        use_password_auth: bool = False
    ) -> Dict[str, str]:
        """
        分析SSH错误信息，返回精确的错误类型和描述
        
        Args:
            return_code: SSH命令返回码
            stderr: SSH错误输出
            host: 主机地址
            port: SSH端口
            user: SSH用户
            use_password_auth: 是否使用密码认证
            
        Returns:
            Dict[str, str]: 包含message, error_type, details的字典
        """
        stderr_lower = stderr.lower()
        
        # 网络不可达
        if "no route to host" in stderr_lower or "network is unreachable" in stderr_lower:
            return {
                "message": "网络不可达",
                "error_type": "network_unreachable",
                "details": f"无法连接到主机 {host}，请检查网络连接和主机IP地址是否正确"
            }
        
        # 主机名解析失败
        if "could not resolve hostname" in stderr_lower or "name or service not known" in stderr_lower:
            return {
                "message": "主机名解析失败",
                "error_type": "hostname_resolution_failed",
                "details": f"无法解析主机名 {host}，请检查主机名或IP地址是否正确"
            }
        
        # 连接被拒绝（端口不对或SSH服务未运行）
        if "connection refused" in stderr_lower:
            return {
                "message": "连接被拒绝",
                "error_type": "connection_refused",
                "details": f"主机 {host}:{port} 拒绝连接，可能原因：\n1. SSH服务未运行\n2. 端口号错误（当前: {port}）\n3. 防火墙阻止连接"
            }
        
        # 连接超时
        if "connection timed out" in stderr_lower or "timed out" in stderr_lower:
            return {
                "message": "连接超时",
                "error_type": "connection_timeout",
                "details": f"连接到 {host}:{port} 超时，可能原因：\n1. 主机不在线\n2. 防火墙阻止\n3. 网络延迟过高"
            }
        
        # 权限被拒绝（根据认证方式返回不同的错误信息）
        if "permission denied" in stderr_lower:
            if use_password_auth:
                # 密码认证失败
                return {
                    "message": "SSH密码认证失败",
                    "error_type": "password_authentication_failed",
                    "details": f"SSH密码认证失败，可能原因：\n1. 密码错误\n2. 用户名错误（当前: {user}）\n3. 用户不存在或被禁用\n4. SSH服务器禁用了密码认证\n5. 用户无SSH登录权限"
                }
            else:
                # 密钥认证失败
                if "publickey" in stderr_lower:
                    return {
                        "message": "SSH密钥认证失败",
                        "error_type": "key_authentication_failed",
                        "details": f"SSH密钥认证失败，可能原因：\n1. 私钥文件不存在或路径错误\n2. 私钥权限不正确（应为 600 或 400）\n3. 公钥未添加到目标主机的 ~/.ssh/authorized_keys\n4. 私钥与公钥不匹配\n5. 用户名错误（当前: {user}）"
                    }
                else:
                    return {
                        "message": "认证失败",
                        "error_type": "authentication_failed",
                        "details": f"用户 {user} 认证失败，可能原因：\n1. 用户名错误\n2. 用户不存在\n3. 用户无SSH登录权限"
                    }
        
        # 主机密钥验证失败
        if "host key verification failed" in stderr_lower:
            return {
                "message": "主机密钥验证失败",
                "error_type": "host_key_verification_failed",
                "details": f"主机密钥验证失败，主机 {host} 的密钥可能已更改"
            }
        
        # 密钥文件权限问题
        if "bad permissions" in stderr_lower or "permissions are too open" in stderr_lower:
            return {
                "message": "密钥文件权限错误",
                "error_type": "key_permissions_error",
                "details": "SSH私钥文件权限过于开放，请设置为600 (chmod 600 keyfile)"
            }
        
        # 密钥文件不存在
        if "no such file or directory" in stderr_lower and "identity" in stderr_lower:
            return {
                "message": "密钥文件不存在",
                "error_type": "key_file_not_found",
                "details": "指定的SSH私钥文件不存在，请检查文件路径"
            }
        
        # 端口不可达
        if "port" in stderr_lower and ("unreachable" in stderr_lower or "filtered" in stderr_lower):
            return {
                "message": "端口不可达",
                "error_type": "port_unreachable",
                "details": f"端口 {port} 不可达，可能被防火墙过滤或端口号错误"
            }
        
        # 通用错误
        return {
            "message": f"SSH连接失败 (返回码: {return_code})",
            "error_type": "ssh_error",
            "details": f"SSH错误信息:\n{stderr[:500]}" if stderr else "未知错误"
        }

    async def ping_group(self, group_name: str) -> Dict[str, Dict[str, Any]]:
        """
        测试组中所有主机的连接
        
        Args:
            group_name: 组名
            
        Returns:
            Dict[str, Dict[str, Any]]: 主机名到连接测试结果的映射
        """
        hosts = await self.list_hosts(group_name=group_name)
        results = {}
        
        for host in hosts:
            result = await self.ping_host(host.id)
            results[host.hostname] = result
        
        return results
    
    async def get_hosts_count_fast(
        self,
        group_name: Optional[str] = None,
        active_only: bool = True
    ) -> int:
        """
        快速获取主机数量（优化：直接count，不查询数据）
        
        优化点:
        1. 使用 func.count() 直接在数据库中计数
        2. 不查询完整数据，只返回数量
        3. 支持按组和状态筛选
        
        Args:
            group_name: 组名筛选
            active_only: 是否只统计激活的主机
            
        Returns:
            int: 主机数量
        """
        from sqlalchemy import select, func, and_
        from ansible_web_ui.models.host import Host
        
        # 构建查询
        query = select(func.count(Host.id))
        
        # 应用筛选条件
        conditions = []
        
        if active_only:
            conditions.append(Host.is_active == True)
        
        if group_name:
            # 需要join group表
            from ansible_web_ui.models.host_group import HostGroup
            query = query.join(HostGroup, Host.group_id == HostGroup.id)
            conditions.append(HostGroup.name == group_name)
        
        if conditions:
            query = query.where(and_(*conditions))
        
        # 执行查询
        result = await self.db.execute(query)
        count = result.scalar()
        
        return count or 0


    async def gather_host_facts(self, host_id: int) -> Dict[str, Any]:
        """
        收集主机系统信息（使用SSH直接执行命令）
        
        通过SSH连接到主机并执行系统命令来收集信息
        
        Args:
            host_id: 主机ID
            
        Returns:
            Dict[str, Any]: 包含收集结果的字典
                - success: bool - 是否成功
                - message: str - 消息
                - facts: dict - 系统信息（如果成功）
                - error: str - 错误信息（如果失败）
        """
        import paramiko
        import json
        from pathlib import Path
        
        host = await self.get_host(host_id)
        if not host:
            return {
                "success": False,
                "message": "主机不存在",
                "error": f"主机ID {host_id} 不存在于数据库中"
            }
        
        # 判断认证方式
        use_password_auth = bool(host.ansible_ssh_pass and not host.ansible_ssh_private_key_file)
        
        # 获取连接参数
        port = host.ansible_port or 22
        user = host.ansible_user or "root"
        hostname = host.ansible_host
        
        # 创建SSH客户端
        ssh_client = paramiko.SSHClient()
        ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        try:
            # 根据认证方式连接
            if use_password_auth:
                ssh_client.connect(
                    hostname=hostname,
                    port=port,
                    username=user,
                    password=host.ansible_ssh_pass,
                    timeout=10,
                    allow_agent=False,
                    look_for_keys=False
                )
            else:
                key_file = host.ansible_ssh_private_key_file
                if key_file:
                    key_path = Path(key_file).expanduser()
                    if not key_path.exists():
                        return {
                            "success": False,
                            "message": "SSH密钥文件不存在",
                            "error": f"私钥文件不存在: {key_file}"
                        }
                    
                    ssh_client.connect(
                        hostname=hostname,
                        port=port,
                        username=user,
                        key_filename=str(key_path),
                        timeout=10,
                        allow_agent=False,
                        look_for_keys=False
                    )
                else:
                    ssh_client.connect(
                        hostname=hostname,
                        port=port,
                        username=user,
                        timeout=10,
                        allow_agent=True,
                        look_for_keys=True
                    )
            
            # 收集系统信息的命令
            commands = {
                "os_info": "cat /etc/os-release 2>/dev/null || cat /etc/redhat-release 2>/dev/null || echo 'Unknown'",
                "kernel": "uname -r",
                "kernel_version": "uname -v",
                "architecture": "uname -m",
                "hostname": "hostname",
                "fqdn": "hostname -f 2>/dev/null || hostname",
                "cpu_info": "cat /proc/cpuinfo | grep 'model name' | head -1 | cut -d':' -f2 | xargs",
                "cpu_cores": "nproc",
                "memory_total": "free -m | grep Mem | awk '{print $2}'",
                "memory_free": "free -m | grep Mem | awk '{print $4}'",
                "swap_total": "free -m | grep Swap | awk '{print $2}'",
                "swap_free": "free -m | grep Swap | awk '{print $4}'",
                "python_version": "python3 --version 2>&1 || python --version 2>&1",
                # 💿 磁盘信息
                "disk_info": "df -BM | tail -n +2 | awk '{print $1\"|\"$2\"|\"$3\"|\"$4\"|\"$5\"|\"$6}'",
                "disk_fstype": "df -T | tail -n +2 | awk '{print $1\"|\"$2}'",  # 文件系统类型
                # 🌐 网络接口信息（增强版）
                "network_interfaces": "ip -o link show | awk '{print $2,$9}' | sed 's/:$//'",
                "network_ipv4": "ip -4 -o addr show | awk '{print $2,$4}'",
                "network_ipv6": "ip -6 -o addr show | awk '{print $2,$4}'",
                "network_mac": "ip -o link show | awk '{print $2,$17}' | sed 's/:$//'",  # MAC 地址
                "network_stats": "cat /proc/net/dev | tail -n +3 | awk '{print $1,$2,$10}'",  # 接收和发送字节数
                # ⏱️ 系统运行时间
                "uptime_seconds": "cat /proc/uptime | awk '{print $1}'",
                "boot_time": "who -b | awk '{print $3,$4}'",
            }
            
            # 执行所有命令并收集结果
            import logging
            logger = logging.getLogger(__name__)
            
            results = {}
            for key, cmd in commands.items():
                try:
                    stdin, stdout, stderr = ssh_client.exec_command(cmd, timeout=5)
                    output = stdout.read().decode('utf-8').strip()
                    results[key] = output
                    
                    # 调试日志
                    if key in ['disk_info', 'network_interfaces', 'uptime_seconds']:
                        logger.info(f"命令 {key} 执行成功，输出长度: {len(output)}")
                        if not output:
                            logger.warning(f"命令 {key} 返回空结果")
                except Exception as e:
                    logger.error(f"命令 {key} 执行失败: {e}")
                    results[key] = None
            
            # 关闭连接
            ssh_client.close()
            
            # 解析OS信息
            os_info = {}
            if results.get("os_info") and results["os_info"] != "Unknown":
                for line in results["os_info"].split('\n'):
                    if '=' in line:
                        key, value = line.split('=', 1)
                        os_info[key.strip()] = value.strip().strip('"')
            
            # 💿 解析磁盘信息（只保留有实际挂载点的分区）
            disks = []
            
            # 🎯 定义需要过滤的设备类型和挂载点
            excluded_device_prefixes = ('tmpfs', 'devtmpfs', 'udev', 'none', 'overlay')
            excluded_mount_prefixes = ('/dev', '/sys', '/proc', '/run', '/snap')
            excluded_mount_points = ('/boot',)  # 🎯 排除 /boot 分区
            
            # 📂 解析文件系统类型
            fstype_map = {}
            if results.get("disk_fstype"):
                for line in results["disk_fstype"].split('\n'):
                    if line.strip():
                        parts = line.split('|')
                        if len(parts) >= 2:
                            device = parts[0]
                            fstype = parts[1]
                            fstype_map[device] = fstype
            
            if results.get("disk_info"):
                for line in results["disk_info"].split('\n'):
                    if line.strip():
                        parts = line.split('|')
                        if len(parts) >= 6:
                            try:
                                device = parts[0]
                                mount = parts[5]
                                
                                # 🎯 过滤虚拟文件系统
                                if any(device.startswith(prefix) for prefix in excluded_device_prefixes):
                                    continue
                                
                                # 🎯 过滤特殊挂载点前缀
                                if any(mount.startswith(prefix) for prefix in excluded_mount_prefixes):
                                    continue
                                
                                # 🎯 过滤特定挂载点（精确匹配）
                                if mount in excluded_mount_points:
                                    continue
                                
                                # 🎯 必须有有效挂载点
                                if not mount or mount.strip() == '':
                                    continue
                                
                                total_str = parts[1].replace('M', '')
                                used_str = parts[2].replace('M', '')
                                free_str = parts[3].replace('M', '')
                                percentage_str = parts[4].replace('%', '')
                                
                                total_mb = int(total_str) if total_str.isdigit() else 0
                                used_mb = int(used_str) if used_str.isdigit() else 0
                                free_mb = int(free_str) if free_str.isdigit() else 0
                                percentage = int(percentage_str) if percentage_str.isdigit() else 0
                                
                                # 📂 获取文件系统类型
                                fstype = fstype_map.get(device, "unknown")
                                
                                disks.append({
                                    "device": device,
                                    "total_mb": total_mb,
                                    "used_mb": used_mb,
                                    "free_mb": free_mb,
                                    "percentage": percentage,
                                    "mount": mount,
                                    "fstype": fstype  # 📂 实际的文件系统类型
                                })
                            except (ValueError, IndexError):
                                continue
            
            # 🌐 解析网络接口信息（只保留物理网络接口）
            interfaces = []
            
            # 🎯 定义需要过滤的接口前缀和关键词
            excluded_interface_prefixes = (
                'lo', 'docker', 'br-', 'veth', 'virbr', 'vmnet', 'vboxnet',
                'tun', 'tap', 'zt', 'wg', 'utun', 'awdl', 'llw', 'bridge'
            )
            excluded_interface_keywords = (
                'vmware', 'virtualbox', 'zerotier', 'tailscale', 'hamachi',
                'virtual', 'loopback', 'tunnel', 'vpn'
            )
            
            if results.get("network_interfaces"):
                # 解析接口状态
                interface_status = {}
                for line in results["network_interfaces"].split('\n'):
                    if line.strip():
                        parts = line.split()
                        if len(parts) >= 2:
                            iface_name = parts[0].rstrip(':')  # 移除末尾的冒号
                            status = parts[1].upper()
                            interface_status[iface_name] = status
                
                # 解析IPv4地址
                ipv4_addrs = {}
                if results.get("network_ipv4"):
                    for line in results["network_ipv4"].split('\n'):
                        if line.strip():
                            parts = line.split()
                            if len(parts) >= 2:
                                iface_name = parts[0]
                                ipv4 = parts[1].split('/')[0]  # 移除CIDR后缀
                                ipv4_addrs[iface_name] = ipv4
                
                # 解析IPv6地址
                ipv6_addrs = {}
                if results.get("network_ipv6"):
                    for line in results["network_ipv6"].split('\n'):
                        if line.strip() and 'fe80' not in line.lower():  # 排除链路本地地址
                            parts = line.split()
                            if len(parts) >= 2:
                                iface_name = parts[0]
                                ipv6 = parts[1].split('/')[0]
                                ipv6_addrs[iface_name] = ipv6
                
                # 解析MAC地址
                mac_addrs = {}
                if results.get("network_mac"):
                    for line in results["network_mac"].split('\n'):
                        if line.strip():
                            parts = line.split()
                            if len(parts) >= 2:
                                iface_name = parts[0].rstrip(':')  # 移除末尾的冒号
                                mac = parts[1]
                                # 验证MAC地址格式
                                if ':' in mac and len(mac) == 17:
                                    mac_addrs[iface_name] = mac
                
                # 解析网络流量统计
                traffic_stats = {}
                if results.get("network_stats"):
                    for line in results["network_stats"].split('\n'):
                        if line.strip():
                            parts = line.split()
                            if len(parts) >= 3:
                                iface_name = parts[0].rstrip(':')  # 移除冒号
                                try:
                                    bytes_recv = int(parts[1])
                                    bytes_sent = int(parts[2])
                                    traffic_stats[iface_name] = {
                                        "bytes_recv": bytes_recv,
                                        "bytes_sent": bytes_sent
                                    }
                                except (ValueError, IndexError):
                                    continue
                
                # 组合接口信息（应用过滤规则）
                for iface_name, status in interface_status.items():
                    iface_name_lower = iface_name.lower()
                    
                    # 🎯 过滤虚拟网络接口（前缀匹配）
                    if any(iface_name_lower.startswith(prefix) for prefix in excluded_interface_prefixes):
                        continue
                    
                    # 🎯 过滤虚拟网络接口（关键词匹配）
                    if any(keyword in iface_name_lower for keyword in excluded_interface_keywords):
                        continue
                    
                    # 🎯 只保留有 IP 地址的接口（至少有 IPv4 或 IPv6）
                    ipv4 = ipv4_addrs.get(iface_name)
                    ipv6 = ipv6_addrs.get(iface_name)
                    
                    if not ipv4 and not ipv6:
                        continue
                    
                    # 获取流量统计
                    traffic = traffic_stats.get(iface_name, {})
                    
                    interfaces.append({
                        "name": iface_name,
                        "status": status.lower(),
                        "ipv4": ipv4,
                        "ipv6": ipv6,
                        "mac": mac_addrs.get(iface_name),
                        "bytes_recv": traffic.get("bytes_recv", 0),
                        "bytes_sent": traffic.get("bytes_sent", 0),
                        "speed": None  # 需要额外命令获取，暂不实现
                    })
            
            # ⏱️ 解析系统运行时间
            uptime_info = None
            if results.get("uptime_seconds"):
                try:
                    uptime_seconds = int(float(results["uptime_seconds"]))
                    days = uptime_seconds // 86400
                    hours = (uptime_seconds % 86400) // 3600
                    minutes = (uptime_seconds % 3600) // 60
                    
                    # 计算启动时间
                    from datetime import datetime, timedelta
                    boot_time = datetime.utcnow() - timedelta(seconds=uptime_seconds)
                    
                    uptime_info = {
                        "uptime_seconds": uptime_seconds,
                        "days": days,
                        "hours": hours,
                        "minutes": minutes,
                        "boot_time": boot_time.isoformat()
                    }
                except (ValueError, TypeError):
                    pass
            
            # 构建系统信息
            system_info = {
                "os": {
                    "distribution": os_info.get('NAME', 'Unknown'),
                    "distribution_version": os_info.get('VERSION_ID', 'Unknown'),
                    "distribution_release": os_info.get('VERSION', 'Unknown'),
                    "system": "Linux",
                },
                "kernel": {
                    "kernel": results.get("kernel", "Unknown"),
                    "kernel_version": results.get("kernel_version", "Unknown"),
                },
                "hardware": {
                    "architecture": results.get("architecture", "Unknown"),
                    "machine": results.get("architecture", "Unknown"),
                    "processor": [results.get("cpu_info", "Unknown")],
                    "processor_cores": int(results.get("cpu_cores", 0)) if results.get("cpu_cores", "").isdigit() else 0,
                    "processor_count": 1,
                    "processor_threads_per_core": 1,
                    "processor_vcpus": int(results.get("cpu_cores", 0)) if results.get("cpu_cores", "").isdigit() else 0,
                },
                "memory": {
                    "memtotal_mb": int(results.get("memory_total", 0)) if results.get("memory_total", "").isdigit() else 0,
                    "memfree_mb": int(results.get("memory_free", 0)) if results.get("memory_free", "").isdigit() else 0,
                    "swaptotal_mb": int(results.get("swap_total", 0)) if results.get("swap_total", "").isdigit() else 0,
                    "swapfree_mb": int(results.get("swap_free", 0)) if results.get("swap_free", "").isdigit() else 0,
                },
                "disks": disks,  # 💿 磁盘信息（保留空列表）
                "network": {
                    "hostname": results.get("hostname", "Unknown"),
                    "fqdn": results.get("fqdn", "Unknown"),
                    "domain": results.get("fqdn", "").split('.', 1)[1] if '.' in results.get("fqdn", "") else "",
                    "interfaces": interfaces,  # 🌐 网络接口（保留空列表）
                },
                "uptime": uptime_info if uptime_info else {},  # ⏱️ 运行时间（保留空字典）
                "python": {
                    "version": results.get("python_version", "Unknown").replace("Python ", ""),
                    "executable": "/usr/bin/python3",
                },
                "collected_at": None  # 将在下面设置
            }
            
            # 添加收集时间
            from ansible_web_ui.utils.timezone import now
            system_info["collected_at"] = now().isoformat()
            
            # 保存到extra_data
            extra_data = host.extra_data or {}
            if isinstance(extra_data, str):
                extra_data = json.loads(extra_data)
            extra_data['system_info'] = system_info
            
            # 调试日志
            import logging
            logger = logging.getLogger(__name__)
            logger.info(f"准备保存系统信息到主机 {host_id}")
            logger.info(f"system_info 包含字段: {list(system_info.keys())}")
            logger.info(f"disks 数量: {len(system_info.get('disks', []))}")
            logger.info(f"interfaces 数量: {len(system_info.get('network', {}).get('interfaces', []))}")
            logger.info(f"uptime 存在: {'uptime' in system_info}")
            logger.info(f"extra_data keys: {list(extra_data.keys())}")
            logger.info(f"extra_data['system_info'] keys: {list(extra_data['system_info'].keys())}")
            
            # 更新主机
            logger.info(f"调用 host_service.update(host_id={host_id}, extra_data=...)")
            updated_host = await self.host_service.update(host_id, extra_data=extra_data)
            logger.info(f"update 返回: {updated_host is not None}")
            
            if not updated_host:
                logger.error(f"主机 {host_id} 更新失败 - update返回None")
                return {
                    "success": False,
                    "message": "保存系统信息失败",
                    "error": "数据库更新失败"
                }
            
            logger.info(f"主机 {host_id} 更新成功")
            # 验证保存的数据
            saved_system_info = updated_host.extra_data.get('system_info', {}) if updated_host.extra_data else {}
            logger.info(f"保存后的 disks 数量: {len(saved_system_info.get('disks', []))}")
            logger.info(f"保存后的 interfaces 数量: {len(saved_system_info.get('network', {}).get('interfaces', []))}")
            
            return {
                "success": True,
                "message": "系统信息收集成功",
                "facts": system_info
            }
            
        except paramiko.AuthenticationException:
            return {
                "success": False,
                "message": "SSH认证失败",
                "error": "无法连接到主机，请检查SSH配置"
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"收集异常: {type(e).__name__}",
                "error": str(e)
            }
        finally:
            # 确保SSH连接被关闭
            try:
                ssh_client.close()
            except:
                pass

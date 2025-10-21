"""
权限管理模块

定义系统权限和基于角色的访问控制逻辑。
"""

from enum import Enum
from typing import Dict, List, Set
from ansible_web_ui.models.user import User, UserRole


class Permission(str, Enum):
    """
    系统权限枚举
    """
    # 用户管理权限
    VIEW_USERS = "view_users"
    CREATE_USERS = "create_users"
    UPDATE_USERS = "update_users"
    DELETE_USERS = "delete_users"
    MANAGE_USER_ROLES = "manage_user_roles"
    
    # 主机管理权限
    VIEW_HOSTS = "view_hosts"
    CREATE_HOSTS = "create_hosts"
    UPDATE_HOSTS = "update_hosts"
    DELETE_HOSTS = "delete_hosts"
    MANAGE_HOST_GROUPS = "manage_host_groups"
    
    # Playbook管理权限
    VIEW_PLAYBOOKS = "view_playbooks"
    CREATE_PLAYBOOKS = "create_playbooks"
    UPDATE_PLAYBOOKS = "update_playbooks"
    DELETE_PLAYBOOKS = "delete_playbooks"
    UPLOAD_PLAYBOOKS = "upload_playbooks"
    
    # 任务执行权限
    VIEW_TASKS = "view_tasks"
    EXECUTE_TASKS = "execute_tasks"
    CANCEL_TASKS = "cancel_tasks"
    RETRY_TASKS = "retry_tasks"
    
    # 执行历史权限
    VIEW_EXECUTION_HISTORY = "view_execution_history"
    VIEW_EXECUTION_LOGS = "view_execution_logs"
    DELETE_EXECUTION_HISTORY = "delete_execution_history"
    EXPORT_EXECUTION_DATA = "export_execution_data"
    
    # 系统配置权限
    VIEW_SYSTEM_CONFIG = "view_system_config"
    UPDATE_SYSTEM_CONFIG = "update_system_config"
    MANAGE_ANSIBLE_CONFIG = "manage_ansible_config"
    
    # 监控和统计权限
    VIEW_SYSTEM_STATS = "view_system_stats"
    VIEW_PERFORMANCE_METRICS = "view_performance_metrics"
    
    # 系统管理权限
    SYSTEM_ADMIN = "system_admin"
    BACKUP_SYSTEM = "backup_system"
    RESTORE_SYSTEM = "restore_system"


class PermissionManager:
    """
    权限管理器
    
    管理角色权限映射和权限检查逻辑。
    """
    
    # 角色权限映射
    ROLE_PERMISSIONS: Dict[UserRole, Set[Permission]] = {
        UserRole.VIEWER: {
            # 查看者只能查看信息，不能修改
            Permission.VIEW_USERS,
            Permission.VIEW_HOSTS,
            Permission.VIEW_PLAYBOOKS,
            Permission.VIEW_TASKS,
            Permission.VIEW_EXECUTION_HISTORY,
            Permission.VIEW_EXECUTION_LOGS,
            Permission.VIEW_SYSTEM_CONFIG,
            Permission.VIEW_SYSTEM_STATS,
            Permission.VIEW_PERFORMANCE_METRICS,
        },
        
        UserRole.OPERATOR: {
            # 操作员可以执行任务和管理资源
            Permission.VIEW_USERS,
            Permission.VIEW_HOSTS,
            Permission.CREATE_HOSTS,
            Permission.UPDATE_HOSTS,
            Permission.DELETE_HOSTS,
            Permission.MANAGE_HOST_GROUPS,
            Permission.VIEW_PLAYBOOKS,
            Permission.CREATE_PLAYBOOKS,
            Permission.UPDATE_PLAYBOOKS,
            Permission.DELETE_PLAYBOOKS,
            Permission.UPLOAD_PLAYBOOKS,
            Permission.VIEW_TASKS,
            Permission.EXECUTE_TASKS,
            Permission.CANCEL_TASKS,
            Permission.RETRY_TASKS,
            Permission.VIEW_EXECUTION_HISTORY,
            Permission.VIEW_EXECUTION_LOGS,
            Permission.EXPORT_EXECUTION_DATA,
            Permission.VIEW_SYSTEM_CONFIG,
            Permission.VIEW_SYSTEM_STATS,
            Permission.VIEW_PERFORMANCE_METRICS,
        },
        
        UserRole.ADMIN: {
            # 管理员拥有所有权限
            Permission.VIEW_USERS,
            Permission.CREATE_USERS,
            Permission.UPDATE_USERS,
            Permission.DELETE_USERS,
            Permission.MANAGE_USER_ROLES,
            Permission.VIEW_HOSTS,
            Permission.CREATE_HOSTS,
            Permission.UPDATE_HOSTS,
            Permission.DELETE_HOSTS,
            Permission.MANAGE_HOST_GROUPS,
            Permission.VIEW_PLAYBOOKS,
            Permission.CREATE_PLAYBOOKS,
            Permission.UPDATE_PLAYBOOKS,
            Permission.DELETE_PLAYBOOKS,
            Permission.UPLOAD_PLAYBOOKS,
            Permission.VIEW_TASKS,
            Permission.EXECUTE_TASKS,
            Permission.CANCEL_TASKS,
            Permission.RETRY_TASKS,
            Permission.VIEW_EXECUTION_HISTORY,
            Permission.VIEW_EXECUTION_LOGS,
            Permission.DELETE_EXECUTION_HISTORY,
            Permission.EXPORT_EXECUTION_DATA,
            Permission.VIEW_SYSTEM_CONFIG,
            Permission.UPDATE_SYSTEM_CONFIG,
            Permission.MANAGE_ANSIBLE_CONFIG,
            Permission.VIEW_SYSTEM_STATS,
            Permission.VIEW_PERFORMANCE_METRICS,
            Permission.SYSTEM_ADMIN,
            Permission.BACKUP_SYSTEM,
            Permission.RESTORE_SYSTEM,
        }
    }
    
    @classmethod
    def get_role_permissions(cls, role: UserRole) -> Set[Permission]:
        """
        获取角色的所有权限
        
        Args:
            role: 用户角色
            
        Returns:
            Set[Permission]: 权限集合
        """
        return cls.ROLE_PERMISSIONS.get(role, set())
    
    @classmethod
    def has_permission(cls, user: User, permission: Permission) -> bool:
        """
        检查用户是否有特定权限
        
        Args:
            user: 用户对象
            permission: 权限
            
        Returns:
            bool: 是否有权限
        """
        # 检查用户是否激活
        if not user.is_active:
            return False
        
        # 超级用户拥有所有权限
        if user.is_superuser:
            return True
        
        # 检查角色权限
        role_permissions = cls.get_role_permissions(user.role)
        return permission in role_permissions
    
    @classmethod
    def has_any_permission(cls, user: User, permissions: List[Permission]) -> bool:
        """
        检查用户是否有任一权限
        
        Args:
            user: 用户对象
            permissions: 权限列表
            
        Returns:
            bool: 是否有任一权限
        """
        return any(cls.has_permission(user, perm) for perm in permissions)
    
    @classmethod
    def has_all_permissions(cls, user: User, permissions: List[Permission]) -> bool:
        """
        检查用户是否有所有权限
        
        Args:
            user: 用户对象
            permissions: 权限列表
            
        Returns:
            bool: 是否有所有权限
        """
        return all(cls.has_permission(user, perm) for perm in permissions)
    
    @classmethod
    def get_user_permissions(cls, user: User) -> Set[Permission]:
        """
        获取用户的所有权限
        
        Args:
            user: 用户对象
            
        Returns:
            Set[Permission]: 用户权限集合
        """
        if not user.is_active:
            return set()
        
        if user.is_superuser:
            # 超级用户拥有所有权限
            return set(Permission)
        
        return cls.get_role_permissions(user.role)
    
    @classmethod
    def can_access_resource(cls, user: User, resource_type: str, action: str) -> bool:
        """
        检查用户是否可以访问特定资源
        
        Args:
            user: 用户对象
            resource_type: 资源类型 (users, hosts, playbooks, tasks, etc.)
            action: 操作类型 (view, create, update, delete)
            
        Returns:
            bool: 是否可以访问
        """
        # 构建权限名称
        permission_name = f"{action}_{resource_type}"
        
        try:
            permission = Permission(permission_name)
            return cls.has_permission(user, permission)
        except ValueError:
            # 如果权限不存在，默认拒绝访问
            return False
    
    @classmethod
    def get_accessible_resources(cls, user: User) -> Dict[str, List[str]]:
        """
        获取用户可访问的资源和操作
        
        Args:
            user: 用户对象
            
        Returns:
            Dict[str, List[str]]: 资源和操作映射
        """
        permissions = cls.get_user_permissions(user)
        resources = {}
        
        for permission in permissions:
            # 解析权限名称
            parts = permission.value.split('_', 1)
            if len(parts) == 2:
                action, resource = parts
                if resource not in resources:
                    resources[resource] = []
                resources[resource].append(action)
        
        return resources
    
    @classmethod
    def check_resource_ownership(cls, user: User, resource_owner_id: int) -> bool:
        """
        检查资源所有权
        
        Args:
            user: 用户对象
            resource_owner_id: 资源所有者ID
            
        Returns:
            bool: 是否拥有资源或有管理权限
        """
        # 超级用户和管理员可以访问所有资源
        if user.is_superuser or user.is_admin:
            return True
        
        # 用户只能访问自己的资源
        return user.id == resource_owner_id


class ResourcePermissionChecker:
    """
    资源权限检查器
    
    提供特定资源的权限检查逻辑。
    """
    
    @staticmethod
    def can_manage_users(user: User) -> bool:
        """检查是否可以管理用户"""
        return PermissionManager.has_any_permission(user, [
            Permission.CREATE_USERS,
            Permission.UPDATE_USERS,
            Permission.DELETE_USERS,
            Permission.MANAGE_USER_ROLES
        ])
    
    @staticmethod
    def can_manage_hosts(user: User) -> bool:
        """检查是否可以管理主机"""
        return PermissionManager.has_any_permission(user, [
            Permission.CREATE_HOSTS,
            Permission.UPDATE_HOSTS,
            Permission.DELETE_HOSTS,
            Permission.MANAGE_HOST_GROUPS
        ])
    
    @staticmethod
    def can_manage_playbooks(user: User) -> bool:
        """检查是否可以管理Playbook"""
        return PermissionManager.has_any_permission(user, [
            Permission.CREATE_PLAYBOOKS,
            Permission.UPDATE_PLAYBOOKS,
            Permission.DELETE_PLAYBOOKS,
            Permission.UPLOAD_PLAYBOOKS
        ])
    
    @staticmethod
    def can_execute_tasks(user: User) -> bool:
        """检查是否可以执行任务"""
        return PermissionManager.has_permission(user, Permission.EXECUTE_TASKS)
    
    @staticmethod
    def can_view_sensitive_data(user: User) -> bool:
        """检查是否可以查看敏感数据"""
        return PermissionManager.has_any_permission(user, [
            Permission.VIEW_SYSTEM_CONFIG,
            Permission.SYSTEM_ADMIN
        ])
    
    @staticmethod
    def can_modify_system(user: User) -> bool:
        """检查是否可以修改系统配置"""
        return PermissionManager.has_any_permission(user, [
            Permission.UPDATE_SYSTEM_CONFIG,
            Permission.MANAGE_ANSIBLE_CONFIG,
            Permission.SYSTEM_ADMIN
        ])


# 权限组定义
PERMISSION_GROUPS = {
    "用户管理": [
        Permission.VIEW_USERS,
        Permission.CREATE_USERS,
        Permission.UPDATE_USERS,
        Permission.DELETE_USERS,
        Permission.MANAGE_USER_ROLES,
    ],
    "主机管理": [
        Permission.VIEW_HOSTS,
        Permission.CREATE_HOSTS,
        Permission.UPDATE_HOSTS,
        Permission.DELETE_HOSTS,
        Permission.MANAGE_HOST_GROUPS,
    ],
    "Playbook管理": [
        Permission.VIEW_PLAYBOOKS,
        Permission.CREATE_PLAYBOOKS,
        Permission.UPDATE_PLAYBOOKS,
        Permission.DELETE_PLAYBOOKS,
        Permission.UPLOAD_PLAYBOOKS,
    ],
    "任务执行": [
        Permission.VIEW_TASKS,
        Permission.EXECUTE_TASKS,
        Permission.CANCEL_TASKS,
        Permission.RETRY_TASKS,
    ],
    "历史记录": [
        Permission.VIEW_EXECUTION_HISTORY,
        Permission.VIEW_EXECUTION_LOGS,
        Permission.DELETE_EXECUTION_HISTORY,
        Permission.EXPORT_EXECUTION_DATA,
    ],
    "系统配置": [
        Permission.VIEW_SYSTEM_CONFIG,
        Permission.UPDATE_SYSTEM_CONFIG,
        Permission.MANAGE_ANSIBLE_CONFIG,
    ],
    "监控统计": [
        Permission.VIEW_SYSTEM_STATS,
        Permission.VIEW_PERFORMANCE_METRICS,
    ],
    "系统管理": [
        Permission.SYSTEM_ADMIN,
        Permission.BACKUP_SYSTEM,
        Permission.RESTORE_SYSTEM,
    ]
}
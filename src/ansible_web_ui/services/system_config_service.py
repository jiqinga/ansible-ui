"""
系统配置服务

提供系统配置管理相关的业务逻辑。
"""

from typing import Optional, List, Dict, Any, Union
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ansible_web_ui.models.system_config import SystemConfig
from ansible_web_ui.services.base import BaseService


class SystemConfigService(BaseService[SystemConfig]):
    """
    系统配置服务类
    
    提供系统配置的读取、更新、验证等功能。
    """
    
    def __init__(self, db_session: AsyncSession):
        super().__init__(SystemConfig, db_session)

    async def get_config_by_key(self, key: str) -> Optional[SystemConfig]:
        """
        根据配置键获取配置
        
        Args:
            key: 配置键名
            
        Returns:
            Optional[SystemConfig]: 配置对象或None
        """
        return await self.get_by_field("key", key)

    async def get_config_value(self, key: str, default: Any = None) -> Any:
        """
        获取配置值
        
        Args:
            key: 配置键名
            default: 默认值
            
        Returns:
            Any: 配置值或默认值
        """
        config = await self.get_config_by_key(key)
        if config:
            return config.get_value()
        return default

    async def set_config_value(self, key: str, value: Any) -> bool:
        """
        设置配置值
        
        Args:
            key: 配置键名
            value: 配置值
            
        Returns:
            bool: 是否设置成功
        """
        config = await self.get_config_by_key(key)
        if not config:
            return False
        
        # 验证值
        is_valid, error_msg = config.validate_value(value)
        if not is_valid:
            raise ValueError(f"配置值无效: {error_msg}")
        
        config.set_value(value)
        await self.db.commit()
        return True

    async def create_config(
        self,
        key: str,
        value: Any,
        description: Optional[str] = None,
        category: str = "general",
        is_sensitive: bool = False,
        is_readonly: bool = False,
        requires_restart: bool = False,
        validation_rule: Optional[Dict[str, Any]] = None,
        default_value: Optional[Any] = None
    ) -> SystemConfig:
        """
        创建新配置
        
        Args:
            key: 配置键名
            value: 配置值
            description: 配置描述
            category: 配置分类
            is_sensitive: 是否为敏感信息
            is_readonly: 是否只读
            requires_restart: 修改后是否需要重启
            validation_rule: 验证规则
            default_value: 默认值
            
        Returns:
            SystemConfig: 创建的配置对象
        """
        config = SystemConfig(
            key=key,
            description=description,
            category=category,
            is_sensitive=is_sensitive,
            is_readonly=is_readonly,
            requires_restart=requires_restart
        )
        
        # 设置值和规则
        config.set_value(value)
        if validation_rule:
            config.set_validation_rule(validation_rule)
        if default_value is not None:
            config.default_value = str(default_value)
        
        self.db.add(config)
        await self.db.commit()
        await self.db.refresh(config)
        return config

    async def get_configs_by_category(self, category: str) -> List[SystemConfig]:
        """
        根据分类获取配置列表
        
        Args:
            category: 配置分类
            
        Returns:
            List[SystemConfig]: 配置列表
        """
        return await self.get_by_filters({"category": category})

    async def get_all_categories(self) -> List[str]:
        """
        获取所有配置分类
        
        Returns:
            List[str]: 分类列表
        """
        result = await self.db.execute(
            select(SystemConfig.category).distinct().order_by(SystemConfig.category)
        )
        return result.scalars().all()

    async def get_ansible_configs(self) -> Dict[str, Any]:
        """
        获取所有Ansible相关配置
        
        Returns:
            Dict[str, Any]: Ansible配置字典
        """
        configs = await self.get_configs_by_category("ansible")
        return {
            config.key.replace("ansible.", ""): config.get_value()
            for config in configs
        }

    async def get_app_configs(self) -> Dict[str, Any]:
        """
        获取所有应用配置
        
        Returns:
            Dict[str, Any]: 应用配置字典
        """
        configs = await self.get_by_filters(
            {"category": ["security", "performance", "maintenance", "features"]}
        )
        return {
            config.key: config.get_value()
            for config in configs
        }

    async def get_ui_configs(self) -> Dict[str, Any]:
        """
        获取所有UI配置
        
        Returns:
            Dict[str, Any]: UI配置字典
        """
        configs = await self.get_configs_by_category("ui")
        return {
            config.key.replace("ui.", ""): config.get_value()
            for config in configs
        }

    async def update_multiple_configs(self, config_updates: Dict[str, Any]) -> Dict[str, bool]:
        """
        批量更新配置
        
        Args:
            config_updates: 配置更新字典 {key: value}
            
        Returns:
            Dict[str, bool]: 更新结果 {key: success}
        """
        results = {}
        
        for key, value in config_updates.items():
            try:
                success = await self.set_config_value(key, value)
                results[key] = success
            except Exception as e:
                results[key] = False
        
        return results

    async def reset_config_to_default(self, key: str) -> bool:
        """
        重置配置为默认值
        
        Args:
            key: 配置键名
            
        Returns:
            bool: 是否重置成功
        """
        config = await self.get_config_by_key(key)
        if not config or not config.default_value:
            return False
        
        default_value = config.get_default_value()
        if default_value is not None:
            config.set_value(default_value)
            await self.db.commit()
            return True
        
        return False

    async def get_sensitive_configs(self) -> List[SystemConfig]:
        """
        获取所有敏感配置
        
        Returns:
            List[SystemConfig]: 敏感配置列表
        """
        return await self.get_by_filters({"is_sensitive": True})

    async def get_readonly_configs(self) -> List[SystemConfig]:
        """
        获取所有只读配置
        
        Returns:
            List[SystemConfig]: 只读配置列表
        """
        return await self.get_by_filters({"is_readonly": True})

    async def get_restart_required_configs(self) -> List[SystemConfig]:
        """
        获取需要重启的配置
        
        Returns:
            List[SystemConfig]: 需要重启的配置列表
        """
        return await self.get_by_filters({"requires_restart": True})

    async def validate_config_batch(self, config_data: Dict[str, Any]) -> Dict[str, str]:
        """
        批量验证配置值
        
        Args:
            config_data: 配置数据字典
            
        Returns:
            Dict[str, str]: 验证错误信息 {key: error_message}
        """
        errors = {}
        
        for key, value in config_data.items():
            config = await self.get_config_by_key(key)
            if not config:
                errors[key] = f"配置项 '{key}' 不存在"
                continue
            
            if config.is_readonly:
                errors[key] = f"配置项 '{key}' 为只读，不能修改"
                continue
            
            is_valid, error_msg = config.validate_value(value)
            if not is_valid:
                errors[key] = error_msg
        
        return errors

    async def export_configs(self, category: Optional[str] = None) -> Dict[str, Any]:
        """
        导出配置
        
        Args:
            category: 可选的分类过滤
            
        Returns:
            Dict[str, Any]: 配置导出数据
        """
        if category:
            configs = await self.get_configs_by_category(category)
        else:
            configs = await self.get_all()
        
        export_data = {}
        for config in configs:
            if not config.is_sensitive:  # 不导出敏感配置
                export_data[config.key] = {
                    "value": config.get_value(),
                    "description": config.description,
                    "category": config.category,
                    "default_value": config.get_default_value()
                }
        
        return export_data

    async def import_configs(self, config_data: Dict[str, Any], overwrite: bool = False) -> Dict[str, str]:
        """
        导入配置
        
        Args:
            config_data: 配置数据
            overwrite: 是否覆盖现有配置
            
        Returns:
            Dict[str, str]: 导入结果 {key: status}
        """
        results = {}
        
        for key, data in config_data.items():
            try:
                existing_config = await self.get_config_by_key(key)
                
                if existing_config and not overwrite:
                    results[key] = "跳过（配置已存在）"
                    continue
                
                if existing_config:
                    # 更新现有配置
                    success = await self.set_config_value(key, data.get("value"))
                    results[key] = "更新成功" if success else "更新失败"
                else:
                    # 创建新配置
                    await self.create_config(
                        key=key,
                        value=data.get("value"),
                        description=data.get("description"),
                        category=data.get("category", "general")
                    )
                    results[key] = "创建成功"
                    
            except Exception as e:
                results[key] = f"错误: {str(e)}"
        
        return results
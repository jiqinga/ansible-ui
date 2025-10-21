"""
配置管理服务

提供系统配置管理、Ansible配置文件管理和配置验证功能。
"""

import os
import configparser
import json
import shutil
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple, Union
from sqlalchemy.ext.asyncio import AsyncSession

from ansible_web_ui.services.system_config_service import SystemConfigService
from ansible_web_ui.models.system_config import SystemConfig
from ansible_web_ui.utils.validation import validate_config_value


class ConfigManagementService:
    """
    配置管理服务类
    
    提供系统配置和Ansible配置文件的统一管理。
    """
    
    def __init__(self, db_session: AsyncSession):
        self.db = db_session
        self.system_config_service = SystemConfigService(db_session)
        self.ansible_config_path = Path("config/ansible.cfg")
        self.ansible_config_backup_path = Path("config/ansible.cfg.backup")
        
    async def initialize_default_configs(self) -> None:
        """
        初始化默认配置项
        """
        default_configs = self._get_default_config_definitions()
        
        for config_def in default_configs:
            existing = await self.system_config_service.get_config_by_key(config_def["key"])
            if not existing:
                await self.system_config_service.create_config(**config_def)
    
    def _get_default_config_definitions(self) -> List[Dict[str, Any]]:
        """
        获取默认配置定义
        
        Returns:
            List[Dict[str, Any]]: 默认配置定义列表
        """
        return [
            # Ansible基础配置
            {
                "key": "ansible.inventory",
                "value": "../inventory/hosts.ini",
                "description": "Ansible inventory文件路径",
                "category": "ansible",
                "validation_rule": {"type": "string", "min_length": 1},
                "default_value": "../inventory/hosts.ini"
            },
            {
                "key": "ansible.host_key_checking",
                "value": False,
                "description": "是否检查主机密钥",
                "category": "ansible",
                "validation_rule": {"type": "boolean"},
                "default_value": False
            },
            {
                "key": "ansible.timeout",
                "value": 30,
                "description": "连接超时时间（秒）",
                "category": "ansible",
                "validation_rule": {"type": "integer", "min": 1, "max": 300},
                "default_value": 30
            },
            {
                "key": "ansible.forks",
                "value": 5,
                "description": "并发执行数量",
                "category": "ansible",
                "validation_rule": {"type": "integer", "min": 1, "max": 50},
                "default_value": 5
            },
            {
                "key": "ansible.gathering",
                "value": "implicit",
                "description": "Facts收集策略",
                "category": "ansible",
                "validation_rule": {"type": "string", "enum": ["implicit", "explicit", "smart"]},
                "default_value": "implicit"
            },
            {
                "key": "ansible.log_path",
                "value": "../logs/ansible.log",
                "description": "Ansible日志文件路径",
                "category": "ansible",
                "validation_rule": {"type": "string", "min_length": 1},
                "default_value": "../logs/ansible.log"
            },
            
            # SSH连接配置
            {
                "key": "ansible.ssh_args",
                "value": "-o ControlMaster=auto -o ControlPersist=60s -o UserKnownHostsFile=/dev/null -o IdentitiesOnly=yes",
                "description": "SSH连接参数",
                "category": "ansible",
                "validation_rule": {"type": "string"},
                "default_value": "-o ControlMaster=auto -o ControlPersist=60s -o UserKnownHostsFile=/dev/null -o IdentitiesOnly=yes"
            },
            {
                "key": "ansible.pipelining",
                "value": True,
                "description": "启用SSH管道",
                "category": "ansible",
                "validation_rule": {"type": "boolean"},
                "default_value": True
            },
            
            # 应用配置
            {
                "key": "app.max_concurrent_tasks",
                "value": 10,
                "description": "最大并发任务数",
                "category": "performance",
                "validation_rule": {"type": "integer", "min": 1, "max": 100},
                "default_value": 10
            },
            {
                "key": "app.task_timeout",
                "value": 3600,
                "description": "任务超时时间（秒）",
                "category": "performance",
                "validation_rule": {"type": "integer", "min": 60, "max": 86400},
                "default_value": 3600
            },
            {
                "key": "app.log_retention_days",
                "value": 30,
                "description": "日志保留天数",
                "category": "maintenance",
                "validation_rule": {"type": "integer", "min": 1, "max": 365},
                "default_value": 30
            },
            {
                "key": "app.auto_cleanup_enabled",
                "value": True,
                "description": "启用自动清理",
                "category": "maintenance",
                "validation_rule": {"type": "boolean"},
                "default_value": True
            },
            
            # 安全配置
            {
                "key": "security.session_timeout",
                "value": 3600,
                "description": "会话超时时间（秒）",
                "category": "security",
                "validation_rule": {"type": "integer", "min": 300, "max": 86400},
                "default_value": 3600
            },
            {
                "key": "security.max_login_attempts",
                "value": 5,
                "description": "最大登录尝试次数",
                "category": "security",
                "validation_rule": {"type": "integer", "min": 1, "max": 20},
                "default_value": 5
            },
            {
                "key": "security.password_min_length",
                "value": 8,
                "description": "密码最小长度",
                "category": "security",
                "validation_rule": {"type": "integer", "min": 6, "max": 50},
                "default_value": 8
            },
            
            # UI配置
            {
                "key": "ui.theme",
                "value": "glassmorphism",
                "description": "界面主题",
                "category": "ui",
                "validation_rule": {"type": "string", "enum": ["glassmorphism", "dark", "light"]},
                "default_value": "glassmorphism"
            },
            {
                "key": "ui.language",
                "value": "zh-CN",
                "description": "界面语言",
                "category": "ui",
                "validation_rule": {"type": "string", "enum": ["zh-CN", "en-US"]},
                "default_value": "zh-CN"
            },
            {
                "key": "ui.items_per_page",
                "value": 20,
                "description": "每页显示项目数",
                "category": "ui",
                "validation_rule": {"type": "integer", "min": 5, "max": 100},
                "default_value": 20
            }
        ]
    
    async def get_config_value(self, key: str, default: Any = None) -> Any:
        """
        获取配置值
        
        Args:
            key: 配置键名
            default: 默认值
            
        Returns:
            Any: 配置值
        """
        return await self.system_config_service.get_config_value(key, default)
    
    async def set_config_value(self, key: str, value: Any) -> Tuple[bool, Optional[str]]:
        """
        设置配置值
        
        Args:
            key: 配置键名
            value: 配置值
            
        Returns:
            Tuple[bool, Optional[str]]: (是否成功, 错误信息)
        """
        try:
            success = await self.system_config_service.set_config_value(key, value)
            
            # 如果是Ansible配置，同步更新配置文件
            if key.startswith("ansible.") and success:
                await self._sync_ansible_config()
            
            return success, None
        except Exception as e:
            return False, str(e)
    
    async def get_configs_by_category(self, category: str) -> Dict[str, Any]:
        """
        根据分类获取配置
        
        Args:
            category: 配置分类
            
        Returns:
            Dict[str, Any]: 配置字典
        """
        configs = await self.system_config_service.get_configs_by_category(category)
        return {
            config.key: {
                "value": config.get_value(),
                "description": config.description,
                "is_sensitive": config.is_sensitive,
                "is_readonly": config.is_readonly,
                "requires_restart": config.requires_restart,
                "validation_rule": config.get_validation_rule(),
                "default_value": config.get_default_value()
            }
            for config in configs
        }
    
    async def update_multiple_configs(self, config_updates: Dict[str, Any]) -> Dict[str, Any]:
        """
        批量更新配置
        
        Args:
            config_updates: 配置更新字典
            
        Returns:
            Dict[str, Any]: 更新结果
        """
        # 先验证所有配置
        validation_errors = await self.system_config_service.validate_config_batch(config_updates)
        if validation_errors:
            return {
                "success": False,
                "errors": validation_errors,
                "updated": {}
            }
        
        # 执行更新
        results = await self.system_config_service.update_multiple_configs(config_updates)
        
        # 检查是否有Ansible配置更新
        ansible_updated = any(key.startswith("ansible.") for key in config_updates.keys())
        if ansible_updated:
            await self._sync_ansible_config()
        
        return {
            "success": all(results.values()),
            "errors": {},
            "updated": results
        }
    
    async def reset_config_to_default(self, key: str) -> Tuple[bool, Optional[str]]:
        """
        重置配置为默认值
        
        Args:
            key: 配置键名
            
        Returns:
            Tuple[bool, Optional[str]]: (是否成功, 错误信息)
        """
        try:
            success = await self.system_config_service.reset_config_to_default(key)
            
            if key.startswith("ansible.") and success:
                await self._sync_ansible_config()
            
            return success, None
        except Exception as e:
            return False, str(e)
    
    async def get_ansible_config_file_content(self) -> str:
        """
        获取Ansible配置文件内容
        
        Returns:
            str: 配置文件内容
        """
        try:
            return self.ansible_config_path.read_text(encoding='utf-8')
        except FileNotFoundError:
            return ""
        except Exception as e:
            raise Exception(f"读取Ansible配置文件失败: {str(e)}")
    
    async def update_ansible_config_file(self, content: str) -> Tuple[bool, Optional[str]]:
        """
        更新Ansible配置文件
        
        Args:
            content: 新的配置文件内容
            
        Returns:
            Tuple[bool, Optional[str]]: (是否成功, 错误信息)
        """
        try:
            # 验证配置文件格式
            is_valid, error_msg = self._validate_ansible_config_content(content)
            if not is_valid:
                return False, error_msg
            
            # 备份原文件
            if self.ansible_config_path.exists():
                shutil.copy2(self.ansible_config_path, self.ansible_config_backup_path)
            
            # 写入新内容
            self.ansible_config_path.write_text(content, encoding='utf-8')
            
            # 同步到数据库配置
            await self._sync_config_from_file()
            
            return True, None
        except Exception as e:
            return False, f"更新Ansible配置文件失败: {str(e)}"
    
    async def restore_ansible_config_backup(self) -> Tuple[bool, Optional[str]]:
        """
        恢复Ansible配置文件备份
        
        Returns:
            Tuple[bool, Optional[str]]: (是否成功, 错误信息)
        """
        try:
            if not self.ansible_config_backup_path.exists():
                return False, "备份文件不存在"
            
            shutil.copy2(self.ansible_config_backup_path, self.ansible_config_path)
            await self._sync_config_from_file()
            
            return True, None
        except Exception as e:
            return False, f"恢复配置文件失败: {str(e)}"
    
    async def _sync_ansible_config(self) -> None:
        """
        将数据库中的Ansible配置同步到配置文件
        """
        try:
            # 获取所有Ansible配置
            ansible_configs = await self.system_config_service.get_ansible_configs()
            
            # 读取现有配置文件
            config = configparser.ConfigParser()
            if self.ansible_config_path.exists():
                config.read(self.ansible_config_path, encoding='utf-8')
            
            # 确保必要的section存在
            if 'defaults' not in config:
                config.add_section('defaults')
            if 'ssh_connection' not in config:
                config.add_section('ssh_connection')
            if 'inventory' not in config:
                config.add_section('inventory')
            
            # 更新配置值
            for key, value in ansible_configs.items():
                if key in ['inventory', 'host_key_checking', 'timeout', 'gathering', 'log_path', 'forks']:
                    config.set('defaults', key, str(value))
                elif key in ['ssh_args', 'pipelining']:
                    config.set('ssh_connection', key, str(value))
            
            # 写入文件
            with open(self.ansible_config_path, 'w', encoding='utf-8') as f:
                config.write(f)
                
        except Exception as e:
            raise Exception(f"同步Ansible配置失败: {str(e)}")
    
    async def _sync_config_from_file(self) -> None:
        """
        从配置文件同步配置到数据库
        """
        try:
            if not self.ansible_config_path.exists():
                return
            
            config = configparser.ConfigParser()
            config.read(self.ansible_config_path, encoding='utf-8')
            
            # 同步defaults section
            if 'defaults' in config:
                for key, value in config['defaults'].items():
                    db_key = f"ansible.{key}"
                    await self._update_config_from_file_value(db_key, value)
            
            # 同步ssh_connection section
            if 'ssh_connection' in config:
                for key, value in config['ssh_connection'].items():
                    db_key = f"ansible.{key}"
                    await self._update_config_from_file_value(db_key, value)
                    
        except Exception as e:
            raise Exception(f"从配置文件同步失败: {str(e)}")
    
    async def _update_config_from_file_value(self, key: str, value: str) -> None:
        """
        从文件值更新数据库配置
        
        Args:
            key: 配置键名
            value: 配置值（字符串）
        """
        config = await self.system_config_service.get_config_by_key(key)
        if not config:
            return
        
        # 根据验证规则转换类型
        rule = config.get_validation_rule()
        if rule and 'type' in rule:
            if rule['type'] == 'boolean':
                value = value.lower() in ('true', 'yes', '1', 'on')
            elif rule['type'] == 'integer':
                try:
                    value = int(value)
                except ValueError:
                    return
        
        config.set_value(value)
        await self.db.commit()
    
    def _validate_ansible_config_content(self, content: str) -> Tuple[bool, Optional[str]]:
        """
        验证Ansible配置文件内容
        
        Args:
            content: 配置文件内容
            
        Returns:
            Tuple[bool, Optional[str]]: (是否有效, 错误信息)
        """
        try:
            config = configparser.ConfigParser()
            config.read_string(content)
            
            # 检查必要的section
            required_sections = ['defaults']
            for section in required_sections:
                if section not in config:
                    return False, f"缺少必要的配置段: [{section}]"
            
            # 验证关键配置项
            if 'defaults' in config:
                defaults = config['defaults']
                
                # 验证数值类型配置
                numeric_configs = ['timeout', 'forks', 'poll_interval']
                for key in numeric_configs:
                    if key in defaults:
                        try:
                            int(defaults[key])
                        except ValueError:
                            return False, f"配置项 {key} 必须是数字"
                
                # 验证布尔类型配置
                boolean_configs = ['host_key_checking', 'display_skipped_hosts', 'display_ok_hosts']
                for key in boolean_configs:
                    if key in defaults:
                        value = defaults[key].lower()
                        if value not in ('true', 'false', 'yes', 'no', '1', '0', 'on', 'off'):
                            return False, f"配置项 {key} 必须是布尔值"
            
            return True, None
        except configparser.Error as e:
            return False, f"配置文件格式错误: {str(e)}"
        except Exception as e:
            return False, f"验证配置文件时发生错误: {str(e)}"
    
    async def get_config_categories(self) -> List[Dict[str, Any]]:
        """
        获取所有配置分类及其统计信息
        
        Returns:
            List[Dict[str, Any]]: 分类信息列表
        """
        categories = await self.system_config_service.get_all_categories()
        result = []
        
        for category in categories:
            configs = await self.system_config_service.get_configs_by_category(category)
            result.append({
                "name": category,
                "display_name": self._get_category_display_name(category),
                "count": len(configs),
                "description": self._get_category_description(category)
            })
        
        return result
    
    def _get_category_display_name(self, category: str) -> str:
        """
        获取分类显示名称
        
        Args:
            category: 分类名称
            
        Returns:
            str: 显示名称
        """
        display_names = {
            "ansible": "Ansible配置",
            "security": "安全设置",
            "performance": "性能配置",
            "maintenance": "维护设置",
            "ui": "界面配置",
            "general": "通用设置"
        }
        return display_names.get(category, category)
    
    def _get_category_description(self, category: str) -> str:
        """
        获取分类描述
        
        Args:
            category: 分类名称
            
        Returns:
            str: 分类描述
        """
        descriptions = {
            "ansible": "Ansible执行引擎相关配置",
            "security": "系统安全和认证相关配置",
            "performance": "系统性能和资源使用配置",
            "maintenance": "系统维护和清理配置",
            "ui": "用户界面显示和交互配置",
            "general": "其他通用系统配置"
        }
        return descriptions.get(category, "")
    
    async def validate_config_changes(self, changes: Dict[str, Any]) -> Dict[str, Any]:
        """
        验证配置变更
        
        Args:
            changes: 配置变更字典
            
        Returns:
            Dict[str, Any]: 验证结果
        """
        validation_errors = await self.system_config_service.validate_config_batch(changes)
        
        # 检查需要重启的配置
        restart_required = []
        for key in changes.keys():
            config = await self.system_config_service.get_config_by_key(key)
            if config and config.requires_restart:
                restart_required.append(key)
        
        return {
            "valid": len(validation_errors) == 0,
            "errors": validation_errors,
            "restart_required": restart_required,
            "warnings": self._get_config_warnings(changes)
        }
    
    def _get_config_warnings(self, changes: Dict[str, Any]) -> List[str]:
        """
        获取配置变更警告
        
        Args:
            changes: 配置变更字典
            
        Returns:
            List[str]: 警告信息列表
        """
        warnings = []
        
        # 检查性能相关警告
        if "ansible.forks" in changes and changes["ansible.forks"] > 20:
            warnings.append("并发数设置过高可能影响系统性能")
        
        if "ansible.timeout" in changes and changes["ansible.timeout"] < 10:
            warnings.append("连接超时时间过短可能导致任务执行失败")
        
        if "app.max_concurrent_tasks" in changes and changes["app.max_concurrent_tasks"] > 50:
            warnings.append("最大并发任务数过高可能导致系统资源不足")
        
        return warnings
    
    async def create_config_backup(self, backup_name: str, description: Optional[str] = None, 
                                 categories: Optional[List[str]] = None) -> Tuple[bool, Optional[str]]:
        """
        创建配置备份
        
        Args:
            backup_name: 备份名称
            description: 备份描述
            categories: 要备份的配置分类
            
        Returns:
            Tuple[bool, Optional[str]]: (是否成功, 错误信息)
        """
        try:
            import json
            from datetime import datetime
            from ansible_web_ui.utils.timezone import now
            
            # 创建备份目录
            backup_dir = Path("data/backups/configs")
            backup_dir.mkdir(parents=True, exist_ok=True)
            
            # 获取要备份的配置
            backup_data = {
                "metadata": {
                    "name": backup_name,
                    "description": description or "",
                    "created_at": now().isoformat(),
                    "categories": categories or [],
                    "version": "1.0"
                },
                "configs": {}
            }
            
            if categories:
                # 备份指定分类的配置
                for category in categories:
                    configs = await self.get_configs_by_category(category)
                    for key, config_data in configs.items():
                        backup_data["configs"][key] = config_data
            else:
                # 备份所有配置
                all_categories = await self.system_config_service.get_all_categories()
                for category in all_categories:
                    configs = await self.get_configs_by_category(category)
                    for key, config_data in configs.items():
                        backup_data["configs"][key] = config_data
            
            # 保存备份文件
            backup_file = backup_dir / f"{backup_name}.json"
            with open(backup_file, 'w', encoding='utf-8') as f:
                json.dump(backup_data, f, ensure_ascii=False, indent=2)
            
            return True, None
        except Exception as e:
            return False, f"创建配置备份失败: {str(e)}"
    
    async def list_config_backups(self) -> List[Dict[str, Any]]:
        """
        列出所有配置备份
        
        Returns:
            List[Dict[str, Any]]: 备份信息列表
        """
        try:
            import json
            from datetime import datetime
            
            backup_dir = Path("data/backups/configs")
            if not backup_dir.exists():
                return []
            
            backups = []
            for backup_file in backup_dir.glob("*.json"):
                try:
                    with open(backup_file, 'r', encoding='utf-8') as f:
                        backup_data = json.load(f)
                    
                    metadata = backup_data.get("metadata", {})
                    configs = backup_data.get("configs", {})
                    
                    # 获取文件大小
                    file_size = backup_file.stat().st_size
                    
                    # 统计分类
                    categories = set()
                    for key in configs.keys():
                        if "." in key:
                            category = key.split(".")[0]
                            categories.add(category)
                    
                    backup_info = {
                        "name": metadata.get("name", backup_file.stem),
                        "description": metadata.get("description", ""),
                        "created_at": metadata.get("created_at", ""),
                        "size": file_size,
                        "config_count": len(configs),
                        "categories": list(categories)
                    }
                    backups.append(backup_info)
                except Exception:
                    # 跳过损坏的备份文件
                    continue
            
            # 按创建时间排序
            backups.sort(key=lambda x: x["created_at"], reverse=True)
            return backups
        except Exception:
            return []
    
    async def restore_config_backup(self, backup_name: str, overwrite: bool = False, 
                                  categories: Optional[List[str]] = None) -> Tuple[bool, Optional[str], Dict[str, str]]:
        """
        恢复配置备份
        
        Args:
            backup_name: 备份名称
            overwrite: 是否覆盖现有配置
            categories: 要恢复的配置分类
            
        Returns:
            Tuple[bool, Optional[str], Dict[str, str]]: (是否成功, 错误信息, 恢复结果详情)
        """
        try:
            import json
            
            backup_dir = Path("data/backups/configs")
            backup_file = backup_dir / f"{backup_name}.json"
            
            if not backup_file.exists():
                return False, f"备份文件 '{backup_name}' 不存在", {}
            
            # 读取备份数据
            with open(backup_file, 'r', encoding='utf-8') as f:
                backup_data = json.load(f)
            
            configs = backup_data.get("configs", {})
            results = {}
            
            # 过滤要恢复的配置
            if categories:
                filtered_configs = {}
                for key, config_data in configs.items():
                    if "." in key:
                        category = key.split(".")[0]
                        if category in categories:
                            filtered_configs[key] = config_data
                configs = filtered_configs
            
            # 恢复配置
            for key, config_data in configs.items():
                try:
                    # 检查配置是否已存在
                    existing_config = await self.system_config_service.get_config_by_key(key)
                    
                    if existing_config and not overwrite:
                        results[key] = "跳过（配置已存在）"
                        continue
                    
                    # 恢复配置值
                    success, error = await self.set_config_value(key, config_data["value"])
                    if success:
                        results[key] = "恢复成功"
                    else:
                        results[key] = f"恢复失败: {error}"
                except Exception as e:
                    results[key] = f"恢复失败: {str(e)}"
            
            success_count = sum(1 for status in results.values() if "成功" in status)
            total_count = len(results)
            
            return success_count > 0, None, results
        except Exception as e:
            return False, f"恢复配置备份失败: {str(e)}", {}
    
    async def delete_config_backup(self, backup_name: str) -> Tuple[bool, Optional[str]]:
        """
        删除配置备份
        
        Args:
            backup_name: 备份名称
            
        Returns:
            Tuple[bool, Optional[str]]: (是否成功, 错误信息)
        """
        try:
            backup_dir = Path("data/backups/configs")
            backup_file = backup_dir / f"{backup_name}.json"
            
            if not backup_file.exists():
                return False, f"备份文件 '{backup_name}' 不存在"
            
            backup_file.unlink()
            return True, None
        except Exception as e:
            return False, f"删除配置备份失败: {str(e)}"
    
    async def compare_configs(self, backup_name: str) -> Tuple[bool, Optional[str], List[Dict[str, Any]]]:
        """
        比较当前配置与备份配置的差异
        
        Args:
            backup_name: 备份名称
            
        Returns:
            Tuple[bool, Optional[str], List[Dict[str, Any]]]: (是否成功, 错误信息, 差异列表)
        """
        try:
            import json
            
            backup_dir = Path("data/backups/configs")
            backup_file = backup_dir / f"{backup_name}.json"
            
            if not backup_file.exists():
                return False, f"备份文件 '{backup_name}' 不存在", []
            
            # 读取备份数据
            with open(backup_file, 'r', encoding='utf-8') as f:
                backup_data = json.load(f)
            
            backup_configs = backup_data.get("configs", {})
            differences = []
            
            # 获取当前所有配置
            current_configs = {}
            all_categories = await self.system_config_service.get_all_categories()
            for category in all_categories:
                configs = await self.get_configs_by_category(category)
                current_configs.update(configs)
            
            # 比较配置
            all_keys = set(backup_configs.keys()) | set(current_configs.keys())
            
            for key in all_keys:
                backup_value = backup_configs.get(key, {}).get("value")
                current_value = current_configs.get(key, {}).get("value")
                
                if key not in backup_configs:
                    # 新增的配置
                    differences.append({
                        "key": key,
                        "current_value": current_value,
                        "new_value": None,
                        "action": "delete"
                    })
                elif key not in current_configs:
                    # 删除的配置
                    differences.append({
                        "key": key,
                        "current_value": None,
                        "new_value": backup_value,
                        "action": "add"
                    })
                elif backup_value != current_value:
                    # 修改的配置
                    differences.append({
                        "key": key,
                        "current_value": current_value,
                        "new_value": backup_value,
                        "action": "update"
                    })
            
            return True, None, differences
        except Exception as e:
            return False, f"比较配置失败: {str(e)}", []
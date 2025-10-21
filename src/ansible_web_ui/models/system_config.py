"""
系统配置数据模型

定义系统配置参数和Ansible配置相关的数据结构。
"""

from typing import Any, Dict, Optional, Union
from sqlalchemy import Column, String, Text, Boolean, Integer
from ansible_web_ui.models.base import BaseModel
import json


class SystemConfig(BaseModel):
    """
    系统配置模型
    
    存储系统级别的配置参数，包括Ansible配置、应用设置等。
    """
    __tablename__ = "system_config"

    # 配置键值
    key = Column(
        String(100), 
        unique=True, 
        nullable=False, 
        index=True,
        comment="配置键名"
    )
    value = Column(
        Text, 
        nullable=False,
        comment="配置值（JSON格式存储）"
    )
    
    # 配置元信息
    description = Column(
        Text, 
        nullable=True,
        comment="配置描述"
    )
    category = Column(
        String(50), 
        nullable=False, 
        default="general",
        index=True,
        comment="配置分类"
    )
    
    # 配置属性
    is_sensitive = Column(
        Boolean, 
        nullable=False, 
        default=False,
        comment="是否为敏感信息"
    )
    is_readonly = Column(
        Boolean, 
        nullable=False, 
        default=False,
        comment="是否只读"
    )
    requires_restart = Column(
        Boolean, 
        nullable=False, 
        default=False,
        comment="修改后是否需要重启"
    )
    
    # 验证规则
    validation_rule = Column(
        Text, 
        nullable=True,
        comment="值验证规则（JSON格式）"
    )
    default_value = Column(
        Text, 
        nullable=True,
        comment="默认值"
    )

    def __repr__(self) -> str:
        return f"<SystemConfig(key='{self.key}', category='{self.category}')>"

    def get_value(self) -> Any:
        """
        获取配置值（自动解析JSON）
        
        Returns:
            Any: 解析后的配置值
        """
        try:
            return json.loads(self.value)
        except (json.JSONDecodeError, TypeError):
            return self.value

    def set_value(self, value: Any) -> None:
        """
        设置配置值（自动转换为JSON）
        
        Args:
            value: 要设置的值
        """
        if isinstance(value, (dict, list, tuple)):
            self.value = json.dumps(value, ensure_ascii=False)
        elif isinstance(value, (int, float, bool)):
            self.value = json.dumps(value)
        else:
            self.value = str(value)

    def get_validation_rule(self) -> Optional[Dict[str, Any]]:
        """
        获取验证规则
        
        Returns:
            Optional[Dict[str, Any]]: 验证规则字典
        """
        if not self.validation_rule:
            return None
        try:
            return json.loads(self.validation_rule)
        except (json.JSONDecodeError, TypeError):
            return None

    def set_validation_rule(self, rule: Dict[str, Any]) -> None:
        """
        设置验证规则
        
        Args:
            rule: 验证规则字典
        """
        self.validation_rule = json.dumps(rule, ensure_ascii=False)

    def get_default_value(self) -> Any:
        """
        获取默认值
        
        Returns:
            Any: 默认值
        """
        if not self.default_value:
            return None
        try:
            return json.loads(self.default_value)
        except (json.JSONDecodeError, TypeError):
            return self.default_value

    def validate_value(self, value: Any) -> tuple[bool, Optional[str]]:
        """
        验证配置值
        
        Args:
            value: 要验证的值
            
        Returns:
            tuple[bool, Optional[str]]: (是否有效, 错误信息)
        """
        rule = self.get_validation_rule()
        if not rule:
            return True, None

        # 类型验证
        if "type" in rule:
            expected_type = rule["type"]
            if expected_type == "string" and not isinstance(value, str):
                return False, f"值必须是字符串类型"
            elif expected_type == "integer" and not isinstance(value, int):
                return False, f"值必须是整数类型"
            elif expected_type == "boolean" and not isinstance(value, bool):
                return False, f"值必须是布尔类型"
            elif expected_type == "array" and not isinstance(value, list):
                return False, f"值必须是数组类型"

        # 范围验证
        if "min" in rule and isinstance(value, (int, float)) and value < rule["min"]:
            return False, f"值不能小于 {rule['min']}"
        if "max" in rule and isinstance(value, (int, float)) and value > rule["max"]:
            return False, f"值不能大于 {rule['max']}"

        # 长度验证
        if "min_length" in rule and isinstance(value, str) and len(value) < rule["min_length"]:
            return False, f"字符串长度不能小于 {rule['min_length']}"
        if "max_length" in rule and isinstance(value, str) and len(value) > rule["max_length"]:
            return False, f"字符串长度不能大于 {rule['max_length']}"

        # 枚举验证
        if "enum" in rule and value not in rule["enum"]:
            return False, f"值必须是以下选项之一: {', '.join(map(str, rule['enum']))}"

        return True, None

    @classmethod
    def get_ansible_configs(cls) -> Dict[str, Any]:
        """
        获取所有Ansible相关配置
        
        Returns:
            Dict[str, Any]: Ansible配置字典
        """
        # 这个方法需要在服务层实现，这里只是定义接口
        return {}

    @classmethod
    def get_app_configs(cls) -> Dict[str, Any]:
        """
        获取所有应用配置
        
        Returns:
            Dict[str, Any]: 应用配置字典
        """
        # 这个方法需要在服务层实现，这里只是定义接口
        return {}
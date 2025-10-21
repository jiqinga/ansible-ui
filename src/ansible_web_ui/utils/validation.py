"""
数据验证工具

提供主机配置、变量等数据的验证功能。
"""

import re
import json
import ipaddress
from typing import Any, Dict, List, Optional, Union, Tuple
from pydantic import ValidationError


def validate_hostname(hostname: str) -> Tuple[bool, Optional[str]]:
    """
    验证主机名格式
    
    Args:
        hostname: 主机名
        
    Returns:
        Tuple[bool, Optional[str]]: (是否有效, 错误信息)
    """
    if not hostname or not isinstance(hostname, str):
        return False, "主机名不能为空"
    
    if len(hostname) > 255:
        return False, "主机名长度不能超过255个字符"
    
    # 主机名格式验证：字母、数字、连字符、点
    if not re.match(r'^[a-zA-Z0-9]([a-zA-Z0-9\-\.]*[a-zA-Z0-9])?$', hostname):
        return False, "主机名格式无效，只能包含字母、数字、连字符和点"
    
    # 不能以连字符开头或结尾
    if hostname.startswith('-') or hostname.endswith('-'):
        return False, "主机名不能以连字符开头或结尾"
    
    # 不能包含连续的点
    if '..' in hostname:
        return False, "主机名不能包含连续的点"
    
    return True, None


def validate_ip_address(ip_str: str) -> Tuple[bool, Optional[str]]:
    """
    验证IP地址格式
    
    Args:
        ip_str: IP地址字符串
        
    Returns:
        Tuple[bool, Optional[str]]: (是否有效, 错误信息)
    """
    if not ip_str or not isinstance(ip_str, str):
        return False, "IP地址不能为空"
    
    try:
        ipaddress.ip_address(ip_str)
        return True, None
    except ValueError:
        return False, "IP地址格式无效"


def validate_ansible_host(ansible_host: str) -> Tuple[bool, Optional[str]]:
    """
    验证Ansible主机地址（IP或域名）
    
    Args:
        ansible_host: Ansible主机地址
        
    Returns:
        Tuple[bool, Optional[str]]: (是否有效, 错误信息)
    """
    if not ansible_host or not isinstance(ansible_host, str):
        return False, "Ansible主机地址不能为空"
    
    # 尝试验证为IP地址
    is_valid_ip, _ = validate_ip_address(ansible_host)
    if is_valid_ip:
        return True, None
    
    # 尝试验证为域名
    is_valid_hostname, error_msg = validate_hostname(ansible_host)
    if is_valid_hostname:
        return True, None
    
    return False, f"Ansible主机地址格式无效：{error_msg}"


def validate_port_number(port: Union[int, str]) -> Tuple[bool, Optional[str]]:
    """
    验证端口号
    
    Args:
        port: 端口号
        
    Returns:
        Tuple[bool, Optional[str]]: (是否有效, 错误信息)
    """
    try:
        port_int = int(port)
        if 1 <= port_int <= 65535:
            return True, None
        else:
            return False, "端口号必须在1-65535之间"
    except (ValueError, TypeError):
        return False, "端口号必须是有效的整数"


def validate_variable_name(var_name: str) -> Tuple[bool, Optional[str]]:
    """
    验证变量名格式
    
    Args:
        var_name: 变量名
        
    Returns:
        Tuple[bool, Optional[str]]: (是否有效, 错误信息)
    """
    if not var_name or not isinstance(var_name, str):
        return False, "变量名不能为空"
    
    # Ansible变量名规则：以字母或下划线开头，只能包含字母、数字、下划线
    if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', var_name):
        return False, "变量名必须以字母或下划线开头，只能包含字母、数字和下划线"
    
    # 检查保留字
    reserved_words = {
        'ansible_host', 'ansible_port', 'ansible_user', 'ansible_password',
        'ansible_ssh_private_key_file', 'ansible_become', 'ansible_become_user',
        'ansible_become_method', 'ansible_connection', 'inventory_hostname',
        'group_names', 'groups', 'hostvars', 'play_hosts', 'ansible_play_hosts'
    }
    
    if var_name in reserved_words:
        return False, f"变量名 '{var_name}' 是Ansible保留字，不能使用"
    
    return True, None


def validate_ansible_variables(variables: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    验证Ansible变量字典
    
    Args:
        variables: 变量字典
        
    Returns:
        Tuple[bool, List[str]]: (是否全部有效, 错误信息列表)
    """
    if not isinstance(variables, dict):
        return False, ["变量必须是字典格式"]
    
    errors = []
    
    for key, value in variables.items():
        # 验证变量名
        is_valid_name, name_error = validate_variable_name(key)
        if not is_valid_name:
            errors.append(f"变量名 '{key}': {name_error}")
            continue
        
        # 验证变量值（基本类型检查）
        if not _is_serializable_value(value):
            errors.append(f"变量 '{key}' 的值不能序列化为JSON")
    
    return len(errors) == 0, errors


def validate_json_data(data: Any) -> Tuple[bool, Optional[str]]:
    """
    验证数据是否可以序列化为JSON
    
    Args:
        data: 要验证的数据
        
    Returns:
        Tuple[bool, Optional[str]]: (是否有效, 错误信息)
    """
    try:
        json.dumps(data, ensure_ascii=False)
        return True, None
    except (TypeError, ValueError) as e:
        return False, f"数据无法序列化为JSON: {str(e)}"


def validate_group_name(group_name: str) -> Tuple[bool, Optional[str]]:
    """
    验证主机组名格式
    
    Args:
        group_name: 组名
        
    Returns:
        Tuple[bool, Optional[str]]: (是否有效, 错误信息)
    """
    if not group_name or not isinstance(group_name, str):
        return False, "组名不能为空"
    
    if len(group_name) > 100:
        return False, "组名长度不能超过100个字符"
    
    # 组名格式：字母、数字、下划线、连字符
    if not re.match(r'^[a-zA-Z0-9_\-]+$', group_name):
        return False, "组名只能包含字母、数字、下划线和连字符"
    
    # 检查Ansible保留组名
    reserved_groups = {'all', '_meta'}
    if group_name in reserved_groups:
        return False, f"组名 '{group_name}' 是Ansible保留字，不能使用"
    
    return True, None


def validate_tag_name(tag: str) -> Tuple[bool, Optional[str]]:
    """
    验证标签名格式
    
    Args:
        tag: 标签名
        
    Returns:
        Tuple[bool, Optional[str]]: (是否有效, 错误信息)
    """
    if not tag or not isinstance(tag, str):
        return False, "标签不能为空"
    
    tag = tag.strip()
    if not tag:
        return False, "标签不能为空白字符"
    
    if len(tag) > 50:
        return False, "标签长度不能超过50个字符"
    
    # 标签格式：字母、数字、下划线、连字符、中文
    if not re.match(r'^[a-zA-Z0-9_\-\u4e00-\u9fff]+$', tag):
        return False, "标签只能包含字母、数字、下划线、连字符和中文字符"
    
    return True, None


def validate_tags_list(tags: List[str]) -> Tuple[bool, List[str]]:
    """
    验证标签列表
    
    Args:
        tags: 标签列表
        
    Returns:
        Tuple[bool, List[str]]: (是否全部有效, 错误信息列表)
    """
    if not isinstance(tags, list):
        return False, ["标签必须是列表格式"]
    
    errors = []
    seen_tags = set()
    
    for tag in tags:
        is_valid, error_msg = validate_tag_name(tag)
        if not is_valid:
            errors.append(error_msg)
        elif tag in seen_tags:
            errors.append(f"标签 '{tag}' 重复")
        else:
            seen_tags.add(tag)
    
    return len(errors) == 0, errors


def sanitize_variable_name(name: str) -> str:
    """
    清理变量名，使其符合Ansible规范
    
    Args:
        name: 原始变量名
        
    Returns:
        str: 清理后的变量名
    """
    if not name:
        return "var"
    
    # 移除非法字符，只保留字母、数字、下划线
    sanitized = re.sub(r'[^a-zA-Z0-9_]', '_', name)
    
    # 确保以字母或下划线开头
    if sanitized and sanitized[0].isdigit():
        sanitized = f"var_{sanitized}"
    
    # 如果为空或只有下划线，使用默认名称
    if not sanitized or sanitized.replace('_', '') == '':
        sanitized = "var"
    
    return sanitized


def _is_serializable_value(value: Any) -> bool:
    """
    检查值是否可以序列化为JSON
    
    Args:
        value: 要检查的值
        
    Returns:
        bool: 是否可序列化
    """
    try:
        json.dumps(value, ensure_ascii=False)
        return True
    except (TypeError, ValueError):
        return False


def validate_ssh_key_path(key_path: str) -> Tuple[bool, Optional[str]]:
    """
    验证SSH密钥文件路径格式
    
    Args:
        key_path: SSH密钥文件路径
        
    Returns:
        Tuple[bool, Optional[str]]: (是否有效, 错误信息)
    """
    if not key_path or not isinstance(key_path, str):
        return False, "SSH密钥路径不能为空"
    
    # 基本路径格式检查
    if len(key_path) > 500:
        return False, "SSH密钥路径长度不能超过500个字符"
    
    # 检查是否包含危险字符
    dangerous_chars = ['..', '|', ';', '&', '$', '`']
    for char in dangerous_chars:
        if char in key_path:
            return False, f"SSH密钥路径不能包含危险字符: {char}"
    
    return True, None


def validate_become_method(method: str) -> Tuple[bool, Optional[str]]:
    """
    验证提权方法
    
    Args:
        method: 提权方法
        
    Returns:
        Tuple[bool, Optional[str]]: (是否有效, 错误信息)
    """
    if not method or not isinstance(method, str):
        return False, "提权方法不能为空"
    
    valid_methods = {'sudo', 'su', 'pbrun', 'pfexec', 'doas', 'dzdo', 'ksu', 'runas'}
    
    if method not in valid_methods:
        return False, f"提权方法必须是以下之一: {', '.join(valid_methods)}"
    
    return True, None

def validate_config_value(value: Any, validation_rule: Optional[Dict[str, Any]] = None) -> Tuple[bool, Optional[str]]:
    """
    验证配置值
    
    Args:
        value: 要验证的值
        validation_rule: 验证规则字典
        
    Returns:
        Tuple[bool, Optional[str]]: (是否有效, 错误信息)
    """
    if not validation_rule:
        return True, None
    
    # 类型验证
    if "type" in validation_rule:
        expected_type = validation_rule["type"]
        if expected_type == "string" and not isinstance(value, str):
            return False, "值必须是字符串类型"
        elif expected_type == "integer" and not isinstance(value, int):
            return False, "值必须是整数类型"
        elif expected_type == "boolean" and not isinstance(value, bool):
            return False, "值必须是布尔类型"
        elif expected_type == "array" and not isinstance(value, list):
            return False, "值必须是数组类型"
        elif expected_type == "object" and not isinstance(value, dict):
            return False, "值必须是对象类型"
    
    # 范围验证
    if "min" in validation_rule and isinstance(value, (int, float)):
        if value < validation_rule["min"]:
            return False, f"值不能小于 {validation_rule['min']}"
    
    if "max" in validation_rule and isinstance(value, (int, float)):
        if value > validation_rule["max"]:
            return False, f"值不能大于 {validation_rule['max']}"
    
    # 长度验证
    if "min_length" in validation_rule and isinstance(value, str):
        if len(value) < validation_rule["min_length"]:
            return False, f"字符串长度不能小于 {validation_rule['min_length']}"
    
    if "max_length" in validation_rule and isinstance(value, str):
        if len(value) > validation_rule["max_length"]:
            return False, f"字符串长度不能大于 {validation_rule['max_length']}"
    
    # 枚举验证
    if "enum" in validation_rule:
        if value not in validation_rule["enum"]:
            return False, f"值必须是以下选项之一: {', '.join(map(str, validation_rule['enum']))}"
    
    # 正则表达式验证
    if "pattern" in validation_rule and isinstance(value, str):
        pattern = validation_rule["pattern"]
        if not re.match(pattern, value):
            return False, f"值不符合格式要求: {pattern}"
    
    # 自定义验证函数
    if "custom_validator" in validation_rule:
        validator_name = validation_rule["custom_validator"]
        if validator_name == "ip_address":
            return validate_ip_address(value)
        elif validator_name == "hostname":
            return validate_hostname(value)
        elif validator_name == "port":
            return validate_port_number(value)
        elif validator_name == "ssh_key_path":
            return validate_ssh_key_path(value)
    
    return True, None


def validate_ansible_config_key(key: str, value: Any) -> Tuple[bool, Optional[str]]:
    """
    验证Ansible配置项
    
    Args:
        key: 配置键名
        value: 配置值
        
    Returns:
        Tuple[bool, Optional[str]]: (是否有效, 错误信息)
    """
    # 定义Ansible配置项的验证规则
    ansible_config_rules = {
        "inventory": {"type": "string", "min_length": 1},
        "host_key_checking": {"type": "boolean"},
        "timeout": {"type": "integer", "min": 1, "max": 300},
        "forks": {"type": "integer", "min": 1, "max": 100},
        "gathering": {"type": "string", "enum": ["implicit", "explicit", "smart"]},
        "log_path": {"type": "string", "min_length": 1},
        "ssh_args": {"type": "string"},
        "pipelining": {"type": "boolean"},
        "poll_interval": {"type": "integer", "min": 1, "max": 60},
        "transport": {"type": "string", "enum": ["smart", "ssh", "paramiko", "local"]},
        "stdout_callback": {"type": "string"},
        "stderr_callback": {"type": "string"},
        "callback_whitelist": {"type": "string"},
        "fact_caching": {"type": "string", "enum": ["memory", "jsonfile", "redis"]},
        "fact_caching_timeout": {"type": "integer", "min": 0, "max": 86400},
        "display_skipped_hosts": {"type": "boolean"},
        "display_ok_hosts": {"type": "boolean"},
        "control_path": {"type": "string"}
    }
    
    # 移除ansible.前缀
    config_key = key.replace("ansible.", "")
    
    if config_key in ansible_config_rules:
        rule = ansible_config_rules[config_key]
        return validate_config_value(value, rule)
    
    return True, None


def validate_app_config_key(key: str, value: Any) -> Tuple[bool, Optional[str]]:
    """
    验证应用配置项
    
    Args:
        key: 配置键名
        value: 配置值
        
    Returns:
        Tuple[bool, Optional[str]]: (是否有效, 错误信息)
    """
    # 定义应用配置项的验证规则
    app_config_rules = {
        "app.max_concurrent_tasks": {"type": "integer", "min": 1, "max": 100},
        "app.task_timeout": {"type": "integer", "min": 60, "max": 86400},
        "app.log_retention_days": {"type": "integer", "min": 1, "max": 365},
        "app.auto_cleanup_enabled": {"type": "boolean"},
        "security.session_timeout": {"type": "integer", "min": 300, "max": 86400},
        "security.max_login_attempts": {"type": "integer", "min": 1, "max": 20},
        "security.password_min_length": {"type": "integer", "min": 6, "max": 50},
        "ui.theme": {"type": "string", "enum": ["glassmorphism", "dark", "light"]},
        "ui.language": {"type": "string", "enum": ["zh-CN", "en-US"]},
        "ui.items_per_page": {"type": "integer", "min": 5, "max": 100}
    }
    
    if key in app_config_rules:
        rule = app_config_rules[key]
        return validate_config_value(value, rule)
    
    return True, None


def validate_file_path(file_path: str, must_exist: bool = False) -> Tuple[bool, Optional[str]]:
    """
    验证文件路径格式
    
    Args:
        file_path: 文件路径
        must_exist: 是否必须存在
        
    Returns:
        Tuple[bool, Optional[str]]: (是否有效, 错误信息)
    """
    if not file_path or not isinstance(file_path, str):
        return False, "文件路径不能为空"
    
    # 基本路径格式检查
    if len(file_path) > 500:
        return False, "文件路径长度不能超过500个字符"
    
    # 检查是否包含危险字符
    dangerous_chars = ['|', ';', '&', '\n', '`']
    for char in dangerous_chars:
        if char in file_path:
            return False, f"文件路径不能包含危险字符: {char}"
    
    # 检查路径遍历攻击
    if '..' in file_path:
        return False, "文件路径不能包含相对路径符号"
    
    # 如果需要检查文件是否存在
    if must_exist:
        import os
        if not os.path.exists(file_path):
            return False, "指定的文件不存在"
    
    return True, None


def validate_log_level(level: str) -> Tuple[bool, Optional[str]]:
    """
    验证日志级别
    
    Args:
        level: 日志级别
        
    Returns:
        Tuple[bool, Optional[str]]: (是否有效, 错误信息)
    """
    if not level or not isinstance(level, str):
        return False, "日志级别不能为空"
    
    valid_levels = {'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'}
    level_upper = level.upper()
    
    if level_upper not in valid_levels:
        return False, f"日志级别必须是以下之一: {', '.join(valid_levels)}"
    
    return True, None
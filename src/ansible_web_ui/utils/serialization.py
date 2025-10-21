"""
序列化工具

提供主机配置和Inventory数据的序列化和反序列化功能。
"""

import json
import yaml
import configparser
from typing import Any, Dict, List, Optional, Union, Tuple
from io import StringIO
import re


def serialize_host_config(host_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    序列化主机配置数据
    
    Args:
        host_data: 主机数据字典
        
    Returns:
        Dict[str, Any]: 序列化后的配置
    """
    config = {}
    
    # 基本连接参数
    if 'ansible_host' in host_data:
        config['ansible_host'] = host_data['ansible_host']
    
    if 'ansible_port' in host_data and host_data['ansible_port'] != 22:
        config['ansible_port'] = host_data['ansible_port']
    
    if 'ansible_user' in host_data and host_data['ansible_user']:
        config['ansible_user'] = host_data['ansible_user']
    
    if 'ansible_ssh_private_key_file' in host_data and host_data['ansible_ssh_private_key_file']:
        config['ansible_ssh_private_key_file'] = host_data['ansible_ssh_private_key_file']
    
    # 提权参数
    if host_data.get('ansible_become', False):
        config['ansible_become'] = True
        if 'ansible_become_user' in host_data and host_data['ansible_become_user']:
            config['ansible_become_user'] = host_data['ansible_become_user']
        if 'ansible_become_method' in host_data and host_data['ansible_become_method']:
            config['ansible_become_method'] = host_data['ansible_become_method']
    
    # 自定义变量
    if 'variables' in host_data and host_data['variables']:
        config.update(host_data['variables'])
    
    return config


def deserialize_host_config(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    反序列化主机配置数据
    
    Args:
        config: 配置字典
        
    Returns:
        Dict[str, Any]: 反序列化后的主机数据
    """
    host_data = {}
    variables = {}
    
    # 提取Ansible内置参数
    ansible_params = {
        'ansible_host', 'ansible_port', 'ansible_user', 'ansible_ssh_private_key_file',
        'ansible_become', 'ansible_become_user', 'ansible_become_method'
    }
    
    for key, value in config.items():
        if key in ansible_params:
            host_data[key] = value
        else:
            variables[key] = value
    
    if variables:
        host_data['variables'] = variables
    
    return host_data


def serialize_group_config(group_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    序列化主机组配置数据
    
    Args:
        group_data: 主机组数据字典
        
    Returns:
        Dict[str, Any]: 序列化后的配置
    """
    config = {}
    
    # 组变量
    if 'variables' in group_data and group_data['variables']:
        config.update(group_data['variables'])
    
    return config


def deserialize_group_config(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    反序列化主机组配置数据
    
    Args:
        config: 配置字典
        
    Returns:
        Dict[str, Any]: 反序列化后的组数据
    """
    return {'variables': config}


def generate_ansible_inventory_ini(
    hosts: List[Dict[str, Any]], 
    groups: List[Dict[str, Any]]
) -> str:
    """
    生成Ansible INI格式的inventory文件
    
    Args:
        hosts: 主机列表
        groups: 主机组列表
        
    Returns:
        str: INI格式的inventory内容
    """
    config = configparser.ConfigParser(allow_no_value=True)
    config.optionxform = str  # 保持键名大小写
    
    # 按组组织主机
    group_hosts = {}
    group_vars = {}
    
    # 收集组信息
    for group in groups:
        group_name = group['name']
        group_hosts[group_name] = []
        if group.get('variables'):
            group_vars[group_name] = group['variables']
    
    # 收集主机信息
    for host in hosts:
        if not host.get('is_active', True):
            continue
            
        group_name = host.get('group_name', 'ungrouped')
        hostname = host['hostname']
        
        if group_name not in group_hosts:
            group_hosts[group_name] = []
        
        # 生成主机行
        host_config = serialize_host_config(host)
        if len(host_config) == 1 and 'ansible_host' in host_config:
            # 只有ansible_host参数
            host_line = f"{hostname} ansible_host={host_config['ansible_host']}"
        else:
            # 多个参数
            params = []
            for key, value in host_config.items():
                if isinstance(value, bool):
                    params.append(f"{key}={'true' if value else 'false'}")
                else:
                    params.append(f"{key}={value}")
            host_line = f"{hostname} {' '.join(params)}"
        
        group_hosts[group_name].append(host_line)
    
    # 生成INI内容
    output = StringIO()
    
    # 写入主机组
    for group_name, host_lines in group_hosts.items():
        if host_lines:  # 只写入有主机的组
            output.write(f"[{group_name}]\n")
            for host_line in host_lines:
                output.write(f"{host_line}\n")
            output.write("\n")
    
    # 写入组变量
    for group_name, variables in group_vars.items():
        if variables and group_name in group_hosts and group_hosts[group_name]:
            output.write(f"[{group_name}:vars]\n")
            for key, value in variables.items():
                if isinstance(value, bool):
                    output.write(f"{key}={'true' if value else 'false'}\n")
                elif isinstance(value, (list, dict)):
                    output.write(f"{key}={json.dumps(value)}\n")
                else:
                    output.write(f"{key}={value}\n")
            output.write("\n")
    
    return output.getvalue()


def generate_ansible_inventory_yaml(
    hosts: List[Dict[str, Any]], 
    groups: List[Dict[str, Any]]
) -> str:
    """
    生成Ansible YAML格式的inventory文件
    
    Args:
        hosts: 主机列表
        groups: 主机组列表
        
    Returns:
        str: YAML格式的inventory内容
    """
    inventory = {'all': {'children': {}}}
    
    # 按组组织主机
    group_data = {}
    
    # 初始化组结构
    for group in groups:
        group_name = group['name']
        group_data[group_name] = {
            'hosts': {},
            'vars': group.get('variables', {})
        }
    
    # 添加主机到组
    for host in hosts:
        if not host.get('is_active', True):
            continue
            
        group_name = host.get('group_name', 'ungrouped')
        hostname = host['hostname']
        
        if group_name not in group_data:
            group_data[group_name] = {'hosts': {}, 'vars': {}}
        
        host_config = serialize_host_config(host)
        group_data[group_name]['hosts'][hostname] = host_config
    
    # 构建最终的inventory结构
    for group_name, data in group_data.items():
        if data['hosts']:  # 只包含有主机的组
            group_info = {'hosts': data['hosts']}
            if data['vars']:
                group_info['vars'] = data['vars']
            inventory['all']['children'][group_name] = group_info
    
    return yaml.dump(inventory, default_flow_style=False, allow_unicode=True, indent=2)


def generate_ansible_inventory_json(
    hosts: List[Dict[str, Any]], 
    groups: List[Dict[str, Any]]
) -> str:
    """
    生成Ansible JSON格式的inventory文件
    
    Args:
        hosts: 主机列表
        groups: 主机组列表
        
    Returns:
        str: JSON格式的inventory内容
    """
    inventory = {"_meta": {"hostvars": {}}}
    
    # 按组组织主机
    group_hosts = {}
    group_vars = {}
    
    # 收集组信息
    for group in groups:
        group_name = group['name']
        group_hosts[group_name] = []
        if group.get('variables'):
            group_vars[group_name] = group['variables']
    
    # 收集主机信息
    for host in hosts:
        if not host.get('is_active', True):
            continue
            
        group_name = host.get('group_name', 'ungrouped')
        hostname = host['hostname']
        
        if group_name not in group_hosts:
            group_hosts[group_name] = []
        
        group_hosts[group_name].append(hostname)
        
        # 添加主机变量到hostvars
        host_config = serialize_host_config(host)
        if host_config:
            inventory["_meta"]["hostvars"][hostname] = host_config
    
    # 添加组信息到inventory
    for group_name, host_list in group_hosts.items():
        if host_list:  # 只包含有主机的组
            group_info = {"hosts": host_list}
            if group_name in group_vars and group_vars[group_name]:
                group_info["vars"] = group_vars[group_name]
            inventory[group_name] = group_info
    
    return json.dumps(inventory, indent=2, ensure_ascii=False)


def parse_ansible_inventory_ini(content: str) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    解析Ansible INI格式的inventory文件
    
    Args:
        content: INI格式的inventory内容
        
    Returns:
        Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]: (主机列表, 主机组列表)
    """
    hosts = []
    groups = []
    group_vars = {}
    
    # 手动解析INI内容，因为configparser对于Ansible inventory格式支持不够好
    lines = content.strip().split('\n')
    current_section = None
    current_section_type = None  # 'hosts' or 'vars'
    
    for line in lines:
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        
        # 检查是否是section头
        if line.startswith('['):
            if not line.endswith(']'):
                raise ValueError(f"INI格式解析错误: 无效的section头 '{line}'")
            
            section_name = line[1:-1]
            if section_name.endswith(':vars'):
                current_section = section_name[:-5]
                current_section_type = 'vars'
                if current_section not in group_vars:
                    group_vars[current_section] = {}
            else:
                current_section = section_name
                current_section_type = 'hosts'
            continue
        
        if current_section is None:
            continue
        
        if current_section_type == 'vars':
            # 解析组变量
            if '=' in line:
                key, value = line.split('=', 1)
                group_vars[current_section][key.strip()] = _parse_ini_value(value.strip())
        
        elif current_section_type == 'hosts':
            # 解析主机行
            if '=' in line:
                # 包含变量的主机行
                hostname, host_vars = _parse_host_line(line)
            else:
                # 只有主机名的行
                hostname = line.strip()
                host_vars = {}
            
            # 合并主机配置
            host_config = deserialize_host_config(host_vars)
            host_data = {
                'hostname': hostname,
                'group_name': current_section,
                **host_config
            }
            
            # 确保有ansible_host
            if 'ansible_host' not in host_data:
                host_data['ansible_host'] = hostname
            
            hosts.append(host_data)
    
    # 创建组信息
    processed_groups = set()
    for host in hosts:
        group_name = host['group_name']
        if group_name not in processed_groups:
            group_data = {
                'name': group_name,
                'variables': group_vars.get(group_name, {})
            }
            groups.append(group_data)
            processed_groups.add(group_name)
    
    return hosts, groups


def _parse_ini_value(value: str) -> Any:
    """
    解析INI值，尝试转换为适当的Python类型
    
    Args:
        value: INI值字符串
        
    Returns:
        Any: 解析后的值
    """
    if not value:
        return ""
    
    # 尝试解析为布尔值
    if value.lower() in ('true', 'yes', '1'):
        return True
    elif value.lower() in ('false', 'no', '0'):
        return False
    
    # 尝试解析为数字
    try:
        if '.' in value:
            return float(value)
        else:
            return int(value)
    except ValueError:
        pass
    
    # 尝试解析为JSON
    try:
        return json.loads(value)
    except (json.JSONDecodeError, ValueError):
        pass
    
    # 返回原始字符串
    return value


def _parse_host_line(line: str) -> Tuple[str, Dict[str, Any]]:
    """
    解析主机行，提取主机名和变量
    
    Args:
        line: 主机行字符串
        
    Returns:
        Tuple[str, Dict[str, Any]]: (主机名, 变量字典)
    """
    parts = line.strip().split()
    if not parts:
        raise ValueError("主机行不能为空")
    
    hostname = parts[0]
    variables = {}
    
    # 解析key=value对
    for part in parts[1:]:
        if '=' in part:
            key, value = part.split('=', 1)
            variables[key] = _parse_ini_value(value)
    
    return hostname, variables


def export_inventory_to_file(
    hosts: List[Dict[str, Any]], 
    groups: List[Dict[str, Any]], 
    format_type: str = "ini"
) -> str:
    """
    导出inventory到指定格式
    
    Args:
        hosts: 主机列表
        groups: 主机组列表
        format_type: 导出格式 (ini/yaml/json)
        
    Returns:
        str: 导出的内容
    """
    if format_type.lower() == "ini":
        return generate_ansible_inventory_ini(hosts, groups)
    elif format_type.lower() == "yaml":
        return generate_ansible_inventory_yaml(hosts, groups)
    elif format_type.lower() == "json":
        return generate_ansible_inventory_json(hosts, groups)
    else:
        raise ValueError(f"不支持的导出格式: {format_type}")


def import_inventory_from_content(
    content: str, 
    format_type: str = "ini"
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    从内容导入inventory
    
    Args:
        content: inventory内容
        format_type: 格式类型 (ini/yaml/json)
        
    Returns:
        Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]: (主机列表, 主机组列表)
    """
    if format_type.lower() == "ini":
        return parse_ansible_inventory_ini(content)
    elif format_type.lower() == "yaml":
        return _parse_ansible_inventory_yaml(content)
    elif format_type.lower() == "json":
        return _parse_ansible_inventory_json(content)
    else:
        raise ValueError(f"不支持的导入格式: {format_type}")


def _parse_ansible_inventory_yaml(content: str) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    解析YAML格式的inventory
    
    Args:
        content: YAML内容
        
    Returns:
        Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]: (主机列表, 主机组列表)
    """
    try:
        data = yaml.safe_load(content)
    except yaml.YAMLError as e:
        raise ValueError(f"YAML格式解析错误: {str(e)}")
    
    hosts = []
    groups = []
    
    if not isinstance(data, dict) or 'all' not in data:
        raise ValueError("YAML inventory必须包含'all'组")
    
    all_group = data['all']
    if 'children' in all_group:
        for group_name, group_data in all_group['children'].items():
            group_info = {
                'name': group_name,
                'variables': group_data.get('vars', {})
            }
            groups.append(group_info)
            
            if 'hosts' in group_data:
                for hostname, host_vars in group_data['hosts'].items():
                    host_data = {
                        'hostname': hostname,
                        'group_name': group_name,
                        **deserialize_host_config(host_vars or {})
                    }
                    hosts.append(host_data)
    
    return hosts, groups


def _parse_ansible_inventory_json(content: str) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    解析JSON格式的inventory
    
    Args:
        content: JSON内容
        
    Returns:
        Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]: (主机列表, 主机组列表)
    """
    try:
        data = json.loads(content)
    except json.JSONDecodeError as e:
        raise ValueError(f"JSON格式解析错误: {str(e)}")
    
    hosts = []
    groups = []
    
    hostvars = data.get('_meta', {}).get('hostvars', {})
    
    for key, value in data.items():
        if key == '_meta':
            continue
        
        if isinstance(value, dict) and 'hosts' in value:
            group_name = key
            group_info = {
                'name': group_name,
                'variables': value.get('vars', {})
            }
            groups.append(group_info)
            
            for hostname in value['hosts']:
                host_vars = hostvars.get(hostname, {})
                host_data = {
                    'hostname': hostname,
                    'group_name': group_name,
                    **deserialize_host_config(host_vars)
                }
                hosts.append(host_data)
    
    return hosts, groups
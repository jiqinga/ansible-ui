"""
Playbook验证服务

提供YAML语法验证和Ansible playbook结构检查功能。
"""

import yaml
import re
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
from ansible_web_ui.schemas.playbook_schemas import PlaybookValidationResult, ValidationIssue


class PlaybookValidationService:
    """
    Playbook验证服务类
    
    负责验证Playbook的YAML语法和Ansible结构。
    """
    
    def __init__(self):
        """初始化验证服务"""
        # Ansible playbook必需的顶级键
        self.required_top_level_keys = {'hosts'}
        
        # 可选的顶级键
        self.optional_top_level_keys = {
            'name', 'vars', 'vars_files', 'vars_prompt', 'tasks', 'handlers',
            'roles', 'pre_tasks', 'post_tasks', 'tags', 'gather_facts',
            'remote_user', 'sudo', 'sudo_user', 'become', 'become_user',
            'become_method', 'connection', 'port', 'accelerate', 'accelerate_port',
            'accelerate_ipv6', 'serial', 'strategy', 'max_fail_percentage',
            'any_errors_fatal', 'ignore_errors', 'ignore_unreachable',
            'check_mode', 'diff', 'force_handlers', 'run_once', 'delegate_to',
            'delegate_facts', 'local_action', 'transport', 'environment',
            'no_log', 'when', 'block', 'rescue', 'always'
        }
        
        # 任务必需的键
        self.required_task_keys = set()  # 任务可以只有action模块
        
        # 任务可选的键
        self.optional_task_keys = {
            'name', 'action', 'when', 'with_items', 'with_dict', 'with_fileglob',
            'with_together', 'with_subelements', 'with_nested', 'with_random_choice',
            'with_first_found', 'with_lines', 'with_indexed_items', 'with_flattened',
            'with_sequence', 'loop', 'loop_control', 'until', 'retries', 'delay',
            'changed_when', 'failed_when', 'ignore_errors', 'ignore_unreachable',
            'register', 'delegate_to', 'delegate_facts', 'local_action',
            'run_once', 'become', 'become_user', 'become_method', 'remote_user',
            'sudo', 'sudo_user', 'connection', 'port', 'environment', 'no_log',
            'tags', 'notify', 'listen', 'check_mode', 'diff', 'vars',
            'args', 'async', 'poll', 'throttle', 'any_errors_fatal'
        }
        
        # 常见的Ansible模块
        self.common_modules = {
            'debug', 'copy', 'file', 'template', 'lineinfile', 'replace',
            'shell', 'command', 'script', 'raw', 'service', 'systemd',
            'package', 'yum', 'apt', 'pip', 'git', 'unarchive', 'get_url',
            'uri', 'wait_for', 'pause', 'fail', 'assert', 'set_fact',
            'include', 'include_tasks', 'include_vars', 'import_tasks',
            'import_playbook', 'meta', 'add_host', 'group_by', 'setup',
            'gather_facts', 'ping', 'user', 'group', 'authorized_key',
            'cron', 'mount', 'filesystem', 'lvg', 'lvol', 'parted',
            'firewalld', 'iptables', 'selinux', 'seboolean', 'docker_container',
            'docker_image', 'docker_network', 'docker_volume'
        }
    
    def validate_yaml_syntax(self, content: str) -> Tuple[bool, List[str]]:
        """
        验证YAML语法
        
        Args:
            content: YAML内容
            
        Returns:
            Tuple[bool, List[str]]: (是否有效, 错误列表)
        """
        errors = []
        
        try:
            # 尝试解析YAML
            yaml.safe_load(content)
            return True, []
            
        except yaml.YAMLError as e:
            error_msg = str(e)
            
            # 提取行号信息
            if hasattr(e, 'problem_mark'):
                mark = e.problem_mark
                error_msg = f"第{mark.line + 1}行，第{mark.column + 1}列: {error_msg}"
            
            errors.append(f"YAML语法错误: {error_msg}")
            return False, errors
        
        except Exception as e:
            errors.append(f"YAML解析失败: {str(e)}")
            return False, errors
    
    def validate_playbook_structure(self, content: str) -> Tuple[bool, List[str], List[str]]:
        """
        验证Ansible playbook结构
        
        Args:
            content: Playbook内容
            
        Returns:
            Tuple[bool, List[str], List[str]]: (是否有效, 错误列表, 警告列表)
        """
        errors = []
        warnings = []
        
        try:
            # 首先验证YAML语法
            is_valid_yaml, yaml_errors = self.validate_yaml_syntax(content)
            if not is_valid_yaml:
                return False, yaml_errors, warnings
            
            # 解析YAML内容
            try:
                data = yaml.safe_load(content)
            except Exception as e:
                errors.append(f"无法解析YAML内容: {str(e)}")
                return False, errors, warnings
            
            # 检查是否为空
            if data is None:
                errors.append("Playbook内容为空")
                return False, errors, warnings
            
            # 检查是否为列表（playbook应该是play的列表）
            if not isinstance(data, list):
                errors.append("Playbook必须是一个列表（包含一个或多个play）")
                return False, errors, warnings
            
            # 检查是否为空列表
            if len(data) == 0:
                errors.append("Playbook不能为空列表")
                return False, errors, warnings
            
            # 验证每个play
            for i, play in enumerate(data):
                play_errors, play_warnings = self._validate_play(play, i + 1)
                errors.extend(play_errors)
                warnings.extend(play_warnings)
            
            return len(errors) == 0, errors, warnings
            
        except Exception as e:
            errors.append(f"验证过程中发生错误: {str(e)}")
            return False, errors, warnings
    
    def _validate_play(self, play: Any, play_index: int) -> Tuple[List[str], List[str]]:
        """
        验证单个play
        
        Args:
            play: play数据
            play_index: play索引（从1开始）
            
        Returns:
            Tuple[List[str], List[str]]: (错误列表, 警告列表)
        """
        errors = []
        warnings = []
        
        # 检查play是否为字典
        if not isinstance(play, dict):
            errors.append(f"第{play_index}个play必须是字典格式")
            return errors, warnings
        
        # 检查必需的键
        for required_key in self.required_top_level_keys:
            if required_key not in play:
                errors.append(f"第{play_index}个play缺少必需的键: {required_key}")
        
        # 检查未知的键
        all_valid_keys = self.required_top_level_keys | self.optional_top_level_keys
        for key in play.keys():
            if key not in all_valid_keys and not self._is_module_name(key):
                warnings.append(f"第{play_index}个play包含未知的键: {key}")
        
        # 验证hosts字段
        if 'hosts' in play:
            hosts_errors, hosts_warnings = self._validate_hosts(play['hosts'], play_index)
            errors.extend(hosts_errors)
            warnings.extend(hosts_warnings)
        
        # 验证tasks字段
        if 'tasks' in play:
            tasks_errors, tasks_warnings = self._validate_tasks(play['tasks'], play_index)
            errors.extend(tasks_errors)
            warnings.extend(tasks_warnings)
        
        # 验证handlers字段
        if 'handlers' in play:
            handlers_errors, handlers_warnings = self._validate_handlers(play['handlers'], play_index)
            errors.extend(handlers_errors)
            warnings.extend(handlers_warnings)
        
        # 验证roles字段
        if 'roles' in play:
            roles_errors, roles_warnings = self._validate_roles(play['roles'], play_index)
            errors.extend(roles_errors)
            warnings.extend(roles_warnings)
        
        # 检查是否有任务定义
        has_tasks = any(key in play for key in ['tasks', 'roles', 'pre_tasks', 'post_tasks'])
        if not has_tasks:
            warnings.append(f"第{play_index}个play没有定义任何任务（tasks、roles、pre_tasks或post_tasks）")
        
        return errors, warnings
    
    def _validate_hosts(self, hosts: Any, play_index: int) -> Tuple[List[str], List[str]]:
        """
        验证hosts字段
        
        Args:
            hosts: hosts值
            play_index: play索引
            
        Returns:
            Tuple[List[str], List[str]]: (错误列表, 警告列表)
        """
        errors = []
        warnings = []
        
        if isinstance(hosts, str):
            # 字符串格式的hosts
            if not hosts.strip():
                errors.append(f"第{play_index}个play的hosts不能为空字符串")
            elif hosts.strip() == 'localhost':
                warnings.append(f"第{play_index}个play使用localhost作为目标主机")
        elif isinstance(hosts, list):
            # 列表格式的hosts
            if len(hosts) == 0:
                errors.append(f"第{play_index}个play的hosts列表不能为空")
            else:
                for i, host in enumerate(hosts):
                    if not isinstance(host, str):
                        errors.append(f"第{play_index}个play的hosts列表中第{i+1}项必须是字符串")
                    elif not host.strip():
                        errors.append(f"第{play_index}个play的hosts列表中第{i+1}项不能为空字符串")
        else:
            errors.append(f"第{play_index}个play的hosts必须是字符串或字符串列表")
        
        return errors, warnings
    
    def _validate_tasks(self, tasks: Any, play_index: int) -> Tuple[List[str], List[str]]:
        """
        验证tasks字段
        
        Args:
            tasks: tasks值
            play_index: play索引
            
        Returns:
            Tuple[List[str], List[str]]: (错误列表, 警告列表)
        """
        errors = []
        warnings = []
        
        if not isinstance(tasks, list):
            errors.append(f"第{play_index}个play的tasks必须是列表")
            return errors, warnings
        
        for i, task in enumerate(tasks):
            task_errors, task_warnings = self._validate_task(task, play_index, i + 1)
            errors.extend(task_errors)
            warnings.extend(task_warnings)
        
        return errors, warnings
    
    def _validate_task(self, task: Any, play_index: int, task_index: int) -> Tuple[List[str], List[str]]:
        """
        验证单个任务
        
        Args:
            task: 任务数据
            play_index: play索引
            task_index: 任务索引
            
        Returns:
            Tuple[List[str], List[str]]: (错误列表, 警告列表)
        """
        errors = []
        warnings = []
        
        if not isinstance(task, dict):
            errors.append(f"第{play_index}个play的第{task_index}个任务必须是字典格式")
            return errors, warnings
        
        # 检查是否有模块调用
        has_module = False
        module_count = 0
        
        for key in task.keys():
            if self._is_module_name(key):
                has_module = True
                module_count += 1
        
        if not has_module:
            errors.append(f"第{play_index}个play的第{task_index}个任务没有指定任何模块")
        elif module_count > 1:
            warnings.append(f"第{play_index}个play的第{task_index}个任务指定了多个模块，这可能不是预期的")
        
        # 检查任务名称
        if 'name' not in task:
            warnings.append(f"第{play_index}个play的第{task_index}个任务建议添加name字段以提高可读性")
        elif not isinstance(task['name'], str) or not task['name'].strip():
            warnings.append(f"第{play_index}个play的第{task_index}个任务的name应该是非空字符串")
        
        # 检查未知的键
        all_valid_keys = self.required_task_keys | self.optional_task_keys
        for key in task.keys():
            if key not in all_valid_keys and not self._is_module_name(key):
                warnings.append(f"第{play_index}个play的第{task_index}个任务包含未知的键: {key}")
        
        return errors, warnings
    
    def _validate_handlers(self, handlers: Any, play_index: int) -> Tuple[List[str], List[str]]:
        """
        验证handlers字段
        
        Args:
            handlers: handlers值
            play_index: play索引
            
        Returns:
            Tuple[List[str], List[str]]: (错误列表, 警告列表)
        """
        errors = []
        warnings = []
        
        if not isinstance(handlers, list):
            errors.append(f"第{play_index}个play的handlers必须是列表")
            return errors, warnings
        
        for i, handler in enumerate(handlers):
            handler_errors, handler_warnings = self._validate_task(handler, play_index, i + 1)
            # 将任务错误转换为handler错误
            handler_errors = [msg.replace("任务", "handler") for msg in handler_errors]
            handler_warnings = [msg.replace("任务", "handler") for msg in handler_warnings]
            errors.extend(handler_errors)
            warnings.extend(handler_warnings)
        
        return errors, warnings
    
    def _validate_roles(self, roles: Any, play_index: int) -> Tuple[List[str], List[str]]:
        """
        验证roles字段
        
        Args:
            roles: roles值
            play_index: play索引
            
        Returns:
            Tuple[List[str], List[str]]: (错误列表, 警告列表)
        """
        errors = []
        warnings = []
        
        if not isinstance(roles, list):
            errors.append(f"第{play_index}个play的roles必须是列表")
            return errors, warnings
        
        for i, role in enumerate(roles):
            if isinstance(role, str):
                # 简单的角色名
                if not role.strip():
                    errors.append(f"第{play_index}个play的第{i+1}个role名称不能为空")
            elif isinstance(role, dict):
                # 复杂的角色定义
                if 'role' not in role and 'name' not in role:
                    errors.append(f"第{play_index}个play的第{i+1}个role必须包含'role'或'name'字段")
            else:
                errors.append(f"第{play_index}个play的第{i+1}个role必须是字符串或字典")
        
        return errors, warnings
    
    def _is_module_name(self, key: str) -> bool:
        """
        检查键是否可能是模块名
        
        Args:
            key: 键名
            
        Returns:
            bool: 是否可能是模块名
        """
        # 首先检查是否是已知的任务关键字，如果是则不是模块名
        all_task_keys = self.required_task_keys | self.optional_task_keys
        if key in all_task_keys:
            return False
        
        # 检查是否是已知的常见模块
        if key in self.common_modules:
            return True
        
        # 检查是否是带命名空间的模块（如 ansible.builtin.debug）
        if '.' in key and all(part.replace('_', '').replace('-', '').isalnum() for part in key.split('.')):
            return True
        
        # 检查是否符合模块名的一般模式
        # 模块名通常是小写字母、数字和下划线的组合，但要排除已知的任务关键字
        if re.match(r'^[a-z][a-z0-9_]*$', key) and key not in all_task_keys:
            return True
        
        return False
    
    def _parse_message_to_issue(self, message: str, severity: str = 'warning') -> ValidationIssue:
        """
        将字符串消息解析为结构化的验证问题
        
        Args:
            message: 错误或警告消息
            severity: 严重程度 ('error' 或 'warning')
            
        Returns:
            ValidationIssue: 结构化的验证问题
        """
        # 尝试从消息中提取行号和列号
        # 格式示例: "第1个play的第2个任务建议添加name字段"
        line = 0
        column = 0
        suggestion = None
        
        # 提取行号（play索引）
        play_match = re.search(r'第(\d+)个play', message)
        if play_match:
            line = int(play_match.group(1))
        
        # 提取任务索引
        task_match = re.search(r'第(\d+)个任务', message)
        if task_match:
            column = int(task_match.group(1))
        
        # 提取建议
        if '建议' in message:
            parts = message.split('建议')
            if len(parts) > 1:
                suggestion = '建议' + parts[1]
        
        return ValidationIssue(
            line=line,
            column=column,
            message=message,
            suggestion=suggestion,
            severity=severity
        )
    
    def validate_playbook_content(self, content: str) -> PlaybookValidationResult:
        """
        完整验证Playbook内容
        
        Args:
            content: Playbook内容
            
        Returns:
            PlaybookValidationResult: 验证结果
        """
        # 首先验证YAML语法
        is_valid_yaml, yaml_errors = self.validate_yaml_syntax(content)
        
        if not is_valid_yaml:
            # 将字符串错误转换为结构化对象
            error_issues = [self._parse_message_to_issue(error, 'error') for error in yaml_errors]
            
            return PlaybookValidationResult(
                is_valid=False,
                errors=error_issues,
                warnings=[],
                syntax_errors=[{
                    'type': 'yaml_syntax',
                    'message': error,
                    'line': None,
                    'column': None
                } for error in yaml_errors]
            )
        
        # 验证Playbook结构
        is_valid_structure, structure_errors, structure_warnings = self.validate_playbook_structure(content)
        
        # 将字符串错误和警告转换为结构化对象
        error_issues = [self._parse_message_to_issue(error, 'error') for error in structure_errors]
        warning_issues = [self._parse_message_to_issue(warning, 'warning') for warning in structure_warnings]
        
        # 构建详细的语法错误信息
        syntax_errors = []
        
        # 添加结构错误到语法错误列表
        for error in structure_errors:
            syntax_errors.append({
                'type': 'structure',
                'message': error,
                'line': None,
                'column': None
            })
        
        return PlaybookValidationResult(
            is_valid=is_valid_structure,
            errors=error_issues,
            warnings=warning_issues,
            syntax_errors=syntax_errors
        )
    
    def validate_playbook_file(self, file_path: str) -> PlaybookValidationResult:
        """
        验证Playbook文件
        
        Args:
            file_path: 文件路径
            
        Returns:
            PlaybookValidationResult: 验证结果
        """
        try:
            path = Path(file_path)
            
            if not path.exists():
                error_msg = f"文件不存在: {file_path}"
                return PlaybookValidationResult(
                    is_valid=False,
                    errors=[ValidationIssue(
                        line=0,
                        column=0,
                        message=error_msg,
                        severity='error'
                    )],
                    warnings=[],
                    syntax_errors=[{
                        'type': 'file_error',
                        'message': error_msg,
                        'line': None,
                        'column': None
                    }]
                )
            
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            return self.validate_playbook_content(content)
            
        except UnicodeDecodeError as e:
            error_msg = f"文件编码错误: {str(e)}"
            return PlaybookValidationResult(
                is_valid=False,
                errors=[ValidationIssue(
                    line=0,
                    column=0,
                    message=error_msg,
                    severity='error'
                )],
                warnings=[],
                syntax_errors=[{
                    'type': 'encoding_error',
                    'message': error_msg,
                    'line': None,
                    'column': None
                }]
            )
        except Exception as e:
            error_msg = f"读取文件失败: {str(e)}"
            return PlaybookValidationResult(
                is_valid=False,
                errors=[ValidationIssue(
                    line=0,
                    column=0,
                    message=error_msg,
                    severity='error'
                )],
                warnings=[],
                syntax_errors=[{
                    'type': 'file_error',
                    'message': error_msg,
                    'line': None,
                    'column': None
                }]
            )
    
    def get_validation_suggestions(self, content: str) -> List[str]:
        """
        获取验证建议
        
        Args:
            content: Playbook内容
            
        Returns:
            List[str]: 建议列表
        """
        suggestions = []
        
        try:
            # 解析YAML内容
            data = yaml.safe_load(content)
            
            if isinstance(data, list) and len(data) > 0:
                for i, play in enumerate(data):
                    if isinstance(play, dict):
                        # 建议添加play名称
                        if 'name' not in play:
                            suggestions.append(f"建议为第{i+1}个play添加name字段以提高可读性")
                        
                        # 建议使用become而不是sudo
                        if 'sudo' in play:
                            suggestions.append(f"第{i+1}个play建议使用'become'替代已弃用的'sudo'")
                        
                        # 检查tasks
                        if 'tasks' in play and isinstance(play['tasks'], list):
                            for j, task in enumerate(play['tasks']):
                                if isinstance(task, dict):
                                    # 建议添加任务名称
                                    if 'name' not in task:
                                        suggestions.append(f"建议为第{i+1}个play的第{j+1}个任务添加name字段")
                                    
                                    # 建议使用become而不是sudo
                                    if 'sudo' in task:
                                        suggestions.append(f"第{i+1}个play的第{j+1}个任务建议使用'become'替代'sudo'")
        
        except Exception:
            # 如果解析失败，不提供建议
            pass
        
        return suggestions
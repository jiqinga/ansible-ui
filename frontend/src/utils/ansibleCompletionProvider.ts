/**
 * 🎯 Ansible Monaco Editor 智能提示提供器
 * 
 * 提供 Ansible Playbook 编写时的自动补全功能：
 * - Ansible 关键字
 * - 常用模块
 * - 任务属性
 * - 条件和循环语法
 */

import type * as Monaco from 'monaco-editor'

/**
 * 📝 Ansible 关键字补全
 */
const ANSIBLE_KEYWORDS = [
  { label: 'name', detail: '任务名称', insertText: 'name: ' },
  { label: 'hosts', detail: '目标主机', insertText: 'hosts: ' },
  { label: 'tasks', detail: '任务列表', insertText: 'tasks:\n  - ' },
  { label: 'vars', detail: '变量定义', insertText: 'vars:\n  ' },
  { label: 'become', detail: '提权执行', insertText: 'become: yes' },
  { label: 'become_user', detail: '提权用户', insertText: 'become_user: root' },
  { label: 'gather_facts', detail: '收集系统信息', insertText: 'gather_facts: yes' },
  { label: 'when', detail: '条件执行', insertText: 'when: ' },
  { label: 'loop', detail: '循环执行', insertText: 'loop:\n  - ' },
  { label: 'with_items', detail: '遍历列表', insertText: 'with_items:\n  - ' },
  { label: 'register', detail: '保存结果', insertText: 'register: ' },
  { label: 'ignore_errors', detail: '忽略错误', insertText: 'ignore_errors: yes' },
  { label: 'changed_when', detail: '变更条件', insertText: 'changed_when: ' },
  { label: 'failed_when', detail: '失败条件', insertText: 'failed_when: ' },
  { label: 'tags', detail: '任务标签', insertText: 'tags:\n  - ' },
  { label: 'notify', detail: '触发处理器', insertText: 'notify: ' },
  { label: 'handlers', detail: '处理器列表', insertText: 'handlers:\n  - ' },
  { label: 'roles', detail: '角色列表', insertText: 'roles:\n  - ' },
  { label: 'pre_tasks', detail: '前置任务', insertText: 'pre_tasks:\n  - ' },
  { label: 'post_tasks', detail: '后置任务', insertText: 'post_tasks:\n  - ' },
  { label: 'vars_files', detail: '变量文件', insertText: 'vars_files:\n  - ' },
  { label: 'environment', detail: '环境变量', insertText: 'environment:\n  ' },
  { label: 'delegate_to', detail: '委托执行', insertText: 'delegate_to: ' },
  { label: 'run_once', detail: '只运行一次', insertText: 'run_once: yes' },
  { label: 'serial', detail: '串行执行', insertText: 'serial: ' },
  { label: 'max_fail_percentage', detail: '最大失败百分比', insertText: 'max_fail_percentage: ' },
]

/**
 * 🔧 Ansible 常用模块补全
 */
const ANSIBLE_MODULES = [
  // 系统模块
  { label: 'shell', detail: '执行 Shell 命令', insertText: 'shell: |\n  ' },
  { label: 'command', detail: '执行命令', insertText: 'command: ' },
  { label: 'script', detail: '执行脚本', insertText: 'script: ' },
  { label: 'raw', detail: '执行原始命令', insertText: 'raw: ' },
  
  // 文件模块
  { label: 'copy', detail: '复制文件', insertText: 'copy:\n  src: \n  dest: ' },
  { label: 'file', detail: '管理文件', insertText: 'file:\n  path: \n  state: ' },
  { label: 'template', detail: '模板文件', insertText: 'template:\n  src: \n  dest: ' },
  { label: 'lineinfile', detail: '修改文件行', insertText: 'lineinfile:\n  path: \n  line: ' },
  { label: 'blockinfile', detail: '修改文件块', insertText: 'blockinfile:\n  path: \n  block: |\n    ' },
  { label: 'fetch', detail: '获取文件', insertText: 'fetch:\n  src: \n  dest: ' },
  { label: 'synchronize', detail: '同步文件', insertText: 'synchronize:\n  src: \n  dest: ' },
  
  // 包管理
  { label: 'apt', detail: 'Debian/Ubuntu 包管理', insertText: 'apt:\n  name: \n  state: present' },
  { label: 'yum', detail: 'RedHat/CentOS 包管理', insertText: 'yum:\n  name: \n  state: present' },
  { label: 'dnf', detail: 'Fedora 包管理', insertText: 'dnf:\n  name: \n  state: present' },
  { label: 'package', detail: '通用包管理', insertText: 'package:\n  name: \n  state: present' },
  { label: 'pip', detail: 'Python 包管理', insertText: 'pip:\n  name: \n  state: present' },
  
  // 服务管理
  { label: 'service', detail: '管理服务', insertText: 'service:\n  name: \n  state: started' },
  { label: 'systemd', detail: 'Systemd 服务', insertText: 'systemd:\n  name: \n  state: started' },
  
  // 用户管理
  { label: 'user', detail: '管理用户', insertText: 'user:\n  name: \n  state: present' },
  { label: 'group', detail: '管理组', insertText: 'group:\n  name: \n  state: present' },
  
  // Git
  { label: 'git', detail: 'Git 仓库', insertText: 'git:\n  repo: \n  dest: ' },
  
  // Docker
  { label: 'docker_container', detail: 'Docker 容器', insertText: 'docker_container:\n  name: \n  image: ' },
  { label: 'docker_image', detail: 'Docker 镜像', insertText: 'docker_image:\n  name: \n  source: pull' },
  
  // 调试
  { label: 'debug', detail: '调试输出', insertText: 'debug:\n  msg: ' },
  { label: 'assert', detail: '断言检查', insertText: 'assert:\n  that:\n    - ' },
  { label: 'fail', detail: '失败退出', insertText: 'fail:\n  msg: ' },
  
  // 其他
  { label: 'set_fact', detail: '设置变量', insertText: 'set_fact:\n  ' },
  { label: 'include_tasks', detail: '包含任务', insertText: 'include_tasks: ' },
  { label: 'import_tasks', detail: '导入任务', insertText: 'import_tasks: ' },
  { label: 'include_role', detail: '包含角色', insertText: 'include_role:\n  name: ' },
  { label: 'wait_for', detail: '等待条件', insertText: 'wait_for:\n  ' },
  { label: 'uri', detail: 'HTTP 请求', insertText: 'uri:\n  url: \n  method: GET' },
  { label: 'get_url', detail: '下载文件', insertText: 'get_url:\n  url: \n  dest: ' },
  { label: 'unarchive', detail: '解压文件', insertText: 'unarchive:\n  src: \n  dest: ' },
  { label: 'cron', detail: '定时任务', insertText: 'cron:\n  name: \n  job: ' },
  { label: 'mount', detail: '挂载文件系统', insertText: 'mount:\n  path: \n  src: \n  fstype: ' },
]

/**
 * 📋 Playbook 模板片段
 */
const ANSIBLE_SNIPPETS = [
  {
    label: 'playbook',
    detail: '完整 Playbook 模板',
    insertText: `---
- name: \${1:Playbook 名称}
  hosts: \${2:all}
  become: yes
  
  tasks:
    - name: \${3:任务名称}
      \${4:debug}:
        msg: "\${5:Hello Ansible}"
`
  },
  {
    label: 'task',
    detail: '任务模板',
    insertText: `- name: \${1:任务名称}
  \${2:shell}: \${3:命令}
  when: \${4:条件}
  register: \${5:result}
`
  },
  {
    label: 'handler',
    detail: '处理器模板',
    insertText: `- name: \${1:处理器名称}
  \${2:service}:
    name: \${3:服务名}
    state: restarted
`
  },
  {
    label: 'role',
    detail: '角色模板',
    insertText: `- role: \${1:角色名}
  vars:
    \${2:变量名}: \${3:值}
`
  },
]

/**
 * 🎯 注册 Ansible 智能提示提供器
 */
export function registerAnsibleCompletionProvider(monaco: typeof Monaco) {
  monaco.languages.registerCompletionItemProvider('yaml', {
    triggerCharacters: [' ', '-', '\n'],
    provideCompletionItems: (model, position) => {
      const word = model.getWordUntilPosition(position)
      const range = {
        startLineNumber: position.lineNumber,
        endLineNumber: position.lineNumber,
        startColumn: word.startColumn,
        endColumn: word.endColumn,
      }

      // 🔍 总是提供所有补全建议
      const suggestions: Monaco.languages.CompletionItem[] = []

      // 添加关键字
      ANSIBLE_KEYWORDS.forEach(item => {
        suggestions.push({
          label: item.label,
          kind: monaco.languages.CompletionItemKind.Keyword,
          detail: item.detail,
          insertText: item.insertText,
          range: range,
        })
      })

      // 添加模块
      ANSIBLE_MODULES.forEach(item => {
        suggestions.push({
          label: item.label,
          kind: monaco.languages.CompletionItemKind.Function,
          detail: item.detail,
          insertText: item.insertText,
          insertTextRules: monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet,
          range: range,
        })
      })

      // 添加代码片段
      ANSIBLE_SNIPPETS.forEach(item => {
        suggestions.push({
          label: item.label,
          kind: monaco.languages.CompletionItemKind.Snippet,
          detail: item.detail,
          insertText: item.insertText,
          insertTextRules: monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet,
          range: range,
        })
      })

      return { suggestions }
    },
  })
}

/**
 * 🎨 注册 Ansible 语法高亮增强
 */
export function registerAnsibleTheme(monaco: typeof Monaco) {
  monaco.editor.defineTheme('ansible-dark', {
    base: 'vs-dark',
    inherit: true,
    rules: [
      { token: 'keyword', foreground: 'C586C0', fontStyle: 'bold' },
      { token: 'string', foreground: 'CE9178' },
      { token: 'number', foreground: 'B5CEA8' },
      { token: 'comment', foreground: '6A9955', fontStyle: 'italic' },
    ],
    colors: {
      'editor.background': '#1e1e1e',
      'editor.foreground': '#d4d4d4',
      'editor.lineHighlightBackground': '#2a2a2a',
      'editorCursor.foreground': '#aeafad',
      'editor.selectionBackground': '#264f78',
    },
  })
}

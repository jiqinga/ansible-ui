/**
 * 🔧 Ansible配置面板
 * 
 * 功能：
 * - Ansible配置文件编辑
 * - 配置语法验证
 * - 配置备份和恢复
 * - 配置模板管理
 */

import React, { useState, useEffect, useRef } from 'react'
import { motion } from 'framer-motion'
import { useTranslation } from 'react-i18next'
import {
  WrenchScrewdriverIcon,
  DocumentTextIcon,
  CheckCircleIcon,
  ExclamationTriangleIcon,
  ArrowPathIcon,
  DocumentDuplicateIcon,
  ClockIcon,
  EyeIcon,
  PencilIcon
} from '@heroicons/react/24/outline'

import GlassCard from '../UI/GlassCard'
import GlassButton from '../UI/GlassButton'
import GlassModal from '../UI/GlassModal'
import { useNotification } from '../../contexts/NotificationContext'
import { AnsibleConfigService, SystemStatus } from '../../services/settingsService'

interface AnsibleConfigPanelProps {
  onRefresh?: () => void
  systemStatus?: SystemStatus | null
}

// 🏷️ Ansible配置文件信息类型
interface AnsibleConfigInfo {
  content: string
  is_valid: boolean
  last_modified?: string
  backup_available: boolean
}

// 📋 Ansible配置模板
const ANSIBLE_CONFIG_TEMPLATES = {
  basic: `[defaults]
# 基础配置
host_key_checking = False
inventory = ./inventory
remote_user = ansible
private_key_file = ~/.ssh/id_rsa
timeout = 30
gathering = implicit
fact_caching = memory
fact_caching_timeout = 86400

[inventory]
# 主机清单配置
enable_plugins = host_list, script, auto, yaml, ini, toml

[privilege_escalation]
# 权限提升配置
become = True
become_method = sudo
become_user = root
become_ask_pass = False

[ssh_connection]
# SSH连接配置
ssh_args = -C -o ControlMaster=auto -o ControlPersist=60s
pipelining = True
control_path = /tmp/ansible-ssh-%%h-%%p-%%r`,

  advanced: `[defaults]
# 高级配置
host_key_checking = False
inventory = ./inventory
remote_user = ansible
private_key_file = ~/.ssh/id_rsa
timeout = 30
gathering = smart
fact_caching = jsonfile
fact_caching_connection = /tmp/ansible_facts_cache
fact_caching_timeout = 86400
callback_plugins = profile_tasks
stdout_callback = yaml
bin_ansible_callbacks = True
log_path = /var/log/ansible.log
retry_files_enabled = False
roles_path = ./roles
collections_paths = ./collections

[inventory]
# 主机清单配置
enable_plugins = host_list, script, auto, yaml, ini, toml
cache = True
cache_plugin = jsonfile
cache_timeout = 3600
cache_connection = /tmp/ansible_inventory_cache

[privilege_escalation]
# 权限提升配置
become = True
become_method = sudo
become_user = root
become_ask_pass = False

[ssh_connection]
# SSH连接配置
ssh_args = -C -o ControlMaster=auto -o ControlPersist=60s -o UserKnownHostsFile=/dev/null
pipelining = True
control_path = /tmp/ansible-ssh-%%h-%%p-%%r
retries = 3

[persistent_connection]
# 持久连接配置
connect_timeout = 30
command_timeout = 30

[colors]
# 颜色配置
highlight = white
verbose = blue
warn = bright purple
error = red
debug = dark gray
deprecate = purple
skip = cyan
unreachable = red
ok = green
changed = yellow
diff_add = green
diff_remove = red
diff_lines = cyan`,

  performance: `[defaults]
# 性能优化配置
host_key_checking = False
inventory = ./inventory
remote_user = ansible
private_key_file = ~/.ssh/id_rsa
timeout = 10
gathering = smart
fact_caching = redis
fact_caching_connection = localhost:6379:0
fact_caching_timeout = 86400
forks = 50
poll_interval = 0.001
callback_plugins = profile_tasks
stdout_callback = yaml
strategy = free
retry_files_enabled = False

[inventory]
# 主机清单配置
enable_plugins = host_list, script, auto, yaml, ini, toml
cache = True
cache_plugin = redis
cache_timeout = 3600
cache_connection = localhost:6379:1

[privilege_escalation]
# 权限提升配置
become = True
become_method = sudo
become_user = root
become_ask_pass = False

[ssh_connection]
# SSH连接配置优化
ssh_args = -C -o ControlMaster=auto -o ControlPersist=300s -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no
pipelining = True
control_path = /tmp/ansible-ssh-%%h-%%p-%%r
retries = 2
control_path_dir = /tmp/.ansible/cp

[persistent_connection]
# 持久连接配置
connect_timeout = 10
command_timeout = 10`
}

/**
 * 🔧 Ansible配置面板组件
 */
const AnsibleConfigPanel: React.FC<AnsibleConfigPanelProps> = ({ 
  onRefresh, 
  systemStatus 
}) => {
  const { t } = useTranslation()
  const notification = useNotification()
  const textareaRef = useRef<HTMLTextAreaElement>(null)
  
  // 🎯 状态管理
  const [configInfo, setConfigInfo] = useState<AnsibleConfigInfo | null>(null)
  const [editedContent, setEditedContent] = useState('')
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [isEditing, setIsEditing] = useState(false)
  const [showTemplateModal, setShowTemplateModal] = useState(false)
  const [showRestoreModal, setShowRestoreModal] = useState(false)
  const [selectedTemplate, setSelectedTemplate] = useState<keyof typeof ANSIBLE_CONFIG_TEMPLATES>('basic')

  // 🔄 初始化加载
  useEffect(() => {
    loadAnsibleConfig()
  }, [])

  /**
   * 📄 加载Ansible配置文件
   */
  const loadAnsibleConfig = async () => {
    try {
      setLoading(true)
      const config = await AnsibleConfigService.getConfigFile()
      setConfigInfo(config)
      setEditedContent(config.content)
    } catch (error) {
      console.error('❌ 加载Ansible配置失败:', error)
      showNotification('加载Ansible配置失败', 'error')
    } finally {
      setLoading(false)
    }
  }

  /**
   * 💾 保存配置文件
   */
  const saveConfig = async () => {
    try {
      setSaving(true)
      const result = await AnsibleConfigService.updateConfigFile(editedContent)
      
      if (result.success) {
        showNotification('Ansible配置保存成功', 'success')
        setIsEditing(false)
        await loadAnsibleConfig()
        
        if (result.restart_required.length > 0) {
          showNotification('配置已更新，建议重启相关服务', 'warning')
        }
        
        onRefresh?.()
      } else {
        showNotification(`配置保存失败: ${Object.values(result.errors)[0]}`, 'error')
      }
    } catch (error: any) {
      console.error('❌ 保存配置失败:', error)
      showNotification(error.response?.data?.detail || '保存配置失败', 'error')
    } finally {
      setSaving(false)
    }
  }

  /**
   * 🔄 恢复备份
   */
  const restoreBackup = async () => {
    try {
      setSaving(true)
      const result = await AnsibleConfigService.restoreBackup()
      
      if (result.success) {
        showNotification('配置备份恢复成功', 'success')
        setShowRestoreModal(false)
        await loadAnsibleConfig()
        setIsEditing(false)
        onRefresh?.()
      } else {
        showNotification(`恢复备份失败: ${Object.values(result.errors)[0]}`, 'error')
      }
    } catch (error: any) {
      console.error('❌ 恢复备份失败:', error)
      showNotification(error.response?.data?.detail || '恢复备份失败', 'error')
    } finally {
      setSaving(false)
    }
  }

  /**
   * 📋 应用模板
   */
  const applyTemplate = (templateKey: keyof typeof ANSIBLE_CONFIG_TEMPLATES) => {
    setEditedContent(ANSIBLE_CONFIG_TEMPLATES[templateKey])
    setIsEditing(true)
    setShowTemplateModal(false)
    showNotification('模板已应用，请保存配置', 'info')
  }

  /**
   * 🔄 取消编辑
   */
  const cancelEdit = () => {
    setEditedContent(configInfo?.content || '')
    setIsEditing(false)
  }

  /**
   * 🎨 渲染配置状态
   */
  const renderConfigStatus = () => {
    if (!configInfo) return null

    return (
      <GlassCard className="mb-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <div className={`p-3 rounded-xl ${
              configInfo.is_valid 
                ? 'bg-gradient-to-r from-green-400 to-green-600' 
                : 'bg-gradient-to-r from-red-400 to-red-600'
            }`}>
              {configInfo.is_valid ? (
                <CheckCircleIcon className="w-6 h-6 text-white" />
              ) : (
                <ExclamationTriangleIcon className="w-6 h-6 text-white" />
              )}
            </div>
            
            <div>
              <h3 className="text-lg font-semibold text-glass-text-primary">
                Ansible配置状态
              </h3>
              <p className={`text-sm ${
                configInfo.is_valid ? 'text-green-400' : 'text-red-400'
              }`}>
                {configInfo.is_valid ? '配置文件有效' : '配置文件存在问题'}
              </p>
            </div>
          </div>
          
          <div className="text-right">
            {configInfo.last_modified && (
              <div className="flex items-center text-sm text-glass-text-secondary mb-1">
                <ClockIcon className="w-4 h-4 mr-1" />
                最后修改: {new Date(configInfo.last_modified).toLocaleString('zh-CN')}
              </div>
            )}
            
            {configInfo.backup_available && (
              <div className="flex items-center text-sm text-blue-400">
                <DocumentDuplicateIcon className="w-4 h-4 mr-1" />
                备份可用
              </div>
            )}
          </div>
        </div>
      </GlassCard>
    )
  }

  /**
   * 🎨 渲染操作栏
   */
  const renderActionBar = () => (
    <GlassCard className="mb-6">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-lg font-semibold text-glass-text-primary mb-1">
            配置文件编辑
          </h3>
          <p className="text-sm text-glass-text-secondary">
            编辑Ansible配置文件，配置自动化执行参数
          </p>
        </div>
        
        <div className="flex items-center space-x-3">
          {isEditing ? (
            <>
              <GlassButton
                variant="secondary"
                onClick={cancelEdit}
                disabled={saving}
              >
                取消
              </GlassButton>
              <GlassButton
                variant="primary"
                onClick={saveConfig}
                disabled={saving}
              >
                {saving ? '保存中...' : '保存配置'}
              </GlassButton>
            </>
          ) : (
            <>
              <GlassButton
                variant="secondary"
                onClick={() => setShowTemplateModal(true)}
              >
                <DocumentTextIcon className="w-4 h-4 mr-2" />
                使用模板
              </GlassButton>
              
              {configInfo?.backup_available && (
                <GlassButton
                  variant="secondary"
                  onClick={() => setShowRestoreModal(true)}
                >
                  <ArrowPathIcon className="w-4 h-4 mr-2" />
                  恢复备份
                </GlassButton>
              )}
              
              <GlassButton
                variant="primary"
                onClick={() => setIsEditing(true)}
              >
                <PencilIcon className="w-4 h-4 mr-2" />
                编辑配置
              </GlassButton>
            </>
          )}
        </div>
      </div>
    </GlassCard>
  )

  /**
   * 🎨 渲染配置编辑器
   */
  const renderConfigEditor = () => (
    <GlassCard>
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-glass-text-primary flex items-center">
          <WrenchScrewdriverIcon className="w-5 h-5 mr-2" />
          ansible.cfg
        </h3>
        
        <div className="flex items-center space-x-2">
          {isEditing ? (
            <span className="px-3 py-1 text-sm bg-blue-500/20 text-blue-400 rounded-full">
              编辑模式
            </span>
          ) : (
            <span className="px-3 py-1 text-sm bg-gray-500/20 text-gray-400 rounded-full">
              只读模式
            </span>
          )}
        </div>
      </div>
      
      <div className="relative">
        <textarea
          ref={textareaRef}
          value={editedContent}
          onChange={(e) => setEditedContent(e.target.value)}
          readOnly={!isEditing}
          className={`w-full h-96 p-4 bg-black/20 border border-white/20 rounded-lg text-glass-text-primary font-mono text-sm resize-none focus:outline-none focus:ring-2 focus:ring-blue-500/50 ${
            !isEditing ? 'cursor-default' : ''
          }`}
          placeholder="Ansible配置文件内容..."
          spellCheck={false}
        />
        
        {!isEditing && (
          <div className="absolute inset-0 bg-transparent cursor-default" />
        )}
      </div>
      
      <div className="mt-4 flex items-center justify-between text-sm text-glass-text-secondary">
        <div className="flex items-center space-x-4">
          <span>行数: {editedContent.split('\n').length}</span>
          <span>字符数: {editedContent.length}</span>
        </div>
        
        {isEditing && (
          <div className="flex items-center space-x-2 text-yellow-400">
            <ExclamationTriangleIcon className="w-4 h-4" />
            <span>配置已修改，请保存</span>
          </div>
        )}
      </div>
    </GlassCard>
  )

  if (loading) {
    return (
      <GlassCard>
        <div className="flex items-center justify-center py-12">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-white/30"></div>
          <span className="ml-3 text-glass-text-secondary">加载Ansible配置...</span>
        </div>
      </GlassCard>
    )
  }

  return (
    <div className="space-y-6">
      {/* 配置状态 */}
      {renderConfigStatus()}
      
      {/* 操作栏 */}
      {renderActionBar()}
      
      {/* 配置编辑器 */}
      {renderConfigEditor()}
      
      {/* 模板选择模态框 */}
      <GlassModal
        isOpen={showTemplateModal}
        onClose={() => setShowTemplateModal(false)}
        title="选择配置模板"
        size="lg"
      >
        <div className="space-y-4">
          <p className="text-glass-text-secondary">
            选择一个配置模板作为起点，您可以在此基础上进行自定义修改。
          </p>
          
          <div className="space-y-3">
            <div
              className={`p-4 glass-container cursor-pointer transition-all ${
                selectedTemplate === 'basic' ? 'ring-2 ring-blue-500/50' : ''
              }`}
              onClick={() => setSelectedTemplate('basic')}
            >
              <h4 className="font-medium text-glass-text-primary mb-2">基础配置</h4>
              <p className="text-sm text-glass-text-secondary">
                包含最基本的Ansible配置选项，适合初学者和简单环境
              </p>
            </div>
            
            <div
              className={`p-4 glass-container cursor-pointer transition-all ${
                selectedTemplate === 'advanced' ? 'ring-2 ring-blue-500/50' : ''
              }`}
              onClick={() => setSelectedTemplate('advanced')}
            >
              <h4 className="font-medium text-glass-text-primary mb-2">高级配置</h4>
              <p className="text-sm text-glass-text-secondary">
                包含更多高级选项，如缓存、日志、回调插件等，适合生产环境
              </p>
            </div>
            
            <div
              className={`p-4 glass-container cursor-pointer transition-all ${
                selectedTemplate === 'performance' ? 'ring-2 ring-blue-500/50' : ''
              }`}
              onClick={() => setSelectedTemplate('performance')}
            >
              <h4 className="font-medium text-glass-text-primary mb-2">性能优化配置</h4>
              <p className="text-sm text-glass-text-secondary">
                针对大规模环境优化的配置，包含并发、缓存、连接优化等
              </p>
            </div>
          </div>
          
          <div className="border-t border-white/10 pt-4">
            <h4 className="font-medium text-glass-text-primary mb-2">模板预览</h4>
            <div className="max-h-40 overflow-y-auto bg-black/20 border border-white/20 rounded-lg p-3">
              <pre className="text-xs text-glass-text-secondary font-mono whitespace-pre-wrap">
                {ANSIBLE_CONFIG_TEMPLATES[selectedTemplate].substring(0, 500)}
                {ANSIBLE_CONFIG_TEMPLATES[selectedTemplate].length > 500 && '...'}
              </pre>
            </div>
          </div>
          
          <div className="flex justify-end space-x-3">
            <GlassButton
              variant="secondary"
              onClick={() => setShowTemplateModal(false)}
            >
              取消
            </GlassButton>
            <GlassButton
              variant="primary"
              onClick={() => applyTemplate(selectedTemplate)}
            >
              应用模板
            </GlassButton>
          </div>
        </div>
      </GlassModal>
      
      {/* 恢复备份确认模态框 */}
      <GlassModal
        isOpen={showRestoreModal}
        onClose={() => setShowRestoreModal(false)}
        title="恢复配置备份"
      >
        <div className="space-y-4">
          <div className="p-4 bg-yellow-500/10 border border-yellow-500/20 rounded-lg">
            <p className="text-sm text-yellow-400">
              ⚠️ 恢复备份将覆盖当前配置文件，请确认操作
            </p>
          </div>
          
          <p className="text-glass-text-secondary">
            确定要从备份文件恢复Ansible配置吗？当前的配置修改将会丢失。
          </p>
          
          <div className="flex justify-end space-x-3">
            <GlassButton
              variant="secondary"
              onClick={() => setShowRestoreModal(false)}
            >
              取消
            </GlassButton>
            <GlassButton
              variant="primary"
              onClick={restoreBackup}
              disabled={saving}
              className="bg-orange-500/20 hover:bg-orange-500/30 text-orange-400"
            >
              {saving ? '恢复中...' : '确认恢复'}
            </GlassButton>
          </div>
        </div>
      </GlassModal>
    </div>
  )
}

export default AnsibleConfigPanel
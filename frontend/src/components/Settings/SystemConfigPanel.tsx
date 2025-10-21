/**
 * 🔧 系统配置面板
 * 
 * 功能：
 * - 分类显示配置项
 * - 配置项编辑和验证
 * - 批量配置更新
 * - 配置重置功能
 */

import React, { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { useTranslation } from 'react-i18next'
import {
  CogIcon,
  PencilIcon,
  CheckIcon,
  XMarkIcon,
  ArrowPathIcon,
  ExclamationTriangleIcon,
  InformationCircleIcon
} from '@heroicons/react/24/outline'

import GlassCard from '../UI/GlassCard'
import GlassButton from '../UI/GlassButton'
import GlassInput from '../UI/GlassInput'
import GlassSelect from '../UI/GlassSelect'
import GlassModal from '../UI/GlassModal'
import { useNotification } from '../../contexts/NotificationContext'
import { 
  ConfigService, 
  ConfigItem, 
  ConfigCategory, 
  SystemStatus,
  ConfigValidationResult 
} from '../../services/settingsService'

interface SystemConfigPanelProps {
  onRefresh?: () => void
  systemStatus?: SystemStatus | null
}

/**
 * 🔧 系统配置面板组件
 */
const SystemConfigPanel: React.FC<SystemConfigPanelProps> = ({ 
  onRefresh, 
  systemStatus 
}) => {
  const { t } = useTranslation()
  const notification = useNotification()
  
  // 🎯 状态管理
  const [categories, setCategories] = useState<ConfigCategory[]>([])
  const [activeCategory, setActiveCategory] = useState<string>('')
  const [configs, setConfigs] = useState<ConfigItem[]>([])
  const [editingConfigs, setEditingConfigs] = useState<Record<string, any>>({})
  const [validationResult, setValidationResult] = useState<ConfigValidationResult | null>(null)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [showResetModal, setShowResetModal] = useState(false)
  const [resetKeys, setResetKeys] = useState<string[]>([])

  // 🔄 初始化加载
  useEffect(() => {
    loadCategories()
  }, [])

  // 🔄 加载分类配置
  useEffect(() => {
    if (activeCategory) {
      loadConfigs(activeCategory)
    }
  }, [activeCategory])

  /**
   * 📋 加载配置分类
   */
  const loadCategories = async () => {
    try {
      setLoading(true)
      const categoriesData = await ConfigService.getCategories()
      setCategories(categoriesData)
      
      // 设置默认活动分类
      if (categoriesData.length > 0 && !activeCategory) {
        setActiveCategory(categoriesData[0].name)
      }
    } catch (error) {
      console.error('❌ 加载配置分类失败:', error)
      notification.error('加载配置分类失败')
    } finally {
      setLoading(false)
    }
  }

  /**
   * 📄 加载分类配置项
   */
  const loadConfigs = async (category: string) => {
    try {
      setLoading(true)
      const configsData = await ConfigService.getConfigsByCategory(category)
      setConfigs(configsData)
      setEditingConfigs({})
      setValidationResult(null)
    } catch (error) {
      console.error('❌ 加载配置项失败:', error)
      notification.error('加载配置项失败')
    } finally {
      setLoading(false)
    }
  }

  /**
   * ✏️ 开始编辑配置项
   */
  const startEditing = (config: ConfigItem) => {
    if (config.is_readonly) return
    
    setEditingConfigs(prev => ({
      ...prev,
      [config.key]: config.value
    }))
  }

  /**
   * 🚫 取消编辑
   */
  const cancelEditing = (key: string) => {
    setEditingConfigs(prev => {
      const newEditing = { ...prev }
      delete newEditing[key]
      return newEditing
    })
  }

  /**
   * 💾 保存单个配置
   */
  const saveConfig = async (key: string) => {
    try {
      setSaving(true)
      const value = editingConfigs[key]
      
      // 验证配置
      const validation = await ConfigService.validateConfigs({ [key]: value })
      if (!validation.valid) {
        notification.error('配置验证失败', validation.errors[key])
        return
      }
      
      // 更新配置
      const result = await ConfigService.updateConfig(key, value)
      if (result.success) {
        notification.success('配置更新成功')
        
        // 更新本地状态
        setConfigs(prev => prev.map(config => 
          config.key === key ? { ...config, value } : config
        ))
        
        // 取消编辑状态
        cancelEditing(key)
        
        // 如果需要重启，显示提示
        if (result.restart_required.length > 0) {
          notification.warning('配置已更新，部分更改需要重启服务才能生效')
        }
        
        // 刷新系统状态
        onRefresh?.()
      } else {
        notification.error('配置更新失败', result.errors[key])
      }
    } catch (error) {
      console.error('❌ 保存配置失败:', error)
      notification.error('保存配置失败')
    } finally {
      setSaving(false)
    }
  }

  /**
   * 📝 批量保存配置
   */
  const batchSaveConfigs = async () => {
    if (Object.keys(editingConfigs).length === 0) return
    
    try {
      setSaving(true)
      
      // 验证所有配置
      const validation = await ConfigService.validateConfigs(editingConfigs)
      setValidationResult(validation)
      
      if (!validation.valid) {
        notification.error('部分配置验证失败，请检查后重试')
        return
      }
      
      // 批量更新配置
      const result = await ConfigService.batchUpdateConfigs(editingConfigs)
      if (result.success) {
        notification.success('批量配置更新成功')
        
        // 重新加载配置
        await loadConfigs(activeCategory)
        
        // 如果需要重启，显示提示
        if (result.restart_required.length > 0) {
          notification.warning('配置已更新，部分更改需要重启服务才能生效')
        }
        
        // 刷新系统状态
        onRefresh?.()
      } else {
        notification.error('批量配置更新失败')
      }
    } catch (error) {
      console.error('❌ 批量保存配置失败:', error)
      notification.error('批量保存配置失败')
    } finally {
      setSaving(false)
    }
  }

  /**
   * 🔄 重置配置
   */
  const resetConfigs = async () => {
    if (resetKeys.length === 0) return
    
    try {
      setSaving(true)
      const result = await ConfigService.resetConfigs(resetKeys)
      
      if (result.success) {
        notification.success('配置重置成功')
        await loadConfigs(activeCategory)
        onRefresh?.()
      } else {
        notification.error('配置重置失败')
      }
    } catch (error) {
      console.error('❌ 重置配置失败:', error)
      notification.error('重置配置失败')
    } finally {
      setSaving(false)
      setShowResetModal(false)
      setResetKeys([])
    }
  }

  /**
   * 🎨 渲染分类选择器
   */
  const renderCategorySelector = () => (
    <div className="flex flex-wrap gap-2 mb-6">
      {categories.map((category) => (
        <GlassButton
          key={category.name}
          variant={activeCategory === category.name ? 'primary' : 'secondary'}
          size="sm"
          onClick={() => setActiveCategory(category.name)}
          className="flex items-center space-x-2"
        >
          <CogIcon className="w-4 h-4" />
          <span>{category.display_name}</span>
          <span className="text-xs opacity-70">({category.config_count})</span>
        </GlassButton>
      ))}
    </div>
  )

  /**
   * 🎨 渲染配置项
   */
  const renderConfigItem = (config: ConfigItem) => {
    const isEditing = config.key in editingConfigs
    const hasError = validationResult?.errors[config.key]
    const hasWarning = validationResult?.warnings[config.key]
    
    return (
      <motion.div
        key={config.key}
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="glass-container p-4"
      >
        <div className="flex items-start justify-between mb-3">
          <div className="flex-1">
            <div className="flex items-center space-x-2 mb-1">
              <h4 className="font-medium text-glass-text-primary">
                {config.key}
              </h4>
              {config.is_readonly && (
                <span className="px-2 py-1 text-xs bg-gray-500/20 text-gray-400 rounded">
                  只读
                </span>
              )}
              {config.is_sensitive && (
                <span className="px-2 py-1 text-xs bg-red-500/20 text-red-400 rounded">
                  敏感
                </span>
              )}
              {config.requires_restart && (
                <span className="px-2 py-1 text-xs bg-yellow-500/20 text-yellow-400 rounded">
                  需重启
                </span>
              )}
            </div>
            <p className="text-sm text-glass-text-secondary mb-2">
              {config.description}
            </p>
          </div>
          
          {!config.is_readonly && (
            <div className="flex items-center space-x-2">
              {isEditing ? (
                <>
                  <GlassButton
                    variant="primary"
                    size="sm"
                    onClick={() => saveConfig(config.key)}
                    disabled={saving}
                  >
                    <CheckIcon className="w-4 h-4" />
                  </GlassButton>
                  <GlassButton
                    variant="secondary"
                    size="sm"
                    onClick={() => cancelEditing(config.key)}
                    disabled={saving}
                  >
                    <XMarkIcon className="w-4 h-4" />
                  </GlassButton>
                </>
              ) : (
                <GlassButton
                  variant="secondary"
                  size="sm"
                  onClick={() => startEditing(config)}
                >
                  <PencilIcon className="w-4 h-4" />
                </GlassButton>
              )}
            </div>
          )}
        </div>
        
        {/* 配置值编辑 */}
        <div className="space-y-2">
          {isEditing ? (
            <div>
              {typeof config.value === 'boolean' ? (
                <GlassSelect
                  value={editingConfigs[config.key] ? 'true' : 'false'}
                  onChange={(value) => setEditingConfigs(prev => ({
                    ...prev,
                    [config.key]: value === 'true'
                  }))}
                  options={[
                    { value: 'true', label: '是' },
                    { value: 'false', label: '否' }
                  ]}
                />
              ) : (
                <GlassInput
                  type={config.is_sensitive ? 'password' : 'text'}
                  value={editingConfigs[config.key] || ''}
                  onChange={(e) => setEditingConfigs(prev => ({
                    ...prev,
                    [config.key]: e.target.value
                  }))}
                  placeholder={`默认值: ${config.default_value || '无'}`}
                />
              )}
            </div>
          ) : (
            <div className="p-3 bg-white/5 rounded-lg">
              <code className="text-sm text-glass-text-primary">
                {config.is_sensitive ? '••••••••' : String(config.value)}
              </code>
            </div>
          )}
          
          {/* 错误和警告提示 */}
          {hasError && (
            <div className="flex items-center space-x-2 text-red-400 text-sm">
              <ExclamationTriangleIcon className="w-4 h-4" />
              <span>{hasError}</span>
            </div>
          )}
          
          {hasWarning && (
            <div className="flex items-center space-x-2 text-yellow-400 text-sm">
              <InformationCircleIcon className="w-4 h-4" />
              <span>{hasWarning}</span>
            </div>
          )}
        </div>
      </motion.div>
    )
  }

  /**
   * 🎨 渲染操作栏
   */
  const renderActionBar = () => {
    const hasEditing = Object.keys(editingConfigs).length > 0
    const editableConfigs = configs.filter(c => !c.is_readonly)
    
    return (
      <GlassCard className="mb-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <h3 className="text-lg font-semibold text-glass-text-primary">
              配置管理操作
            </h3>
            {hasEditing && (
              <span className="px-3 py-1 text-sm bg-blue-500/20 text-blue-400 rounded-full">
                {Object.keys(editingConfigs).length} 项待保存
              </span>
            )}
          </div>
          
          <div className="flex items-center space-x-3">
            {hasEditing && (
              <>
                <GlassButton
                  variant="primary"
                  onClick={batchSaveConfigs}
                  disabled={saving}
                >
                  {saving ? '保存中...' : '批量保存'}
                </GlassButton>
                <GlassButton
                  variant="secondary"
                  onClick={() => setEditingConfigs({})}
                  disabled={saving}
                >
                  取消全部
                </GlassButton>
              </>
            )}
            
            <GlassButton
              variant="secondary"
              onClick={() => {
                setResetKeys(editableConfigs.map(c => c.key))
                setShowResetModal(true)
              }}
              disabled={editableConfigs.length === 0}
            >
              <ArrowPathIcon className="w-4 h-4 mr-2" />
              重置分类
            </GlassButton>
          </div>
        </div>
      </GlassCard>
    )
  }

  if (loading) {
    return (
      <GlassCard>
        <div className="flex items-center justify-center py-12">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-white/30"></div>
          <span className="ml-3 text-glass-text-secondary">加载配置中...</span>
        </div>
      </GlassCard>
    )
  }

  return (
    <div className="space-y-6">
      {/* 分类选择器 */}
      {renderCategorySelector()}
      
      {/* 操作栏 */}
      {renderActionBar()}
      
      {/* 配置项列表 */}
      <div className="grid gap-4">
        {configs.map(renderConfigItem)}
      </div>
      
      {configs.length === 0 && (
        <GlassCard>
          <div className="text-center py-12">
            <CogIcon className="w-12 h-12 text-glass-text-secondary mx-auto mb-4" />
            <p className="text-glass-text-secondary">
              该分类下暂无配置项
            </p>
          </div>
        </GlassCard>
      )}
      
      {/* 重置确认模态框 */}
      <GlassModal
        isOpen={showResetModal}
        onClose={() => setShowResetModal(false)}
        title="确认重置配置"
      >
        <div className="space-y-4">
          <p className="text-glass-text-secondary">
            确定要将以下配置项重置为默认值吗？此操作不可撤销。
          </p>
          
          <div className="max-h-40 overflow-y-auto space-y-2">
            {resetKeys.map(key => (
              <div key={key} className="p-2 bg-white/5 rounded text-sm">
                {key}
              </div>
            ))}
          </div>
          
          <div className="flex justify-end space-x-3">
            <GlassButton
              variant="secondary"
              onClick={() => setShowResetModal(false)}
            >
              取消
            </GlassButton>
            <GlassButton
              variant="primary"
              onClick={resetConfigs}
              disabled={saving}
            >
              {saving ? '重置中...' : '确认重置'}
            </GlassButton>
          </div>
        </div>
      </GlassModal>
    </div>
  )
}

export default SystemConfigPanel
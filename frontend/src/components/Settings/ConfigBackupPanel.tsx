/**
 * 💾 配置备份面板
 * 
 * 功能：
 * - 创建配置备份
 * - 查看备份列表
 * - 恢复配置备份
 * - 比较配置差异
 * - 导入导出配置
 */

import React, { useState, useEffect } from 'react'
import {
  DocumentDuplicateIcon,
  PlusIcon,
  ArrowDownTrayIcon,
  ArrowUpTrayIcon,
  TrashIcon,
  EyeIcon,
  ArrowPathIcon,
  FolderIcon,
  DocumentIcon
} from '@heroicons/react/24/outline'

import GlassCard from '../UI/GlassCard'
import GlassButton from '../UI/GlassButton'
import GlassInput from '../UI/GlassInput'
import GlassModal from '../UI/GlassModal'
import GlassTable from '../UI/GlassTable'
import { useNotification } from '../../contexts/NotificationContext'
import { 
  ConfigBackupService, 
  ConfigImportExportService,
  ConfigService,
  ConfigBackup, 
  ConfigCategory,
  SystemStatus 
} from '../../services/settingsService'

interface ConfigBackupPanelProps {
  onRefresh?: () => void
  systemStatus?: SystemStatus | null
}

// 🏷️ 备份表单数据类型
interface BackupFormData {
  backup_name: string
  description: string
  include_categories: string[]
}

// 🏷️ 恢复表单数据类型
interface RestoreFormData {
  backup_name: string
  overwrite: boolean
  restore_categories: string[]
}

/**
 * 💾 配置备份面板组件
 */
const ConfigBackupPanel: React.FC<ConfigBackupPanelProps> = ({ 
  onRefresh
}) => {
  const { success: showSuccess, error: showError } = useNotification()
  
  // 🎯 状态管理
  const [backups, setBackups] = useState<ConfigBackup[]>([])
  const [categories, setCategories] = useState<ConfigCategory[]>([])
  const [loading, setLoading] = useState(true)
  const [creating, setCreating] = useState(false)
  const [restoring, setRestoring] = useState(false)
  
  // 🎨 模态框状态
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [showRestoreModal, setShowRestoreModal] = useState(false)
  const [showDeleteModal, setShowDeleteModal] = useState(false)
  const [showCompareModal, setShowCompareModal] = useState(false)
  const [showImportModal, setShowImportModal] = useState(false)
  const [selectedBackup, setSelectedBackup] = useState<ConfigBackup | null>(null)
  
  // 📝 表单数据
  const [backupForm, setBackupForm] = useState<BackupFormData>({
    backup_name: '',
    description: '',
    include_categories: []
  })
  const [restoreForm, setRestoreForm] = useState<RestoreFormData>({
    backup_name: '',
    overwrite: false,
    restore_categories: []
  })
  
  // 📊 比较结果
  const [compareResult, setCompareResult] = useState<any>(null)
  const [importFile, setImportFile] = useState<File | null>(null)
  const [importOverwrite, setImportOverwrite] = useState(false)

  // 🔄 初始化加载
  useEffect(() => {
    loadBackups()
    loadCategories()
  }, [])

  /**
   * 📋 加载备份列表
   */
  const loadBackups = async () => {
    try {
      setLoading(true)
      const backupsData = await ConfigBackupService.getBackups()
      setBackups(backupsData)
    } catch (error) {
      console.error('❌ 加载备份列表失败:', error)
      showError('加载备份列表失败')
    } finally {
      setLoading(false)
    }
  }

  /**
   * 📋 加载配置分类
   */
  const loadCategories = async () => {
    try {
      const categoriesData = await ConfigService.getCategories()
      setCategories(categoriesData)
    } catch (error) {
      console.error('❌ 加载配置分类失败:', error)
    }
  }

  /**
   * 💾 创建备份
   */
  const createBackup = async () => {
    try {
      setCreating(true)
      await ConfigBackupService.createBackup(backupForm)
      showSuccess('配置备份创建成功')
      setShowCreateModal(false)
      resetBackupForm()
      loadBackups()
    } catch (error: any) {
      console.error('❌ 创建备份失败:', error)
      showError(error.response?.data?.detail || '创建备份失败')
    } finally {
      setCreating(false)
    }
  }

  /**
   * 🔄 恢复备份
   */
  const restoreBackup = async () => {
    try {
      setRestoring(true)
      const result = await ConfigBackupService.restoreBackup(restoreForm)
      
      if (result.success) {
        const count = result.success_count || Object.keys(result.updated).filter(k => result.updated[k]).length
        showSuccess(`配置恢复成功，共恢复 ${count} 项配置`)
      } else {
        const successCount = result.success_count || Object.keys(result.updated).filter(k => result.updated[k]).length
        const errorCount = result.error_count || Object.keys(result.errors).length
        showError(`配置恢复部分失败，成功 ${successCount} 项，失败 ${errorCount} 项`)
      }
      
      setShowRestoreModal(false)
      resetRestoreForm()
      onRefresh?.()
    } catch (error: any) {
      console.error('❌ 恢复备份失败:', error)
      showError(error.response?.data?.detail || '恢复备份失败')
    } finally {
      setRestoring(false)
    }
  }

  /**
   * 🗑️ 删除备份
   */
  const deleteBackup = async () => {
    if (!selectedBackup) return
    
    try {
      await ConfigBackupService.deleteBackup(selectedBackup.name)
      showSuccess('备份删除成功')
      setShowDeleteModal(false)
      setSelectedBackup(null)
      loadBackups()
    } catch (error: any) {
      console.error('❌ 删除备份失败:', error)
      showError(error.response?.data?.detail || '删除备份失败')
    }
  }

  /**
   * 🔍 比较配置差异
   */
  const compareWithBackup = async (backupName: string) => {
    try {
      const result = await ConfigBackupService.compareWithBackup(backupName)
      setCompareResult(result)
      setShowCompareModal(true)
    } catch (error: any) {
      console.error('❌ 比较配置失败:', error)
      showError(error.response?.data?.detail || '比较配置失败')
    }
  }

  /**
   * 📤 导出配置
   */
  const exportConfig = async (category: string) => {
    try {
      const blob = await ConfigImportExportService.exportConfigs(category)
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `${category}_config_${new Date().toISOString().split('T')[0]}.json`
      document.body.appendChild(a)
      a.click()
      window.URL.revokeObjectURL(url)
      document.body.removeChild(a)
      showSuccess('配置导出成功')
    } catch (error: any) {
      console.error('❌ 导出配置失败:', error)
      showError(error.response?.data?.detail || '导出配置失败')
    }
  }

  /**
   * 📥 导入配置
   */
  const importConfig = async () => {
    if (!importFile) return
    
    try {
      const result = await ConfigImportExportService.importConfigs(importFile, importOverwrite)
      
      if (result.success) {
        const count = result.success_count || result.total_count || 0
        showSuccess(`配置导入成功，共导入 ${count} 项配置`)
      } else {
        const successCount = result.success_count || 0
        const errorCount = result.error_count || 0
        showError(`配置导入部分失败，成功 ${successCount} 项，失败 ${errorCount} 项`)
      }
      
      setShowImportModal(false)
      setImportFile(null)
      setImportOverwrite(false)
      onRefresh?.()
    } catch (error: any) {
      console.error('❌ 导入配置失败:', error)
      showError(error.response?.data?.detail || '导入配置失败')
    }
  }

  /**
   * 🔄 重置表单
   */
  const resetBackupForm = () => {
    setBackupForm({
      backup_name: '',
      description: '',
      include_categories: []
    })
  }

  const resetRestoreForm = () => {
    setRestoreForm({
      backup_name: '',
      overwrite: false,
      restore_categories: []
    })
  }

  /**
   * 🎨 渲染操作栏
   */
  const renderActionBar = () => (
    <GlassCard className="mb-6">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-lg font-semibold text-glass-text-primary mb-1">
            配置备份管理
          </h3>
          <p className="text-sm text-glass-text-secondary">
            创建、恢复和管理系统配置备份
          </p>
        </div>
        
        <div className="flex items-center space-x-3">
          <GlassButton
            variant="secondary"
            onClick={() => setShowImportModal(true)}
          >
            <ArrowUpTrayIcon className="w-4 h-4 mr-2" />
            导入配置
          </GlassButton>
          
          <GlassButton
            variant="primary"
            onClick={() => setShowCreateModal(true)}
          >
            <PlusIcon className="w-4 h-4 mr-2" />
            创建备份
          </GlassButton>
        </div>
      </div>
    </GlassCard>
  )

  /**
   * 🎨 渲染导出面板
   */
  const renderExportPanel = () => (
    <GlassCard className="mb-6">
      <h3 className="text-lg font-semibold text-glass-text-primary mb-4 flex items-center">
        <ArrowDownTrayIcon className="w-5 h-5 mr-2" />
        配置导出
      </h3>
      
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3">
        {categories.map((category) => (
          <GlassButton
            key={category.name}
            variant="secondary"
            size="sm"
            onClick={() => exportConfig(category.name)}
            className="flex items-center justify-center space-x-2"
          >
            <FolderIcon className="w-4 h-4" />
            <span>{category.display_name}</span>
          </GlassButton>
        ))}
      </div>
    </GlassCard>
  )

  /**
   * 🎨 渲染备份表格
   */
  const renderBackupTable = () => {
    const columns = [
      {
        key: 'name',
        title: '备份名称',
        render: (backup: ConfigBackup) => (
          <div>
            <p className="font-medium text-glass-text-primary">{backup.name}</p>
            {backup.description && (
              <p className="text-sm text-glass-text-secondary">{backup.description}</p>
            )}
          </div>
        )
      },
      {
        key: 'created_at',
        title: '创建时间',
        render: (backup: ConfigBackup) => (
          <span className="text-sm text-glass-text-secondary">
            {new Date(backup.created_at).toLocaleString('zh-CN')}
          </span>
        )
      },
      {
        key: 'config_count',
        title: '配置项数',
        render: (backup: ConfigBackup) => (
          <span className="font-medium text-glass-text-primary">
            {backup.config_count}
          </span>
        )
      },
      {
        key: 'categories',
        title: '包含分类',
        render: (backup: ConfigBackup) => (
          <div className="flex flex-wrap gap-1">
            {backup.categories.map((category) => (
              <span
                key={category}
                className="px-2 py-1 text-xs bg-blue-500/20 text-blue-400 rounded"
              >
                {category}
              </span>
            ))}
          </div>
        )
      },
      {
        key: 'size',
        title: '文件大小',
        render: (backup: ConfigBackup) => (
          <span className="text-sm text-glass-text-secondary">
            {(backup.size / 1024).toFixed(1)} KB
          </span>
        )
      },
      {
        key: 'actions',
        title: '操作',
        render: (backup: ConfigBackup) => (
          <div className="flex items-center space-x-2">
            <GlassButton
              variant="secondary"
              size="sm"
              onClick={() => compareWithBackup(backup.name)}
              title="比较差异"
            >
              <EyeIcon className="w-4 h-4" />
            </GlassButton>
            
            <GlassButton
              variant="secondary"
              size="sm"
              onClick={() => {
                setRestoreForm({
                  backup_name: backup.name,
                  overwrite: false,
                  restore_categories: backup.categories
                })
                setShowRestoreModal(true)
              }}
              title="恢复备份"
            >
              <ArrowPathIcon className="w-4 h-4" />
            </GlassButton>
            
            <GlassButton
              variant="secondary"
              size="sm"
              onClick={() => {
                setSelectedBackup(backup)
                setShowDeleteModal(true)
              }}
              className="text-red-400 hover:text-red-300"
              title="删除备份"
            >
              <TrashIcon className="w-4 h-4" />
            </GlassButton>
          </div>
        )
      }
    ]

    return (
      <GlassTable
        columns={columns}
        data={backups}
        loading={loading}
      />
    )
  }

  return (
    <div className="space-y-6">
      {/* 操作栏 */}
      {renderActionBar()}
      
      {/* 导出面板 */}
      {renderExportPanel()}
      
      {/* 备份表格 */}
      {renderBackupTable()}
      
      {backups.length === 0 && !loading && (
        <GlassCard>
          <div className="text-center py-12">
            <DocumentDuplicateIcon className="w-12 h-12 text-glass-text-secondary mx-auto mb-4" />
            <p className="text-glass-text-secondary">
              暂无配置备份，点击"创建备份"开始备份配置
            </p>
          </div>
        </GlassCard>
      )}
      
      {/* 创建备份模态框 */}
      <GlassModal
        isOpen={showCreateModal}
        onClose={() => {
          setShowCreateModal(false)
          resetBackupForm()
        }}
        title="创建配置备份"
      >
        <div className="space-y-4">
          <GlassInput
            label="备份名称"
            value={backupForm.backup_name}
            onChange={(e) => setBackupForm(prev => ({ ...prev, backup_name: e.target.value }))}
            placeholder="请输入备份名称"
            required
          />
          
          <GlassInput
            label="备份描述"
            value={backupForm.description}
            onChange={(e) => setBackupForm(prev => ({ ...prev, description: e.target.value }))}
            placeholder="请输入备份描述（可选）"
          />
          
          <div>
            <label className="block text-sm font-medium text-glass-text-primary mb-2">
              包含分类
            </label>
            <div className="grid grid-cols-2 gap-2">
              {categories.map((category) => (
                <label key={category.name} className="flex items-center space-x-2">
                  <input
                    type="checkbox"
                    checked={backupForm.include_categories.includes(category.name)}
                    onChange={(e) => {
                      if (e.target.checked) {
                        setBackupForm(prev => ({
                          ...prev,
                          include_categories: [...prev.include_categories, category.name]
                        }))
                      } else {
                        setBackupForm(prev => ({
                          ...prev,
                          include_categories: prev.include_categories.filter(c => c !== category.name)
                        }))
                      }
                    }}
                    className="w-4 h-4 text-blue-600 bg-transparent border-2 border-white/30 rounded focus:ring-blue-500"
                  />
                  <span className="text-sm text-glass-text-secondary">
                    {category.display_name}
                  </span>
                </label>
              ))}
            </div>
          </div>
          
          <div className="flex justify-end space-x-3">
            <GlassButton
              variant="secondary"
              onClick={() => {
                setShowCreateModal(false)
                resetBackupForm()
              }}
            >
              取消
            </GlassButton>
            <GlassButton
              variant="primary"
              onClick={createBackup}
              disabled={!backupForm.backup_name || creating}
            >
              {creating ? '创建中...' : '创建备份'}
            </GlassButton>
          </div>
        </div>
      </GlassModal>
      
      {/* 恢复备份模态框 */}
      <GlassModal
        isOpen={showRestoreModal}
        onClose={() => {
          setShowRestoreModal(false)
          resetRestoreForm()
        }}
        title="恢复配置备份"
      >
        <div className="space-y-4">
          <div className="p-4 bg-yellow-500/10 border border-yellow-500/20 rounded-lg">
            <p className="text-sm text-yellow-400">
              ⚠️ 恢复备份将覆盖当前配置，请谨慎操作
            </p>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-glass-text-primary mb-2">
              备份名称
            </label>
            <p className="text-glass-text-secondary">{restoreForm.backup_name}</p>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-glass-text-primary mb-2">
              恢复分类
            </label>
            <div className="grid grid-cols-2 gap-2">
              {categories.map((category) => (
                <label key={category.name} className="flex items-center space-x-2">
                  <input
                    type="checkbox"
                    checked={restoreForm.restore_categories.includes(category.name)}
                    onChange={(e) => {
                      if (e.target.checked) {
                        setRestoreForm(prev => ({
                          ...prev,
                          restore_categories: [...prev.restore_categories, category.name]
                        }))
                      } else {
                        setRestoreForm(prev => ({
                          ...prev,
                          restore_categories: prev.restore_categories.filter(c => c !== category.name)
                        }))
                      }
                    }}
                    className="w-4 h-4 text-blue-600 bg-transparent border-2 border-white/30 rounded focus:ring-blue-500"
                  />
                  <span className="text-sm text-glass-text-secondary">
                    {category.display_name}
                  </span>
                </label>
              ))}
            </div>
          </div>
          
          <div className="flex items-center space-x-3">
            <input
              type="checkbox"
              id="overwrite"
              checked={restoreForm.overwrite}
              onChange={(e) => setRestoreForm(prev => ({ ...prev, overwrite: e.target.checked }))}
              className="w-4 h-4 text-blue-600 bg-transparent border-2 border-white/30 rounded focus:ring-blue-500"
            />
            <label htmlFor="overwrite" className="text-sm text-glass-text-secondary">
              覆盖现有配置
            </label>
          </div>
          
          <div className="flex justify-end space-x-3">
            <GlassButton
              variant="secondary"
              onClick={() => {
                setShowRestoreModal(false)
                resetRestoreForm()
              }}
            >
              取消
            </GlassButton>
            <GlassButton
              variant="primary"
              onClick={restoreBackup}
              disabled={restoreForm.restore_categories.length === 0 || restoring}
            >
              {restoring ? '恢复中...' : '确认恢复'}
            </GlassButton>
          </div>
        </div>
      </GlassModal>
      
      {/* 删除确认模态框 */}
      <GlassModal
        isOpen={showDeleteModal}
        onClose={() => {
          setShowDeleteModal(false)
          setSelectedBackup(null)
        }}
        title="确认删除备份"
      >
        <div className="space-y-4">
          <p className="text-glass-text-secondary">
            确定要删除备份 <span className="font-medium text-glass-text-primary">
              {selectedBackup?.name}
            </span> 吗？此操作不可撤销。
          </p>
          
          <div className="flex justify-end space-x-3">
            <GlassButton
              variant="secondary"
              onClick={() => {
                setShowDeleteModal(false)
                setSelectedBackup(null)
              }}
            >
              取消
            </GlassButton>
            <GlassButton
              variant="primary"
              onClick={deleteBackup}
              className="bg-red-500/20 hover:bg-red-500/30 text-red-400"
            >
              确认删除
            </GlassButton>
          </div>
        </div>
      </GlassModal>
      
      {/* 配置差异比较模态框 */}
      <GlassModal
        isOpen={showCompareModal}
        onClose={() => {
          setShowCompareModal(false)
          setCompareResult(null)
        }}
        title="配置差异比较"
        size="lg"
      >
        {compareResult && (
          <div className="space-y-4">
            <div className="grid grid-cols-3 gap-4 text-center">
              <div className="glass-container p-3">
                <p className="text-2xl font-bold text-green-400">{compareResult.additions}</p>
                <p className="text-sm text-glass-text-secondary">新增</p>
              </div>
              <div className="glass-container p-3">
                <p className="text-2xl font-bold text-blue-400">{compareResult.updates}</p>
                <p className="text-sm text-glass-text-secondary">更新</p>
              </div>
              <div className="glass-container p-3">
                <p className="text-2xl font-bold text-red-400">{compareResult.deletions}</p>
                <p className="text-sm text-glass-text-secondary">删除</p>
              </div>
            </div>
            
            <div className="max-h-96 overflow-y-auto space-y-2">
              {compareResult.differences.map((diff: any, index: number) => (
                <div key={index} className="glass-container p-3">
                  <div className="flex items-center justify-between mb-2">
                    <span className="font-medium text-glass-text-primary">{diff.key}</span>
                    <span className={`px-2 py-1 text-xs rounded ${
                      diff.action === 'add' ? 'bg-green-500/20 text-green-400' :
                      diff.action === 'update' ? 'bg-blue-500/20 text-blue-400' :
                      'bg-red-500/20 text-red-400'
                    }`}>
                      {diff.action === 'add' ? '新增' : diff.action === 'update' ? '更新' : '删除'}
                    </span>
                  </div>
                  
                  {diff.action !== 'add' && (
                    <div className="mb-2">
                      <p className="text-xs text-glass-text-secondary mb-1">当前值:</p>
                      <code className="text-xs bg-red-500/10 text-red-400 p-1 rounded">
                        {String(diff.current_value)}
                      </code>
                    </div>
                  )}
                  
                  {diff.action !== 'delete' && (
                    <div>
                      <p className="text-xs text-glass-text-secondary mb-1">备份值:</p>
                      <code className="text-xs bg-green-500/10 text-green-400 p-1 rounded">
                        {String(diff.new_value)}
                      </code>
                    </div>
                  )}
                </div>
              ))}
            </div>
            
            <div className="flex justify-end">
              <GlassButton
                variant="secondary"
                onClick={() => {
                  setShowCompareModal(false)
                  setCompareResult(null)
                }}
              >
                关闭
              </GlassButton>
            </div>
          </div>
        )}
      </GlassModal>
      
      {/* 导入配置模态框 */}
      <GlassModal
        isOpen={showImportModal}
        onClose={() => {
          setShowImportModal(false)
          setImportFile(null)
          setImportOverwrite(false)
        }}
        title="导入配置文件"
      >
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-glass-text-primary mb-2">
              选择配置文件
            </label>
            <input
              type="file"
              accept=".json"
              onChange={(e) => setImportFile(e.target.files?.[0] || null)}
              className="w-full p-3 bg-white/5 border border-white/20 rounded-lg text-glass-text-primary file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:bg-blue-500/20 file:text-blue-400 hover:file:bg-blue-500/30"
            />
          </div>
          
          {importFile && (
            <div className="glass-container p-3">
              <div className="flex items-center space-x-2">
                <DocumentIcon className="w-5 h-5 text-blue-400" />
                <span className="text-glass-text-primary">{importFile.name}</span>
                <span className="text-sm text-glass-text-secondary">
                  ({(importFile.size / 1024).toFixed(1)} KB)
                </span>
              </div>
            </div>
          )}
          
          <div className="flex items-center space-x-3">
            <input
              type="checkbox"
              id="import_overwrite"
              checked={importOverwrite}
              onChange={(e) => setImportOverwrite(e.target.checked)}
              className="w-4 h-4 text-blue-600 bg-transparent border-2 border-white/30 rounded focus:ring-blue-500"
            />
            <label htmlFor="import_overwrite" className="text-sm text-glass-text-secondary">
              覆盖现有配置
            </label>
          </div>
          
          <div className="flex justify-end space-x-3">
            <GlassButton
              variant="secondary"
              onClick={() => {
                setShowImportModal(false)
                setImportFile(null)
                setImportOverwrite(false)
              }}
            >
              取消
            </GlassButton>
            <GlassButton
              variant="primary"
              onClick={importConfig}
              disabled={!importFile}
            >
              导入配置
            </GlassButton>
          </div>
        </div>
      </GlassModal>
    </div>
  )
}

export default ConfigBackupPanel
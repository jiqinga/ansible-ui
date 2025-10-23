import React, { useState, useEffect, useCallback } from 'react'
import { createPortal } from 'react-dom'
import { motion } from 'framer-motion'

import Editor from '@monaco-editor/react'
import {
  DocumentTextIcon,
  PlayIcon,
  CheckCircleIcon,
  ExclamationTriangleIcon,
  PlusIcon,
  TrashIcon,
  ArrowPathIcon,
  DocumentArrowDownIcon
} from '@heroicons/react/24/outline'

import GlassCard from '../components/UI/GlassCard'
import GlassButton from '../components/UI/GlassButton'
import GlassInput from '../components/UI/GlassInput'
import GlassModal from '../components/UI/GlassModal'
import { useNotification } from '../contexts/NotificationContext'
import PlaybookService, { ValidationResult } from '../services/playbookService'
import { registerAnsibleCompletionProvider, registerAnsibleTheme } from '../utils/ansibleCompletionProvider'
import { extractErrorMessage } from '../utils/errorHandler'

// 🎯 标记是否已注册 Ansible 功能
let ansibleFeaturesRegistered = false

/**
 * 🎨 Playbook编辑器页面
 * 
 * 功能：
 * - 玻璃态文件浏览器
 * - Monaco Editor集成
 * - 实时语法验证
 * - 文件管理操作
 * - 中文界面支持
 */
const Playbooks: React.FC = () => {

  const { success, error } = useNotification()

  // 📁 Playbook列表状态
  const [selectedPlaybook, setSelectedPlaybook] = useState<any | null>(null)

  // 📝 编辑器状态
  const [editorContent, setEditorContent] = useState('')
  const [originalContent, setOriginalContent] = useState('')
  const [isModified, setIsModified] = useState(false)
  const [isLoading, setIsLoading] = useState(false)
  const [isSaving, setIsSaving] = useState(false)
  const [isEditorReady, setIsEditorReady] = useState(false)
  const [isLoadingContent, setIsLoadingContent] = useState(false)

  // ✅ 验证状态
  const [validationResult, setValidationResult] = useState<ValidationResult | null>(null)
  const [isValidating, setIsValidating] = useState(false)

  // 🔍 搜索状态
  const [searchTerm, setSearchTerm] = useState('')
  const [filteredPlaybooks, setFilteredPlaybooks] = useState<any[]>([])

  // 📝 新建文件模态框
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [newFileName, setNewFileName] = useState('')

  // 🗑️ 删除确认对话框
  const [showDeleteDialog, setShowDeleteDialog] = useState(false)
  const [playbookToDelete, setPlaybookToDelete] = useState<any | null>(null)

  /**
   * 📂 加载Playbook列表
   */
  const loadPlaybooks = useCallback(async (search?: string) => {
    setIsLoading(true)
    try {
      const result = await PlaybookService.getPlaybooks(1, 100, search)
      setFilteredPlaybooks(result.items)
    } catch (err: any) {
      const errorMsg = extractErrorMessage(err, '无法加载文件列表')
      error(`❌ ${errorMsg}`)
    } finally {
      setIsLoading(false)
    }
  }, [error])

  /**
   * ✅ 验证Playbook内容
   */
  const validateContent = useCallback(async (content: string) => {
    if (!content.trim()) {
      setValidationResult(null)
      return
    }

    setIsValidating(true)
    try {
      const result = await PlaybookService.validatePlaybook(content)
      setValidationResult(result)
    } catch (error) {
      console.error('验证失败:', error)
    } finally {
      setIsValidating(false)
    }
  }, [])

  /**
   * 📄 加载Playbook内容
   */
  const loadPlaybookContent = useCallback(async (playbook: any) => {
    // 🎯 立即设置选中状态，显示加载指示器
    setSelectedPlaybook(playbook)
    setIsLoadingContent(true)
    
    try {
      const response = await PlaybookService.getPlaybookContent(playbook.id)
      
      // 🚀 内容加载完成后立即更新编辑器
      setEditorContent(response.content)
      setOriginalContent(response.content)
      setIsModified(false)

      // 🔄 自动验证（异步执行，不阻塞UI）
      setTimeout(() => {
        validateContent(response.content)
      }, 100)
    } catch (err: any) {
      const errorMsg = extractErrorMessage(err, '无法读取文件内容')
      error(`❌ 加载失败：${errorMsg}`)
      // 加载失败时清空选中状态
      setSelectedPlaybook(null)
    } finally {
      setIsLoadingContent(false)
    }
  }, [error, validateContent])

  /**
   * 💾 保存Playbook内容
   */
  const savePlaybook = useCallback(async () => {
    if (!selectedPlaybook || !isModified) return

    setIsSaving(true)
    try {
      // 使用Playbook ID保存到数据库
      await PlaybookService.savePlaybookContent(selectedPlaybook.id, editorContent)
      setOriginalContent(editorContent)
      setIsModified(false)
      success(`✅ ${selectedPlaybook.filename} 保存成功`)

      // 重新加载列表
      loadPlaybooks(searchTerm)
    } catch (err: any) {
      const errorMsg = extractErrorMessage(err, '保存失败')
      error(`❌ ${errorMsg}`)
    } finally {
      setIsSaving(false)
    }
  }, [selectedPlaybook, isModified, editorContent, searchTerm, success, error, loadPlaybooks])

  /**
   * 📝 创建新文件
   */
  const createNewFile = useCallback(async () => {
    if (!newFileName.trim()) return

    const fileName = newFileName.endsWith('.yml') || newFileName.endsWith('.yaml')
      ? newFileName
      : `${newFileName}.yml`

    try {
      await PlaybookService.createPlaybook({
        filename: fileName,
        content: `---
- name: ${fileName.replace(/\.(yml|yaml)$/, '')}
  hosts: all
  become: yes
  
  tasks:
    - name: 示例任务
      debug:
        msg: "Hello from ${fileName}"
`
      })

      setNewFileName('')
      setShowCreateModal(false)
      success(`✅ 文件 ${fileName} 创建成功`)

      // 🔄 重新加载列表
      loadPlaybooks(searchTerm)
    } catch (err: any) {
      console.error('❌ 创建文件失败', err)

      // 🔍 解析错误信息，提供更友好的提示
      if (err.response?.status === 409) {
        // 文件名冲突 - 提供清晰的说明和建议
        error(`📁 文件名冲突：${fileName} 已经存在，请尝试使用其他名称`)
      } else if (err.response?.status === 400) {
        // 请求参数错误
        const errorMsg = extractErrorMessage(err, '文件名格式不正确，请使用有效的文件名')
        error(`⚠️ ${errorMsg}`)
      } else {
        // 显示后端返回的详细错误信息
        error(`❌ ${extractErrorMessage(err, '创建文件失败')}`)
      }
    }
  }, [newFileName, searchTerm, loadPlaybooks, success, error])

  /**
   * 🗑️ 显示删除确认对话框
   */
  const showDeleteConfirmation = useCallback((playbook: any) => {
    setPlaybookToDelete(playbook)
    setShowDeleteDialog(true)
  }, [])

  /**
   * 🗑️ 执行删除Playbook
   */
  const confirmDeletePlaybook = useCallback(async () => {
    if (!playbookToDelete) return

    try {
      // 使用Playbook ID删除
      await PlaybookService.deletePlaybook(playbookToDelete.id)
      success(`✅ ${playbookToDelete.filename} 已删除`)

      // 🔄 重新加载列表
      loadPlaybooks(searchTerm)

      // 如果删除的是当前打开的Playbook，清空编辑器
      if (selectedPlaybook?.id === playbookToDelete.id) {
        setSelectedPlaybook(null)
        setEditorContent('')
        setOriginalContent('')
        setIsModified(false)
        setValidationResult(null)
      }
    } catch (err: any) {
      const errorMsg = extractErrorMessage(err, '删除失败')
      error(`❌ ${errorMsg}`)
    } finally {
      setShowDeleteDialog(false)
      setPlaybookToDelete(null)
    }
  }, [playbookToDelete, searchTerm, loadPlaybooks, selectedPlaybook, success, error])

  /**
   * 🚫 取消删除
   */
  const cancelDeletePlaybook = useCallback(() => {
    setShowDeleteDialog(false)
    setPlaybookToDelete(null)
  }, [])



  /**
   * 🔍 搜索Playbook
   */
  const handleSearch = useCallback((term: string) => {
    setSearchTerm(term)
    loadPlaybooks(term)
  }, [loadPlaybooks])

  /**
   * 📝 编辑器内容变化处理
   */
  const handleEditorChange = useCallback((value: string | undefined) => {
    const content = value || ''
    setEditorContent(content)
    setIsModified(content !== originalContent)

    // 🔄 延迟验证以避免频繁调用
    const timeoutId = setTimeout(() => {
      validateContent(content)
    }, 1000)

    return () => clearTimeout(timeoutId)
  }, [originalContent, validateContent])

  // 🔄 初始化加载
  useEffect(() => {
    loadPlaybooks()
  }, [loadPlaybooks])

  // ⌨️ 键盘快捷键
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.ctrlKey || e.metaKey) {
        switch (e.key) {
          case 's':
            e.preventDefault()
            if (isModified) savePlaybook()
            break
          case 'n':
            e.preventDefault()
            setShowCreateModal(true)
            break
        }
      }
    }

    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [isModified, savePlaybook])

  /**
   * 🎨 渲染Playbook列表项
   */
  const renderPlaybookItem = (playbook: any) => {
    const isSelected = selectedPlaybook?.id === playbook.id

    return (
      <motion.div
        key={playbook.id}
        className={`
          flex items-center gap-2 px-3 py-2 rounded-lg cursor-pointer
          transition-all duration-200 hover:bg-white/10
          ${isSelected ? 'bg-white/20 border border-white/30' : ''}
        `}
        onClick={() => loadPlaybookContent(playbook)}
        whileHover={{ y: -2 }}
        whileTap={{ y: 0 }}
      >
        <DocumentTextIcon className="w-5 h-5 text-green-300" />

        <div className="flex-1 min-w-0">
          <div className="text-white/90 text-sm font-medium truncate">
            {playbook.display_name || playbook.filename}
          </div>
          {playbook.description && (
            <div className="text-white/50 text-xs truncate">
              {playbook.description}
            </div>
          )}
        </div>

        <div className="flex items-center gap-2">
          {!playbook.is_valid && (
            <ExclamationTriangleIcon className="w-4 h-4 text-red-400" title="验证失败" />
          )}
          <span className="text-xs text-white/50">
            {playbook.file_size ? `${Math.round(playbook.file_size / 1024)}KB` : ''}
          </span>
          <GlassButton
            size="sm"
            variant="ghost"
            onClick={(e) => {
              e.stopPropagation()
              showDeleteConfirmation(playbook)
            }}
            className="opacity-0 group-hover:opacity-100 transition-opacity"
          >
            <TrashIcon className="w-4 h-4" />
          </GlassButton>
        </div>
      </motion.div>
    )
  }

  /**
   * 🎨 渲染验证结果
   */
  const renderValidationResult = () => {
    if (!validationResult) return null

    const { errors, warnings } = validationResult
    const hasIssues = errors.length > 0 || warnings.length > 0

    if (!hasIssues) {
      return (
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          className="flex items-center gap-2 px-3 py-2 bg-green-500/20 border border-green-500/30 rounded-lg"
        >
          <CheckCircleIcon className="w-5 h-5 text-green-400" />
          <span className="text-green-300 text-sm font-medium">
            ✅ Playbook语法正确
          </span>
        </motion.div>
      )
    }

    return (
      <motion.div
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        className="space-y-2"
      >
        {errors.map((error, index) => (
          <div
            key={index}
            className="flex items-start gap-2 px-3 py-2 bg-red-500/20 border border-red-500/30 rounded-lg"
          >
            <ExclamationTriangleIcon className="w-5 h-5 text-red-400 mt-0.5" />
            <div className="flex-1">
              <div className="text-red-300 text-sm font-medium">
                第 {error.line} 行，第 {error.column} 列
              </div>
              <div className="text-red-200 text-sm">
                {error.message}
              </div>
            </div>
          </div>
        ))}

        {warnings.map((warning, index) => (
          <div
            key={index}
            className="flex items-start gap-2 px-3 py-2 bg-yellow-500/20 border border-yellow-500/30 rounded-lg"
          >
            <ExclamationTriangleIcon className="w-5 h-5 text-yellow-400 mt-0.5" />
            <div className="flex-1">
              <div className="text-yellow-300 text-sm font-medium">
                第 {warning.line} 行，第 {warning.column} 列
              </div>
              <div className="text-yellow-200 text-sm">
                {warning.message}
              </div>
              {warning.suggestion && (
                <div className="text-yellow-100 text-xs mt-1">
                  💡 建议：{warning.suggestion}
                </div>
              )}
            </div>
          </div>
        ))}
      </motion.div>
    )
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-900 via-blue-900 to-indigo-900 p-6">
      <div className="max-w-7xl mx-auto">
        {/* 🎯 页面标题 */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-8"
        >
          <h1 className="text-4xl font-bold text-white mb-2">
            📝 Playbook编辑器
          </h1>
          <p className="text-white/70">
            创建和编辑Ansible Playbook，支持实时语法验证和玻璃态界面
          </p>
        </motion.div>

        <div className="grid grid-cols-12 gap-6 h-[calc(100vh-200px)]">
          {/* 📁 文件浏览器面板 */}
          <motion.div
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            className="col-span-3"
          >
            <GlassCard className="h-full flex flex-col">
              {/* 🔍 搜索和操作栏 */}
              <div className="flex flex-col gap-3 mb-4">
                <div className="flex items-center justify-between">
                  <h2 className="text-lg font-semibold text-white">
                    📁 文件浏览器
                  </h2>
                  <GlassButton
                    size="sm"
                    onClick={() => setShowCreateModal(true)}
                    title="新建文件 (Ctrl+N)"
                  >
                    <PlusIcon className="w-4 h-4" />
                  </GlassButton>
                </div>

                <GlassInput
                  placeholder="🔍 搜索文件..."
                  value={searchTerm}
                  onChange={(e) => handleSearch(e.target.value)}
                  className="text-sm"
                />

                <div className="flex gap-2">
                  <GlassButton
                    size="sm"
                    variant="ghost"
                    onClick={() => loadPlaybooks(searchTerm)}
                    disabled={isLoading}
                    title="刷新列表"
                  >
                    <ArrowPathIcon className={`w-4 h-4 ${isLoading ? 'animate-spin' : ''}`} />
                  </GlassButton>
                </div>
              </div>

              {/* 📂 Playbook列表 */}
              <div className="flex-1 overflow-y-auto space-y-1 group">
                {isLoading ? (
                  <div className="flex items-center justify-center py-8">
                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-white/50"></div>
                  </div>
                ) : filteredPlaybooks.length === 0 ? (
                  <div className="text-center py-8 text-white/50">
                    {searchTerm ? '🔍 未找到匹配的Playbook' : '📁 暂无Playbook'}
                    <div className="mt-4">
                      <GlassButton
                        size="sm"
                        onClick={() => setShowCreateModal(true)}
                      >
                        <PlusIcon className="w-4 h-4 mr-2" />
                        创建第一个Playbook
                      </GlassButton>
                    </div>
                  </div>
                ) : (
                  filteredPlaybooks.map(playbook => renderPlaybookItem(playbook))
                )}
              </div>
            </GlassCard>
          </motion.div>

          {/* 📝 编辑器面板 */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="col-span-6"
          >
            <GlassCard className="h-full flex flex-col">
              {/* 📄 文件信息栏 */}
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-3">
                  {selectedPlaybook ? (
                    <>
                      <DocumentTextIcon className="w-6 h-6 text-green-300" />
                      <div>
                        <h3 className="text-lg font-semibold text-white">
                          {selectedPlaybook.display_name || selectedPlaybook.filename}
                        </h3>
                        <p className="text-sm text-white/60">
                          {selectedPlaybook.description || selectedPlaybook.filename}
                        </p>
                      </div>
                      {isModified && (
                        <span className="px-2 py-1 bg-orange-500/20 border border-orange-500/30 rounded text-orange-300 text-xs">
                          未保存
                        </span>
                      )}
                    </>
                  ) : (
                    <div className="text-white/60">
                      👈 请选择一个Playbook开始编辑
                    </div>
                  )}
                </div>

                {selectedPlaybook && (
                  <div className="flex gap-2">
                    <GlassButton
                      size="sm"
                      onClick={savePlaybook}
                      disabled={!isModified || isSaving}
                      title="保存Playbook (Ctrl+S)"
                    >
                      {isSaving ? (
                        <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white/50"></div>
                      ) : (
                        <DocumentArrowDownIcon className="w-4 h-4" />
                      )}
                      保存
                    </GlassButton>
                  </div>
                )}
              </div>

              {/* 🎨 Monaco编辑器 */}
              <div className="flex-1 rounded-lg overflow-hidden border border-white/20 relative">
                {selectedPlaybook ? (
                  <>
                    {/* 📥 内容加载指示器 */}
                    {isLoadingContent && (
                      <div className="absolute inset-0 bg-black/40 backdrop-blur-sm z-10 flex items-center justify-center">
                        <div className="text-center">
                          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-white/70 mx-auto mb-4"></div>
                          <p className="text-white/90 text-lg font-medium">
                            📥 正在加载文件内容...
                          </p>
                          <p className="text-white/60 text-sm mt-2">
                            {selectedPlaybook.filename}
                          </p>
                        </div>
                      </div>
                    )}
                    
                    {/* 🎨 编辑器加载指示器 */}
                    {!isEditorReady && !isLoadingContent && (
                      <div className="absolute inset-0 bg-black/40 backdrop-blur-sm z-10 flex items-center justify-center">
                        <div className="text-center">
                          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-white/70 mx-auto mb-4"></div>
                          <p className="text-white/90 text-lg font-medium">
                            🎨 正在初始化编辑器...
                          </p>
                          <p className="text-white/60 text-sm mt-2">
                            首次加载可能需要几秒钟
                          </p>
                        </div>
                      </div>
                    )}
                    
                    <Editor
                      height="100%"
                      defaultLanguage="yaml"
                      value={editorContent}
                      onChange={handleEditorChange}
                      onMount={(editor, monaco) => {
                        // 🎯 只注册一次 Ansible 功能
                        if (!ansibleFeaturesRegistered) {
                          registerAnsibleTheme(monaco)
                          registerAnsibleCompletionProvider(monaco)
                          ansibleFeaturesRegistered = true
                        }
                        
                        // 🎨 应用主题
                        monaco.editor.setTheme('ansible-dark')
                        
                        // ✅ 编辑器加载完成
                        setIsEditorReady(true)
                      }}
                      theme="vs-dark"
                      loading={
                        <div className="h-full flex items-center justify-center bg-black/20">
                          <div className="text-center">
                            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-white/70 mx-auto mb-4"></div>
                            <p className="text-white/90 text-lg font-medium">
                              🎨 正在加载编辑器...
                            </p>
                          </div>
                        </div>
                      }
                      options={{
                        minimap: { enabled: false },
                        fontSize: 14,
                        lineNumbers: 'on',
                        roundedSelection: false,
                        scrollBeyondLastLine: false,
                        automaticLayout: true,
                        tabSize: 2,
                        insertSpaces: true,
                        wordWrap: 'on',
                        folding: true,
                        lineDecorationsWidth: 10,
                        lineNumbersMinChars: 3,
                        glyphMargin: false,
                        renderLineHighlight: 'line',
                        selectOnLineNumbers: true,
                        cursorStyle: 'line',
                        cursorBlinking: 'blink',
                        renderWhitespace: 'selection',
                        // 🚀 性能优化选项
                        readOnly: isLoadingContent, // 加载时设为只读
                      }}
                    />
                  </>
                ) : (
                  <div className="h-full flex items-center justify-center bg-black/20">
                    <div className="text-center text-white/50">
                      <DocumentTextIcon className="w-16 h-16 mx-auto mb-4 opacity-50" />
                      <p className="text-lg mb-2">选择文件开始编辑</p>
                      <p className="text-sm">
                        支持YAML语法高亮和实时验证
                      </p>
                    </div>
                  </div>
                )}
              </div>
            </GlassCard>
          </motion.div>

          {/* ✅ 验证结果面板 */}
          <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            className="col-span-3"
          >
            <GlassCard className="h-full flex flex-col">
              <div className="flex items-center gap-2 mb-4">
                <CheckCircleIcon className="w-6 h-6 text-green-300" />
                <h2 className="text-lg font-semibold text-white">
                  语法验证
                </h2>
                {isValidating && (
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white/50"></div>
                )}
              </div>

              <div className="flex-1 overflow-y-auto">
                {selectedPlaybook ? (
                  renderValidationResult()
                ) : (
                  <div className="text-center py-8 text-white/50">
                    <CheckCircleIcon className="w-12 h-12 mx-auto mb-3 opacity-50" />
                    <p>选择Playbook后显示验证结果</p>
                  </div>
                )}
              </div>

              {/* 📊 快速操作 */}
              {selectedPlaybook && (
                <div className="mt-4 pt-4 border-t border-white/20">
                  <div className="space-y-2">
                    <GlassButton
                      size="sm"
                      variant="ghost"
                      className="w-full justify-start"
                      onClick={() => validateContent(editorContent)}
                      disabled={isValidating}
                    >
                      <ArrowPathIcon className="w-4 h-4 mr-2" />
                      重新验证
                    </GlassButton>

                    <GlassButton
                      size="sm"
                      variant="ghost"
                      className="w-full justify-start"
                    >
                      <PlayIcon className="w-4 h-4 mr-2" />
                      运行Playbook
                    </GlassButton>
                  </div>
                </div>
              )}
            </GlassCard>
          </motion.div>
        </div>

        {/* 📝 新建文件模态框 */}
        <GlassModal
          isOpen={showCreateModal}
          onClose={() => {
            setShowCreateModal(false)
            setNewFileName('')
          }}
          title="📝 新建Playbook文件"
        >
          <div className="space-y-4">
            <GlassInput
              label="文件名"
              placeholder="例如：deploy-app.yml"
              value={newFileName}
              onChange={(e) => setNewFileName(e.target.value)}
              autoFocus
              onKeyDown={(e) => {
                if (e.key === 'Enter' && newFileName.trim()) {
                  createNewFile()
                }
              }}
            />

            <div className="space-y-2 text-sm text-white/70">
              <div className="flex items-start gap-2">
                <span>💡</span>
                <span>文件将自动添加 .yml 扩展名（如果未指定）</span>
              </div>
              <div className="flex items-start gap-2">
                <span>📌</span>
                <span>文件名不能与现有文件重复</span>
              </div>
            </div>

            <div className="flex gap-3 justify-end">
              <GlassButton
                variant="ghost"
                onClick={() => {
                  setShowCreateModal(false)
                  setNewFileName('')
                }}
              >
                取消
              </GlassButton>
              <GlassButton
                onClick={createNewFile}
                disabled={!newFileName.trim()}
              >
                <PlusIcon className="w-4 h-4 mr-2" />
                创建文件
              </GlassButton>
            </div>
          </div>
        </GlassModal>

        {/* 🗑️ 删除确认对话框 */}
        {showDeleteDialog && createPortal(
          <div
            className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-[9999]"
            onClick={(e) => {
              if (e.target === e.currentTarget) {
                cancelDeletePlaybook()
              }
            }}
          >
            <motion.div
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              className="bg-white/10 backdrop-blur-md rounded-2xl border border-white/20 p-6 w-96 max-w-[90vw]"
              onClick={(e) => e.stopPropagation()}
            >
              <h3 className="text-xl font-semibold text-white mb-4">🗑️ 删除文件</h3>

              <div className="mb-6">
                <p className="text-gray-300 mb-2">
                  确定要删除 <span className="font-semibold text-white">
                    {playbookToDelete?.filename}
                  </span> 吗？
                </p>
                <p className="text-sm text-red-400 mt-2">
                  ⚠️ 此操作无法恢复！
                </p>
              </div>

              <div className="flex gap-3">
                <button
                  onClick={confirmDeletePlaybook}
                  className="flex-1 px-4 py-2 bg-red-500 hover:bg-red-600
                           rounded-lg text-white font-medium transition-colors"
                >
                  确认删除
                </button>
                <button
                  onClick={cancelDeletePlaybook}
                  className="flex-1 px-4 py-2 bg-white/10 hover:bg-white/20
                           rounded-lg text-white font-medium transition-colors"
                >
                  取消
                </button>
              </div>
            </motion.div>
          </div>,
          document.body
        )}
      </div>
    </div>
  )
}

export default Playbooks
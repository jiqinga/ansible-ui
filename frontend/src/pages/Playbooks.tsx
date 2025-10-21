import React, { useState, useEffect, useCallback } from 'react'
import { motion, AnimatePresence } from 'framer-motion'

import Editor from '@monaco-editor/react'
import {
  FolderIcon,
  DocumentTextIcon,
  PlayIcon,
  CheckCircleIcon,
  ExclamationTriangleIcon,
  PlusIcon,
  TrashIcon,
  ArrowPathIcon,
  DocumentArrowDownIcon,

  ChevronRightIcon,
  ChevronDownIcon
} from '@heroicons/react/24/outline'
import { FolderOpenIcon } from '@heroicons/react/24/solid'

import GlassCard from '../components/UI/GlassCard'
import GlassButton from '../components/UI/GlassButton'
import GlassInput from '../components/UI/GlassInput'
import GlassModal from '../components/UI/GlassModal'
import { useNotification } from '../contexts/NotificationContext'
import PlaybookService, { FileItem, ValidationResult } from '../services/playbookService'

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

  // 📁 文件浏览器状态
  const [files, setFiles] = useState<FileItem[]>([])
  const [currentPath, setCurrentPath] = useState('')
  const [selectedFile, setSelectedFile] = useState<FileItem | null>(null)
  const [expandedFolders, setExpandedFolders] = useState<Set<string>>(new Set())

  // 📝 编辑器状态
  const [editorContent, setEditorContent] = useState('')
  const [originalContent, setOriginalContent] = useState('')
  const [isModified, setIsModified] = useState(false)
  const [isLoading, setIsLoading] = useState(false)
  const [isSaving, setIsSaving] = useState(false)

  // ✅ 验证状态
  const [validationResult, setValidationResult] = useState<ValidationResult | null>(null)
  const [isValidating, setIsValidating] = useState(false)

  // 🔍 搜索状态
  const [searchTerm, setSearchTerm] = useState('')
  const [filteredFiles, setFilteredFiles] = useState<FileItem[]>([])

  // 📝 新建文件模态框
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [newFileName, setNewFileName] = useState('')

  /**
   * 📂 加载文件列表
   */
  const loadFiles = useCallback(async (path: string = '') => {
    setIsLoading(true)
    try {
      const fileList = await PlaybookService.getPlaybooks(path)
      setFiles(fileList)
      setFilteredFiles(fileList)
      setCurrentPath(path)
    } catch (err) {
      error('❌ 加载文件列表失败')
    } finally {
      setIsLoading(false)
    }
  }, [error])

  /**
   * 📄 加载文件内容
   */
  const loadFileContent = useCallback(async (file: FileItem) => {
    if (file.is_directory) return

    setIsLoading(true)
    try {
      const content = await PlaybookService.getPlaybookContent(file.path)
      setEditorContent(content)
      setOriginalContent(content)
      setSelectedFile(file)
      setIsModified(false)
      
      // 🔄 自动验证
      validateContent(content)
    } catch (err) {
      error('❌ 加载文件内容失败')
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
   * 💾 保存文件内容
   */
  const saveFile = useCallback(async () => {
    if (!selectedFile || !isModified) return

    setIsSaving(true)
    try {
      await PlaybookService.savePlaybookContent(selectedFile.path, editorContent)
      setOriginalContent(editorContent)
      setIsModified(false)
      success('✅ 文件保存成功')
    } catch (error) {
      console.error('❌ 保存文件失败', error)
    } finally {
      setIsSaving(false)
    }
  }, [selectedFile, isModified, editorContent, success, error])

  /**
   * 📝 创建新文件
   */
  const createNewFile = useCallback(async () => {
    if (!newFileName.trim()) return

    try {
      const fileName = newFileName.endsWith('.yml') || newFileName.endsWith('.yaml') 
        ? newFileName 
        : `${newFileName}.yml`

      await PlaybookService.createPlaybook({
        filename: fileName,  // 修改为 filename 以匹配后端 API
        content: `---
- name: ${fileName.replace(/\.(yml|yaml)$/, '')}
  hosts: all
  become: yes
  
  tasks:
    - name: 示例任务
      debug:
        msg: "Hello from ${fileName}"
`,
        path: currentPath
      })

      setNewFileName('')
      setShowCreateModal(false)
      success('✅ 文件创建成功')
      
      // 🔄 重新加载文件列表
      loadFiles(currentPath)
    } catch (error) {
      console.error('❌ 创建文件失败', error)
    }
  }, [newFileName, currentPath, loadFiles, success, error])

  /**
   * 🗑️ 删除文件
   */
  const deleteFile = useCallback(async (file: FileItem) => {
    if (!confirm(`确定要删除 ${file.name} 吗？`)) return

    try {
      await PlaybookService.deletePlaybook(file.path)
      success('✅ 文件删除成功')
      
      // 🔄 重新加载文件列表
      loadFiles(currentPath)
      
      // 如果删除的是当前打开的文件，清空编辑器
      if (selectedFile?.path === file.path) {
        setSelectedFile(null)
        setEditorContent('')
        setOriginalContent('')
        setIsModified(false)
        setValidationResult(null)
      }
    } catch (error) {
      console.error('❌ 删除文件失败', error)
    }
  }, [currentPath, loadFiles, selectedFile, success, error])

  /**
   * 📁 切换文件夹展开状态
   */
  const toggleFolder = useCallback((folderPath: string) => {
    setExpandedFolders(prev => {
      const newSet = new Set(prev)
      if (newSet.has(folderPath)) {
        newSet.delete(folderPath)
      } else {
        newSet.add(folderPath)
      }
      return newSet
    })
  }, [])

  /**
   * 🔍 搜索文件
   */
  const handleSearch = useCallback((term: string) => {
    setSearchTerm(term)
    if (!term.trim()) {
      setFilteredFiles(files)
      return
    }

    const filtered = files.filter(file => 
      file.name.toLowerCase().includes(term.toLowerCase())
    )
    setFilteredFiles(filtered)
  }, [files])

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
    loadFiles()
  }, [loadFiles])

  // ⌨️ 键盘快捷键
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.ctrlKey || e.metaKey) {
        switch (e.key) {
          case 's':
            e.preventDefault()
            if (isModified) saveFile()
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
  }, [isModified, saveFile])
  /**

   * 🎨 渲染文件树项目
   */
  const renderFileItem = (file: FileItem, level: number = 0) => {
    const isExpanded = expandedFolders.has(file.path)
    const isSelected = selectedFile?.path === file.path

    return (
      <div key={file.path} className="select-none">
        <motion.div
          className={`
            flex items-center gap-2 px-3 py-2 rounded-lg cursor-pointer
            transition-all duration-200 hover:bg-white/10
            ${isSelected ? 'bg-white/20 border border-white/30' : ''}
          `}
          style={{ paddingLeft: `${12 + level * 16}px` }}
          onClick={() => {
            if (file.is_directory) {
              toggleFolder(file.path)
            } else {
              loadFileContent(file)
            }
          }}
          whileHover={{ y: -2 }}
          whileTap={{ y: 0 }}
        >
          {file.is_directory ? (
            <>
              {isExpanded ? (
                <ChevronDownIcon className="w-4 h-4 text-white/70" />
              ) : (
                <ChevronRightIcon className="w-4 h-4 text-white/70" />
              )}
              {isExpanded ? (
                <FolderOpenIcon className="w-5 h-5 text-blue-300" />
              ) : (
                <FolderIcon className="w-5 h-5 text-blue-300" />
              )}
            </>
          ) : (
            <>
              <div className="w-4 h-4" />
              <DocumentTextIcon className="w-5 h-5 text-green-300" />
            </>
          )}
          
          <span className="flex-1 text-white/90 text-sm font-medium">
            {file.name}
          </span>
          
          {!file.is_directory && (
            <div className="flex items-center gap-1">
              <span className="text-xs text-white/50">
                {file.size ? `${Math.round(file.size / 1024)}KB` : ''}
              </span>
              <GlassButton
                size="sm"
                variant="ghost"
                onClick={(e) => {
                  e.stopPropagation()
                  deleteFile(file)
                }}
                className="opacity-0 group-hover:opacity-100 transition-opacity"
              >
                <TrashIcon className="w-4 h-4" />
              </GlassButton>
            </div>
          )}
        </motion.div>
        
        {file.is_directory && isExpanded && file.children && (
          <AnimatePresence>
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: 'auto' }}
              exit={{ opacity: 0, height: 0 }}
              transition={{ duration: 0.2 }}
            >
              {file.children.map(child => renderFileItem(child, level + 1))}
            </motion.div>
          </AnimatePresence>
        )}
      </div>
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
                    onClick={() => loadFiles(currentPath)}
                    disabled={isLoading}
                    title="刷新文件列表"
                  >
                    <ArrowPathIcon className={`w-4 h-4 ${isLoading ? 'animate-spin' : ''}`} />
                  </GlassButton>
                </div>
              </div>

              {/* 📂 文件树 */}
              <div className="flex-1 overflow-y-auto space-y-1 group">
                {isLoading ? (
                  <div className="flex items-center justify-center py-8">
                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-white/50"></div>
                  </div>
                ) : filteredFiles.length === 0 ? (
                  <div className="text-center py-8 text-white/50">
                    {searchTerm ? '🔍 未找到匹配的文件' : '📁 暂无文件'}
                  </div>
                ) : (
                  filteredFiles.map(file => renderFileItem(file))
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
                  {selectedFile ? (
                    <>
                      <DocumentTextIcon className="w-6 h-6 text-green-300" />
                      <div>
                        <h3 className="text-lg font-semibold text-white">
                          {selectedFile.name}
                        </h3>
                        <p className="text-sm text-white/60">
                          {selectedFile.path}
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
                      👈 请选择一个文件开始编辑
                    </div>
                  )}
                </div>

                {selectedFile && (
                  <div className="flex gap-2">
                    <GlassButton
                      size="sm"
                      onClick={saveFile}
                      disabled={!isModified || isSaving}
                      title="保存文件 (Ctrl+S)"
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
              <div className="flex-1 rounded-lg overflow-hidden border border-white/20">
                {selectedFile ? (
                  <Editor
                    height="100%"
                    defaultLanguage="yaml"
                    value={editorContent}
                    onChange={handleEditorChange}
                    theme="vs-dark"
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
                      renderWhitespace: 'selection'
                    }}
                  />
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
                {selectedFile ? (
                  renderValidationResult()
                ) : (
                  <div className="text-center py-8 text-white/50">
                    <CheckCircleIcon className="w-12 h-12 mx-auto mb-3 opacity-50" />
                    <p>选择文件后显示验证结果</p>
                  </div>
                )}
              </div>

              {/* 📊 快速操作 */}
              {selectedFile && (
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
            />
            
            <div className="text-sm text-white/60">
              💡 文件将自动添加 .yml 扩展名（如果未指定）
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
                创建文件
              </GlassButton>
            </div>
          </div>
        </GlassModal>
      </div>
    </div>
  )
}

export default Playbooks
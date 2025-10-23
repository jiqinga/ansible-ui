/**
 * 📁 项目浏览器组件
 */

import React, { useState, useEffect, useRef } from 'react';
import { createPortal } from 'react-dom';
import { motion } from 'framer-motion';
import {
  FolderIcon,
  PlusIcon,
  ArrowPathIcon,
} from '@heroicons/react/24/outline';
import { FileTreeView } from './FileTreeView';
import { ProjectSwitcher } from './ProjectSwitcher';
import { projectService } from '../../services/projectService';
import type { Project, FileNode } from '../../types/project';
import { extractErrorMessage } from '../../utils/errorHandler';
import { useNotification } from '../../contexts/NotificationContext';

interface ProjectExplorerProps {
  projectId?: number;
  onFileSelect?: (file: FileNode) => void;
  onProjectChange?: (project: Project) => void;
  refreshTrigger?: number; // 🔄 用于触发刷新的计数器
}

export const ProjectExplorer: React.FC<ProjectExplorerProps> = ({
  projectId,
  onFileSelect,
  onProjectChange,
  refreshTrigger,
}) => {
  // 🔔 通知功能
  const { success, error: showError } = useNotification();

  const [projects, setProjects] = useState<Project[]>([]);
  const [recentProjects, setRecentProjects] = useState<Project[]>([]);
  const [selectedProject, setSelectedProject] = useState<Project | null>(null);
  const [fileTree, setFileTree] = useState<FileNode | null>(null);
  const [selectedPath, setSelectedPath] = useState<string>('');
  const [selectedNode, setSelectedNode] = useState<FileNode | null>(null); // 🎯 记录选中的节点
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string>('');
  const [showNewFileDialog, setShowNewFileDialog] = useState(false);
  const [newFileName, setNewFileName] = useState('');
  const [showDeleteDialog, setShowDeleteDialog] = useState(false);
  const [projectToDelete, setProjectToDelete] = useState<Project | null>(null);
  const [showDeleteFileDialog, setShowDeleteFileDialog] = useState(false);
  const [fileToDelete, setFileToDelete] = useState<FileNode | null>(null);

  // 使用 ref 跟踪是否已经加载过
  const hasLoadedRef = useRef(false);

  // 加载项目列表
  useEffect(() => {
    // 防止重复加载
    if (!hasLoadedRef.current) {
      hasLoadedRef.current = true;
      loadProjects();
    }
  }, []);



  // 当projectId变化时，加载对应项目
  useEffect(() => {
    if (projectId) {
      loadProject(projectId);
    }
  }, [projectId]);

  // 🔄 当 refreshTrigger 变化时，重新加载项目列表
  useEffect(() => {
    if (refreshTrigger !== undefined && refreshTrigger > 0) {
      // 重新加载项目列表，但保持当前选中的项目
      loadProjects();
    }
  }, [refreshTrigger]);

  const loadProjects = async () => {
    try {
      setLoading(true);
      setError('');
      const data = await projectService.getProjects();
      setProjects(data.projects);

      // 🔄 如果当前有选中的项目，检查它是否还在列表中
      if (selectedProject) {
        const stillExists = data.projects.find(p => p.id === selectedProject.id);
        if (stillExists) {
          // 项目仍然存在，更新项目信息（可能有变化）
          const updatedProject = await projectService.getProject(selectedProject.id);
          setSelectedProject(updatedProject);
        } else {
          // 项目已被删除，清空选择
          setSelectedProject(null);
          setFileTree(null);
        }
      }

      // 如果有项目且没有选中项目，选中第一个
      if (data.projects.length > 0 && !selectedProject) {
        await loadProject(data.projects[0].id);
      } else if (data.projects.length === 0) {
        setError('暂无项目，请先创建一个项目');
      }
    } catch (err: any) {
      console.error('加载项目列表失败:', err);
      setError(extractErrorMessage(err, '加载项目列表失败'));
    } finally {
      setLoading(false);
    }
  };

  const loadProject = async (id: number, forceRefresh = false) => {
    // 防止重复加载同一个项目（除非强制刷新）
    if (!forceRefresh && selectedProject?.id === id && fileTree) {
      return;
    }

    try {
      setLoading(true);
      setError('');

      // 加载项目详情
      const project = await projectService.getProject(id);
      setSelectedProject(project);

      // 更新最近使用列表
      setRecentProjects((prev) => {
        const filtered = prev.filter((p) => p.id !== project.id);
        return [project, ...filtered].slice(0, 5); // 保留最近5个
      });

      if (onProjectChange) {
        onProjectChange(project);
      }

      // 加载文件树
      const structure = await projectService.getProjectFiles(id);
      setFileTree(structure.structure);
    } catch (err: any) {
      console.error('加载项目失败:', err);
      setError(extractErrorMessage(err, '加载项目失败'));
      // 清空文件树
      setFileTree(null);
    } finally {
      setLoading(false);
    }
  };

  const handleProjectSelect = async (project: Project) => {
    await loadProject(project.id);
  };

  const handleFileClick = (node: FileNode) => {
    setSelectedPath(node.path);
    setSelectedNode(node); // 🎯 保存选中的节点

    if (node.type === 'file' && onFileSelect) {
      onFileSelect(node);
    }
  };

  const handleRefresh = async () => {
    if (selectedProject) {
      // 🔄 强制刷新，忽略防重复加载逻辑
      await loadProject(selectedProject.id, true);
    }
  };

  const handleNewFile = () => {
    if (!selectedProject) {
      alert('请先选择一个项目');
      return;
    }

    // 🎯 根据选中的节点设置默认路径
    let defaultPath = '';
    if (selectedNode) {
      if (selectedNode.type === 'directory') {
        // 如果选中的是目录，在该目录下创建
        defaultPath = selectedNode.path + '/';
      } else {
        // 如果选中的是文件，在文件所在目录下创建
        const lastSlashIndex = selectedNode.path.lastIndexOf('/');
        if (lastSlashIndex > 0) {
          defaultPath = selectedNode.path.substring(0, lastSlashIndex + 1);
        }
      }
    }

    setNewFileName(defaultPath);
    setShowNewFileDialog(true);
  };

  const handleCreateFile = async () => {
    if (!selectedProject || !newFileName.trim()) {
      return;
    }

    try {
      setLoading(true);

      // 创建新文件（空内容）
      await projectService.writeFile(selectedProject.id, newFileName.trim(), '');

      // 🔄 强制刷新文件树 - 重新加载项目文件结构
      const structure = await projectService.getProjectFiles(selectedProject.id);
      setFileTree(structure.structure);

      // 重置状态
      setShowNewFileDialog(false);
      setNewFileName('');

      // ✅ 显示成功提示
      success(`文件 ${newFileName.trim()} 创建成功`);
    } catch (err: any) {
      showError('创建文件失败', extractErrorMessage(err, '创建文件失败'));
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteProject = (project: Project) => {
    setProjectToDelete(project);
    setShowDeleteDialog(true);
  };

  const confirmDeleteFile = async () => {
    if (!selectedProject || !fileToDelete) return;

    try {
      setLoading(true);
      const fileName = fileToDelete.name;
      const fileType = fileToDelete.type === 'directory' ? '目录' : '文件';

      await projectService.deleteFile(selectedProject.id, fileToDelete.path);

      // 🔄 强制刷新文件树
      const structure = await projectService.getProjectFiles(selectedProject.id);
      setFileTree(structure.structure);

      // 清空选中状态
      setSelectedPath('');
      setSelectedNode(null);

      // 关闭对话框
      setShowDeleteFileDialog(false);
      setFileToDelete(null);

      // ✅ 显示成功提示
      success(`${fileType} "${fileName}" 已成功删除`);
    } catch (err: any) {
      showError('删除失败', extractErrorMessage(err, '删除文件失败'));
    } finally {
      setLoading(false);
    }
  };

  const confirmDeleteProject = async () => {
    if (!projectToDelete) return;

    try {
      setLoading(true);
      const projectName = projectToDelete.display_name || projectToDelete.name;
      await projectService.deleteProject(projectToDelete.id);

      // 刷新项目列表
      await loadProjects();

      // 从最近使用列表中移除
      setRecentProjects(recentProjects.filter((p) => p.id !== projectToDelete.id));

      // 如果删除的是当前选中的项目，清空选择
      if (selectedProject?.id === projectToDelete.id) {
        setSelectedProject(null);
        setFileTree(null);
      }

      setShowDeleteDialog(false);
      setProjectToDelete(null);

      // ✅ 显示成功提示
      success(`项目 "${projectName}" 已成功删除`);
    } catch (err: any) {
      showError('删除项目失败', extractErrorMessage(err, '删除项目失败'));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="h-full flex flex-col bg-white/10 backdrop-blur-md rounded-2xl border border-white/20">
      {/* 头部 */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-white/10">
        <div className="flex items-center gap-2">
          <FolderIcon className="w-5 h-5 text-blue-400" />
          <h3 className="text-lg font-semibold text-white">项目浏览器</h3>
        </div>

        <div className="flex items-center gap-2">
          <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            onClick={handleRefresh}
            className="p-2 rounded-lg bg-white/10 hover:bg-white/20 transition-colors"
            title="刷新"
          >
            <ArrowPathIcon className="w-4 h-4 text-white" />
          </motion.button>

          <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            onClick={handleNewFile}
            className="p-2 rounded-lg bg-white/10 hover:bg-white/20 transition-colors"
            title="新建文件"
            disabled={!selectedProject}
          >
            <PlusIcon className="w-4 h-4 text-white" />
          </motion.button>
        </div>
      </div>

      {/* 项目切换器 */}
      <div className="p-4 border-b border-white/10">
        <ProjectSwitcher
          projects={projects}
          activeProject={selectedProject}
          onProjectSelect={handleProjectSelect}
          onProjectDelete={handleDeleteProject}
          recentProjects={recentProjects}
        />
      </div>

      {/* 文件树 */}
      <div className="flex-1 overflow-y-auto p-2">
        {loading && (
          <div className="flex items-center justify-center h-32">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-white"></div>
          </div>
        )}

        {error && (
          <div className="p-4 bg-red-500/20 border border-red-500/30 rounded-lg">
            <p className="text-red-200 text-sm">{error}</p>
          </div>
        )}

        {!loading && !error && fileTree && (
          <FileTreeView
            node={fileTree}
            onNodeClick={handleFileClick}
            onNodeDelete={(node) => {
              setFileToDelete(node);
              setShowDeleteFileDialog(true);
            }}
            selectedPath={selectedPath}
          />
        )}

        {!loading && !error && !fileTree && (
          <div className="flex flex-col items-center justify-center h-32 text-gray-400">
            <FolderIcon className="w-12 h-12 mb-2" />
            <p className="text-sm">选择一个项目开始</p>
          </div>
        )}
      </div>

      {/* 删除文件确认对话框 */}
      {showDeleteFileDialog && createPortal(
        <div
          className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-[9999]"
          onClick={(e) => {
            if (e.target === e.currentTarget) {
              setShowDeleteFileDialog(false);
              setFileToDelete(null);
            }
          }}
        >
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            className="bg-white/10 backdrop-blur-md rounded-2xl border border-white/20 p-6 w-96 max-w-[90vw]"
            onClick={(e) => e.stopPropagation()}
          >
            <h3 className="text-xl font-semibold text-white mb-4">
              🗑️ 删除{fileToDelete?.type === 'directory' ? '目录' : '文件'}
            </h3>

            <div className="mb-6">
              <p className="text-gray-300 mb-2">
                确定要删除 <span className="font-semibold text-white">
                  {fileToDelete?.name}
                </span> 吗？
              </p>
              {fileToDelete?.type === 'directory' && (
                <p className="text-sm text-red-400 mb-2">
                  ⚠️ 此操作将删除该目录及其所有子文件和子目录！
                </p>
              )}
              <p className="text-sm text-gray-400">
                📁 路径: {fileToDelete?.path}
              </p>
              <p className="text-sm text-red-400 mt-2">
                ⚠️ 此操作无法恢复！
              </p>
            </div>

            <div className="flex gap-3">
              <button
                onClick={confirmDeleteFile}
                disabled={loading}
                className="flex-1 px-4 py-2 bg-red-500 hover:bg-red-600 disabled:bg-gray-500
                         rounded-lg text-white font-medium transition-colors"
              >
                {loading ? '删除中...' : '确认删除'}
              </button>
              <button
                onClick={() => {
                  setShowDeleteFileDialog(false);
                  setFileToDelete(null);
                }}
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

      {/* 删除项目确认对话框 */}
      {showDeleteDialog && createPortal(
        <div
          className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-[9999]"
          onClick={(e) => {
            if (e.target === e.currentTarget) {
              setShowDeleteDialog(false);
              setProjectToDelete(null);
            }
          }}
        >
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            className="bg-white/10 backdrop-blur-md rounded-2xl border border-white/20 p-6 w-96 max-w-[90vw]"
            onClick={(e) => e.stopPropagation()}
          >
            <h3 className="text-xl font-semibold text-white mb-4">🗑️ 删除项目</h3>

            <div className="mb-6">
              <p className="text-gray-300 mb-2">
                确定要删除项目 <span className="font-semibold text-white">
                  {projectToDelete?.display_name || projectToDelete?.name}
                </span> 吗？
              </p>
              <p className="text-sm text-red-400">
                ⚠️ 此操作将删除项目的所有文件和配置，且无法恢复！
              </p>
            </div>

            <div className="flex gap-3">
              <button
                onClick={confirmDeleteProject}
                disabled={loading}
                className="flex-1 px-4 py-2 bg-red-500 hover:bg-red-600 disabled:bg-gray-500
                         rounded-lg text-white font-medium transition-colors"
              >
                {loading ? '删除中...' : '确认删除'}
              </button>
              <button
                onClick={() => {
                  setShowDeleteDialog(false);
                  setProjectToDelete(null);
                }}
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

      {/* 新建文件对话框 - 使用 Portal 渲染到 body */}
      {showNewFileDialog && createPortal(
        <div
          className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-[9999]"
          onClick={(e) => {
            if (e.target === e.currentTarget) {
              setShowNewFileDialog(false);
              setNewFileName('');
            }
          }}
        >
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            className="bg-white/10 backdrop-blur-md rounded-2xl border border-white/20 p-6 w-96 max-w-[90vw]"
            onClick={(e) => e.stopPropagation()}
          >
            <h3 className="text-xl font-semibold text-white mb-4">📄 新建文件</h3>

            <div className="mb-4">
              <label className="block text-sm text-gray-300 mb-2">
                文件路径（相对于项目根目录）
              </label>
              <input
                type="text"
                value={newFileName}
                onChange={(e) => setNewFileName(e.target.value)}
                placeholder="例如: playbooks/site.yml"
                className="w-full px-3 py-2 bg-white/10 border border-white/20 rounded-lg text-white
                         placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-400/50"
                onKeyDown={(e) => {
                  if (e.key === 'Enter') {
                    handleCreateFile();
                  } else if (e.key === 'Escape') {
                    setShowNewFileDialog(false);
                    setNewFileName('');
                  }
                }}
                autoFocus
              />
              <p className="text-xs text-gray-400 mt-1">
                {selectedNode && selectedNode.type === 'directory'
                  ? `📁 将在目录 "${selectedNode.path}" 下创建文件`
                  : selectedNode && selectedNode.type === 'file'
                    ? `📁 将在 "${selectedNode.path.substring(0, selectedNode.path.lastIndexOf('/') || 0)}" 目录下创建文件`
                    : '💡 提示：可以包含目录路径，系统会自动创建所需目录'
                }
              </p>
            </div>

            <div className="flex gap-3">
              <button
                onClick={handleCreateFile}
                disabled={!newFileName.trim() || loading}
                className="flex-1 px-4 py-2 bg-blue-500 hover:bg-blue-600 disabled:bg-gray-500
                         rounded-lg text-white font-medium transition-colors"
              >
                {loading ? '创建中...' : '创建'}
              </button>
              <button
                onClick={() => {
                  setShowNewFileDialog(false);
                  setNewFileName('');
                }}
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
  );
};

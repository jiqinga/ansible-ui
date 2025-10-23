/**
 * 📦 项目管理页面
 */

import React, { useState } from 'react';
import { PlusIcon } from '@heroicons/react/24/outline';
import { ProjectExplorer } from '../components/Project/ProjectExplorer';
import { MultiTabEditor } from '../components/Project/MultiTabEditor';
import { ProjectWizard } from '../components/Project/ProjectWizard';
import { projectService } from '../services/projectService';
import type { Project, FileNode, EditorTab } from '../types/project';

export const Projects: React.FC = () => {
  const [selectedProject, setSelectedProject] = useState<Project | null>(null);
  const [editorTabs, setEditorTabs] = useState<EditorTab[]>([]);
  const [activeTabId, setActiveTabId] = useState<string>('');
  const [isWizardOpen, setIsWizardOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [refreshTrigger, setRefreshTrigger] = useState(0); // 🔄 刷新触发器

  const handleFileSelect = async (file: FileNode) => {
    if (file.type !== 'file' || !selectedProject) return;

    // 检查文件是否已打开
    const existingTab = editorTabs.find((tab) => tab.path === file.path);
    if (existingTab) {
      setActiveTabId(existingTab.id);
      return;
    }

    try {
      setLoading(true);
      
      // 读取文件内容
      const content = await projectService.readFile(selectedProject.id, file.path);
      
      // 创建新标签
      const newTab: EditorTab = {
        id: `${selectedProject.id}-${file.path}`,
        title: file.name,
        path: file.path,
        content,
        isDirty: false,
      };

      setEditorTabs([...editorTabs, newTab]);
      setActiveTabId(newTab.id);
    } catch (error) {
      console.error('读取文件失败:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleTabClose = (tabId: string) => {
    const tab = editorTabs.find((t) => t.id === tabId);
    
    // 如果文件有未保存的更改，提示用户
    if (tab?.isDirty) {
      const confirmed = window.confirm('文件有未保存的更改，确定要关闭吗？');
      if (!confirmed) return;
    }

    setEditorTabs(editorTabs.filter((t) => t.id !== tabId));
  };

  const handleContentChange = (tabId: string, content: string) => {
    setEditorTabs(
      editorTabs.map((tab) =>
        tab.id === tabId
          ? { ...tab, content, isDirty: content !== tab.content }
          : tab
      )
    );
  };

  const handleSave = async (tabId: string, content: string) => {
    const tab = editorTabs.find((t) => t.id === tabId);
    if (!tab || !selectedProject) return;

    try {
      setLoading(true);
      
      await projectService.writeFile(selectedProject.id, tab.path, content);
      
      // 标记为已保存
      setEditorTabs(
        editorTabs.map((t) =>
          t.id === tabId ? { ...t, isDirty: false } : t
        )
      );
    } catch (error) {
      console.error('保存文件失败:', error);
      alert('保存文件失败');
    } finally {
      setLoading(false);
    }
  };

  const handleProjectComplete = (project: Project) => {
    setSelectedProject(project);
    // 🔄 触发项目列表刷新
    setRefreshTrigger(prev => prev + 1);
  };

  return (
    <div className="min-h-screen p-6">
      {/* 页面头部 */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-3xl font-bold text-white mb-2">📦 项目管理</h1>
          <p className="text-gray-300">管理Ansible项目和文件</p>
        </div>

        <button
          onClick={() => setIsWizardOpen(true)}
          className="flex items-center gap-2 px-6 py-3 bg-blue-500 hover:bg-blue-600
                   rounded-xl text-white font-medium transition-all
                   hover:-translate-y-1 active:translate-y-0
                   shadow-lg hover:shadow-xl"
        >
          <PlusIcon className="w-5 h-5" />
          新建项目
        </button>
      </div>

      {/* 主要内容区域 */}
      <div className="grid grid-cols-12 gap-6 h-[calc(100vh-200px)]">
        {/* 左侧：项目浏览器 */}
        <div className="col-span-3">
          <ProjectExplorer
            onFileSelect={handleFileSelect}
            onProjectChange={setSelectedProject}
            refreshTrigger={refreshTrigger}
          />
        </div>

        {/* 右侧：编辑器 */}
        <div className="col-span-9">
          <MultiTabEditor
            tabs={editorTabs}
            activeTabId={activeTabId}
            onTabChange={setActiveTabId}
            onTabClose={handleTabClose}
            onContentChange={handleContentChange}
            onSave={handleSave}
          />
        </div>
      </div>

      {/* 项目创建向导 */}
      <ProjectWizard
        isOpen={isWizardOpen}
        onClose={() => setIsWizardOpen(false)}
        onComplete={handleProjectComplete}
      />

      {/* 加载指示器 */}
      {loading && (
        <div className="fixed bottom-4 right-4 px-4 py-2 bg-blue-500 text-white rounded-lg shadow-lg">
          处理中...
        </div>
      )}
    </div>
  );
};

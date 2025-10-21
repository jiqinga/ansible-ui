/**
 * 📝 多标签编辑器组件
 */

import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { XMarkIcon, DocumentIcon } from '@heroicons/react/24/outline';
import Editor from '@monaco-editor/react';
import type { EditorTab } from '../../types/project';

interface MultiTabEditorProps {
  tabs: EditorTab[];
  activeTabId?: string;
  onTabChange?: (tabId: string) => void;
  onTabClose?: (tabId: string) => void;
  onContentChange?: (tabId: string, content: string) => void;
  onSave?: (tabId: string, content: string) => void;
}

export const MultiTabEditor: React.FC<MultiTabEditorProps> = ({
  tabs,
  activeTabId,
  onTabChange,
  onTabClose,
  onContentChange,
  onSave,
}) => {
  const [currentTabId, setCurrentTabId] = useState<string>(activeTabId || tabs[0]?.id);
  const [editorContent, setEditorContent] = useState<Record<string, string>>({});

  useEffect(() => {
    if (activeTabId) {
      setCurrentTabId(activeTabId);
    }
  }, [activeTabId]);

  // 初始化编辑器内容
  useEffect(() => {
    const content: Record<string, string> = {};
    tabs.forEach((tab) => {
      content[tab.id] = tab.content;
    });
    setEditorContent(content);
  }, [tabs]);

  const currentTab = tabs.find((tab) => tab.id === currentTabId);

  const handleTabClick = (tabId: string) => {
    setCurrentTabId(tabId);
    if (onTabChange) {
      onTabChange(tabId);
    }
  };

  const handleTabClose = (e: React.MouseEvent, tabId: string) => {
    e.stopPropagation();
    
    if (onTabClose) {
      onTabClose(tabId);
    }
    
    // 如果关闭的是当前标签，切换到下一个标签
    if (tabId === currentTabId) {
      const currentIndex = tabs.findIndex((tab) => tab.id === tabId);
      const nextTab = tabs[currentIndex + 1] || tabs[currentIndex - 1];
      if (nextTab) {
        setCurrentTabId(nextTab.id);
      }
    }
  };

  const handleEditorChange = (value: string | undefined) => {
    if (value !== undefined && currentTab) {
      setEditorContent((prev) => ({
        ...prev,
        [currentTab.id]: value,
      }));
      
      if (onContentChange) {
        onContentChange(currentTab.id, value);
      }
    }
  };

  const handleSave = () => {
    if (currentTab && onSave) {
      onSave(currentTab.id, editorContent[currentTab.id] || '');
    }
  };

  // 获取文件语言
  const getLanguage = (filename: string): string => {
    const ext = filename.split('.').pop()?.toLowerCase();
    const languageMap: Record<string, string> = {
      yml: 'yaml',
      yaml: 'yaml',
      py: 'python',
      js: 'javascript',
      ts: 'typescript',
      json: 'json',
      md: 'markdown',
      txt: 'plaintext',
      cfg: 'ini',
      ini: 'ini',
      sh: 'shell',
    };
    return languageMap[ext || ''] || 'plaintext';
  };

  // 键盘快捷键
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Ctrl+S / Cmd+S 保存
      if ((e.ctrlKey || e.metaKey) && e.key === 's') {
        e.preventDefault();
        handleSave();
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [currentTab, editorContent]);

  if (tabs.length === 0) {
    return (
      <div className="h-full flex items-center justify-center bg-white/5 backdrop-blur-md rounded-2xl border border-white/20">
        <div className="text-center text-gray-400">
          <DocumentIcon className="w-16 h-16 mx-auto mb-4 opacity-50" />
          <p className="text-lg">没有打开的文件</p>
          <p className="text-sm mt-2">从项目浏览器中选择文件开始编辑</p>
        </div>
      </div>
    );
  }

  return (
    <div className="h-full flex flex-col bg-white/5 backdrop-blur-md rounded-2xl border border-white/20 overflow-hidden">
      {/* 标签栏 */}
      <div className="flex items-center gap-1 px-2 py-2 bg-white/5 border-b border-white/10 overflow-x-auto">
        <AnimatePresence>
          {tabs.map((tab) => (
            <motion.div
              key={tab.id}
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.9 }}
              transition={{ duration: 0.15 }}
              className={`
                flex items-center gap-2 px-3 py-2 rounded-lg cursor-pointer
                transition-all duration-200 min-w-[120px] max-w-[200px]
                ${
                  tab.id === currentTabId
                    ? 'bg-white/20 text-white'
                    : 'bg-white/5 text-gray-300 hover:bg-white/10'
                }
              `}
              onClick={() => handleTabClick(tab.id)}
            >
              <DocumentIcon className="w-4 h-4 flex-shrink-0" />
              <span className="text-sm truncate flex-1">{tab.title}</span>
              {tab.isDirty && (
                <div className="w-2 h-2 rounded-full bg-blue-400 flex-shrink-0" />
              )}
              <motion.button
                whileHover={{ scale: 1.2 }}
                whileTap={{ scale: 0.9 }}
                onClick={(e) => handleTabClose(e, tab.id)}
                className="flex-shrink-0 hover:bg-white/20 rounded p-0.5"
              >
                <XMarkIcon className="w-3 h-3" />
              </motion.button>
            </motion.div>
          ))}
        </AnimatePresence>
      </div>

      {/* 编辑器区域 */}
      <div className="flex-1 overflow-hidden">
        {currentTab && (
          <Editor
            height="100%"
            language={currentTab.language || getLanguage(currentTab.title)}
            value={editorContent[currentTab.id] || ''}
            onChange={handleEditorChange}
            theme="vs-dark"
            options={{
              minimap: { enabled: true },
              fontSize: 14,
              lineNumbers: 'on',
              roundedSelection: true,
              scrollBeyondLastLine: false,
              automaticLayout: true,
              tabSize: 2,
              wordWrap: 'on',
            }}
          />
        )}
      </div>

      {/* 状态栏 */}
      <div className="flex items-center justify-between px-4 py-2 bg-white/5 border-t border-white/10 text-xs text-gray-400">
        <div className="flex items-center gap-4">
          <span>{currentTab?.title}</span>
          {currentTab && (
            <span>
              {currentTab.language || getLanguage(currentTab.title)}
            </span>
          )}
        </div>
        <div className="flex items-center gap-4">
          {currentTab?.isDirty && <span className="text-blue-400">● 未保存</span>}
          <span>Ctrl+S 保存</span>
        </div>
      </div>
    </div>
  );
};

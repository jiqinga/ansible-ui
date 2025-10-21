/**
 * 🌲 文件树视图组件
 */

import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  FolderIcon,
  FolderOpenIcon,
  DocumentIcon,
  ChevronRightIcon,
  ChevronDownIcon,
} from '@heroicons/react/24/outline';
import type { FileNode } from '../../types/project';

interface FileTreeViewProps {
  node: FileNode;
  level?: number;
  onNodeClick?: (node: FileNode) => void;
  selectedPath?: string;
}

export const FileTreeView: React.FC<FileTreeViewProps> = ({
  node,
  level = 0,
  onNodeClick,
  selectedPath,
}) => {
  const [isExpanded, setIsExpanded] = useState(level < 2); // 默认展开前两层

  const isDirectory = node.type === 'directory';
  const hasChildren = isDirectory && node.children && node.children.length > 0;
  const isSelected = node.path === selectedPath;

  const handleToggle = (e: React.MouseEvent) => {
    e.stopPropagation();
    if (isDirectory) {
      setIsExpanded(!isExpanded);
    }
  };

  const handleClick = () => {
    if (onNodeClick) {
      onNodeClick(node);
    }
    if (isDirectory && !isExpanded) {
      setIsExpanded(true);
    }
  };

  const getFileIcon = () => {
    if (isDirectory) {
      return isExpanded ? (
        <FolderOpenIcon className="w-5 h-5 text-blue-400" />
      ) : (
        <FolderIcon className="w-5 h-5 text-blue-400" />
      );
    }

    // 根据文件扩展名返回不同颜色
    const ext = node.name.split('.').pop()?.toLowerCase();
    const colorMap: Record<string, string> = {
      yml: 'text-green-400',
      yaml: 'text-green-400',
      py: 'text-yellow-400',
      js: 'text-yellow-300',
      ts: 'text-blue-300',
      json: 'text-orange-400',
      md: 'text-gray-400',
      txt: 'text-gray-400',
      cfg: 'text-purple-400',
      ini: 'text-purple-400',
    };

    const color = colorMap[ext || ''] || 'text-gray-300';

    return <DocumentIcon className={`w-5 h-5 ${color}`} />;
  };

  return (
    <div className="select-none">
      {/* 当前节点 */}
      <motion.div
        className={`
          flex items-center gap-2 px-3 py-2 rounded-lg cursor-pointer
          transition-all duration-200
          ${isSelected ? 'bg-white/20 backdrop-blur-md' : 'hover:bg-white/10'}
        `}
        style={{ paddingLeft: `${level * 20 + 12}px` }}
        onClick={handleClick}
        whileHover={{ x: 2 }}
      >
        {/* 展开/折叠图标 */}
        {isDirectory && hasChildren && (
          <motion.div
            onClick={handleToggle}
            className="flex-shrink-0"
            animate={{ rotate: isExpanded ? 90 : 0 }}
            transition={{ duration: 0.2 }}
          >
            <ChevronRightIcon className="w-4 h-4 text-gray-400" />
          </motion.div>
        )}

        {/* 占位符（无子节点时） */}
        {isDirectory && !hasChildren && <div className="w-4" />}

        {/* 文件/文件夹图标 */}
        <div className="flex-shrink-0">{getFileIcon()}</div>

        {/* 文件名 */}
        <span
          className={`
            text-sm truncate
            ${isSelected ? 'text-white font-medium' : 'text-gray-200'}
          `}
        >
          {node.name}
        </span>

        {/* 文件大小 */}
        {!isDirectory && node.size !== undefined && (
          <span className="ml-auto text-xs text-gray-400 flex-shrink-0">
            {formatFileSize(node.size)}
          </span>
        )}
      </motion.div>

      {/* 子节点 */}
      <AnimatePresence>
        {isDirectory && isExpanded && hasChildren && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="overflow-hidden"
          >
            {node.children!.map((child, index) => (
              <FileTreeView
                key={`${child.path}-${index}`}
                node={child}
                level={level + 1}
                onNodeClick={onNodeClick}
                selectedPath={selectedPath}
              />
            ))}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

/**
 * 格式化文件大小
 */
function formatFileSize(bytes: number): string {
  if (bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return `${(bytes / Math.pow(k, i)).toFixed(1)} ${sizes[i]}`;
}

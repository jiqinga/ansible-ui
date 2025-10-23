/**
 * 🔄 项目切换器组件
 */

import React, { useState } from 'react';
import { motion } from 'framer-motion';
import {
  MagnifyingGlassIcon,
  ClockIcon,
  TrashIcon,
  ChevronDownIcon,
} from '@heroicons/react/24/outline';
import { createPortal } from 'react-dom';
import type { Project } from '../../types/project';

interface ProjectSwitcherProps {
  projects: Project[];
  activeProject: Project | null;
  onProjectSelect: (project: Project) => void;
  onProjectDelete?: (project: Project) => void;
  recentProjects?: Project[];
}

export const ProjectSwitcher: React.FC<ProjectSwitcherProps> = ({
  projects,
  activeProject,
  onProjectSelect,
  onProjectDelete,
  recentProjects = [],
}) => {
  const [showPicker, setShowPicker] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');

  // 过滤项目列表
  const filteredProjects = projects.filter((project) => {
    const displayName = project.display_name || project.name;
    return displayName.toLowerCase().includes(searchQuery.toLowerCase());
  });

  // 获取其他项目（排除最近使用的）
  const otherProjects = filteredProjects.filter(
    (project) => !recentProjects.find((p) => p.id === project.id)
  );

  const handleProjectClick = (project: Project) => {
    onProjectSelect(project);
    setShowPicker(false);
    setSearchQuery('');
  };

  return (
    <>
      {/* 项目选择按钮 */}
      <button
        onClick={() => setShowPicker(true)}
        className="w-full px-4 py-2.5 bg-white/20 backdrop-blur-md border border-white/30 
                 rounded-xl text-white text-left flex items-center justify-between
                 hover:bg-white/30 transition-all focus:outline-none focus:ring-2 focus:ring-purple-400/50"
      >
        <div className="flex-1 min-w-0">
          <div className="text-xs text-white/60 mb-0.5">当前项目</div>
          <div className="font-semibold truncate">
            {activeProject
              ? activeProject.display_name || activeProject.name
              : '选择项目'}
          </div>
        </div>
        <ChevronDownIcon className="w-5 h-5 text-white/80 flex-shrink-0 ml-2" />
      </button>

      {/* 项目选择器弹窗 */}
      {showPicker &&
        createPortal(
          <div
            className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-[9999]"
            onClick={(e) => {
              if (e.target === e.currentTarget) {
                setShowPicker(false);
                setSearchQuery('');
              }
            }}
          >
            <motion.div
              initial={{ opacity: 0, scale: 0.95, y: 20 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.95, y: 20 }}
              transition={{ duration: 0.2, ease: [0.4, 0, 0.2, 1] }}
              className="bg-white/15 backdrop-blur-2xl rounded-2xl border border-white/20 
                       w-[600px] max-w-[90vw] max-h-[80vh] overflow-hidden flex flex-col shadow-2xl"
              onClick={(e) => e.stopPropagation()}
            >
              {/* 搜索框 */}
              <div className="p-6 border-b border-white/10">
                <div className="relative">
                  <MagnifyingGlassIcon className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-white/60" />
                  <input
                    type="text"
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    placeholder="搜索项目..."
                    className="w-full pl-11 pr-4 py-3.5 bg-white/10 border border-white/20 rounded-xl 
                             text-white placeholder-white/50 focus:outline-none focus:ring-2 
                             focus:ring-purple-400/50 focus:bg-white/15 focus:border-purple-400/50 
                             transition-all font-medium"
                    autoFocus
                  />
                </div>
              </div>

              {/* 项目列表 */}
              <div className="flex-1 overflow-y-auto p-6">
                {/* 最近使用 */}
                {recentProjects.length > 0 && searchQuery === '' && (
                  <div className="mb-6">
                    <div className="flex items-center gap-2 mb-3 px-1">
                      <ClockIcon className="w-4 h-4 text-purple-400" />
                      <h3 className="text-sm font-bold text-white/90 uppercase tracking-wide">
                        最近使用
                      </h3>
                    </div>
                    <div className="space-y-2">
                      {recentProjects.map((project) => (
                        <motion.div
                          key={project.id}
                          whileHover={{ translateY: -2 }}
                          transition={{ duration: 0.2 }}
                          className="group px-5 py-4 bg-white/10 hover:bg-white/20 rounded-xl 
                                   cursor-pointer transition-all duration-200 border border-white/20
                                   hover:border-purple-400/50 hover:shadow-lg"
                        >
                          <div
                            onClick={() => handleProjectClick(project)}
                            className="flex items-center justify-between"
                          >
                            <div className="flex-1 min-w-0">
                              <span className="text-white font-bold text-base">
                                {project.display_name || project.name}
                              </span>
                              {project.description && (
                                <p className="text-sm text-white/60 mt-1 truncate">
                                  {project.description}
                                </p>
                              )}
                            </div>
                            <div className="flex items-center gap-2 flex-shrink-0 ml-3">
                              {activeProject?.id === project.id && (
                                <span className="text-xs px-3 py-1.5 bg-gradient-to-r from-purple-500 to-blue-500 
                                             rounded-full text-white font-bold shadow-md">
                                  ✓ 当前
                                </span>
                              )}
                              {onProjectDelete && (
                                <button
                                  onClick={(e) => {
                                    e.stopPropagation();
                                    onProjectDelete(project);
                                    setShowPicker(false);
                                  }}
                                  className="opacity-0 group-hover:opacity-100 p-2 rounded-lg hover:bg-red-500/20 
                                           transition-all duration-200"
                                  title="删除项目"
                                >
                                  <TrashIcon className="w-4 h-4 text-red-400" />
                                </button>
                              )}
                            </div>
                          </div>
                        </motion.div>
                      ))}
                    </div>
                  </div>
                )}

                {/* 所有项目 */}
                {otherProjects.length > 0 && (
                  <div>
                    <h3 className="text-sm font-bold text-white/90 mb-3 px-1 uppercase tracking-wide">
                      {searchQuery ? '🔍 搜索结果' : '📁 所有项目'}
                    </h3>
                    <div className="space-y-2">
                      {otherProjects.map((project) => (
                        <motion.div
                          key={project.id}
                          whileHover={{ translateY: -2 }}
                          transition={{ duration: 0.2 }}
                          className="group px-5 py-4 bg-white/10 hover:bg-white/20 rounded-xl 
                                   cursor-pointer transition-all duration-200 border border-white/20
                                   hover:border-purple-400/50 hover:shadow-lg"
                        >
                          <div
                            onClick={() => handleProjectClick(project)}
                            className="flex items-center justify-between"
                          >
                            <div className="flex-1 min-w-0">
                              <span className="text-white font-bold text-base">
                                {project.display_name || project.name}
                              </span>
                              {project.description && (
                                <p className="text-sm text-white/60 mt-1 truncate">
                                  {project.description}
                                </p>
                              )}
                            </div>
                            {onProjectDelete && (
                              <button
                                onClick={(e) => {
                                  e.stopPropagation();
                                  onProjectDelete(project);
                                  setShowPicker(false);
                                }}
                                className="opacity-0 group-hover:opacity-100 p-2 rounded-lg hover:bg-red-500/20 
                                         transition-all duration-200 flex-shrink-0 ml-3"
                                title="删除项目"
                              >
                                <TrashIcon className="w-4 h-4 text-red-400" />
                              </button>
                            )}
                          </div>
                        </motion.div>
                      ))}
                    </div>
                  </div>
                )}

                {/* 无结果 */}
                {filteredProjects.length === 0 && (
                  <div className="text-center py-16">
                    <div className="text-5xl mb-4">🔍</div>
                    <p className="text-white/90 font-semibold text-lg">未找到匹配的项目</p>
                    <p className="text-white/60 text-sm mt-2">尝试使用其他关键词搜索</p>
                  </div>
                )}
              </div>

              {/* 底部提示 */}
              <div className="px-6 py-4 border-t border-white/10 bg-white/5">
                <p className="text-xs text-white/70 text-center font-medium">
                  💡 提示：点击项目名称切换，悬停显示删除按钮
                </p>
              </div>
            </motion.div>
          </div>,
          document.body
        )}
    </>
  );
};

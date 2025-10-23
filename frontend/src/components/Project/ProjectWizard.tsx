/**
 * 🧙 项目创建向导组件
 */

import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  XMarkIcon,
  FolderIcon,
  CheckCircleIcon,
  ArrowRightIcon,
  ArrowLeftIcon,
} from '@heroicons/react/24/outline';
import { projectService } from '../../services/projectService';
import type { Project, ProjectCreate } from '../../types/project';
import { extractErrorMessage } from '../../utils/errorHandler';

interface ProjectWizardProps {
  isOpen: boolean;
  onClose: () => void;
  onComplete: (project: Project) => void;
}

const PROJECT_TYPES = [
  {
    value: 'standard',
    label: '标准项目',
    description: '包含完整的Ansible项目结构，适合大型项目',
    icon: '📦',
  },
  {
    value: 'simple',
    label: '简单项目',
    description: '单文件项目，适合快速测试和小型任务',
    icon: '📄',
  },
  {
    value: 'role-based',
    label: 'Role项目',
    description: '以Role为中心的项目结构',
    icon: '🎭',
  },
];

const TEMPLATES = {
  standard: [
    { value: 'standard', label: '标准模板', description: '完整的目录结构' },
  ],
  simple: [
    { value: 'simple', label: '简单模板', description: '最小化结构' },
  ],
  'role-based': [
    { value: 'role-based', label: 'Role模板', description: 'Role为中心' },
  ],
};

export const ProjectWizard: React.FC<ProjectWizardProps> = ({
  isOpen,
  onClose,
  onComplete,
}) => {
  const [step, setStep] = useState(1);
  const [formData, setFormData] = useState<ProjectCreate>({
    name: '',
    display_name: '',
    description: '',
    project_type: 'standard',
    template: 'standard',
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  // 🔄 当对话框关闭时重置表单
  React.useEffect(() => {
    if (!isOpen) {
      // 延迟重置，等待关闭动画完成
      const timer = setTimeout(() => {
        setFormData({
          name: '',
          display_name: '',
          description: '',
          project_type: 'standard',
          template: 'standard',
        });
        setStep(1);
        setError('');
      }, 300);
      return () => clearTimeout(timer);
    }
  }, [isOpen]);

  const handleNext = () => {
    if (step < 3) {
      setStep(step + 1);
    }
  };

  const handleBack = () => {
    if (step > 1) {
      setStep(step - 1);
    }
  };

  const handleSubmit = async () => {
    try {
      setLoading(true);
      setError('');
      
      const project = await projectService.createProject(formData);
      onComplete(project);
      onClose(); // 关闭对话框，useEffect 会自动重置表单
    } catch (err: any) {
      setError(extractErrorMessage(err, '创建项目失败'));
    } finally {
      setLoading(false);
    }
  };

  const canProceed = () => {
    if (step === 1) {
      return formData.name.trim() !== '';
    }
    return true;
  };

  if (!isOpen) return null;

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm"
        onClick={onClose}
      >
        <motion.div
          initial={{ scale: 0.9, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          exit={{ scale: 0.9, opacity: 0 }}
          onClick={(e) => e.stopPropagation()}
          className="w-full max-w-2xl bg-white/10 backdrop-blur-md rounded-2xl border border-white/20 overflow-hidden"
        >
          {/* 头部 */}
          <div className="flex items-center justify-between p-6 border-b border-white/10">
            <div className="flex items-center gap-3">
              <FolderIcon className="w-6 h-6 text-blue-400" />
              <h2 className="text-xl font-semibold text-white">创建新项目</h2>
            </div>
            <button
              onClick={onClose}
              className="p-2 rounded-lg hover:bg-white/10 transition-colors"
            >
              <XMarkIcon className="w-5 h-5 text-gray-400" />
            </button>
          </div>

          {/* 步骤指示器 */}
          <div className="flex items-center justify-center gap-4 p-6 border-b border-white/10">
            {[1, 2, 3].map((s) => (
              <div key={s} className="flex items-center gap-2">
                <div
                  className={`
                    w-8 h-8 rounded-full flex items-center justify-center
                    transition-all duration-300
                    ${
                      s === step
                        ? 'bg-blue-500 text-white'
                        : s < step
                        ? 'bg-green-500 text-white'
                        : 'bg-white/10 text-gray-400'
                    }
                  `}
                >
                  {s < step ? <CheckCircleIcon className="w-5 h-5" /> : s}
                </div>
                {s < 3 && (
                  <div
                    className={`w-16 h-1 rounded ${
                      s < step ? 'bg-green-500' : 'bg-white/10'
                    }`}
                  />
                )}
              </div>
            ))}
          </div>

          {/* 内容区域 */}
          <div className="p-6 min-h-[300px]">
            <AnimatePresence mode="wait">
              {/* 步骤1：基本信息 */}
              {step === 1 && (
                <motion.div
                  key="step1"
                  initial={{ opacity: 0, x: 20 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: -20 }}
                  className="space-y-4"
                >
                  <h3 className="text-lg font-medium text-white mb-4">基本信息</h3>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-300 mb-2">
                      项目名称 *
                    </label>
                    <input
                      type="text"
                      value={formData.name}
                      onChange={(e) =>
                        setFormData({ ...formData, name: e.target.value })
                      }
                      className="w-full px-4 py-2 bg-white/10 border border-white/20 rounded-lg
                               text-white placeholder-gray-400
                               focus:outline-none focus:ring-2 focus:ring-blue-400/50"
                      placeholder="my-ansible-project"
                    />
                    <p className="mt-1 text-xs text-gray-400">
                      项目唯一标识符，只能包含字母、数字、下划线和连字符
                    </p>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-300 mb-2">
                      显示名称
                    </label>
                    <input
                      type="text"
                      value={formData.display_name}
                      onChange={(e) =>
                        setFormData({ ...formData, display_name: e.target.value })
                      }
                      className="w-full px-4 py-2 bg-white/10 border border-white/20 rounded-lg
                               text-white placeholder-gray-400
                               focus:outline-none focus:ring-2 focus:ring-blue-400/50"
                      placeholder="我的Ansible项目"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-300 mb-2">
                      项目描述
                    </label>
                    <textarea
                      value={formData.description}
                      onChange={(e) =>
                        setFormData({ ...formData, description: e.target.value })
                      }
                      rows={3}
                      className="w-full px-4 py-2 bg-white/10 border border-white/20 rounded-lg
                               text-white placeholder-gray-400
                               focus:outline-none focus:ring-2 focus:ring-blue-400/50"
                      placeholder="项目描述..."
                    />
                  </div>
                </motion.div>
              )}

              {/* 步骤2：项目类型 */}
              {step === 2 && (
                <motion.div
                  key="step2"
                  initial={{ opacity: 0, x: 20 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: -20 }}
                  className="space-y-4"
                >
                  <h3 className="text-lg font-medium text-white mb-4">选择项目类型</h3>
                  
                  <div className="grid grid-cols-1 gap-4">
                    {PROJECT_TYPES.map((type) => (
                      <div
                        key={type.value}
                        onClick={() => {
                          setFormData({
                            ...formData,
                            project_type: type.value as any,
                            template: type.value,
                          });
                        }}
                        className={`
                          p-4 rounded-lg border-2 cursor-pointer transition-all
                          hover:-translate-y-1
                          ${
                            formData.project_type === type.value
                              ? 'border-blue-400 bg-blue-500/20'
                              : 'border-white/20 bg-white/5 hover:bg-white/10'
                          }
                        `}
                      >
                        <div className="flex items-start gap-3">
                          <span className="text-3xl">{type.icon}</span>
                          <div className="flex-1">
                            <h4 className="text-white font-medium">{type.label}</h4>
                            <p className="text-sm text-gray-300 mt-1">
                              {type.description}
                            </p>
                          </div>
                          {formData.project_type === type.value && (
                            <CheckCircleIcon className="w-6 h-6 text-blue-400" />
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                </motion.div>
              )}

              {/* 步骤3：确认 */}
              {step === 3 && (
                <motion.div
                  key="step3"
                  initial={{ opacity: 0, x: 20 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: -20 }}
                  className="space-y-4"
                >
                  <h3 className="text-lg font-medium text-white mb-4">确认信息</h3>
                  
                  <div className="space-y-3 bg-white/5 rounded-lg p-4">
                    <div>
                      <span className="text-sm text-gray-400">项目名称：</span>
                      <span className="text-white ml-2">{formData.name}</span>
                    </div>
                    {formData.display_name && (
                      <div>
                        <span className="text-sm text-gray-400">显示名称：</span>
                        <span className="text-white ml-2">{formData.display_name}</span>
                      </div>
                    )}
                    {formData.description && (
                      <div>
                        <span className="text-sm text-gray-400">描述：</span>
                        <span className="text-white ml-2">{formData.description}</span>
                      </div>
                    )}
                    <div>
                      <span className="text-sm text-gray-400">项目类型：</span>
                      <span className="text-white ml-2">
                        {PROJECT_TYPES.find((t) => t.value === formData.project_type)?.label}
                      </span>
                    </div>
                  </div>

                  {error && (
                    <div className="p-4 bg-red-500/20 border border-red-500/30 rounded-lg">
                      <p className="text-red-200 text-sm">{error}</p>
                    </div>
                  )}
                </motion.div>
              )}
            </AnimatePresence>
          </div>

          {/* 底部按钮 */}
          <div className="flex items-center justify-between p-6 border-t border-white/10">
            <button
              onClick={handleBack}
              disabled={step === 1}
              className="flex items-center gap-2 px-4 py-2 rounded-lg
                       bg-white/10 hover:bg-white/20 disabled:opacity-50 disabled:cursor-not-allowed
                       transition-colors text-white"
            >
              <ArrowLeftIcon className="w-4 h-4" />
              上一步
            </button>

            <div className="flex items-center gap-3">
              <button
                onClick={onClose}
                className="px-4 py-2 rounded-lg bg-white/10 hover:bg-white/20
                         transition-colors text-white"
              >
                取消
              </button>

              {step < 3 ? (
                <button
                  onClick={handleNext}
                  disabled={!canProceed()}
                  className="flex items-center gap-2 px-4 py-2 rounded-lg
                           bg-blue-500 hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed
                           transition-colors text-white"
                >
                  下一步
                  <ArrowRightIcon className="w-4 h-4" />
                </button>
              ) : (
                <button
                  onClick={handleSubmit}
                  disabled={loading}
                  className="flex items-center gap-2 px-4 py-2 rounded-lg
                           bg-green-500 hover:bg-green-600 disabled:opacity-50
                           transition-colors text-white"
                >
                  {loading ? '创建中...' : '创建项目'}
                </button>
              )}
            </div>
          </div>
        </motion.div>
      </motion.div>
    </AnimatePresence>
  );
};

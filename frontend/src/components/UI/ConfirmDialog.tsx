/**
 * 🎨 玻璃态确认对话框组件
 * 
 * 符合玻璃态设计风格的确认对话框，提供清晰的视觉层次和流畅的动画效果
 */

import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  ExclamationTriangleIcon, 
  InformationCircleIcon,
  XMarkIcon 
} from '@heroicons/react/24/outline';
import GlassButton from './GlassButton';

interface ConfirmDialogProps {
  isOpen: boolean;
  title: string;
  message: string;
  confirmText?: string;
  cancelText?: string;
  type?: 'warning' | 'danger' | 'info';
  onConfirm: () => void;
  onCancel: () => void;
}

/**
 * 🎨 确认对话框组件
 */
const ConfirmDialog: React.FC<ConfirmDialogProps> = ({
  isOpen,
  title,
  message,
  confirmText = '确认',
  cancelText = '取消',
  type = 'warning',
  onConfirm,
  onCancel,
}) => {
  // 🎨 根据类型获取图标和颜色配置
  const getTypeConfig = () => {
    switch (type) {
      case 'danger':
        return {
          icon: ExclamationTriangleIcon,
          iconColor: 'text-red-500',
          iconBg: 'bg-red-500/10',
          iconBorder: 'border-red-500/20',
          titleColor: 'text-gray-800',
          confirmVariant: 'danger' as const,
        };
      case 'warning':
        return {
          icon: ExclamationTriangleIcon,
          iconColor: 'text-amber-500',
          iconBg: 'bg-amber-500/10',
          iconBorder: 'border-amber-500/20',
          titleColor: 'text-gray-800',
          confirmVariant: 'primary' as const,
        };
      case 'info':
        return {
          icon: InformationCircleIcon,
          iconColor: 'text-blue-500',
          iconBg: 'bg-blue-500/10',
          iconBorder: 'border-blue-500/20',
          titleColor: 'text-gray-800',
          confirmVariant: 'primary' as const,
        };
    }
  };

  const config = getTypeConfig();
  const Icon = config.icon;

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          {/* 🎨 背景遮罩 */}
          <motion.div
            className="fixed inset-0 bg-black/30 backdrop-blur-sm z-50"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.2 }}
            onClick={onCancel}
          />

          {/* 🎨 对话框容器 */}
          <div className="fixed inset-0 flex items-center justify-center z-50 p-4 pointer-events-none">
            <motion.div
              className="pointer-events-auto bg-white/40 backdrop-blur-xl border border-white/30 rounded-2xl shadow-2xl max-w-md w-full"
              initial={{ opacity: 0, scale: 0.95, y: 20 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.95, y: 20 }}
              transition={{ 
                type: 'spring', 
                damping: 25,
                stiffness: 300
              }}
              onClick={(e) => e.stopPropagation()}
            >
              <div className="p-6">
                {/* 🎨 关闭按钮 */}
                <button
                  onClick={onCancel}
                  className="absolute top-3 right-3 p-1.5 rounded-lg hover:bg-white/20 transition-colors"
                  aria-label="关闭"
                >
                  <XMarkIcon className="h-4 w-4 text-gray-600" />
                </button>

                {/* 🎨 图标和标题区域 */}
                <div className="flex items-start space-x-4 mb-4">
                  <motion.div
                    className={`flex-shrink-0 w-12 h-12 rounded-xl ${config.iconBg} border ${config.iconBorder} flex items-center justify-center`}
                    initial={{ scale: 0, rotate: -90 }}
                    animate={{ scale: 1, rotate: 0 }}
                    transition={{ 
                      type: 'spring',
                      delay: 0.1,
                      damping: 15
                    }}
                  >
                    <Icon className={`h-6 w-6 ${config.iconColor}`} />
                  </motion.div>

                  <div className="flex-1 pt-1">
                    <h3 className={`text-lg font-semibold ${config.titleColor} mb-2`}>
                      {title}
                    </h3>
                    <p className="text-sm text-gray-700 whitespace-pre-line leading-relaxed">
                      {message}
                    </p>
                  </div>
                </div>

                {/* 🎨 按钮组 */}
                <div className="flex items-center justify-end space-x-3 mt-6">
                  <GlassButton
                    variant="ghost"
                    onClick={onCancel}
                  >
                    {cancelText}
                  </GlassButton>
                  <GlassButton
                    variant={config.confirmVariant}
                    onClick={onConfirm}
                  >
                    {confirmText}
                  </GlassButton>
                </div>
              </div>
            </motion.div>
          </div>
        </>
      )}
    </AnimatePresence>
  );
};

export default ConfirmDialog;

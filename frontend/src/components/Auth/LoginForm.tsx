import React, { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { useTranslation } from 'react-i18next'
import { useNavigate, useLocation } from 'react-router-dom'
import { 
  UserIcon, 
  LockClosedIcon, 
  EyeIcon, 
  EyeSlashIcon,
  ArrowRightIcon,
  ExclamationTriangleIcon,
  CheckCircleIcon
} from '@heroicons/react/24/outline'
import { useAuth } from '../../contexts/AuthContext'
import { LoginCredentials } from '../../types'

import GlassInput from '../UI/GlassInput'
import GlassButton from '../UI/GlassButton'

/**
 * 🔐 登录表单组件
 * 
 * 功能：
 * - 玻璃态登录表单设计
 * - 实时表单验证
 * - 认证状态管理
 * - 中文错误提示
 * - 自动跳转功能
 */
const LoginForm: React.FC = () => {
  const { state, login } = useAuth()
  const { t } = useTranslation()
  const navigate = useNavigate()
  const location = useLocation()

  // 📝 表单状态
  const [formData, setFormData] = useState<LoginCredentials>({
    username: '',
    password: '',
    rememberMe: false,
  })

  const [showPassword, setShowPassword] = useState(false)
  const [isLoading, setIsLoading] = useState(false)
  const [errors, setErrors] = useState<Record<string, string>>({})
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null)

  // 🎨 动画配置
  const containerVariants = {
    hidden: { opacity: 0, y: 20 },
    visible: {
      opacity: 1,
      y: 0,
      transition: {
        duration: 0.5,
        ease: 'easeOut',
      },
    },
  }

  const formVariants = {
    hidden: { opacity: 0, y: 20 },
    visible: {
      opacity: 1,
      y: 0,
      transition: {
        duration: 0.4,
        delay: 0.2,
        staggerChildren: 0.1,
      },
    },
  }

  const itemVariants = {
    hidden: { opacity: 0, y: 10 },
    visible: { opacity: 1, y: 0 },
  }

  // 🔄 如果已登录，自动跳转
  useEffect(() => {
    if (state.isAuthenticated) {
      const from = (location.state as any)?.from || '/dashboard'
      navigate(from, { replace: true })
    }
  }, [state.isAuthenticated, navigate, location])

  // 📝 表单处理
  const handleInputChange = (field: keyof LoginCredentials, value: string | boolean) => {
    setFormData(prev => ({ ...prev, [field]: value }))
    
    // 清除对应字段的错误
    if (errors[field]) {
      setErrors(prev => ({ ...prev, [field]: '' }))
    }
    
    // 清除全局消息
    if (message) {
      setMessage(null)
    }
  }

  // ✅ 表单验证
  const validateForm = (): boolean => {
    const newErrors: Record<string, string> = {}

    // 用户名验证
    if (!formData.username.trim()) {
      newErrors.username = t('auth.inputValidation.usernameRequired')
    } else if (formData.username.length < 3) {
      newErrors.username = t('auth.inputValidation.usernameMinLength')
    }

    // 密码验证
    if (!formData.password) {
      newErrors.password = t('auth.inputValidation.passwordRequired')
    } else if (formData.password.length < 6) {
      newErrors.password = t('auth.inputValidation.passwordMinLength')
    }

    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  // 🚀 提交登录
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    if (!validateForm()) {
      return
    }

    setIsLoading(true)
    setMessage(null)
    
    try {
      const result = await login(formData)
      
      if (result.success) {
        setMessage({
          type: 'success',
          text: result.message || t('auth.loginSuccess'),
        })
        
        // 🎉 登录成功，延迟跳转以显示成功消息
        setTimeout(() => {
          const from = (location.state as any)?.from || '/dashboard'
          navigate(from, { replace: true })
        }, 1500)
      } else {
        // 🚨 根据错误类型提供不同的提示
        let errorMessage = result.message || t('auth.loginFailed')
        
        // 如果错误消息包含特定关键词，提供更友好的提示
        if (errorMessage.includes('用户名或密码错误') || 
            errorMessage.includes('401') ||
            errorMessage.includes('Unauthorized') ||
            errorMessage.includes('Invalid credentials')) {
          errorMessage = t('auth.credentialsError')
        } else if (errorMessage.includes('网络') || 
                   errorMessage.includes('连接') ||
                   errorMessage.includes('Network') ||
                   errorMessage.includes('fetch')) {
          errorMessage = t('auth.connectionError')
        } else if (errorMessage.includes('服务器') || 
                   errorMessage.includes('500') ||
                   errorMessage.includes('502') ||
                   errorMessage.includes('503')) {
          errorMessage = t('auth.serverUnavailable')
        } else if (errorMessage.includes('超时') || 
                   errorMessage.includes('timeout') ||
                   errorMessage.includes('504')) {
          errorMessage = t('auth.requestTimeout')
        } else if (errorMessage.includes('429') || 
                   errorMessage.includes('Too Many')) {
          errorMessage = t('auth.tooManyAttempts')
        }
        
        setMessage({
          type: 'error',
          text: errorMessage,
        })
      }
    } catch (error) {
      console.error('登录错误:', error)
      
      // 🌐 处理网络错误
      let errorMessage = t('auth.networkError')
      
      if (error instanceof Error) {
        if (error.message.includes('用户名或密码错误')) {
          errorMessage = t('auth.credentialsError')
        } else if (error.message.includes('网络') || error.message.includes('连接')) {
          errorMessage = t('auth.connectionError')
        } else if (error.message.includes('服务器')) {
          errorMessage = t('auth.serverUnavailable')
        } else if (error.message.includes('超时')) {
          errorMessage = t('auth.requestTimeout')
        }
      }
      
      setMessage({
        type: 'error',
        text: errorMessage,
      })
    } finally {
      setIsLoading(false)
    }
  }

  // 🎨 消息组件
  const MessageAlert: React.FC<{ message: { type: 'success' | 'error'; text: string } }> = ({ message }) => (
    <motion.div
      className={`mb-6 p-4 rounded-glass-sm border backdrop-blur-sm ${
        message.type === 'success'
          ? 'bg-green-500/15 border-green-400/30 text-green-800'
          : 'bg-red-500/15 border-red-400/30 text-red-800'
      }`}
      initial={{ opacity: 0, y: -10 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -10 }}
      transition={{ duration: 0.4, ease: 'easeOut' }}
    >
      <div className="flex items-start space-x-3">
        <div className={`flex-shrink-0 w-6 h-6 rounded-full flex items-center justify-center ${
          message.type === 'success' 
            ? 'bg-green-500/20' 
            : 'bg-red-500/20'
        }`}>
          {message.type === 'success' ? (
            <CheckCircleIcon className="w-4 h-4 text-green-600" />
          ) : (
            <ExclamationTriangleIcon className="w-4 h-4 text-red-600" />
          )}
        </div>
        <div className="flex-1 min-w-0">
          <p className="text-sm font-medium leading-relaxed">
            {message.text}
          </p>
          {message.type === 'error' && (
            <p className="text-xs mt-1 opacity-75">
              {t('auth.hints.checkCredentials')}
            </p>
          )}
        </div>
      </div>
    </motion.div>
  )

  return (
    <div className="min-h-screen gradient-bg-primary flex items-center justify-center p-4">
      <motion.div
        className="w-full max-w-md"
        variants={containerVariants}
        initial="hidden"
        animate="visible"
      >
        {/* 🎨 登录卡片 */}
        <div className="glass-container p-8">
          {/* 🎨 标题区域 */}
          <motion.div 
            className="text-center mb-8"
            variants={itemVariants}
          >
            <div className="w-16 h-16 mx-auto mb-4 glass-container rounded-full flex items-center justify-center">
              <UserIcon className="w-8 h-8 text-glass-text-accent" />
            </div>
            <h1 className="text-2xl font-bold text-glass-text-primary mb-2">
              🚀 Ansible Web UI
            </h1>
            <p className="text-glass-text-secondary">
              {t('auth.pleaseLogin')}
            </p>
          </motion.div>

          {/* 🔥 消息提示 */}
          {message && <MessageAlert message={message} />}

          {/* 📝 登录表单 */}
          <motion.form 
            onSubmit={handleSubmit}
            variants={formVariants}
            className="space-y-6"
          >
            {/* 👤 用户名输入 */}
            <motion.div variants={itemVariants}>
              <GlassInput
                label={t('auth.username')}
                type="text"
                value={formData.username}
                onChange={(e) => handleInputChange('username', e.target.value)}
                placeholder="请输入用户名"
                error={errors.username}
                disabled={isLoading}
                required
                autoComplete="username"
                className="pl-10"
                leftIcon={<UserIcon className="w-5 h-5 text-glass-text-secondary" />}
              />
            </motion.div>

            {/* 🔒 密码输入 */}
            <motion.div variants={itemVariants}>
              <GlassInput
                label={t('auth.password')}
                type={showPassword ? 'text' : 'password'}
                value={formData.password}
                onChange={(e) => handleInputChange('password', e.target.value)}
                placeholder="请输入密码"
                error={errors.password}
                disabled={isLoading}
                required
                autoComplete="current-password"
                className="pl-10 pr-10"
                leftIcon={<LockClosedIcon className="w-5 h-5 text-glass-text-secondary" />}
                rightIcon={
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="text-glass-text-secondary hover:text-glass-text-primary transition-colors"
                    disabled={isLoading}
                  >
                    {showPassword ? (
                      <EyeSlashIcon className="w-5 h-5" />
                    ) : (
                      <EyeIcon className="w-5 h-5" />
                    )}
                  </button>
                }
              />
            </motion.div>

            {/* ✅ 记住我和忘记密码 */}
            <motion.div 
              className="flex items-center justify-between"
              variants={itemVariants}
            >
              <label className="flex items-center cursor-pointer">
                <input
                  type="checkbox"
                  checked={formData.rememberMe}
                  onChange={(e) => handleInputChange('rememberMe', e.target.checked)}
                  className="w-4 h-4 text-glass-text-accent bg-white/20 border-white/30 rounded focus:ring-glass-text-accent focus:ring-2 transition-colors"
                  disabled={isLoading}
                />
                <span className="ml-2 text-glass-text-secondary text-sm">
                  {t('auth.rememberMe')}
                </span>
              </label>
              <button
                type="button"
                className="text-glass-text-accent text-sm hover:underline transition-colors"
                disabled={isLoading}
              >
                {t('auth.forgotPassword')}
              </button>
            </motion.div>

            {/* 🚀 登录按钮 */}
            <motion.div variants={itemVariants}>
              <GlassButton
                type="submit"
                variant="primary"
                size="lg"
                loading={isLoading}
                disabled={isLoading}
                className="w-full"
              >
                <div className="flex items-center justify-center space-x-2">
                  <span>
                    {isLoading ? t('auth.loggingIn') : `🚀 ${t('auth.login')}`}
                  </span>
                  {!isLoading && <ArrowRightIcon className="w-5 h-5" />}
                </div>
              </GlassButton>
            </motion.div>
          </motion.form>

          {/* 🎨 底部装饰 */}
          <motion.div 
            className="mt-8 text-center"
            variants={itemVariants}
          >
            <p className="text-glass-text-secondary text-sm">
              🎨 现代化玻璃态设计 • 🚀 高性能体验
            </p>
          </motion.div>
        </div>

        {/* 🎨 背景装饰元素 */}
        <div className="absolute inset-0 -z-10 overflow-hidden">
          <motion.div
            className="absolute top-1/4 left-1/4 w-32 h-32 bg-white/10 rounded-full blur-xl"
            animate={{
              scale: [1, 1.2, 1],
              opacity: [0.3, 0.6, 0.3],
            }}
            transition={{
              duration: 4,
              repeat: Infinity,
              ease: 'easeInOut',
            }}
          />
          <motion.div
            className="absolute bottom-1/4 right-1/4 w-24 h-24 bg-white/10 rounded-full blur-xl"
            animate={{
              scale: [1.2, 1, 1.2],
              opacity: [0.6, 0.3, 0.6],
            }}
            transition={{
              duration: 3,
              repeat: Infinity,
              ease: 'easeInOut',
            }}
          />
        </div>
      </motion.div>
    </div>
  )
}

export default LoginForm
/**
 * 👥 用户管理面板
 * 
 * 功能：
 * - 用户列表展示和搜索
 * - 用户创建、编辑、删除
 * - 用户角色和权限管理
 * - 用户状态管理
 */

import React, { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import {
  UsersIcon,
  PlusIcon,
  PencilIcon,
  TrashIcon,
  UserCircleIcon,
  ShieldCheckIcon,
  KeyIcon,
  EyeIcon,
  EyeSlashIcon
} from '@heroicons/react/24/outline'

import GlassCard from '../UI/GlassCard'
import GlassButton from '../UI/GlassButton'
import GlassInput from '../UI/GlassInput'
import GlassSelect from '../UI/GlassSelect'
import GlassModal from '../UI/GlassModal'
import GlassTable from '../UI/GlassTable'
import { useNotification } from '../../contexts/NotificationContext'
import { extractErrorMessage } from '../../utils/errorHandler'
import { 
  UserManagementService, 
  UserInfo, 
  UserStats
} from '../../services/settingsService'

interface UserManagementPanelProps {
  onRefresh?: () => void
}

// 🏷️ 用户表单数据类型
interface UserFormData {
  username: string
  email: string
  password: string
  full_name: string
  role: string
  is_active: boolean
}

// 📋 用户角色选项
const USER_ROLES = [
  { value: 'admin', label: '管理员', color: 'from-red-400 to-red-600' },
  { value: 'operator', label: '操作员', color: 'from-blue-400 to-blue-600' },
  { value: 'viewer', label: '查看者', color: 'from-green-400 to-green-600' }
]

/**
 * 👥 用户管理面板组件
 */
const UserManagementPanel: React.FC<UserManagementPanelProps> = () => {
  const { success, error: showError } = useNotification()
  
  // 🎯 状态管理
  const [users, setUsers] = useState<UserInfo[]>([])
  const [userStats, setUserStats] = useState<UserStats | null>(null)
  const [loading, setLoading] = useState(true)
  const [searchTerm, setSearchTerm] = useState('')
  const [roleFilter, setRoleFilter] = useState<string>('')
  const [statusFilter, setStatusFilter] = useState<string>('')
  const [currentPage, setCurrentPage] = useState(1)
  const [totalUsers, setTotalUsers] = useState(0)
  const pageSize = 10

  // 🎨 模态框状态
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [showEditModal, setShowEditModal] = useState(false)
  const [showDeleteModal, setShowDeleteModal] = useState(false)
  const [showPasswordModal, setShowPasswordModal] = useState(false)
  const [selectedUser, setSelectedUser] = useState<UserInfo | null>(null)
  const [formData, setFormData] = useState<UserFormData>({
    username: '',
    email: '',
    password: '',
    full_name: '',
    role: 'viewer',
    is_active: true
  })
  const [newPassword, setNewPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)

  // 🔄 初始化加载
  useEffect(() => {
    loadUsers()
    loadUserStats()
  }, [currentPage, searchTerm, roleFilter, statusFilter])

  /**
   * 👥 加载用户列表
   */
  const loadUsers = async () => {
    try {
      setLoading(true)
      const params: any = {
        page: currentPage,
        page_size: pageSize
      }
      
      if (searchTerm) params.search = searchTerm
      if (roleFilter) params.role = roleFilter
      if (statusFilter !== '') params.is_active = statusFilter === 'true'
      
      const response = await UserManagementService.getUsers(params)
      setUsers(response.users)
      setTotalUsers(response.total)
    } catch (err) {
      console.error('❌ 加载用户列表失败:', err)
      showError('加载用户列表失败')
    } finally {
      setLoading(false)
    }
  }

  /**
   * 📊 加载用户统计
   */
  const loadUserStats = async () => {
    try {
      const stats = await UserManagementService.getUserStats()
      setUserStats(stats)
    } catch (err) {
      console.error('❌ 加载用户统计失败:', err)
    }
  }

  /**
   * ➕ 创建用户
   */
  const createUser = async () => {
    try {
      await UserManagementService.createUser(formData)
      success('用户创建成功')
      setShowCreateModal(false)
      resetForm()
      loadUsers()
      loadUserStats()
    } catch (err: any) {
      console.error('❌ 创建用户失败:', err)
      showError(extractErrorMessage(err, '创建用户失败'))
    }
  }

  /**
   * ✏️ 更新用户
   */
  const updateUser = async () => {
    if (!selectedUser) return
    
    try {
      const updateData = {
        email: formData.email,
        full_name: formData.full_name,
        role: formData.role,
        is_active: formData.is_active
      }
      
      await UserManagementService.updateUser(selectedUser.id, updateData)
      success('用户信息更新成功')
      setShowEditModal(false)
      resetForm()
      loadUsers()
      loadUserStats()
    } catch (err: any) {
      console.error('❌ 更新用户失败:', err)
      showError(extractErrorMessage(err, '更新用户失败'))
    }
  }

  /**
   * 🗑️ 删除用户
   */
  const deleteUser = async () => {
    if (!selectedUser) return
    
    try {
      await UserManagementService.deleteUser(selectedUser.id)
      success('用户删除成功')
      setShowDeleteModal(false)
      setSelectedUser(null)
      loadUsers()
      loadUserStats()
    } catch (err: any) {
      console.error('❌ 删除用户失败:', err)
      showError(extractErrorMessage(err, '删除用户失败'))
    }
  }

  /**
   * 🔑 重置用户密码
   */
  const resetPassword = async () => {
    if (!selectedUser || !newPassword) return
    
    try {
      await UserManagementService.resetUserPassword(selectedUser.id, newPassword)
      success('密码重置成功')
      setShowPasswordModal(false)
      setSelectedUser(null)
      setNewPassword('')
    } catch (err: any) {
      console.error('❌ 重置密码失败:', err)
      showError(extractErrorMessage(err, '重置密码失败'))
    }
  }

  /**
   * 🔄 切换用户状态
   */
  const toggleUserStatus = async (user: UserInfo) => {
    try {
      if (user.is_active) {
        await UserManagementService.deactivateUser(user.id)
        success('用户已停用')
      } else {
        await UserManagementService.activateUser(user.id)
        success('用户已激活')
      }
      loadUsers()
      loadUserStats()
    } catch (err: any) {
      console.error('❌ 切换用户状态失败:', err)
      showError(extractErrorMessage(err, '操作失败'))
    }
  }

  /**
   * 🔄 重置表单
   */
  const resetForm = () => {
    setFormData({
      username: '',
      email: '',
      password: '',
      full_name: '',
      role: 'viewer',
      is_active: true
    })
    setSelectedUser(null)
  }

  /**
   * 🎨 渲染用户统计卡片
   */
  const renderUserStats = () => {
    if (!userStats) return null

    const statsItems = [
      {
        label: '总用户数',
        value: userStats.total_users,
        color: 'from-blue-400 to-blue-600',
        icon: UsersIcon
      },
      {
        label: '活跃用户',
        value: userStats.active_users,
        color: 'from-green-400 to-green-600',
        icon: UserCircleIcon
      },
      {
        label: '管理员',
        value: userStats.admin_users,
        color: 'from-red-400 to-red-600',
        icon: ShieldCheckIcon
      },
      {
        label: '操作员',
        value: userStats.operator_users,
        color: 'from-purple-400 to-purple-600',
        icon: KeyIcon
      }
    ]

    return (
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        {statsItems.map((item, index) => {
          const Icon = item.icon
          return (
            <motion.div
              key={index}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.1 }}
            >
              <GlassCard className="text-center">
                <div className={`inline-flex p-3 rounded-xl bg-gradient-to-r ${item.color} mb-3`}>
                  <Icon className="w-6 h-6 text-white" />
                </div>
                <p className="text-2xl font-bold text-glass-text-primary mb-1">
                  {item.value}
                </p>
                <p className="text-sm text-glass-text-secondary">
                  {item.label}
                </p>
              </GlassCard>
            </motion.div>
          )
        })}
      </div>
    )
  }

  /**
   * 🎨 渲染搜索和筛选栏
   */
  const renderFilters = () => (
    <GlassCard className="mb-6">
      <div className="flex flex-col md:flex-row gap-4">
        <div className="flex-1">
          <GlassInput
            placeholder="搜索用户名或邮箱..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
        </div>
        
        <div className="flex gap-3">
          <GlassSelect
            value={roleFilter}
            onChange={(value) => setRoleFilter(String(value))}
            options={[
              { value: '', label: '所有角色' },
              ...USER_ROLES.map(role => ({ value: role.value, label: role.label }))
            ]}
            placeholder="筛选角色"
          />
          
          <GlassSelect
            value={statusFilter}
            onChange={(value) => setStatusFilter(String(value))}
            options={[
              { value: '', label: '所有状态' },
              { value: 'true', label: '已激活' },
              { value: 'false', label: '已停用' }
            ]}
            placeholder="筛选状态"
          />
          
          <GlassButton
            variant="primary"
            onClick={() => setShowCreateModal(true)}
          >
            <PlusIcon className="w-4 h-4 mr-2" />
            新建用户
          </GlassButton>
        </div>
      </div>
    </GlassCard>
  )

  /**
   * 🎨 渲染用户表格
   */
  const renderUserTable = () => {
    const columns = [
      {
        key: 'username',
        title: '用户名',
        render: (user: UserInfo) => (
          <div className="flex items-center space-x-3">
            <div className="w-8 h-8 bg-gradient-to-r from-blue-400 to-blue-600 rounded-full flex items-center justify-center">
              <span className="text-white text-sm font-medium">
                {user.username.charAt(0).toUpperCase()}
              </span>
            </div>
            <div>
              <p className="font-medium text-glass-text-primary">{user.username}</p>
              {user.full_name && (
                <p className="text-sm text-glass-text-secondary">{user.full_name}</p>
              )}
            </div>
          </div>
        )
      },
      {
        key: 'email',
        title: '邮箱',
        render: (user: UserInfo) => (
          <span className="text-glass-text-secondary">{user.email}</span>
        )
      },
      {
        key: 'role',
        title: '角色',
        render: (user: UserInfo) => {
          const role = USER_ROLES.find(r => r.value === user.role)
          return (
            <span className={`px-3 py-1 text-xs rounded-full bg-gradient-to-r ${role?.color || 'from-gray-400 to-gray-600'} text-white`}>
              {role?.label || user.role}
            </span>
          )
        }
      },
      {
        key: 'status',
        title: '状态',
        render: (user: UserInfo) => (
          <span className={`px-3 py-1 text-xs rounded-full ${
            user.is_active 
              ? 'bg-green-500/20 text-green-400' 
              : 'bg-red-500/20 text-red-400'
          }`}>
            {user.is_active ? '已激活' : '已停用'}
          </span>
        )
      },
      {
        key: 'last_login',
        title: '最后登录',
        render: (user: UserInfo) => (
          <span className="text-sm text-glass-text-secondary">
            {user.last_login 
              ? new Date(user.last_login).toLocaleString('zh-CN')
              : '从未登录'
            }
          </span>
        )
      },
      {
        key: 'actions',
        title: '操作',
        render: (user: UserInfo) => (
          <div className="flex items-center space-x-2">
            <GlassButton
              variant="secondary"
              size="sm"
              onClick={() => {
                setSelectedUser(user)
                setFormData({
                  username: user.username,
                  email: user.email,
                  password: '',
                  full_name: user.full_name || '',
                  role: user.role,
                  is_active: user.is_active
                })
                setShowEditModal(true)
              }}
            >
              <PencilIcon className="w-4 h-4" />
            </GlassButton>
            
            <GlassButton
              variant="secondary"
              size="sm"
              onClick={() => toggleUserStatus(user)}
            >
              {user.is_active ? (
                <EyeSlashIcon className="w-4 h-4" />
              ) : (
                <EyeIcon className="w-4 h-4" />
              )}
            </GlassButton>
            
            <GlassButton
              variant="secondary"
              size="sm"
              onClick={() => {
                setSelectedUser(user)
                setShowPasswordModal(true)
              }}
            >
              <KeyIcon className="w-4 h-4" />
            </GlassButton>
            
            <GlassButton
              variant="secondary"
              size="sm"
              onClick={() => {
                setSelectedUser(user)
                setShowDeleteModal(true)
              }}
              className="text-red-400 hover:text-red-300"
            >
              <TrashIcon className="w-4 h-4" />
            </GlassButton>
          </div>
        )
      }
    ]

    return (
      <GlassTable
        columns={columns}
        data={users}
        loading={loading}
        pagination={{
          current: currentPage,
          pageSize,
          total: totalUsers,
          onChange: setCurrentPage
        }}
      />
    )
  }

  return (
    <div className="space-y-6">
      {/* 用户统计 */}
      {renderUserStats()}
      
      {/* 搜索和筛选 */}
      {renderFilters()}
      
      {/* 用户表格 */}
      {renderUserTable()}
      
      {/* 创建用户模态框 */}
      <GlassModal
        isOpen={showCreateModal}
        onClose={() => {
          setShowCreateModal(false)
          resetForm()
        }}
        title="创建新用户"
      >
        <div className="space-y-4">
          <GlassInput
            label="用户名"
            value={formData.username}
            onChange={(e) => setFormData(prev => ({ ...prev, username: e.target.value }))}
            placeholder="请输入用户名"
            required
          />
          
          <GlassInput
            label="邮箱"
            type="email"
            value={formData.email}
            onChange={(e) => setFormData(prev => ({ ...prev, email: e.target.value }))}
            placeholder="请输入邮箱地址"
            required
          />
          
          <div className="relative">
            <GlassInput
              label="密码"
              type={showPassword ? 'text' : 'password'}
              value={formData.password}
              onChange={(e) => setFormData(prev => ({ ...prev, password: e.target.value }))}
              placeholder="请输入密码"
              required
            />
            <button
              type="button"
              className="absolute right-3 top-9 text-glass-text-secondary hover:text-glass-text-primary"
              onClick={() => setShowPassword(!showPassword)}
            >
              {showPassword ? (
                <EyeSlashIcon className="w-5 h-5" />
              ) : (
                <EyeIcon className="w-5 h-5" />
              )}
            </button>
          </div>
          
          <GlassInput
            label="真实姓名"
            value={formData.full_name}
            onChange={(e) => setFormData(prev => ({ ...prev, full_name: e.target.value }))}
            placeholder="请输入真实姓名（可选）"
          />
          
          <GlassSelect
            label="用户角色"
            value={formData.role}
            onChange={(value) => setFormData(prev => ({ ...prev, role: String(value) }))}
            options={USER_ROLES.map(role => ({ value: role.value, label: role.label }))}
          />
          
          <div className="flex justify-end space-x-3">
            <GlassButton
              variant="secondary"
              onClick={() => {
                setShowCreateModal(false)
                resetForm()
              }}
            >
              取消
            </GlassButton>
            <GlassButton
              variant="primary"
              onClick={createUser}
              disabled={!formData.username || !formData.email || !formData.password}
            >
              创建用户
            </GlassButton>
          </div>
        </div>
      </GlassModal>
      
      {/* 编辑用户模态框 */}
      <GlassModal
        isOpen={showEditModal}
        onClose={() => {
          setShowEditModal(false)
          resetForm()
        }}
        title="编辑用户信息"
      >
        <div className="space-y-4">
          <GlassInput
            label="用户名"
            value={formData.username}
            disabled
            className="opacity-50"
          />
          
          <GlassInput
            label="邮箱"
            type="email"
            value={formData.email}
            onChange={(e) => setFormData(prev => ({ ...prev, email: e.target.value }))}
            placeholder="请输入邮箱地址"
            required
          />
          
          <GlassInput
            label="真实姓名"
            value={formData.full_name}
            onChange={(e) => setFormData(prev => ({ ...prev, full_name: e.target.value }))}
            placeholder="请输入真实姓名（可选）"
          />
          
          <GlassSelect
            label="用户角色"
            value={formData.role}
            onChange={(value) => setFormData(prev => ({ ...prev, role: String(value) }))}
            options={USER_ROLES.map(role => ({ value: role.value, label: role.label }))}
          />
          
          <div className="flex items-center space-x-3">
            <input
              type="checkbox"
              id="is_active"
              checked={formData.is_active}
              onChange={(e) => setFormData(prev => ({ ...prev, is_active: e.target.checked }))}
              className="w-4 h-4 text-blue-600 bg-transparent border-2 border-white/30 rounded focus:ring-blue-500"
            />
            <label htmlFor="is_active" className="text-glass-text-primary">
              激活用户
            </label>
          </div>
          
          <div className="flex justify-end space-x-3">
            <GlassButton
              variant="secondary"
              onClick={() => {
                setShowEditModal(false)
                resetForm()
              }}
            >
              取消
            </GlassButton>
            <GlassButton
              variant="primary"
              onClick={updateUser}
            >
              保存更改
            </GlassButton>
          </div>
        </div>
      </GlassModal>
      
      {/* 删除用户确认模态框 */}
      <GlassModal
        isOpen={showDeleteModal}
        onClose={() => {
          setShowDeleteModal(false)
          setSelectedUser(null)
        }}
        title="确认删除用户"
      >
        <div className="space-y-4">
          <p className="text-glass-text-secondary">
            确定要删除用户 <span className="font-medium text-glass-text-primary">
              {selectedUser?.username}
            </span> 吗？此操作不可撤销。
          </p>
          
          <div className="flex justify-end space-x-3">
            <GlassButton
              variant="secondary"
              onClick={() => {
                setShowDeleteModal(false)
                setSelectedUser(null)
              }}
            >
              取消
            </GlassButton>
            <GlassButton
              variant="primary"
              onClick={deleteUser}
              className="bg-red-500/20 hover:bg-red-500/30 text-red-400"
            >
              确认删除
            </GlassButton>
          </div>
        </div>
      </GlassModal>
      
      {/* 重置密码模态框 */}
      <GlassModal
        isOpen={showPasswordModal}
        onClose={() => {
          setShowPasswordModal(false)
          setSelectedUser(null)
          setNewPassword('')
        }}
        title="重置用户密码"
      >
        <div className="space-y-4">
          <p className="text-glass-text-secondary">
            为用户 <span className="font-medium text-glass-text-primary">
              {selectedUser?.username}
            </span> 设置新密码：
          </p>
          
          <div className="relative">
            <GlassInput
              label="新密码"
              type={showPassword ? 'text' : 'password'}
              value={newPassword}
              onChange={(e) => setNewPassword(e.target.value)}
              placeholder="请输入新密码"
              required
            />
            <button
              type="button"
              className="absolute right-3 top-9 text-glass-text-secondary hover:text-glass-text-primary"
              onClick={() => setShowPassword(!showPassword)}
            >
              {showPassword ? (
                <EyeSlashIcon className="w-5 h-5" />
              ) : (
                <EyeIcon className="w-5 h-5" />
              )}
            </button>
          </div>
          
          <div className="flex justify-end space-x-3">
            <GlassButton
              variant="secondary"
              onClick={() => {
                setShowPasswordModal(false)
                setSelectedUser(null)
                setNewPassword('')
              }}
            >
              取消
            </GlassButton>
            <GlassButton
              variant="primary"
              onClick={resetPassword}
              disabled={!newPassword}
            >
              重置密码
            </GlassButton>
          </div>
        </div>
      </GlassModal>
    </div>
  )
}

export default UserManagementPanel
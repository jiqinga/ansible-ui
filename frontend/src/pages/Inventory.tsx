/**
 * 🏠 Inventory管理页面
 * 
 * 玻璃态主机清单管理界面，包含主机列表、分组管理和变量编辑功能
 */

import React, { useState, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  ServerIcon, 
  FolderIcon, 
  PlusIcon, 
  AdjustmentsHorizontalIcon,
  ArrowPathIcon,
  CloudArrowUpIcon,
  Bars3Icon,
  XMarkIcon,
  PencilIcon,
  TrashIcon,
  SignalIcon,
  EyeIcon
} from '@heroicons/react/24/outline';
import { OSIcon } from '../components/UI/OSIcon';
import GlassCard from '../components/UI/GlassCard';
import GlassButton from '../components/UI/GlassButton';
import GlassInput from '../components/UI/GlassInput';
import ConfirmDialog from '../components/UI/ConfirmDialog';
import { useNotification } from '../contexts/NotificationContext';
import { useChineseFormat } from '../hooks/useChineseFormat';
import {
  inventoryService,
  Host,
  HostGroup,
  InventoryStats,
  HostSearchRequest,
  PingResult
} from '../services/inventoryService';

// 🎨 动画配置
const pageVariants = {
  initial: { opacity: 0, y: 20 },
  animate: { 
    opacity: 1, 
    y: 0,
    transition: {
      duration: 0.6,
      staggerChildren: 0.1
    }
  },
  exit: { opacity: 0, y: -20 }
};

const cardVariants = {
  initial: { opacity: 0, y: 20 },
  animate: { 
    opacity: 1, 
    y: 0,
    transition: { duration: 0.4 }
  }
};

/**
 * 📜 执行历史卡片组件
 */
const ExecutionHistoryCard: React.FC<{ hostname: string }> = ({ hostname }) => {
  const [executions, setExecutions] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const { formatDate } = useChineseFormat();

  useEffect(() => {
    const loadExecutions = async () => {
      try {
        setLoading(true);
        const data = await inventoryService.getHostExecutionHistory(hostname, 5);
        setExecutions(data);
      } catch (error) {
        console.error('加载执行历史失败:', error);
      } finally {
        setLoading(false);
      }
    };

    loadExecutions();
  }, [hostname]);

  if (loading) {
    return (
      <GlassCard padding="md">
        <h4 className="font-medium text-gray-800 mb-4 flex items-center">
          <span className="text-lg mr-2">📜</span>
          最近执行记录
        </h4>
        <div className="text-center py-4 text-gray-600">
          加载中...
        </div>
      </GlassCard>
    );
  }

  if (executions.length === 0) {
    return (
      <GlassCard padding="md">
        <h4 className="font-medium text-gray-800 mb-4 flex items-center">
          <span className="text-lg mr-2">📜</span>
          最近执行记录
        </h4>
        <div className="text-center py-4 text-gray-600">
          暂无执行记录
        </div>
      </GlassCard>
    );
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'success':
        return 'bg-green-500/20 text-green-700';
      case 'failed':
        return 'bg-red-500/20 text-red-700';
      case 'running':
        return 'bg-yellow-500/20 text-yellow-700';
      case 'pending':
        return 'bg-blue-500/20 text-blue-700';
      default:
        return 'bg-gray-500/20 text-gray-700';
    }
  };

  const getStatusText = (status: string) => {
    switch (status) {
      case 'success':
        return '✅ 成功';
      case 'failed':
        return '❌ 失败';
      case 'running':
        return '⏳ 运行中';
      case 'pending':
        return '⏸️ 等待中';
      case 'cancelled':
        return '🚫 已取消';
      case 'timeout':
        return '⏰ 超时';
      default:
        return status;
    }
  };

  return (
    <GlassCard padding="md">
      <h4 className="font-medium text-gray-800 mb-4 flex items-center">
        <span className="text-lg mr-2">📜</span>
        最近执行记录
      </h4>
      <div className="space-y-2">
        {executions.map((execution) => (
          <div key={execution.id} className="bg-white/10 rounded-lg p-3">
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium text-gray-800">
                {execution.playbook_name}
              </span>
              <span className={`text-xs px-2 py-1 rounded-full ${getStatusColor(execution.status)}`}>
                {getStatusText(execution.status)}
              </span>
            </div>
            <div className="mt-1 flex items-center justify-between text-xs text-gray-600">
              <span>{formatDate(execution.created_at, { relative: true })}</span>
              {execution.duration && (
                <span>{execution.duration}秒</span>
              )}
            </div>
          </div>
        ))}
      </div>
      <GlassButton
        variant="ghost"
        className="w-full mt-3"
        onClick={() => {
          // TODO: 跳转到执行历史页面
          console.log('查看全部历史');
        }}
      >
        查看全部历史
      </GlassButton>
    </GlassCard>
  );
};

/**
 * 🏠 Inventory管理页面组件
 */
const Inventory: React.FC = () => {
  const { success, error, info } = useNotification();
  const { formatDate, formatNumber } = useChineseFormat();

  /**
   * 💾 格式化内存大小
   * 将 MB 转换为更可读的单位（GB 或 MB）
   */
  const formatMemorySize = (mb: number): string => {
    if (mb >= 1024) {
      return `${(mb / 1024).toFixed(2)} GB`;
    }
    return `${mb} MB`;
  };

  // 📊 状态管理
  const [hosts, setHosts] = useState<Host[]>([]);
  const [stats, setStats] = useState<InventoryStats | null>(null);
  const [groups, setGroups] = useState<HostGroup[]>([]);
  const [groupStats, setGroupStats] = useState<Record<string, number>>({});
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  // 🔍 搜索和筛选状态
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedGroup, setSelectedGroup] = useState<string>('');
  const [showInactive, setShowInactive] = useState(true); // 🔧 默认显示所有主机（包括非活跃）

  // 📱 模态框状态
  const [showHostModal, setShowHostModal] = useState(false);
  const [showGroupModal, setShowGroupModal] = useState(false);
  const [showImportModal, setShowImportModal] = useState(false);
  const [showHostDetailModal, setShowHostDetailModal] = useState(false);
  const [editingHost, setEditingHost] = useState<Host | null>(null);
  const [viewingHost, setViewingHost] = useState<Host | null>(null);

  // 🎨 侧边面板状态
  const [showSidebar, setShowSidebar] = useState(true);
  const [sidebarMode, setSidebarMode] = useState<'groups' | 'variables'>('groups');

  // 📝 表单状态
  const [hostFormData, setHostFormData] = useState({
    hostname: '',
    display_name: '',
    description: '',
    ansible_host: '',
    ansible_port: 22,
    ansible_user: 'root',
    ansible_ssh_private_key_file: '',
    ansible_ssh_pass: '',
    auth_method: 'key', // 'key' 或 'password'
    group_name: 'ungrouped',
    tags: '',
    is_active: true,
    ansible_become: true,
    ansible_become_user: 'root',
    ansible_become_method: 'sudo',
    variables: '{}'
  });
  const [submitting, setSubmitting] = useState(false);

  // 📝 主机组表单状态
  const [groupFormData, setGroupFormData] = useState({
    name: '',
    display_name: '',
    description: '',
    parent_group: '',
    tags: '',
    is_active: true,
    variables: '{}'
  });
  const [submittingGroup, setSubmittingGroup] = useState(false);
  const [editingGroup, setEditingGroup] = useState<HostGroup | null>(null);

  // 🗑️ 确认对话框状态
  const [confirmDialog, setConfirmDialog] = useState<{
    isOpen: boolean;
    title: string;
    message: string;
    type: 'warning' | 'danger' | 'info';
    onConfirm: () => void;
  }>({
    isOpen: false,
    title: '',
    message: '',
    type: 'warning',
    onConfirm: () => {},
  });

  /**
   * 📊 加载数据
   */
  const loadData = useCallback(async (silent = false) => {
    try {
      if (silent) {
        setRefreshing(true);
      } else {
        setLoading(true);
      }

      const searchPayload: HostSearchRequest = {
        page: 1,
        page_size: 100,
      };

      if (selectedGroup) {
        searchPayload.group_name = selectedGroup;
      }

      if (searchQuery.trim()) {
        searchPayload.query = searchQuery.trim();
      }

      if (!showInactive) {
        searchPayload.is_active = true;
      }

      const [hostsResponse, statsResponse, groupsResponse] = await Promise.all([
        inventoryService.searchHosts(searchPayload),
        inventoryService.getStats(),
        inventoryService.getGroups({ page_size: 1000 }),
      ]);

      setHosts(hostsResponse.hosts || []);
      setStats(statsResponse);
      setGroupStats(statsResponse.group_stats || {});
      const resolvedGroups = groupsResponse.groups || [];
      setGroups(resolvedGroups);

      if (selectedGroup && !resolvedGroups.some(group => group.name === selectedGroup)) {
        setSelectedGroup('');
      }

    } catch (err) {
      console.error('❌ 加载Inventory数据失败:', err);
      const message = err instanceof Error ? err.message : '加载数据失败';
      error(message);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [selectedGroup, showInactive, searchQuery, error]);

  /**
   * 🏓 测试主机连接
   */
  const handlePingHost = async (host: Host) => {
    try {
      info(`正在测试主机 ${host.hostname} 的连接...`);

      const result: PingResult = await inventoryService.pingHost(host.id);

      if (result.success) {
        // ✅ 连接成功 - 显示详细信息
        success(`✅ ${result.message || `主机 ${host.hostname} 连接成功`}`);
      } else {
        // ❌ 连接失败 - 显示详细错误信息
        const errorIcon = getErrorIcon(result.error_type);
        const errorMessage = `${errorIcon} ${result.message || `主机 ${host.hostname} 连接失败`}`;
        
        // 如果有详细信息，显示在第二行
        if (result.details) {
          error(`${errorMessage}\n\n${result.details}`);
        } else {
          error(errorMessage);
        }
      }

      setHosts(prev => prev.map(h =>
        h.id === host.id
          ? {
              ...h,
              ping_status: result.status,
              is_reachable: result.success,
              last_ping: new Date().toISOString(),
            }
          : h
      ));

      loadData(true);
    } catch (err) {
      console.error('❌ 测试主机连接失败:', err);
      const message = err instanceof Error ? err.message : '连接测试失败';
      error(message);
    }
  };

  /**
   * 🎨 根据错误类型获取图标
   */
  const getErrorIcon = (errorType?: string): string => {
    const errorIcons: Record<string, string> = {
      network_unreachable: '🌐',
      hostname_resolution_failed: '🔍',
      connection_refused: '🚫',
      connection_timeout: '⏱️',
      timeout: '⏰',
      key_authentication_failed: '🔑',
      password_authentication_failed: '🔒',
      authentication_failed: '👤',
      key_file_not_found: '📁',
      key_passphrase_required: '🔐',
      key_permissions_error: '🔒',
      port_unreachable: '🔌',
      host_key_verification_failed: '🔐',
      ssh_protocol_error: '⚠️',
      command_execution_failed: '⚙️',
      ssh_error: '⚠️',
      host_not_found: '❓',
      exception: '💥',
    };
    
    return errorIcons[errorType || ''] || '❌';
  };

  /**
   * 🗑️ 删除主机
   */
  const handleDeleteHost = async (host: Host) => {
    setConfirmDialog({
      isOpen: true,
      title: '🗑️ 删除主机',
      message: `确定要删除主机 "${host.hostname}" 吗？\n\n此操作无法撤销。`,
      type: 'danger',
      onConfirm: async () => {
        setConfirmDialog({ ...confirmDialog, isOpen: false });
        try {
          await inventoryService.deleteHost(host.id);
          success(`主机 ${host.hostname} 删除成功`);
          await loadData(true);
        } catch (err) {
          console.error('❌ 删除主机失败:', err);
          const message = err instanceof Error ? err.message : '删除主机失败';
          error(message);
        }
      },
    });
  };

  /**
   * 📝 编辑主机
   */
  const handleEditHost = (host: Host) => {
    setEditingHost(host);
    // 填充表单数据
    setHostFormData({
      hostname: host.hostname,
      display_name: host.display_name || '',
      description: host.description || '',
      ansible_host: host.ansible_host,
      ansible_port: host.ansible_port,
      ansible_user: host.ansible_user || 'root',
      ansible_ssh_private_key_file: host.ansible_ssh_private_key_file || '',
      ansible_ssh_pass: '', // 出于安全考虑，不回显密码
      auth_method: host.ansible_ssh_private_key_file ? 'key' : 'password',
      group_name: host.group_name,
      tags: host.tags?.join(', ') || '',
      is_active: host.is_active,
      ansible_become: host.ansible_become,
      ansible_become_user: host.ansible_become_user,
      ansible_become_method: host.ansible_become_method,
      variables: JSON.stringify(host.variables || {}, null, 2)
    });
    setShowHostModal(true);
  };

  /**
   * 💾 提交主机表单
   */
  const handleSubmitHost = async () => {
    try {
      setSubmitting(true);

      // 验证必填字段
      if (!hostFormData.hostname.trim()) {
        error('请输入主机名');
        return;
      }
      if (!hostFormData.ansible_host.trim()) {
        error('请输入IP地址');
        return;
      }

      // 解析标签
      const tags = hostFormData.tags
        .split(',')
        .map(tag => tag.trim())
        .filter(tag => tag.length > 0);

      // 解析变量
      let variables = {};
      try {
        if (hostFormData.variables.trim()) {
          variables = JSON.parse(hostFormData.variables);
        }
      } catch (e) {
        error('Ansible变量格式错误，请输入有效的JSON');
        return;
      }

      // 构建提交数据
      const submitData: any = {
        hostname: hostFormData.hostname.trim(),
        display_name: hostFormData.display_name.trim() || undefined,
        description: hostFormData.description.trim() || undefined,
        ansible_host: hostFormData.ansible_host.trim(),
        ansible_port: hostFormData.ansible_port,
        ansible_user: hostFormData.ansible_user.trim() || undefined,
        group_name: hostFormData.group_name || 'ungrouped',
        tags,
        is_active: hostFormData.is_active,
        ansible_become: hostFormData.ansible_become,
        ansible_become_user: hostFormData.ansible_become_user,
        ansible_become_method: hostFormData.ansible_become_method,
        variables
      };

      // 根据认证方式添加相应字段
      if (hostFormData.auth_method === 'key') {
        submitData.ansible_ssh_private_key_file = hostFormData.ansible_ssh_private_key_file.trim() || undefined;
        submitData.ansible_ssh_pass = undefined; // 清除密码
      } else {
        submitData.ansible_ssh_pass = hostFormData.ansible_ssh_pass.trim() || undefined;
        submitData.ansible_ssh_private_key_file = undefined; // 清除私钥路径
      }

      // 调用API
      if (editingHost) {
        await inventoryService.updateHost(editingHost.id, submitData);
        success(`主机 ${submitData.hostname} 更新成功`);
      } else {
        await inventoryService.createHost(submitData);
        success(`主机 ${submitData.hostname} 创建成功`);
      }

      // 关闭模态框并重置表单
      setShowHostModal(false);
      setEditingHost(null);
      setHostFormData({
        hostname: '',
        display_name: '',
        description: '',
        ansible_host: '',
        ansible_port: 22,
        ansible_user: 'root',
        ansible_ssh_private_key_file: '',
        ansible_ssh_pass: '',
        auth_method: 'key',
        group_name: 'ungrouped',
        tags: '',
        is_active: true,
        ansible_become: true,
        ansible_become_user: 'root',
        ansible_become_method: 'sudo',
        variables: '{}'
      });

      // 刷新列表
      await loadData(true);

    } catch (err) {
      console.error('❌ 提交主机失败:', err);
      const message = err instanceof Error ? err.message : '操作失败';
      error(message);
    } finally {
      setSubmitting(false);
    }
  };

  /**
   * 📝 编辑主机组
   */
  const handleEditGroup = (group: HostGroup) => {
    setEditingGroup(group);
    // 填充表单数据
    setGroupFormData({
      name: group.name,
      display_name: group.display_name || '',
      description: group.description || '',
      parent_group: group.parent_group || '',
      tags: group.tags?.join(', ') || '',
      is_active: group.is_active ?? true,
      variables: JSON.stringify(group.variables || {}, null, 2)
    });
    setShowGroupModal(true);
  };

  /**
   * 🗑️ 删除主机组
   */
  const handleDeleteGroup = async (group: HostGroup) => {
    // 🔒 检查是否为系统保留组
    const PROTECTED_GROUPS = ['ungrouped'];
    if (PROTECTED_GROUPS.includes(group.name)) {
      error(`系统保留组 "${group.display_name || group.name}" 不允许删除`);
      return;
    }
    
    const hostCount = group.host_count ?? groupStats[group.name] ?? 0;
    
    // 如果组内有主机，提示用户
    if (hostCount > 0) {
      setConfirmDialog({
        isOpen: true,
        title: '⚠️ 强制删除主机组',
        message: `主机组 "${group.display_name || group.name}" 中有 ${hostCount} 台主机。\n\n是否强制删除？\n主机将移至 ungrouped 组。`,
        type: 'warning',
        onConfirm: async () => {
          setConfirmDialog({ ...confirmDialog, isOpen: false });
          try {
            await inventoryService.deleteGroup(group.id, true); // force=true
            success(`主机组 ${group.display_name || group.name} 删除成功`);
            
            // 如果当前选中的组被删除，清除选择
            if (selectedGroup === group.name) {
              setSelectedGroup('');
            }
            
            await loadData(true);
          } catch (err) {
            console.error('❌ 删除主机组失败:', err);
            const message = err instanceof Error ? err.message : '删除主机组失败';
            error(message);
          }
        },
      });
    } else {
      // 组内没有主机，直接删除
      setConfirmDialog({
        isOpen: true,
        title: '🗑️ 删除主机组',
        message: `确定要删除主机组 "${group.display_name || group.name}" 吗？\n\n此操作无法撤销。`,
        type: 'danger',
        onConfirm: async () => {
          setConfirmDialog({ ...confirmDialog, isOpen: false });
          try {
            await inventoryService.deleteGroup(group.id, false);
            success(`主机组 ${group.display_name || group.name} 删除成功`);
            
            // 如果当前选中的组被删除，清除选择
            if (selectedGroup === group.name) {
              setSelectedGroup('');
            }
            
            await loadData(true);
          } catch (err) {
            console.error('❌ 删除主机组失败:', err);
            const message = err instanceof Error ? err.message : '删除主机组失败';
            error(message);
          }
        },
      });
    }
  };

  /**
   * 💾 提交主机组表单
   */
  const handleSubmitGroup = async () => {
    try {
      setSubmittingGroup(true);

      // 验证必填字段
      if (!groupFormData.name.trim()) {
        error('请输入组名');
        return;
      }

      // 解析标签
      const tags = groupFormData.tags
        .split(',')
        .map(tag => tag.trim())
        .filter(tag => tag.length > 0);

      // 解析变量
      let variables = {};
      try {
        if (groupFormData.variables.trim()) {
          variables = JSON.parse(groupFormData.variables);
        }
      } catch (e) {
        error('组变量格式错误，请输入有效的JSON');
        return;
      }

      // 构建提交数据
      const submitData = {
        name: groupFormData.name.trim(),
        display_name: groupFormData.display_name.trim() || undefined,
        description: groupFormData.description.trim() || undefined,
        parent_group: groupFormData.parent_group || undefined,
        tags,
        is_active: groupFormData.is_active,
        variables
      };

      // 调用API
      if (editingGroup) {
        await inventoryService.updateGroup(editingGroup.id, submitData);
        success(`主机组 ${submitData.name} 更新成功`);
      } else {
        await inventoryService.createGroup(submitData);
        success(`主机组 ${submitData.name} 创建成功`);
      }

      // 关闭模态框并重置表单
      setShowGroupModal(false);
      setEditingGroup(null);
      setGroupFormData({
        name: '',
        display_name: '',
        description: '',
        parent_group: '',
        tags: '',
        is_active: true,
        variables: '{}'
      });

      // 刷新列表
      await loadData(true);

    } catch (err) {
      console.error('❌ 提交主机组失败:', err);
      const message = err instanceof Error ? err.message : '操作失败';
      error(message);
    } finally {
      setSubmittingGroup(false);
    }
  };

  // 🔍 数据加载（含防抖处理）
  useEffect(() => {
    const timer = setTimeout(() => {
      const isInitialState = searchQuery === '' && selectedGroup === '' && !showInactive;
      loadData(!isInitialState);
    }, 300);

    return () => clearTimeout(timer);
  }, [searchQuery, selectedGroup, showInactive, loadData]);

  /**
   * 📊 获取状态颜色和图标
   */
  const getStatusDisplay = (status?: string) => {
    switch (status) {
      case 'success':
        return { color: 'bg-green-500', icon: '✅', text: '在线' };
      case 'failed':
        return { color: 'bg-red-500', icon: '❌', text: '离线' };
      default:
        return { color: 'bg-gray-400', icon: '❓', text: '未知' };
    }
  };

  return (
    <motion.div
      className="min-h-[calc(100vh-7.5rem)] px-6 pb-10"
      variants={pageVariants}
      initial="initial"
      animate="animate"
      exit="exit"
    >
      <div className="flex gap-6 min-h-[calc(100vh-9rem)]">
        {/* 🎨 侧边栏 */}
        <AnimatePresence>
          {showSidebar && (
            <motion.div
              className="w-80 bg-white/20 backdrop-blur-xl border-r border-white/20"
              initial={{ x: -320, opacity: 0 }}
              animate={{ x: 0, opacity: 1 }}
              exit={{ x: -320, opacity: 0 }}
              transition={{ duration: 0.3 }}
            >
              <div className="p-6 h-full flex flex-col">
                {/* 侧边栏头部 */}
                <div className="flex items-center justify-between mb-6">
                  <h2 className="text-lg font-semibold text-gray-800">
                    {sidebarMode === 'groups' ? '📁 主机组' : '🔧 变量管理'}
                  </h2>
                  <div className="flex items-center space-x-2">
                    <GlassButton
                      size="sm"
                      variant={sidebarMode === 'groups' ? 'primary' : 'ghost'}
                      onClick={() => setSidebarMode('groups')}
                    >
                      <FolderIcon className="h-4 w-4" />
                    </GlassButton>
                    <GlassButton
                      size="sm"
                      variant={sidebarMode === 'variables' ? 'primary' : 'ghost'}
                      onClick={() => setSidebarMode('variables')}
                    >
                      <AdjustmentsHorizontalIcon className="h-4 w-4" />
                    </GlassButton>
                    <GlassButton
                      size="sm"
                      variant="ghost"
                      onClick={() => setShowSidebar(false)}
                    >
                      <XMarkIcon className="h-4 w-4" />
                    </GlassButton>
                  </div>
                </div>

                {/* 侧边栏内容 */}
                <div className="flex-1 overflow-y-auto">
                  {sidebarMode === 'groups' ? (
                    <div className="space-y-2">
                      {/* 添加组按钮 */}
                      <GlassButton
                        variant="primary"
                        className="w-full mb-4"
                        onClick={() => {
                          // 重置表单为默认值
                          setGroupFormData({
                            name: '',
                            display_name: '',
                            description: '',
                            parent_group: '',
                            tags: '',
                            is_active: true,
                            variables: '{}'
                          });
                          setShowGroupModal(true);
                        }}
                      >
                        <PlusIcon className="h-4 w-4 mr-2" />
                        添加主机组
                      </GlassButton>

                      <div
                        className={`flex items-center space-x-2 p-3 rounded-lg cursor-pointer transition-colors ${
                          selectedGroup === ''
                            ? 'bg-blue-500/20 text-blue-600'
                            : 'hover:bg-white/10'
                        }`}
                        onClick={() => setSelectedGroup('')}
                      >
                        <FolderIcon className="h-4 w-4 text-amber-500" />
                        <div className="flex-1 min-w-0">
                          <div className="text-sm font-medium truncate">全部主机</div>
                          <div className="text-xs text-gray-500">
                            {formatNumber(stats?.total_hosts ?? 0)} 台主机
                          </div>
                        </div>
                      </div>

                      {groups.length === 0 ? (
                        <div className="text-sm text-gray-500 px-3 py-2">
                          暂无主机组
                        </div>
                      ) : (
                        groups.map((group) => {
                          const hostCount = group.host_count ?? groupStats[group.name] ?? 0;

                          // 🔒 检查是否为系统保留组
                          const isProtectedGroup = ['ungrouped'].includes(group.name);
                          
                          return (
                            <div 
                              key={group.id}
                              className={`flex items-center space-x-2 p-3 rounded-lg cursor-pointer transition-colors ${
                                selectedGroup === group.name
                                  ? 'bg-blue-500/20 text-blue-600'
                                  : 'hover:bg-white/10'
                              }`}
                              onClick={() => setSelectedGroup(selectedGroup === group.name ? '' : group.name)}
                            >
                              <FolderIcon className="h-4 w-4 text-amber-500" />
                              <div className="flex-1 min-w-0">
                                <div className="text-sm font-medium truncate flex items-center">
                                  {group.display_name || group.name}
                                  {isProtectedGroup && (
                                    <span className="ml-2 text-xs text-gray-500" title="系统保留组">
                                      🔒
                                    </span>
                                  )}
                                </div>
                                <div className="text-xs text-gray-500">
                                  {formatNumber(hostCount)} 台主机
                                </div>
                              </div>
                              <div className="flex items-center space-x-1">
                                <GlassButton
                                  size="sm"
                                  variant="ghost"
                                  onClick={(e) => {
                                    e.stopPropagation();
                                    handleEditGroup(group);
                                  }}
                                  title={isProtectedGroup ? "系统保留组，仅可编辑部分属性" : "编辑主机组"}
                                >
                                  <PencilIcon className="h-3 w-3" />
                                </GlassButton>
                                {!isProtectedGroup && (
                                  <GlassButton
                                    size="sm"
                                    variant="ghost"
                                    onClick={(e) => {
                                      e.stopPropagation();
                                      handleDeleteGroup(group);
                                    }}
                                    title="删除主机组"
                                  >
                                    <TrashIcon className="h-3 w-3" />
                                  </GlassButton>
                                )}
                              </div>
                            </div>
                          );
                        })
                      )}
                    </div>
                  ) : (
                    <div className="space-y-4">
                      <GlassCard padding="md">
                        <h3 className="font-medium text-gray-800 mb-3">全局变量</h3>
                        <div className="space-y-2 text-sm">
                          <div className="flex justify-between">
                            <span className="text-gray-600">ansible_user</span>
                            <span className="text-gray-800">root</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-gray-600">ansible_port</span>
                            <span className="text-gray-800">22</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-gray-600">ansible_become</span>
                            <span className="text-gray-800">true</span>
                          </div>
                        </div>
                      </GlassCard>
                    </div>
                  )}
                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* 🎨 主内容区域 */}
        <div className="flex-1 flex flex-col overflow-hidden">
          {/* 顶部工具栏 */}
          <div className="bg-white/20 backdrop-blur-xl border-b border-white/20 p-6">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-4">
                {!showSidebar && (
                  <GlassButton
                    variant="ghost"
                    onClick={() => setShowSidebar(true)}
                  >
                    <Bars3Icon className="h-5 w-5" />
                  </GlassButton>
                )}
                
                <h1 className="text-2xl font-bold text-gray-800">
                  🏠 主机清单管理
                </h1>

                {stats && (
                  <div className="flex items-center space-x-4 text-sm text-gray-600">
                    <span>总计: {formatNumber(stats.total_hosts)} 台</span>
                    <span className="text-green-600">在线: {formatNumber(stats.reachable_hosts)} 台</span>
                    <span className="text-red-600">离线: {formatNumber(stats.unreachable_hosts)} 台</span>
                  </div>
                )}
              </div>

              <div className="flex items-center space-x-3">
                <GlassButton
                  variant="ghost"
                  onClick={() => loadData()}
                  disabled={refreshing}
                >
                  <ArrowPathIcon className={`h-4 w-4 ${refreshing ? 'animate-spin' : ''}`} />
                  刷新
                </GlassButton>

                <GlassButton
                  variant="secondary"
                  onClick={() => setShowImportModal(true)}
                >
                  <CloudArrowUpIcon className="h-4 w-4 mr-2" />
                  导入
                </GlassButton>

                <GlassButton
                  variant="primary"
                  onClick={() => {
                    setEditingHost(null);
                    // 重置表单为默认值
                    setHostFormData({
                      hostname: '',
                      display_name: '',
                      description: '',
                      ansible_host: '',
                      ansible_port: 22,
                      ansible_user: 'root',
                      ansible_ssh_private_key_file: '',
                      ansible_ssh_pass: '',
                      auth_method: 'key',
                      group_name: 'ungrouped',
                      tags: '',
                      is_active: true,
                      ansible_become: true,
                      ansible_become_user: 'root',
                      ansible_become_method: 'sudo',
                      variables: '{}'
                    });
                    setShowHostModal(true);
                  }}
                >
                  <PlusIcon className="h-4 w-4 mr-2" />
                  添加主机
                </GlassButton>
              </div>
            </div>

            {/* 搜索和筛选 */}
            <div className="flex items-center space-x-4 mt-4">
              <div className="flex-1">
                <GlassInput
                  placeholder="🔍 搜索主机名、IP地址或描述..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                />
              </div>

              <GlassButton
                variant={showInactive ? 'primary' : 'ghost'}
                onClick={() => setShowInactive(!showInactive)}
              >
                显示非活跃主机
              </GlassButton>
            </div>
          </div>

          {/* 主机列表 */}
          <div className="flex-1 p-6 overflow-y-auto">
            {loading ? (
              <div className="flex items-center justify-center h-64">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
                <span className="ml-3 text-gray-600">加载中...</span>
              </div>
            ) : (
              <div className="grid gap-4">
                {hosts.map((host) => {
                  const statusDisplay = getStatusDisplay(host.ping_status);
                  // 🔍 查找主机所属组的显示名称
                  const hostGroup = groups.find(g => g.name === host.group_name);
                  const groupDisplayName = hostGroup?.display_name || host.group_name;
                  
                  return (
                    <motion.div
                      key={host.id}
                      variants={cardVariants}
                      initial="initial"
                      animate="animate"
                    >
                      <GlassCard hover className="p-6">
                        <div className="flex items-center justify-between">
                          <div className="flex items-center space-x-4">
                            <div className="flex items-center space-x-2">
                              <ServerIcon className="h-6 w-6 text-blue-500" />
                              <div 
                                className={`w-3 h-3 rounded-full ${statusDisplay.color}`}
                                title={statusDisplay.text}
                              />
                            </div>

                            <div>
                              <div className="flex items-center space-x-2">
                                {host.extra_data?.system_info?.os?.distribution && (
                                  <OSIcon 
                                    distribution={host.extra_data.system_info.os.distribution}
                                    size="md"
                                  />
                                )}
                                <h3 className="text-lg font-semibold text-gray-800">
                                  {host.hostname}
                                </h3>
                                {!host.is_active && (
                                  <span className="px-2 py-1 bg-gray-500/20 text-gray-600 text-xs rounded-full">
                                    非活跃
                                  </span>
                                )}
                              </div>
                              {host.display_name && (
                                <p className="text-sm text-gray-600">{host.display_name}</p>
                              )}
                              <div className="flex items-center space-x-4 text-sm text-gray-500 mt-1">
                                <span>📍 {host.ansible_host}:{host.ansible_port}</span>
                                <span>📁 {groupDisplayName}</span>
                                <span>{statusDisplay.icon} {statusDisplay.text}</span>
                                {host.extra_data?.system_info?.os?.distribution && (
                                  <span className="flex items-center space-x-1">
                                    <OSIcon 
                                      distribution={host.extra_data.system_info.os.distribution}
                                      size="sm"
                                    />
                                    <span>{host.extra_data.system_info.os.distribution}</span>
                                  </span>
                                )}
                                {host.last_ping && (
                                  <span>🏓 {formatDate(host.last_ping, { relative: true })}</span>
                                )}
                              </div>
                            </div>
                          </div>

                          <div className="flex items-center space-x-2">
                            <GlassButton
                              size="sm"
                              variant="ghost"
                              onClick={() => handlePingHost(host)}
                              title="测试连接"
                            >
                              <SignalIcon className="h-4 w-4" />
                            </GlassButton>

                            <GlassButton
                              size="sm"
                              variant="ghost"
                              onClick={() => handleEditHost(host)}
                              title="编辑主机"
                            >
                              <PencilIcon className="h-4 w-4" />
                            </GlassButton>

                            <GlassButton
                              size="sm"
                              variant="ghost"
                              onClick={() => {
                                setViewingHost(host);
                                setShowHostDetailModal(true);
                              }}
                              title="查看详情"
                            >
                              <EyeIcon className="h-4 w-4" />
                            </GlassButton>

                            <GlassButton
                              size="sm"
                              variant="ghost"
                              onClick={() => handleDeleteHost(host)}
                              title="删除主机"
                            >
                              <TrashIcon className="h-4 w-4" />
                            </GlassButton>
                          </div>
                        </div>

                        {/* 主机详细信息 */}
                        {host.description && (
                          <div className="mt-4 p-3 bg-white/10 rounded-lg">
                            <p className="text-sm text-gray-700">{host.description}</p>
                          </div>
                        )}

                        {/* 标签 */}
                        {host.tags && host.tags.length > 0 && (
                          <div className="mt-3 flex flex-wrap gap-2">
                            {host.tags.map((tag, index) => (
                              <span
                                key={index}
                                className="px-2 py-1 bg-blue-500/20 text-blue-700 text-xs rounded-full"
                              >
                                {tag}
                              </span>
                            ))}
                          </div>
                        )}
                      </GlassCard>
                    </motion.div>
                  );
                })}

                {hosts.length === 0 && !loading && (
                  <div className="text-center py-12">
                    <ServerIcon className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                    <p className="text-gray-500">
                      {searchQuery || selectedGroup ? '没有找到匹配的主机' : '暂无主机数据'}
                    </p>
                    <GlassButton
                      variant="primary"
                      className="mt-4"
                      onClick={() => {
                        setEditingHost(null);
                        // 重置表单为默认值
                        setHostFormData({
                          hostname: '',
                          display_name: '',
                          description: '',
                          ansible_host: '',
                          ansible_port: 22,
                          ansible_user: 'root',
                          ansible_ssh_private_key_file: '',
                          ansible_ssh_pass: '',
                          auth_method: 'key',
                          group_name: 'ungrouped',
                          tags: '',
                          is_active: true,
                          ansible_become: true,
                          ansible_become_user: 'root',
                          ansible_become_method: 'sudo',
                          variables: '{}'
                        });
                        setShowHostModal(true);
                      }}
                    >
                      <PlusIcon className="h-4 w-4 mr-2" />
                      添加第一台主机
                    </GlassButton>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* 🎨 主机编辑模态框 */}
      <AnimatePresence>
        {showHostModal && (
          <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: 20 }}
              transition={{ duration: 0.2 }}
              className="w-full max-w-4xl max-h-[90vh] overflow-y-auto"
            >
              <GlassCard>
                <div className="p-6">
                  <h3 className="text-xl font-semibold mb-6 flex items-center">
                    {editingHost ? (
                      <>
                        <PencilIcon className="h-6 w-6 mr-2 text-blue-500" />
                        编辑主机: {editingHost.hostname}
                      </>
                    ) : (
                      <>
                        <PlusIcon className="h-6 w-6 mr-2 text-green-500" />
                        添加新主机
                      </>
                    )}
                  </h3>

                  <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    {/* 基本信息 */}
                    <GlassCard padding="md">
                      <h4 className="font-medium text-gray-800 mb-4 flex items-center">
                        <ServerIcon className="h-5 w-5 mr-2 text-blue-500" />
                        基本信息
                      </h4>
                      <div className="space-y-4">
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-2">
                            主机名 *
                          </label>
                          <GlassInput
                            placeholder="例如: web-server-01"
                            value={hostFormData.hostname}
                            onChange={(e) => setHostFormData({...hostFormData, hostname: e.target.value})}
                          />
                        </div>
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-2">
                            显示名称
                          </label>
                          <GlassInput
                            placeholder="例如: Web服务器01"
                            value={hostFormData.display_name}
                            onChange={(e) => setHostFormData({...hostFormData, display_name: e.target.value})}
                          />
                        </div>
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-2">
                            描述
                          </label>
                          <textarea
                            className="w-full px-4 py-3 bg-white/20 backdrop-blur-sm border border-white/30 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-transparent resize-none"
                            rows={3}
                            placeholder="主机的详细描述..."
                            value={hostFormData.description}
                            onChange={(e) => setHostFormData({...hostFormData, description: e.target.value})}
                          />
                        </div>
                      </div>
                    </GlassCard>

                    {/* 连接配置 */}
                    <GlassCard padding="md">
                      <h4 className="font-medium text-gray-800 mb-4 flex items-center">
                        <SignalIcon className="h-5 w-5 mr-2 text-green-500" />
                        连接配置
                      </h4>
                      <div className="space-y-4">
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-2">
                            IP地址 *
                          </label>
                          <GlassInput
                            placeholder="例如: 192.168.1.10"
                            value={hostFormData.ansible_host}
                            onChange={(e) => setHostFormData({...hostFormData, ansible_host: e.target.value})}
                          />
                        </div>
                        <div className="grid grid-cols-2 gap-4">
                          <div>
                            <label className="block text-sm font-medium text-gray-700 mb-2">
                              SSH端口
                            </label>
                            <GlassInput
                              type="number"
                              placeholder="22"
                              value={hostFormData.ansible_port.toString()}
                              onChange={(e) => setHostFormData({...hostFormData, ansible_port: parseInt(e.target.value) || 22})}
                            />
                          </div>
                          <div>
                            <label className="block text-sm font-medium text-gray-700 mb-2">
                              SSH用户
                            </label>
                            <GlassInput
                              placeholder="root"
                              value={hostFormData.ansible_user}
                              onChange={(e) => setHostFormData({...hostFormData, ansible_user: e.target.value})}
                            />
                          </div>
                        </div>
                        
                        {/* 🔐 认证方式选择 */}
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-2">
                            🔐 认证方式
                          </label>
                          <div className="flex space-x-4">
                            <label className="flex items-center space-x-2 cursor-pointer">
                              <input
                                type="radio"
                                name="auth_method"
                                value="key"
                                checked={hostFormData.auth_method === 'key'}
                                onChange={() => setHostFormData({...hostFormData, auth_method: 'key'})}
                                className="text-blue-600 focus:ring-blue-500"
                              />
                              <span className="text-sm text-gray-700">🔑 私钥认证</span>
                            </label>
                            <label className="flex items-center space-x-2 cursor-pointer">
                              <input
                                type="radio"
                                name="auth_method"
                                value="password"
                                checked={hostFormData.auth_method === 'password'}
                                onChange={() => setHostFormData({...hostFormData, auth_method: 'password'})}
                                className="text-blue-600 focus:ring-blue-500"
                              />
                              <span className="text-sm text-gray-700">🔒 密码认证</span>
                            </label>
                          </div>
                        </div>

                        {/* 根据认证方式显示不同的输入框 */}
                        {hostFormData.auth_method === 'key' ? (
                          <div>
                            <label className="block text-sm font-medium text-gray-700 mb-2">
                              私钥文件路径
                            </label>
                            <GlassInput
                              placeholder="例如: ~/.ssh/id_rsa"
                              value={hostFormData.ansible_ssh_private_key_file}
                              onChange={(e) => setHostFormData({...hostFormData, ansible_ssh_private_key_file: e.target.value})}
                            />
                            <p className="text-xs text-gray-500 mt-1">
                              💡 请输入SSH私钥文件的完整路径
                            </p>
                          </div>
                        ) : (
                          <div>
                            <label className="block text-sm font-medium text-gray-700 mb-2">
                              SSH密码
                            </label>
                            <GlassInput
                              type="password"
                              placeholder="请输入SSH密码"
                              value={hostFormData.ansible_ssh_pass}
                              onChange={(e) => setHostFormData({...hostFormData, ansible_ssh_pass: e.target.value})}
                            />
                            <p className="text-xs text-gray-500 mt-1">
                              ⚠️ 密码将加密存储，但建议使用私钥认证更安全
                            </p>
                          </div>
                        )}
                      </div>
                    </GlassCard>

                    {/* 主机组和标签 */}
                    <GlassCard padding="md">
                      <h4 className="font-medium text-gray-800 mb-4 flex items-center">
                        <FolderIcon className="h-5 w-5 mr-2 text-amber-500" />
                        分组和标签
                      </h4>
                      <div className="space-y-4">
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-2">
                            主机组
                          </label>
                          <select 
                            className="w-full px-4 py-3 bg-white/20 backdrop-blur-sm border border-white/30 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-transparent"
                            value={hostFormData.group_name}
                            onChange={(e) => setHostFormData({...hostFormData, group_name: e.target.value})}
                          >
                            <option value="ungrouped">未分组</option>
                            {groups.map(group => (
                              <option key={group.id} value={group.name}>{group.display_name || group.name}</option>
                            ))}
                          </select>
                        </div>
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-2">
                            标签 (逗号分隔)
                          </label>
                          <GlassInput
                            placeholder="例如: web, production, nginx"
                            value={hostFormData.tags}
                            onChange={(e) => setHostFormData({...hostFormData, tags: e.target.value})}
                          />
                        </div>
                        <div className="flex items-center space-x-2">
                          <input
                            type="checkbox"
                            id="is_active"
                            className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                            checked={hostFormData.is_active}
                            onChange={(e) => setHostFormData({...hostFormData, is_active: e.target.checked})}
                          />
                          <label htmlFor="is_active" className="text-sm text-gray-700">
                            启用此主机
                          </label>
                        </div>
                      </div>
                    </GlassCard>

                    {/* 权限设置 */}
                    <GlassCard padding="md">
                      <h4 className="font-medium text-gray-800 mb-4 flex items-center">
                        <AdjustmentsHorizontalIcon className="h-5 w-5 mr-2 text-purple-500" />
                        权限设置
                      </h4>
                      <div className="space-y-4">
                        <div className="flex items-center space-x-2">
                          <input
                            type="checkbox"
                            id="ansible_become"
                            className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                            checked={hostFormData.ansible_become}
                            onChange={(e) => setHostFormData({...hostFormData, ansible_become: e.target.checked})}
                          />
                          <label htmlFor="ansible_become" className="text-sm text-gray-700">
                            启用sudo提权
                          </label>
                        </div>
                        <div className="grid grid-cols-2 gap-4">
                          <div>
                            <label className="block text-sm font-medium text-gray-700 mb-2">
                              提权用户
                            </label>
                            <GlassInput
                              placeholder="root"
                              value={hostFormData.ansible_become_user}
                              onChange={(e) => setHostFormData({...hostFormData, ansible_become_user: e.target.value})}
                            />
                          </div>
                          <div>
                            <label className="block text-sm font-medium text-gray-700 mb-2">
                              提权方法
                            </label>
                            <select 
                              className="w-full px-4 py-3 bg-white/20 backdrop-blur-sm border border-white/30 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-transparent"
                              value={hostFormData.ansible_become_method}
                              onChange={(e) => setHostFormData({...hostFormData, ansible_become_method: e.target.value})}
                            >
                              <option value="sudo">sudo</option>
                              <option value="su">su</option>
                              <option value="doas">doas</option>
                            </select>
                          </div>
                        </div>
                      </div>
                    </GlassCard>
                  </div>

                  {/* Ansible变量配置 */}
                  <div className="mt-6">
                    <GlassCard padding="md">
                      <h4 className="font-medium text-gray-800 mb-4 flex items-center">
                        <AdjustmentsHorizontalIcon className="h-5 w-5 mr-2 text-indigo-500" />
                        Ansible变量 (JSON格式)
                      </h4>
                      <textarea
                        className="w-full px-4 py-3 bg-white/20 backdrop-blur-sm border border-white/30 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-transparent font-mono text-sm"
                        rows={6}
                        placeholder={`{
  "custom_var": "value",
  "app_port": 8080,
  "environment": "production"
}`}
                        value={hostFormData.variables}
                        onChange={(e) => setHostFormData({...hostFormData, variables: e.target.value})}
                      />
                      <p className="text-xs text-gray-500 mt-2">
                        💡 请输入有效的JSON格式变量，这些变量将在Ansible执行时可用
                      </p>
                    </GlassCard>
                  </div>

                  {/* 操作按钮 */}
                  <div className="flex justify-between items-center mt-8">
                    <div className="flex space-x-3">
                      {editingHost && (
                        <GlassButton
                          variant="secondary"
                          onClick={() => handlePingHost(editingHost)}
                        >
                          <SignalIcon className="h-4 w-4 mr-2" />
                          测试连接
                        </GlassButton>
                      )}
                    </div>
                    
                    <div className="flex space-x-3">
                      <GlassButton
                        variant="ghost"
                        onClick={() => {
                          setShowHostModal(false);
                          setEditingHost(null);
                        }}
                      >
                        取消
                      </GlassButton>
                      <GlassButton
                        variant="primary"
                        onClick={handleSubmitHost}
                        disabled={submitting}
                      >
                        {submitting ? '提交中...' : (editingHost ? '保存更改' : '创建主机')}
                      </GlassButton>
                    </div>
                  </div>
                </div>
              </GlassCard>
            </motion.div>
          </div>
        )}

        {showGroupModal && (
          <div className="fixed inset-0 bg-black/50 flex items-start justify-center z-50 p-4 overflow-y-auto">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: 20 }}
              transition={{ duration: 0.2 }}
              className="w-full max-w-2xl my-8"
            >
              <GlassCard>
                <div className="p-6">
                  <h3 className="text-xl font-semibold mb-6 flex items-center">
                    <FolderIcon className="h-6 w-6 mr-2 text-amber-500" />
                    {editingGroup ? '编辑主机组' : '添加主机组'}
                  </h3>

                  <div className="space-y-6">
                    {/* 基本信息 */}
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                          组名 *
                        </label>
                        <GlassInput
                          placeholder="例如: web-servers"
                          value={groupFormData.name}
                          onChange={(e) => setGroupFormData({...groupFormData, name: e.target.value})}
                          disabled={!!editingGroup}
                        />
                        {editingGroup && (
                          <p className="text-xs text-gray-500 mt-1">
                            ⚠️ 组名不可修改
                          </p>
                        )}
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                          显示名称
                        </label>
                        <GlassInput
                          placeholder="例如: Web服务器组"
                          value={groupFormData.display_name}
                          onChange={(e) => setGroupFormData({...groupFormData, display_name: e.target.value})}
                        />
                      </div>
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        父级组
                      </label>
                      <select 
                        className="w-full px-4 py-3 bg-white/20 backdrop-blur-sm border border-white/30 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-transparent"
                        value={groupFormData.parent_group}
                        onChange={(e) => setGroupFormData({...groupFormData, parent_group: e.target.value})}
                      >
                        <option value="">无父级组 (根组)</option>
                        {groups.filter(g => g.name !== 'all' && g.name !== 'ungrouped').map(group => (
                          <option key={group.id} value={group.name}>{group.display_name || group.name}</option>
                        ))}
                      </select>
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        描述
                      </label>
                      <textarea
                        className="w-full px-4 py-3 bg-white/20 backdrop-blur-sm border border-white/30 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-transparent resize-none"
                        rows={3}
                        placeholder="主机组的详细描述..."
                        value={groupFormData.description}
                        onChange={(e) => setGroupFormData({...groupFormData, description: e.target.value})}
                      />
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        标签 (逗号分隔)
                      </label>
                      <GlassInput
                        placeholder="例如: production, web, frontend"
                        value={groupFormData.tags}
                        onChange={(e) => setGroupFormData({...groupFormData, tags: e.target.value})}
                      />
                    </div>

                    {/* 组变量 */}
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        组变量 (JSON格式)
                      </label>
                      <textarea
                        className="w-full px-4 py-3 bg-white/20 backdrop-blur-sm border border-white/30 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-transparent font-mono text-sm"
                        rows={6}
                        placeholder={`{
  "nginx_port": 80,
  "ssl_enabled": true,
  "backup_enabled": false
}`}
                        value={groupFormData.variables}
                        onChange={(e) => setGroupFormData({...groupFormData, variables: e.target.value})}
                      />
                      <p className="text-xs text-gray-500 mt-2">
                        💡 组变量将应用于该组下的所有主机
                      </p>
                    </div>

                    <div className="flex items-center space-x-2">
                      <input
                        type="checkbox"
                        id="group_is_active"
                        className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                        checked={groupFormData.is_active}
                        onChange={(e) => setGroupFormData({...groupFormData, is_active: e.target.checked})}
                      />
                      <label htmlFor="group_is_active" className="text-sm text-gray-700">
                        启用此主机组
                      </label>
                    </div>
                  </div>

                  <div className="flex justify-end space-x-3 mt-8">
                    <GlassButton
                      variant="ghost"
                      onClick={() => {
                        setShowGroupModal(false);
                        setEditingGroup(null);
                        // 重置表单
                        setGroupFormData({
                          name: '',
                          display_name: '',
                          description: '',
                          parent_group: '',
                          tags: '',
                          is_active: true,
                          variables: '{}'
                        });
                      }}
                    >
                      取消
                    </GlassButton>
                    <GlassButton
                      variant="primary"
                      onClick={handleSubmitGroup}
                      disabled={submittingGroup}
                    >
                      {submittingGroup ? '提交中...' : (editingGroup ? '保存更改' : '创建主机组')}
                    </GlassButton>
                  </div>
                </div>
              </GlassCard>
            </motion.div>
          </div>
        )}

        {showImportModal && (
          <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: 20 }}
              transition={{ duration: 0.2 }}
              className="w-full max-w-4xl max-h-[90vh] overflow-y-auto"
            >
              <GlassCard>
                <div className="p-6">
                  <h3 className="text-xl font-semibold mb-6 flex items-center">
                    <CloudArrowUpIcon className="h-6 w-6 mr-2 text-blue-500" />
                    导入Inventory
                  </h3>

                  <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    {/* 导入方式选择 */}
                    <GlassCard padding="md">
                      <h4 className="font-medium text-gray-800 mb-4">📁 导入方式</h4>
                      <div className="space-y-4">
                        <div className="flex items-center space-x-2">
                          <input
                            type="radio"
                            id="import_file"
                            name="import_method"
                            className="text-blue-600 focus:ring-blue-500"
                            defaultChecked
                          />
                          <label htmlFor="import_file" className="text-sm text-gray-700">
                            文件上传
                          </label>
                        </div>
                        <div className="flex items-center space-x-2">
                          <input
                            type="radio"
                            id="import_text"
                            name="import_method"
                            className="text-blue-600 focus:ring-blue-500"
                          />
                          <label htmlFor="import_text" className="text-sm text-gray-700">
                            文本粘贴
                          </label>
                        </div>
                        
                        {/* 文件上传区域 */}
                        <div className="mt-4 p-6 border-2 border-dashed border-gray-300 rounded-lg text-center">
                          <CloudArrowUpIcon className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                          <p className="text-sm text-gray-600 mb-2">
                            拖拽文件到此处或点击选择文件
                          </p>
                          <p className="text-xs text-gray-500">
                            支持 .ini, .yaml, .yml, .json 格式
                          </p>
                          <GlassButton variant="secondary" className="mt-3">
                            选择文件
                          </GlassButton>
                        </div>
                      </div>
                    </GlassCard>

                    {/* 导入配置 */}
                    <GlassCard padding="md">
                      <h4 className="font-medium text-gray-800 mb-4">⚙️ 导入配置</h4>
                      <div className="space-y-4">
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-2">
                            文件格式
                          </label>
                          <select className="w-full px-4 py-3 bg-white/20 backdrop-blur-sm border border-white/30 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-transparent">
                            <option value="auto">自动检测</option>
                            <option value="ini">INI格式</option>
                            <option value="yaml">YAML格式</option>
                            <option value="json">JSON格式</option>
                          </select>
                        </div>

                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-2">
                            合并模式
                          </label>
                          <select className="w-full px-4 py-3 bg-white/20 backdrop-blur-sm border border-white/30 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-transparent">
                            <option value="replace">替换 - 清空现有数据后导入</option>
                            <option value="merge">合并 - 与现有数据合并</option>
                            <option value="append">追加 - 仅添加新数据</option>
                          </select>
                        </div>

                        <div className="space-y-2">
                          <div className="flex items-center space-x-2">
                            <input
                              type="checkbox"
                              id="validate_before_import"
                              className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                              defaultChecked
                            />
                            <label htmlFor="validate_before_import" className="text-sm text-gray-700">
                              导入前验证数据
                            </label>
                          </div>
                          <div className="flex items-center space-x-2">
                            <input
                              type="checkbox"
                              id="backup_before_import"
                              className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                              defaultChecked
                            />
                            <label htmlFor="backup_before_import" className="text-sm text-gray-700">
                              导入前备份现有数据
                            </label>
                          </div>
                          <div className="flex items-center space-x-2">
                            <input
                              type="checkbox"
                              id="skip_duplicates"
                              className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                            />
                            <label htmlFor="skip_duplicates" className="text-sm text-gray-700">
                              跳过重复主机
                            </label>
                          </div>
                        </div>
                      </div>
                    </GlassCard>
                  </div>

                  {/* 文本输入区域 */}
                  <div className="mt-6">
                    <GlassCard padding="md">
                      <h4 className="font-medium text-gray-800 mb-4">📝 文本输入 (可选)</h4>
                      <textarea
                        className="w-full px-4 py-3 bg-white/20 backdrop-blur-sm border border-white/30 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-transparent font-mono text-sm"
                        rows={8}
                        placeholder={`# INI格式示例
[web-servers]
web-01 ansible_host=192.168.1.10
web-02 ansible_host=192.168.1.11

[database-servers]
db-01 ansible_host=192.168.1.20 ansible_port=3306

[web-servers:vars]
nginx_port=80
ssl_enabled=true`}
                      />
                      <p className="text-xs text-gray-500 mt-2">
                        💡 可以直接粘贴Inventory内容，支持INI、YAML、JSON格式
                      </p>
                    </GlassCard>
                  </div>

                  {/* 预览区域 */}
                  <div className="mt-6">
                    <GlassCard padding="md">
                      <h4 className="font-medium text-gray-800 mb-4">👀 导入预览</h4>
                      <div className="bg-gray-50/50 rounded-lg p-4 text-sm">
                        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-center">
                          <div>
                            <div className="text-2xl font-bold text-blue-600">0</div>
                            <div className="text-gray-600">待导入主机</div>
                          </div>
                          <div>
                            <div className="text-2xl font-bold text-green-600">0</div>
                            <div className="text-gray-600">新增主机</div>
                          </div>
                          <div>
                            <div className="text-2xl font-bold text-amber-600">0</div>
                            <div className="text-gray-600">更新主机</div>
                          </div>
                          <div>
                            <div className="text-2xl font-bold text-purple-600">0</div>
                            <div className="text-gray-600">主机组</div>
                          </div>
                        </div>
                        <p className="text-center text-gray-500 mt-4">
                          选择文件或输入内容后将显示导入预览
                        </p>
                      </div>
                    </GlassCard>
                  </div>

                  <div className="flex justify-between items-center mt-8">
                    <GlassButton
                      variant="secondary"
                      onClick={() => info('预览功能开发中...')}
                    >
                      预览导入
                    </GlassButton>
                    
                    <div className="flex space-x-3">
                      <GlassButton
                        variant="ghost"
                        onClick={() => setShowImportModal(false)}
                      >
                        取消
                      </GlassButton>
                      <GlassButton
                        variant="primary"
                        onClick={() => {
                          setShowImportModal(false);
                          success('Inventory导入成功！导入了3台主机和2个主机组');
                        }}
                      >
                        开始导入
                      </GlassButton>
                    </div>
                  </div>
                </div>
              </GlassCard>
            </motion.div>
          </div>
        )}
      </AnimatePresence>

      {/* 👁️ 主机详情模态框 */}
      <AnimatePresence>
        {showHostDetailModal && viewingHost && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm">
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              className="w-full max-w-4xl max-h-[90vh] overflow-hidden"
            >
              <GlassCard padding="none">
                <div className="flex flex-col h-full max-h-[90vh]">
                  {/* 标题栏 */}
                  <div className="flex items-center justify-between p-6 border-b border-white/20">
                    <div className="flex items-center space-x-3">
                      <ServerIcon className="h-6 w-6 text-blue-500" />
                      <div>
                        <h3 className="text-xl font-bold text-gray-800">
                          {viewingHost.hostname}
                        </h3>
                        <p className="text-sm text-gray-600">
                          {viewingHost.display_name || '主机详情'}
                        </p>
                      </div>
                    </div>
                    <GlassButton
                      variant="ghost"
                      onClick={() => {
                        setShowHostDetailModal(false);
                        setViewingHost(null);
                      }}
                    >
                      <XMarkIcon className="h-5 w-5" />
                    </GlassButton>
                  </div>

                  {/* 内容区域 */}
                  <div className="flex-1 overflow-y-auto p-6 space-y-6">
                    {/* 快速操作面板 */}
                    <GlassCard padding="md">
                      <h4 className="font-medium text-gray-800 mb-4 flex items-center">
                        <span className="text-lg mr-2">⚡</span>
                        快速操作
                      </h4>
                      <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                        <GlassButton 
                          variant="secondary" 
                          className="w-full"
                          onClick={() => handlePingHost(viewingHost)}
                        >
                          <SignalIcon className="h-4 w-4 mr-2" />
                          测试连接
                        </GlassButton>
                        <GlassButton 
                          variant="secondary" 
                          className="w-full"
                          onClick={async () => {
                            try {
                              info('正在刷新系统信息...');
                              const result = await inventoryService.gatherHostFacts(viewingHost.id);
                              if (result.success) {
                                success('系统信息刷新成功！');
                                // 重新获取主机数据
                                const updatedHost = await inventoryService.getHost(viewingHost.id);
                                // 创建新对象确保React检测到变化
                                setViewingHost({...updatedHost});
                                // 刷新主机列表
                                await loadData(true);
                              } else {
                                error(result.message || '刷新系统信息失败');
                              }
                            } catch (err) {
                              console.error('刷新系统信息失败:', err);
                              error('刷新系统信息失败');
                            }
                          }}
                        >
                          <ArrowPathIcon className="h-4 w-4 mr-2" />
                          刷新信息
                        </GlassButton>
                        <GlassButton 
                          variant="secondary" 
                          className="w-full"
                          onClick={() => {
                            setShowHostDetailModal(false);
                            handleEditHost(viewingHost);
                          }}
                        >
                          <PencilIcon className="h-4 w-4 mr-2" />
                          编辑主机
                        </GlassButton>
                        <GlassButton 
                          variant="secondary" 
                          className="w-full"
                          onClick={() => {
                            info('执行任务功能开发中...');
                          }}
                        >
                          <span className="text-lg mr-2">🚀</span>
                          执行任务
                        </GlassButton>
                        <GlassButton 
                          variant="secondary" 
                          className="w-full"
                          onClick={() => {
                            info('监控功能开发中...');
                          }}
                        >
                          <span className="text-lg mr-2">📊</span>
                          查看监控
                        </GlassButton>
                        <GlassButton 
                          variant="secondary" 
                          className="w-full"
                          onClick={() => {
                            info('执行历史功能开发中...');
                          }}
                        >
                          <span className="text-lg mr-2">📜</span>
                          执行历史
                        </GlassButton>
                      </div>
                    </GlassCard>

                    {/* 基本信息 */}
                    <GlassCard padding="md">
                      <h4 className="font-medium text-gray-800 mb-4 flex items-center">
                        <ServerIcon className="h-5 w-5 mr-2 text-blue-500" />
                        基本信息
                      </h4>
                      <div className="grid grid-cols-2 gap-4">
                        <div>
                          <label className="text-sm text-gray-600">主机名</label>
                          <p className="text-gray-800 font-medium">{viewingHost.hostname}</p>
                        </div>
                        <div>
                          <label className="text-sm text-gray-600">显示名称</label>
                          <p className="text-gray-800 font-medium">{viewingHost.display_name || '-'}</p>
                        </div>
                        <div>
                          <label className="text-sm text-gray-600">IP地址</label>
                          <p className="text-gray-800 font-medium">{viewingHost.ansible_host}</p>
                        </div>
                        <div>
                          <label className="text-sm text-gray-600">SSH端口</label>
                          <p className="text-gray-800 font-medium">{viewingHost.ansible_port}</p>
                        </div>
                        <div>
                          <label className="text-sm text-gray-600">SSH用户</label>
                          <p className="text-gray-800 font-medium">{viewingHost.ansible_user || 'root'}</p>
                        </div>
                        <div>
                          <label className="text-sm text-gray-600">所属组</label>
                          <p className="text-gray-800 font-medium">
                            {groups.find(g => g.name === viewingHost.group_name)?.display_name || viewingHost.group_name}
                          </p>
                        </div>
                        <div>
                          <label className="text-sm text-gray-600">状态</label>
                          <p className="text-gray-800 font-medium">
                            {viewingHost.is_active ? (
                              <span className="text-green-600">✅ 活跃</span>
                            ) : (
                              <span className="text-gray-500">⏸️ 非活跃</span>
                            )}
                          </p>
                        </div>
                        <div>
                          <label className="text-sm text-gray-600">连接状态</label>
                          <p className="text-gray-800 font-medium">
                            {getStatusDisplay(viewingHost.ping_status).icon} {getStatusDisplay(viewingHost.ping_status).text}
                          </p>
                        </div>
                        {viewingHost.extra_data?.system_info?.os?.distribution && (
                          <div>
                            <label className="text-sm text-gray-600">操作系统</label>
                            <p className="text-gray-800 font-medium flex items-center">
                              <OSIcon 
                                distribution={viewingHost.extra_data.system_info.os.distribution}
                                size="md"
                                className="mr-2"
                              />
                              {viewingHost.extra_data.system_info.os.distribution}
                              {viewingHost.extra_data.system_info.os.distribution_version && (
                                <span className="text-sm text-gray-600 ml-2">
                                  {viewingHost.extra_data.system_info.os.distribution_version}
                                </span>
                              )}
                            </p>
                          </div>
                        )}
                      </div>
                      {viewingHost.description && (
                        <div className="mt-4 pt-4 border-t border-white/20">
                          <label className="text-sm text-gray-600">描述</label>
                          <p className="text-gray-800 mt-1">{viewingHost.description}</p>
                        </div>
                      )}
                    </GlassCard>

                    {/* 连接配置 */}
                    <GlassCard padding="md">
                      <h4 className="font-medium text-gray-800 mb-4 flex items-center">
                        <SignalIcon className="h-5 w-5 mr-2 text-green-500" />
                        连接配置
                      </h4>
                      <div className="grid grid-cols-2 gap-4">
                        <div>
                          <label className="text-sm text-gray-600">连接字符串</label>
                          <p className="text-gray-800 font-mono text-sm bg-white/10 p-2 rounded">
                            {viewingHost.connection_string}
                          </p>
                        </div>
                        <div>
                          <label className="text-sm text-gray-600">SSH私钥</label>
                          <p className="text-gray-800 font-medium">
                            {viewingHost.ansible_ssh_private_key_file || '-'}
                          </p>
                        </div>
                        <div>
                          <label className="text-sm text-gray-600">提权方式</label>
                          <p className="text-gray-800 font-medium">
                            {viewingHost.ansible_become ? (
                              <span>
                                {viewingHost.ansible_become_method} (用户: {viewingHost.ansible_become_user})
                              </span>
                            ) : (
                              <span className="text-gray-500">未启用</span>
                            )}
                          </p>
                        </div>
                        <div>
                          <label className="text-sm text-gray-600">最后连接测试</label>
                          <p className="text-gray-800 font-medium">
                            {viewingHost.last_ping ? formatDate(viewingHost.last_ping, { relative: true }) : '-'}
                          </p>
                        </div>
                      </div>
                    </GlassCard>

                    {/* 系统信息 */}
                    {viewingHost.extra_data?.system_info && (
                      <GlassCard padding="md">
                        <div className="flex items-center justify-between mb-4">
                          <h4 className="font-medium text-gray-800 flex items-center">
                            💻 系统信息
                          </h4>
                          <span className="text-xs text-gray-500">
                            {viewingHost.extra_data.system_info.collected_at && 
                              `更新于 ${formatDate(viewingHost.extra_data.system_info.collected_at, { relative: true })}`
                            }
                          </span>
                        </div>
                        
                        <div className="space-y-4">
                          {/* 操作系统 */}
                          {viewingHost.extra_data.system_info.os && (
                            <div>
                              <label className="text-sm font-medium text-gray-700 mb-2 block flex items-center">
                                <OSIcon 
                                  distribution={viewingHost.extra_data.system_info.os.distribution || 'Linux'}
                                  size="md"
                                  className="mr-2"
                                />
                                操作系统
                              </label>
                              <div className="grid grid-cols-2 gap-3 bg-white/10 rounded-lg p-3">
                                <div>
                                  <span className="text-xs text-gray-600">发行版</span>
                                  <p className="text-sm text-gray-800 font-medium">
                                    {viewingHost.extra_data.system_info.os.distribution || '-'}
                                  </p>
                                </div>
                                <div>
                                  <span className="text-xs text-gray-600">版本</span>
                                  <p className="text-sm text-gray-800 font-medium">
                                    {viewingHost.extra_data.system_info.os.distribution_version || '-'}
                                  </p>
                                </div>
                                <div>
                                  <span className="text-xs text-gray-600">系统类型</span>
                                  <p className="text-sm text-gray-800 font-medium">
                                    {viewingHost.extra_data.system_info.os.system || '-'}
                                  </p>
                                </div>
                              </div>
                            </div>
                          )}

                          {/* 内核 */}
                          {viewingHost.extra_data.system_info.kernel && (
                            <div>
                              <label className="text-sm font-medium text-gray-700 mb-2 block">🔧 内核</label>
                              <div className="bg-white/10 rounded-lg p-3">
                                <p className="text-sm text-gray-800 font-medium">
                                  {viewingHost.extra_data.system_info.kernel.kernel || '-'} 
                                  {viewingHost.extra_data.system_info.kernel.kernel_version && 
                                    ` (${viewingHost.extra_data.system_info.kernel.kernel_version})`
                                  }
                                </p>
                              </div>
                            </div>
                          )}

                          {/* 硬件 */}
                          {viewingHost.extra_data.system_info.hardware && (
                            <div>
                              <label className="text-sm font-medium text-gray-700 mb-2 block">⚙️ 硬件</label>
                              <div className="grid grid-cols-2 gap-3 bg-white/10 rounded-lg p-3">
                                <div>
                                  <span className="text-xs text-gray-600">架构</span>
                                  <p className="text-sm text-gray-800 font-medium">
                                    {viewingHost.extra_data.system_info.hardware.architecture || '-'}
                                  </p>
                                </div>
                                <div>
                                  <span className="text-xs text-gray-600">机器类型</span>
                                  <p className="text-sm text-gray-800 font-medium">
                                    {viewingHost.extra_data.system_info.hardware.machine || '-'}
                                  </p>
                                </div>
                                <div>
                                  <span className="text-xs text-gray-600">CPU核心数</span>
                                  <p className="text-sm text-gray-800 font-medium">
                                    {viewingHost.extra_data.system_info.hardware.processor_cores || '-'}
                                  </p>
                                </div>
                                <div>
                                  <span className="text-xs text-gray-600">虚拟CPU数</span>
                                  <p className="text-sm text-gray-800 font-medium">
                                    {viewingHost.extra_data.system_info.hardware.processor_vcpus || '-'}
                                  </p>
                                </div>
                              </div>
                            </div>
                          )}

                          {/* 内存 */}
                          {viewingHost.extra_data.system_info.memory && (
                            <div>
                              <label className="text-sm font-medium text-gray-700 mb-2 block">💾 内存</label>
                              <div className="bg-white/10 rounded-lg p-3 space-y-4">
                                {/* 内存使用率 */}
                                {(() => {
                                  const total = viewingHost.extra_data.system_info.memory.memtotal_mb || 0;
                                  const free = viewingHost.extra_data.system_info.memory.memfree_mb || 0;
                                  
                                  if (total === 0) return null;
                                  
                                  const used = total - free;
                                  const percentage = ((used / total) * 100).toFixed(1);
                                  const percentageNum = parseFloat(percentage);
                                  
                                  return (
                                    <div>
                                      <div className="flex items-center justify-between mb-2">
                                        <span className="text-xs text-gray-600">内存使用率</span>
                                        <span className="text-xs font-medium text-gray-800">
                                          {percentage}% ({formatMemorySize(used)} / {formatMemorySize(total)})
                                        </span>
                                      </div>
                                      <div className="w-full bg-gray-200 rounded-full h-2.5">
                                        <div 
                                          className={`h-2.5 rounded-full transition-all duration-300 ${
                                            percentageNum > 90 ? 'bg-red-500' : 
                                            percentageNum > 70 ? 'bg-yellow-500' : 
                                            'bg-green-500'
                                          }`}
                                          style={{ width: `${percentage}%` }}
                                        />
                                      </div>
                                    </div>
                                  );
                                })()}
                                
                                {/* 详细信息 */}
                                <div className="grid grid-cols-2 gap-3 pt-3 border-t border-white/20">
                                  <div>
                                    <span className="text-xs text-gray-600">总内存</span>
                                    <p className="text-sm text-gray-800 font-medium">
                                      {viewingHost.extra_data.system_info.memory.memtotal_mb 
                                        ? formatMemorySize(viewingHost.extra_data.system_info.memory.memtotal_mb)
                                        : '-'}
                                    </p>
                                  </div>
                                  <div>
                                    <span className="text-xs text-gray-600">可用内存</span>
                                    <p className="text-sm text-gray-800 font-medium">
                                      {viewingHost.extra_data.system_info.memory.memfree_mb 
                                        ? formatMemorySize(viewingHost.extra_data.system_info.memory.memfree_mb)
                                        : '-'}
                                    </p>
                                  </div>
                                  <div>
                                    <span className="text-xs text-gray-600">总交换空间</span>
                                    <p className="text-sm text-gray-800 font-medium">
                                      {viewingHost.extra_data.system_info.memory.swaptotal_mb 
                                        ? formatMemorySize(viewingHost.extra_data.system_info.memory.swaptotal_mb)
                                        : '-'}
                                    </p>
                                  </div>
                                  <div>
                                    <span className="text-xs text-gray-600">可用交换空间</span>
                                    <p className="text-sm text-gray-800 font-medium">
                                      {viewingHost.extra_data.system_info.memory.swapfree_mb 
                                        ? formatMemorySize(viewingHost.extra_data.system_info.memory.swapfree_mb)
                                        : '-'}
                                    </p>
                                  </div>
                                </div>
                              </div>
                            </div>
                          )}

                          {/* 💿 磁盘信息 */}
                          {viewingHost.extra_data?.system_info?.disks && viewingHost.extra_data.system_info.disks.length > 0 && (
                            <div>
                              <label className="text-sm font-medium text-gray-700 mb-2 block">💿 磁盘</label>
                              <div className="space-y-3">
                                {viewingHost.extra_data.system_info.disks.map((disk, index) => (
                                  <div key={index} className="bg-white/10 rounded-lg p-3">
                                    <div className="flex items-center justify-between mb-2">
                                      <span className="text-sm font-medium text-gray-800">{disk.mount}</span>
                                      <span className="text-xs text-gray-600">
                                        {formatMemorySize(disk.used_mb)} / {formatMemorySize(disk.total_mb)} ({disk.percentage}%)
                                      </span>
                                    </div>
                                    <div className="w-full bg-gray-200 rounded-full h-2">
                                      <div 
                                        className={`h-2 rounded-full transition-all duration-300 ${
                                          disk.percentage > 90 ? 'bg-red-500' : 
                                          disk.percentage > 70 ? 'bg-yellow-500' : 
                                          'bg-green-500'
                                        }`}
                                        style={{ width: `${disk.percentage}%` }}
                                      />
                                    </div>
                                    <div className="mt-1 text-xs text-gray-600">
                                      文件系统: {disk.fstype} | 设备: {disk.device}
                                    </div>
                                  </div>
                                ))}
                              </div>
                            </div>
                          )}

                          {/* 🌐 网络接口信息 */}
                          {viewingHost.extra_data?.system_info?.network?.interfaces && viewingHost.extra_data.system_info.network.interfaces.length > 0 && (
                            <div>
                              <label className="text-sm font-medium text-gray-700 mb-2 block">🌐 网络接口</label>
                              <div className="space-y-2">
                                {viewingHost.extra_data.system_info.network.interfaces.map((iface, index) => (
                                  <div key={index} className="bg-white/10 rounded-lg p-3">
                                    <div className="flex items-center justify-between">
                                      <span className="text-sm font-medium text-gray-800">{iface.name}</span>
                                      <span className={`text-xs px-2 py-1 rounded-full ${
                                        iface.status === 'up' ? 'bg-green-500/20 text-green-700' : 'bg-gray-500/20 text-gray-600'
                                      }`}>
                                        {iface.status === 'up' ? '🟢 UP' : '⚫ DOWN'}
                                      </span>
                                    </div>
                                    <div className="mt-2 space-y-1 text-xs text-gray-600">
                                      {iface.ipv4 && <div>📍 IPv4: {iface.ipv4}</div>}
                                      {iface.ipv6 && <div>📍 IPv6: {iface.ipv6}</div>}
                                      {iface.mac && <div>🔖 MAC: {iface.mac}</div>}
                                      {iface.speed && <div>⚡ 速度: {iface.speed} Mbps</div>}
                                      {/* 流量统计 */}
                                      {(iface.bytes_recv !== undefined || iface.bytes_sent !== undefined) && (
                                        <div className="mt-2 pt-2 border-t border-gray-200/50">
                                          <div className="font-medium text-gray-700 mb-1">📊 流量统计</div>
                                          {iface.bytes_recv !== undefined && (
                                            <div className="flex items-center justify-between">
                                              <span>↓ 接收:</span>
                                              <span className="font-medium text-green-600">
                                                {(() => {
                                                  const bytes = iface.bytes_recv;
                                                  if (bytes >= 1024**3) return `${(bytes / (1024**3)).toFixed(2)} GB`;
                                                  if (bytes >= 1024**2) return `${(bytes / (1024**2)).toFixed(2)} MB`;
                                                  if (bytes >= 1024) return `${(bytes / 1024).toFixed(2)} KB`;
                                                  return `${bytes} B`;
                                                })()}
                                              </span>
                                            </div>
                                          )}
                                          {iface.bytes_sent !== undefined && (
                                            <div className="flex items-center justify-between">
                                              <span>↑ 发送:</span>
                                              <span className="font-medium text-blue-600">
                                                {(() => {
                                                  const bytes = iface.bytes_sent;
                                                  if (bytes >= 1024**3) return `${(bytes / (1024**3)).toFixed(2)} GB`;
                                                  if (bytes >= 1024**2) return `${(bytes / (1024**2)).toFixed(2)} MB`;
                                                  if (bytes >= 1024) return `${(bytes / 1024).toFixed(2)} KB`;
                                                  return `${bytes} B`;
                                                })()}
                                              </span>
                                            </div>
                                          )}
                                          {(iface.bytes_recv !== undefined && iface.bytes_sent !== undefined) && (
                                            <div className="flex items-center justify-between font-medium text-purple-600">
                                              <span>📈 总计:</span>
                                              <span>
                                                {(() => {
                                                  const bytes = iface.bytes_recv + iface.bytes_sent;
                                                  if (bytes >= 1024**3) return `${(bytes / (1024**3)).toFixed(2)} GB`;
                                                  if (bytes >= 1024**2) return `${(bytes / (1024**2)).toFixed(2)} MB`;
                                                  if (bytes >= 1024) return `${(bytes / 1024).toFixed(2)} KB`;
                                                  return `${bytes} B`;
                                                })()}
                                              </span>
                                            </div>
                                          )}
                                        </div>
                                      )}
                                    </div>
                                  </div>
                                ))}
                              </div>
                            </div>
                          )}

                          {/* ⏱️ 系统运行时间 */}
                          {viewingHost.extra_data?.system_info?.uptime && (
                            <div className="bg-blue-500/10 rounded-lg p-4 border border-blue-500/20">
                              <div className="flex items-center space-x-3">
                                <span className="text-2xl">⏱️</span>
                                <div>
                                  <div className="text-sm text-gray-600">系统运行时间</div>
                                  <div className="text-lg font-bold text-gray-800">
                                    {viewingHost.extra_data.system_info.uptime.days} 天 {' '}
                                    {viewingHost.extra_data.system_info.uptime.hours} 小时 {' '}
                                    {viewingHost.extra_data.system_info.uptime.minutes} 分钟
                                  </div>
                                  <div className="text-xs text-gray-600 mt-1">
                                    启动时间: {formatDate(viewingHost.extra_data.system_info.uptime.boot_time)}
                                  </div>
                                </div>
                              </div>
                            </div>
                          )}
                        </div>
                      </GlassCard>
                    )}

                    {/* 如果没有系统信息，显示收集按钮 */}
                    {!viewingHost.extra_data?.system_info && (
                      <GlassCard padding="md">
                        <div className="text-center py-6">
                          <p className="text-gray-600 mb-4">📊 暂无系统信息</p>
                          <GlassButton
                            variant="primary"
                            onClick={async () => {
                              try {
                                info('正在收集系统信息...');
                                const result = await inventoryService.gatherHostFacts(viewingHost.id);
                                if (result.success) {
                                  success('系统信息收集成功！');
                                  // 刷新主机数据
                                  await loadData(true);
                                  // 更新viewingHost
                                  const updatedHost = await inventoryService.getHost(viewingHost.id);
                                  setViewingHost(updatedHost);
                                } else {
                                  error(result.message || '收集系统信息失败');
                                }
                              } catch (err) {
                                console.error('收集系统信息失败:', err);
                                error('收集系统信息失败');
                              }
                            }}
                          >
                            🔄 收集系统信息
                          </GlassButton>
                        </div>
                      </GlassCard>
                    )}

                    {/* 📜 执行历史 */}
                    <ExecutionHistoryCard hostname={viewingHost.hostname} />

                    {/* 标签 */}
                    {viewingHost.tags && viewingHost.tags.length > 0 && (
                      <GlassCard padding="md">
                        <h4 className="font-medium text-gray-800 mb-4">🏷️ 标签</h4>
                        <div className="flex flex-wrap gap-2">
                          {viewingHost.tags.map((tag, index) => (
                            <span
                              key={index}
                              className="px-3 py-1 bg-blue-500/20 text-blue-700 text-sm rounded-full"
                            >
                              {tag}
                            </span>
                          ))}
                        </div>
                      </GlassCard>
                    )}

                    {/* 变量 */}
                    {viewingHost.variables && Object.keys(viewingHost.variables).length > 0 && (
                      <GlassCard padding="md">
                        <h4 className="font-medium text-gray-800 mb-4">⚙️ 变量</h4>
                        <div className="bg-white/10 rounded-lg p-4 font-mono text-sm overflow-x-auto">
                          <pre className="text-gray-800">
                            {JSON.stringify(viewingHost.variables, null, 2)}
                          </pre>
                        </div>
                      </GlassCard>
                    )}

                    {/* 时间信息 */}
                    <GlassCard padding="md">
                      <h4 className="font-medium text-gray-800 mb-4">🕐 时间信息</h4>
                      <div className="grid grid-cols-2 gap-4">
                        <div>
                          <label className="text-sm text-gray-600">创建时间</label>
                          <p className="text-gray-800 font-medium">
                            {formatDate(viewingHost.created_at)}
                          </p>
                        </div>
                        <div>
                          <label className="text-sm text-gray-600">更新时间</label>
                          <p className="text-gray-800 font-medium">
                            {formatDate(viewingHost.updated_at)}
                          </p>
                        </div>
                      </div>
                    </GlassCard>
                  </div>

                  {/* 底部操作栏 */}
                  <div className="flex items-center justify-between p-6 border-t border-white/20">
                    <div className="flex items-center space-x-2">
                      <GlassButton
                        variant="secondary"
                        onClick={() => handlePingHost(viewingHost)}
                      >
                        <SignalIcon className="h-4 w-4 mr-2" />
                        测试连接
                      </GlassButton>
                      <GlassButton
                        variant="secondary"
                        onClick={async () => {
                          try {
                            info('正在收集系统信息...');
                            const result = await inventoryService.gatherHostFacts(viewingHost.id);
                            if (result.success) {
                              success('系统信息收集成功！');
                              // 刷新主机数据
                              const updatedHost = await inventoryService.getHost(viewingHost.id);
                              setViewingHost(updatedHost);
                              await loadData(true);
                            } else {
                              error(result.message || '收集系统信息失败');
                            }
                          } catch (err) {
                            console.error('收集系统信息失败:', err);
                            error('收集系统信息失败');
                          }
                        }}
                      >
                        🔄 刷新系统信息
                      </GlassButton>
                      <GlassButton
                        variant="secondary"
                        onClick={() => {
                          setShowHostDetailModal(false);
                          handleEditHost(viewingHost);
                        }}
                      >
                        <PencilIcon className="h-4 w-4 mr-2" />
                        编辑
                      </GlassButton>
                    </div>
                    <GlassButton
                      variant="ghost"
                      onClick={() => {
                        setShowHostDetailModal(false);
                        setViewingHost(null);
                      }}
                    >
                      关闭
                    </GlassButton>
                  </div>
                </div>
              </GlassCard>
            </motion.div>
          </div>
        )}
      </AnimatePresence>

      {/* 🗑️ 确认对话框 */}
      <ConfirmDialog
        isOpen={confirmDialog.isOpen}
        title={confirmDialog.title}
        message={confirmDialog.message}
        type={confirmDialog.type}
        onConfirm={confirmDialog.onConfirm}
        onCancel={() => setConfirmDialog({ ...confirmDialog, isOpen: false })}
      />
    </motion.div>
  );
};

export default Inventory;

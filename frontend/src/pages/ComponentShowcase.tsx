import React, { useState } from 'react'
import { motion } from 'framer-motion'
import {
  GlassCard,
  GlassButton,
  GlassInput,
  GlassSelect,
  GlassTable,
  GlassModal,
  GlassTooltip,
} from '@/components/UI'
import ChineseInput from '@/components/UI/ChineseInput'
import ChineseDatePicker from '@/components/UI/ChineseDatePicker'
import LanguageSwitcher from '@/components/UI/LanguageSwitcher'
import { useChineseFormat } from '@/hooks/useChineseFormat'

/**
 * 🎨 玻璃态组件展示页面
 * 
 * 展示所有玻璃态基础组件的使用方法和效果
 */
const ComponentShowcase: React.FC = () => {
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [inputValue, setInputValue] = useState('')
  const [chineseInputValue, setChineseInputValue] = useState('')
  const [selectedDate, setSelectedDate] = useState<Date | null>(null)
  const { formatDate, formatFileSize, formatDuration, isChinese } = useChineseFormat()
  const [selectValue, setSelectValue] = useState('')

  // 🎨 表格数据示例
  const tableData = [
    { id: 1, name: '张三', role: '管理员', status: '活跃', lastLogin: '2024-01-15' },
    { id: 2, name: '李四', role: '操作员', status: '活跃', lastLogin: '2024-01-14' },
    { id: 3, name: '王五', role: '只读', status: '离线', lastLogin: '2024-01-10' },
  ]

  // 🎨 表格列配置
  const tableColumns = [
    { key: 'name', title: '姓名', dataIndex: 'name', sortable: true },
    { key: 'role', title: '角色', dataIndex: 'role' },
    {
      key: 'status',
      title: '状态',
      dataIndex: 'status',
      render: (status: string) => (
        <span className={`px-2 py-1 rounded-full text-xs ${
          status === '活跃' 
            ? 'bg-green-500/20 text-green-700' 
            : 'bg-gray-500/20 text-gray-700'
        }`}>
          {status}
        </span>
      ),
    },
    { key: 'lastLogin', title: '最后登录', dataIndex: 'lastLogin', sortable: true },
  ]

  // 🎨 选择器选项
  const selectOptions = [
    { value: 'option1', label: '选项一', icon: '🎯' },
    { value: 'option2', label: '选项二', icon: '⭐' },
    { value: 'option3', label: '选项三', icon: '🚀' },
  ]

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-600 via-blue-600 to-blue-800 p-6">
      <div className="max-w-7xl mx-auto space-y-8">
        {/* 🎨 页面标题 */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-center"
        >
          <h1 className="text-4xl font-bold text-white mb-4">
            🎨 玻璃态组件展示
          </h1>
          <p className="text-white/80 text-lg">
            现代化的玻璃态设计组件库，提供优雅的用户界面体验
          </p>
        </motion.div>

        {/* 🎨 卡片组件展示 */}
        <section>
          <h2 className="text-2xl font-semibold text-white mb-6">📋 卡片组件</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <GlassCard variant="primary">
              <h3 className="text-xl font-semibold text-glass-text-primary mb-3">
                ✨ 主要卡片
              </h3>
              <p className="text-glass-text-secondary">
                这是一个主要变体的玻璃态卡片，具有较高的透明度和清晰的视觉效果。
              </p>
            </GlassCard>

            <GlassCard variant="secondary">
              <h3 className="text-xl font-semibold text-glass-text-primary mb-3">
                🌟 次要卡片
              </h3>
              <p className="text-glass-text-secondary">
                次要变体的卡片，透明度较低，适合作为辅助内容容器使用。
              </p>
            </GlassCard>

            <GlassCard variant="dark">
              <h3 className="text-xl font-semibold text-glass-text-white mb-3">
                🌙 深色卡片
              </h3>
              <p className="text-glass-text-white/80">
                深色变体的卡片，适合在明亮背景上使用，提供更好的对比度。
              </p>
            </GlassCard>
          </div>
        </section>

        {/* 🎨 按钮组件展示 */}
        <section>
          <h2 className="text-2xl font-semibold text-white mb-6">🔘 按钮组件</h2>
          <GlassCard>
            <div className="space-y-6">
              {/* 按钮变体 */}
              <div>
                <h3 className="text-lg font-medium text-glass-text-primary mb-4">按钮变体</h3>
                <div className="flex flex-wrap gap-3">
                  <GlassButton variant="primary">✨ 主要按钮</GlassButton>
                  <GlassButton variant="secondary">🌟 次要按钮</GlassButton>
                  <GlassButton variant="success">✅ 成功按钮</GlassButton>
                  <GlassButton variant="warning">⚠️ 警告按钮</GlassButton>
                  <GlassButton variant="danger">🚨 危险按钮</GlassButton>
                  <GlassButton variant="ghost">👻 幽灵按钮</GlassButton>
                </div>
              </div>

              {/* 按钮尺寸 */}
              <div>
                <h3 className="text-lg font-medium text-glass-text-primary mb-4">按钮尺寸</h3>
                <div className="flex flex-wrap items-center gap-3">
                  <GlassButton size="xs">超小</GlassButton>
                  <GlassButton size="sm">小型</GlassButton>
                  <GlassButton size="md">中等</GlassButton>
                  <GlassButton size="lg">大型</GlassButton>
                  <GlassButton size="xl">超大</GlassButton>
                </div>
              </div>

              {/* 按钮状态 */}
              <div>
                <h3 className="text-lg font-medium text-glass-text-primary mb-4">按钮状态</h3>
                <div className="flex flex-wrap gap-3">
                  <GlassButton loading>🔄 加载中</GlassButton>
                  <GlassButton disabled>🚫 禁用状态</GlassButton>
                  <GlassButton 
                    leftIcon={
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                      </svg>
                    }
                  >
                    ➕ 带图标
                  </GlassButton>
                </div>
              </div>
            </div>
          </GlassCard>
        </section>

        {/* 🎨 输入框组件展示 */}
        <section>
          <h2 className="text-2xl font-semibold text-white mb-6">📝 输入框组件</h2>
          <GlassCard>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <GlassInput
                label="用户名"
                placeholder="请输入用户名"
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                leftIcon={
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                  </svg>
                }
              />

              <GlassInput
                label="搜索"
                placeholder="搜索内容..."
                variant="search"
                leftIcon={
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                  </svg>
                }
              />

              <GlassInput
                label="密码"
                type="password"
                placeholder="请输入密码"
                helperText="密码长度至少8位"
              />

              <GlassInput
                label="邮箱"
                type="email"
                placeholder="请输入邮箱地址"
                error="请输入有效的邮箱地址"
              />
            </div>
          </GlassCard>
        </section>

        {/* 🎨 选择器组件展示 */}
        <section>
          <h2 className="text-2xl font-semibold text-white mb-6">📋 选择器组件</h2>
          <GlassCard>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <GlassSelect
                label="单选选择器"
                options={selectOptions}
                value={selectValue}
                onChange={(value) => setSelectValue(value as string)}
                placeholder="请选择一个选项"
              />

              <GlassSelect
                label="多选选择器"
                options={selectOptions}
                multiple
                placeholder="请选择多个选项"
              />

              <GlassSelect
                label="可搜索选择器"
                options={selectOptions}
                searchable
                placeholder="搜索并选择"
              />

              <GlassSelect
                label="可清空选择器"
                options={selectOptions}
                clearable
                placeholder="可清空的选择器"
              />
            </div>
          </GlassCard>
        </section>

        {/* 🎨 表格组件展示 */}
        <section>
          <h2 className="text-2xl font-semibold text-white mb-6">📊 表格组件</h2>
          <GlassTable
            columns={tableColumns}
            data={tableData}
            hoverable
            striped
            pagination={{
              current: 1,
              pageSize: 10,
              total: 3,
              onChange: (page, pageSize) => console.log('分页变化:', page, pageSize),
            }}
          />
        </section>

        {/* 🇨🇳 中文组件展示 */}
        <section>
          <h2 className="text-2xl font-semibold text-white mb-6">🇨🇳 中文组件</h2>
          <GlassCard>
            <div className="space-y-6">
              {/* 语言切换器 */}
              <div>
                <h3 className="text-lg font-medium text-glass-text-primary mb-4">🌐 语言切换器</h3>
                <div className="flex items-center gap-4">
                  <LanguageSwitcher />
                  <LanguageSwitcher size="sm" showLabel={false} />
                  <LanguageSwitcher size="lg" />
                </div>
              </div>

              {/* 中文输入框 */}
              <div>
                <h3 className="text-lg font-medium text-glass-text-primary mb-4">📝 中文输入框</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <ChineseInput
                    label="中文姓名"
                    placeholder="请输入您的中文姓名"
                    value={chineseInputValue}
                    onChange={setChineseInputValue}
                    validation="chinese"
                    required
                    showCount
                    maxLength={10}
                  />

                  <ChineseInput
                    label="混合输入"
                    placeholder="支持中英文混合输入"
                    validation="mixed"
                    supportIME
                    helperText="支持中文输入法，实时验证"
                  />
                </div>
              </div>

              {/* 中文日期选择器 */}
              <div>
                <h3 className="text-lg font-medium text-glass-text-primary mb-4">📅 中文日期选择器</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <ChineseDatePicker
                    label="选择日期"
                    value={selectedDate || undefined}
                    onChange={setSelectedDate}
                    placeholder="请选择日期"
                    format="full"
                    showToday
                    showClear
                  />

                  <ChineseDatePicker
                    label="简短格式"
                    format="short"
                    placeholder="选择日期（简短格式）"
                  />
                </div>
              </div>

              {/* 中文格式化展示 */}
              <div>
                <h3 className="text-lg font-medium text-glass-text-primary mb-4">🔢 中文格式化</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  <div className="p-4 bg-white/5 rounded-lg">
                    <h4 className="font-medium text-glass-text-primary mb-2">📅 日期格式</h4>
                    <p className="text-glass-text-secondary text-sm">
                      {formatDate(new Date(), { includeWeekday: true })}
                    </p>
                  </div>

                  <div className="p-4 bg-white/5 rounded-lg">
                    <h4 className="font-medium text-glass-text-primary mb-2">📊 文件大小</h4>
                    <p className="text-glass-text-secondary text-sm">
                      {formatFileSize(1024 * 1024 * 2.5)}
                    </p>
                  </div>

                  <div className="p-4 bg-white/5 rounded-lg">
                    <h4 className="font-medium text-glass-text-primary mb-2">⏱️ 持续时间</h4>
                    <p className="text-glass-text-secondary text-sm">
                      {formatDuration(3665, true)}
                    </p>
                  </div>
                </div>
              </div>

              {/* 语言状态显示 */}
              <div className="p-4 bg-blue-500/10 rounded-lg border border-blue-500/20">
                <h4 className="font-medium text-blue-600 mb-2">🌐 当前语言环境</h4>
                <p className="text-blue-600/80 text-sm">
                  {isChinese ? '🇨🇳 中文环境 - 所有格式化都将使用中文格式' : '🇺🇸 英文环境 - 使用国际化格式'}
                </p>
              </div>
            </div>
          </GlassCard>
        </section>

        {/* 🎨 模态框和工具提示展示 */}
        <section>
          <h2 className="text-2xl font-semibold text-white mb-6">💬 反馈组件</h2>
          <GlassCard>
            <div className="flex flex-wrap gap-4">
              <GlassButton onClick={() => setIsModalOpen(true)}>
                🪟 打开模态框
              </GlassButton>

              <GlassTooltip content="这是一个工具提示信息">
                <GlassButton variant="secondary">
                  💡 悬浮查看提示
                </GlassButton>
              </GlassTooltip>

              <GlassTooltip 
                content="点击触发的工具提示" 
                trigger="click"
                placement="bottom"
              >
                <GlassButton variant="success">
                  👆 点击查看提示
                </GlassButton>
              </GlassTooltip>
            </div>
          </GlassCard>
        </section>

        {/* 🎨 模态框 */}
        <GlassModal
          isOpen={isModalOpen}
          onClose={() => setIsModalOpen(false)}
          title="🎨 玻璃态模态框"
          size="md"
        >
          <div className="space-y-4">
            <p className="text-glass-text-primary">
              这是一个玻璃态模态框的示例。它具有美丽的透明效果和流畅的动画。
            </p>
            
            <div className="flex gap-3 justify-end">
              <GlassButton 
                variant="secondary" 
                onClick={() => setIsModalOpen(false)}
              >
                取消
              </GlassButton>
              <GlassButton onClick={() => setIsModalOpen(false)}>
                确认
              </GlassButton>
            </div>
          </div>
        </GlassModal>
      </div>
    </div>
  )
}

export default ComponentShowcase
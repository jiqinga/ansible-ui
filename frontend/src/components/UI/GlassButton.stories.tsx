import type { Meta, StoryObj } from '@storybook/react'
import GlassButton from './GlassButton'

const meta: Meta<typeof GlassButton> = {
  title: '🎨 Glass UI/GlassButton',
  component: GlassButton,
  parameters: {
    layout: 'centered',
    docs: {
      description: {
        component: '🎨 玻璃态按钮组件 - 提供多种变体、尺寸和状态的现代化按钮',
      },
    },
  },
  tags: ['autodocs'],
  argTypes: {
    variant: {
      control: 'select',
      options: ['primary', 'secondary', 'danger', 'success', 'warning', 'ghost'],
      description: '按钮变体样式',
    },
    size: {
      control: 'select',
      options: ['xs', 'sm', 'md', 'lg', 'xl'],
      description: '按钮尺寸',
    },
    loading: {
      control: 'boolean',
      description: '加载状态',
    },
    disabled: {
      control: 'boolean',
      description: '禁用状态',
    },
    fullWidth: {
      control: 'boolean',
      description: '全宽显示',
    },
  },
}

export default meta
type Story = StoryObj<typeof meta>

// 🎨 基础按钮
export const Default: Story = {
  args: {
    children: '🎨 默认按钮',
  },
}

// 🎨 所有变体
export const Variants: Story = {
  render: () => (
    <div className="flex flex-wrap gap-4">
      <GlassButton variant="primary">✨ 主要按钮</GlassButton>
      <GlassButton variant="secondary">🌟 次要按钮</GlassButton>
      <GlassButton variant="danger">🚨 危险按钮</GlassButton>
      <GlassButton variant="success">✅ 成功按钮</GlassButton>
      <GlassButton variant="warning">⚠️ 警告按钮</GlassButton>
      <GlassButton variant="ghost">👻 幽灵按钮</GlassButton>
    </div>
  ),
}

// 🎨 所有尺寸
export const Sizes: Story = {
  render: () => (
    <div className="flex flex-wrap items-center gap-4">
      <GlassButton size="xs">📦 超小</GlassButton>
      <GlassButton size="sm">📋 小型</GlassButton>
      <GlassButton size="md">📄 中等</GlassButton>
      <GlassButton size="lg">📊 大型</GlassButton>
      <GlassButton size="xl">🎯 超大</GlassButton>
    </div>
  ),
}

// 🎨 带图标的按钮
export const WithIcons: Story = {
  render: () => (
    <div className="flex flex-wrap gap-4">
      <GlassButton 
        leftIcon={
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
          </svg>
        }
      >
        ➕ 添加
      </GlassButton>
      
      <GlassButton 
        rightIcon={
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
          </svg>
        }
        variant="secondary"
      >
        继续 ➡️
      </GlassButton>
      
      <GlassButton 
        leftIcon={
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
          </svg>
        }
        variant="danger"
      >
        🗑️ 删除
      </GlassButton>
    </div>
  ),
}

// 🎨 加载状态
export const Loading: Story = {
  render: () => (
    <div className="flex flex-wrap gap-4">
      <GlassButton loading>🔄 加载中...</GlassButton>
      <GlassButton loading variant="secondary">🔄 处理中...</GlassButton>
      <GlassButton loading variant="success">🔄 保存中...</GlassButton>
    </div>
  ),
}

// 🎨 禁用状态
export const Disabled: Story = {
  render: () => (
    <div className="flex flex-wrap gap-4">
      <GlassButton disabled>🚫 禁用按钮</GlassButton>
      <GlassButton disabled variant="secondary">🚫 禁用次要</GlassButton>
      <GlassButton disabled variant="danger">🚫 禁用危险</GlassButton>
    </div>
  ),
}

// 🎨 全宽按钮
export const FullWidth: Story = {
  render: () => (
    <div className="w-80 space-y-4">
      <GlassButton fullWidth>📏 全宽主要按钮</GlassButton>
      <GlassButton fullWidth variant="secondary">📏 全宽次要按钮</GlassButton>
      <GlassButton fullWidth variant="success">📏 全宽成功按钮</GlassButton>
    </div>
  ),
}

// 🎨 按钮组
export const ButtonGroup: Story = {
  render: () => (
    <div className="space-y-6">
      {/* 水平按钮组 */}
      <div>
        <h4 className="text-glass-text-primary mb-3 font-medium">水平按钮组</h4>
        <div className="flex gap-2">
          <GlassButton size="sm">📝 编辑</GlassButton>
          <GlassButton size="sm" variant="secondary">👁️ 查看</GlassButton>
          <GlassButton size="sm" variant="danger">🗑️ 删除</GlassButton>
        </div>
      </div>
      
      {/* 垂直按钮组 */}
      <div>
        <h4 className="text-glass-text-primary mb-3 font-medium">垂直按钮组</h4>
        <div className="flex flex-col gap-2 w-48">
          <GlassButton>📊 仪表板</GlassButton>
          <GlassButton variant="secondary">👥 用户管理</GlassButton>
          <GlassButton variant="secondary">⚙️ 系统设置</GlassButton>
          <GlassButton variant="ghost">🚪 退出登录</GlassButton>
        </div>
      </div>
    </div>
  ),
}

// 🎨 交互示例
export const Interactive: Story = {
  render: () => {
    const handleClick = () => {
      alert('🎉 按钮被点击了！')
    }
    
    return (
      <div className="space-y-4">
        <GlassButton onClick={handleClick}>
          🎯 点击我试试
        </GlassButton>
        
        <GlassButton 
          variant="success"
          leftIcon={
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
            </svg>
          }
          onClick={() => alert('✅ 操作成功！')}
        >
          确认操作
        </GlassButton>
      </div>
    )
  },
}

// 🎨 响应式按钮
export const Responsive: Story = {
  parameters: {
    viewport: {
      defaultViewport: 'mobile',
    },
  },
  render: () => (
    <div className="space-y-4">
      <GlassButton fullWidth className="glass-mobile:text-sm">
        📱 响应式按钮
      </GlassButton>
      <p className="text-glass-text-secondary text-sm">
        在移动设备上，按钮会自动调整文字大小和内边距
      </p>
    </div>
  ),
}
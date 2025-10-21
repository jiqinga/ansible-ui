import type { Meta, StoryObj } from '@storybook/react'
import GlassCard from './GlassCard'

const meta: Meta<typeof GlassCard> = {
  title: '🎨 Glass UI/GlassCard',
  component: GlassCard,
  parameters: {
    layout: 'centered',
    docs: {
      description: {
        component: '🎨 玻璃态卡片组件 - 提供多种变体和动画效果的现代化卡片容器',
      },
    },
  },
  tags: ['autodocs'],
  argTypes: {
    variant: {
      control: 'select',
      options: ['primary', 'secondary', 'dark'],
      description: '卡片变体样式',
    },
    blur: {
      control: 'select',
      options: ['light', 'normal', 'strong'],
      description: '背景模糊强度',
    },
    padding: {
      control: 'select',
      options: ['none', 'sm', 'md', 'lg', 'xl'],
      description: '内边距大小',
    },
    rounded: {
      control: 'select',
      options: ['sm', 'md', 'lg', 'xl', 'full'],
      description: '圆角大小',
    },
    shadow: {
      control: 'select',
      options: ['none', 'sm', 'md', 'lg'],
      description: '阴影强度',
    },
    hover: {
      control: 'boolean',
      description: '是否启用悬浮效果',
    },
    border: {
      control: 'boolean',
      description: '是否显示边框',
    },
  },
}

export default meta
type Story = StoryObj<typeof meta>

// 🎨 基础卡片
export const Default: Story = {
  args: {
    children: (
      <div>
        <h3 className="text-xl font-semibold text-glass-text-primary mb-4">
          🎨 默认玻璃态卡片
        </h3>
        <p className="text-glass-text-secondary">
          这是一个基础的玻璃态卡片组件，具有透明背景、模糊效果和柔和的阴影。
          支持多种变体和自定义配置选项。
        </p>
      </div>
    ),
  },
}

// 🎨 主要变体
export const Primary: Story = {
  args: {
    variant: 'primary',
    children: (
      <div>
        <h3 className="text-xl font-semibold text-glass-text-primary mb-4">
          ✨ 主要变体
        </h3>
        <p className="text-glass-text-secondary">
          主要变体使用较高的透明度，适合作为主要内容容器。
        </p>
      </div>
    ),
  },
}

// 🎨 次要变体
export const Secondary: Story = {
  args: {
    variant: 'secondary',
    children: (
      <div>
        <h3 className="text-xl font-semibold text-glass-text-primary mb-4">
          🌟 次要变体
        </h3>
        <p className="text-glass-text-secondary">
          次要变体使用较低的透明度，适合作为辅助内容容器。
        </p>
      </div>
    ),
  },
}

// 🎨 深色变体
export const Dark: Story = {
  args: {
    variant: 'dark',
    children: (
      <div>
        <h3 className="text-xl font-semibold text-glass-text-white mb-4">
          🌙 深色变体
        </h3>
        <p className="text-glass-text-white/80">
          深色变体使用最低的透明度，适合在明亮背景上使用。
        </p>
      </div>
    ),
  },
}

// 🎨 不同模糊效果
export const BlurEffects: Story = {
  render: () => (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
      <GlassCard blur="light" padding="lg">
        <h4 className="font-semibold text-glass-text-primary mb-2">💨 轻度模糊</h4>
        <p className="text-glass-text-secondary text-sm">适合需要更清晰背景的场景</p>
      </GlassCard>
      
      <GlassCard blur="normal" padding="lg">
        <h4 className="font-semibold text-glass-text-primary mb-2">🌊 标准模糊</h4>
        <p className="text-glass-text-secondary text-sm">平衡的玻璃态效果</p>
      </GlassCard>
      
      <GlassCard blur="strong" padding="lg">
        <h4 className="font-semibold text-glass-text-primary mb-2">🌀 强度模糊</h4>
        <p className="text-glass-text-secondary text-sm">更强的玻璃态效果</p>
      </GlassCard>
    </div>
  ),
}

// 🎨 不同尺寸
export const Sizes: Story = {
  render: () => (
    <div className="space-y-4">
      <GlassCard padding="sm">
        <p className="text-glass-text-primary">📦 小尺寸卡片</p>
      </GlassCard>
      
      <GlassCard padding="md">
        <p className="text-glass-text-primary">📋 中等尺寸卡片</p>
      </GlassCard>
      
      <GlassCard padding="lg">
        <p className="text-glass-text-primary">📄 大尺寸卡片</p>
      </GlassCard>
      
      <GlassCard padding="xl">
        <p className="text-glass-text-primary">📊 超大尺寸卡片</p>
      </GlassCard>
    </div>
  ),
}

// 🎨 无悬浮效果
export const NoHover: Story = {
  args: {
    hover: false,
    children: (
      <div>
        <h3 className="text-xl font-semibold text-glass-text-primary mb-4">
          🚫 无悬浮效果
        </h3>
        <p className="text-glass-text-secondary">
          这个卡片禁用了悬浮动画效果，适合静态展示内容。
        </p>
      </div>
    ),
  },
}

// 🎨 复杂内容示例
export const ComplexContent: Story = {
  args: {
    children: (
      <div>
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-xl font-semibold text-glass-text-primary">
            📊 数据统计卡片
          </h3>
          <span className="px-3 py-1 bg-green-500/20 text-green-700 rounded-full text-sm">
            ✅ 活跃
          </span>
        </div>
        
        <div className="grid grid-cols-2 gap-4 mb-4">
          <div className="text-center">
            <div className="text-2xl font-bold text-glass-text-accent">1,234</div>
            <div className="text-sm text-glass-text-secondary">总用户</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-glass-text-accent">89%</div>
            <div className="text-sm text-glass-text-secondary">活跃率</div>
          </div>
        </div>
        
        <div className="flex gap-2">
          <button className="flex-1 px-4 py-2 bg-white/20 hover:bg-white/30 rounded-glass-sm 
                           text-glass-text-primary transition-colors">
            📈 查看详情
          </button>
          <button className="flex-1 px-4 py-2 bg-white/20 hover:bg-white/30 rounded-glass-sm 
                           text-glass-text-primary transition-colors">
            ⚙️ 设置
          </button>
        </div>
      </div>
    ),
  },
}

// 🎨 响应式示例
export const Responsive: Story = {
  parameters: {
    viewport: {
      defaultViewport: 'mobile',
    },
  },
  args: {
    children: (
      <div>
        <h3 className="text-lg md:text-xl font-semibold text-glass-text-primary mb-4">
          📱 响应式卡片
        </h3>
        <p className="text-sm md:text-base text-glass-text-secondary">
          这个卡片在移动设备上会自动调整样式，包括减少模糊效果和调整内边距。
          请尝试切换不同的视口大小来查看效果。
        </p>
      </div>
    ),
  },
}
import React from 'react'
import { motion } from 'framer-motion'
import GlassButton from '@/components/UI/GlassButton'
import GlassInput from '@/components/UI/GlassInput'
import GlassSelect from '@/components/UI/GlassSelect'
import GlassCard from '@/components/UI/GlassCard'

/**
 * 🧪 动画效果测试页面
 * 
 * 用于验证修复后的悬停效果是否清晰无模糊
 */
const AnimationTest: React.FC = () => {
  const testOptions = [
    { value: '1', label: '选项一' },
    { value: '2', label: '选项二' },
    { value: '3', label: '选项三' },
  ]

  return (
    <div className="min-h-screen p-8 space-y-8">
      <GlassCard>
        <h1 className="text-3xl font-bold text-glass-text-primary mb-4">
          🧪 动画效果测试页面
        </h1>
        <p className="text-glass-text-secondary mb-6">
          将鼠标悬停在各个元素上，检查文字是否清晰无模糊
        </p>
      </GlassCard>

      {/* 按钮测试 */}
      <GlassCard>
        <h2 className="text-2xl font-bold text-glass-text-primary mb-4">
          ✅ 按钮测试 (使用 Y 轴位移)
        </h2>
        <div className="flex flex-wrap gap-4">
          <GlassButton variant="primary">
            主要按钮 - 悬停测试文字清晰度
          </GlassButton>
          <GlassButton variant="secondary">
            次要按钮 - 悬停测试文字清晰度
          </GlassButton>
          <GlassButton variant="success">
            成功按钮 - 悬停测试文字清晰度
          </GlassButton>
          <GlassButton variant="danger">
            危险按钮 - 悬停测试文字清晰度
          </GlassButton>
        </div>
        <p className="mt-4 text-sm text-glass-text-secondary">
          ✅ 预期效果：悬停时按钮向上移动 2px，文字保持清晰
        </p>
      </GlassCard>

      {/* 输入框测试 */}
      <GlassCard>
        <h2 className="text-2xl font-bold text-glass-text-primary mb-4">
          ✅ 输入框测试 (无 scale 动画)
        </h2>
        <div className="space-y-4 max-w-md">
          <GlassInput
            label="测试输入框"
            placeholder="请输入文字测试清晰度"
          />
          <GlassInput
            label="带图标的输入框"
            placeholder="搜索..."
            leftIcon={
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
            }
          />
        </div>
        <p className="mt-4 text-sm text-glass-text-secondary">
          ✅ 预期效果：聚焦时显示边框高亮，文字保持清晰
        </p>
      </GlassCard>

      {/* 选择器测试 */}
      <GlassCard>
        <h2 className="text-2xl font-bold text-glass-text-primary mb-4">
          ✅ 选择器测试 (使用 X 轴位移)
        </h2>
        <div className="max-w-md">
          <GlassSelect
            label="测试选择器"
            options={testOptions}
            placeholder="请选择一个选项"
          />
        </div>
        <p className="mt-4 text-sm text-glass-text-secondary">
          ✅ 预期效果：选项悬停时向右移动 2px，文字保持清晰
        </p>
      </GlassCard>

      {/* 对比测试 */}
      <GlassCard>
        <h2 className="text-2xl font-bold text-glass-text-primary mb-4">
          🔍 对比测试
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* 错误示例 */}
          <div>
            <h3 className="text-lg font-semibold text-red-600 mb-3">
              ❌ 错误示例 (使用 scale)
            </h3>
            <motion.button
              className="glass-button px-6 py-3 text-base rounded-glass w-full"
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
            >
              悬停时文字会模糊 - Scale 1.05
            </motion.button>
            <p className="mt-2 text-sm text-red-600">
              ⚠️ 注意：悬停时文字会出现模糊
            </p>
          </div>

          {/* 正确示例 */}
          <div>
            <h3 className="text-lg font-semibold text-green-600 mb-3">
              ✅ 正确示例 (使用 Y 轴位移)
            </h3>
            <motion.button
              className="glass-button px-6 py-3 text-base rounded-glass w-full"
              whileHover={{ y: -2 }}
              whileTap={{ y: 0 }}
            >
              悬停时文字保持清晰 - TranslateY -2px
            </motion.button>
            <p className="mt-2 text-sm text-green-600">
              ✅ 文字始终保持清晰锐利
            </p>
          </div>
        </div>
      </GlassCard>

      {/* 卡片测试 */}
      <GlassCard>
        <h2 className="text-2xl font-bold text-glass-text-primary mb-4">
          ✅ 卡片测试 (使用 Y 轴位移)
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {[1, 2, 3].map((i) => (
            <motion.div
              key={i}
              className="glass-container p-6 cursor-pointer"
              whileHover={{ y: -4 }}
              whileTap={{ y: 0 }}
            >
              <h3 className="text-xl font-bold text-glass-text-primary mb-2">
                测试卡片 {i}
              </h3>
              <p className="text-glass-text-secondary">
                悬停测试文字清晰度
              </p>
              <div className="mt-4 text-sm text-glass-text-secondary">
                这是一段较长的文字，用于测试在悬停动画时是否会出现模糊现象。
              </div>
            </motion.div>
          ))}
        </div>
        <p className="mt-4 text-sm text-glass-text-secondary">
          ✅ 预期效果：悬停时卡片向上移动 4px，所有文字保持清晰
        </p>
      </GlassCard>

      {/* 图标按钮测试 */}
      <GlassCard>
        <h2 className="text-2xl font-bold text-glass-text-primary mb-4">
          ✅ 图标按钮测试 (使用透明度)
        </h2>
        <div className="flex gap-4">
          {[1, 2, 3, 4].map((i) => (
            <motion.button
              key={i}
              className="glass-button p-3 rounded-full"
              whileHover={{ opacity: 0.8 }}
              whileTap={{ opacity: 0.6 }}
            >
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
            </motion.button>
          ))}
        </div>
        <p className="mt-4 text-sm text-glass-text-secondary">
          ✅ 预期效果：悬停时透明度降低，图标保持清晰
        </p>
      </GlassCard>

      {/* 测试说明 */}
      <GlassCard>
        <h2 className="text-2xl font-bold text-glass-text-primary mb-4">
          📋 测试检查清单
        </h2>
        <div className="space-y-2 text-glass-text-secondary">
          <div className="flex items-start gap-2">
            <span className="text-green-500">✓</span>
            <span>悬停时文字是否清晰锐利（无模糊）</span>
          </div>
          <div className="flex items-start gap-2">
            <span className="text-green-500">✓</span>
            <span>动画是否流畅自然</span>
          </div>
          <div className="flex items-start gap-2">
            <span className="text-green-500">✓</span>
            <span>点击反馈是否明显</span>
          </div>
          <div className="flex items-start gap-2">
            <span className="text-green-500">✓</span>
            <span>不同浏览器是否表现一致</span>
          </div>
          <div className="flex items-start gap-2">
            <span className="text-green-500">✓</span>
            <span>不同缩放级别（100%, 125%, 150%）是否正常</span>
          </div>
        </div>
      </GlassCard>
    </div>
  )
}

export default AnimationTest

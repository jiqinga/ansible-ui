/**
 * 📊 玻璃态图表组件
 * 
 * 提供各种类型的图表展示，包括：
 * - 折线图
 * - 柱状图
 * - 饼图
 * - 环形图
 */

import React from 'react'
import { motion } from 'framer-motion'

// 📊 图表数据点接口
export interface ChartDataPoint {
  label: string
  value: number
  color?: string
  timestamp?: string
}

// 📈 折线图数据接口
export interface LineChartData {
  datasets: {
    label: string
    data: ChartDataPoint[]
    color: string
    fillColor?: string
  }[]
}

// 📊 柱状图数据接口
export interface BarChartData {
  labels: string[]
  datasets: {
    label: string
    data: number[]
    backgroundColor: string[]
    borderColor?: string[]
  }[]
}

// 🥧 饼图数据接口
export interface PieChartData {
  data: ChartDataPoint[]
  centerText?: string
}

// 📊 图表组件属性接口
interface GlassChartProps {
  type: 'line' | 'bar' | 'pie' | 'doughnut'
  data: LineChartData | BarChartData | PieChartData
  title?: string
  height?: number
  className?: string
  showLegend?: boolean
  showGrid?: boolean
  animated?: boolean
}

/**
 * 📈 简单折线图组件
 */
const SimpleLineChart: React.FC<{
  data: LineChartData
  height: number
  showGrid: boolean
  animated: boolean
}> = ({ data, height, showGrid, animated }) => {
  // 检查是否有数据
  const hasData = data.datasets.some(dataset => dataset.data.length > 0)
  
  if (!hasData) {
    return (
      <div className="relative flex items-center justify-center" style={{ height }}>
        <div className="text-center text-gray-400">
          <svg className="w-16 h-16 mx-auto mb-2 opacity-50" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
          </svg>
          <p className="text-sm">暂无数据</p>
        </div>
      </div>
    )
  }
  
  const allValues = data.datasets.flatMap(dataset => dataset.data.map(point => point.value))
  const maxValue = Math.max(...allValues, 1) // 至少为1避免除零
  const minValue = Math.min(...allValues, 0)
  const range = maxValue - minValue || 1

  // 生成SVG路径
  const generatePath = (points: ChartDataPoint[]) => {
    if (points.length === 0) return ''
    if (points.length === 1) {
      // 单点数据，绘制一个小圆圈
      const y = ((maxValue - points[0].value) / range) * 80 + 10
      return `M 50 ${y}`
    }
    
    const width = 100 // 使用百分比
    const stepX = width / (points.length - 1)
    
    return points
      .map((point, index) => {
        const x = index * stepX
        const y = ((maxValue - point.value) / range) * 80 + 10 // 10% 边距
        return `${index === 0 ? 'M' : 'L'} ${x} ${y}`
      })
      .join(' ')
  }

  return (
    <div className="relative" style={{ height }}>
      <svg
        viewBox="0 0 100 100"
        className="w-full h-full"
        preserveAspectRatio="none"
      >
        {/* 网格线 */}
        {showGrid && (
          <g className="opacity-20">
            {[0, 25, 50, 75, 100].map(y => (
              <line
                key={y}
                x1="0"
                y1={y}
                x2="100"
                y2={y}
                stroke="currentColor"
                strokeWidth="0.2"
              />
            ))}
            {data.datasets[0]?.data.length > 1 && data.datasets[0].data.map((_, index) => {
              const x = (index / (data.datasets[0].data.length - 1)) * 100
              return (
                <line
                  key={index}
                  x1={x}
                  y1="0"
                  x2={x}
                  y2="100"
                  stroke="currentColor"
                  strokeWidth="0.2"
                />
              )
            })}
          </g>
        )}

        {/* 数据线 */}
        {data.datasets.map((dataset, datasetIndex) => {
          if (dataset.data.length === 0) return null
          
          const path = generatePath(dataset.data)
          const fillPath = dataset.data.length > 1 ? path + ` L 100 90 L 0 90 Z` : ''
          
          return (
            <g key={datasetIndex}>
              {/* 填充区域 */}
              {dataset.fillColor && fillPath && (
                <motion.path
                  d={fillPath}
                  fill={dataset.fillColor}
                  fillOpacity={0.2}
                  initial={animated ? { pathLength: 0 } : undefined}
                  animate={animated ? { pathLength: 1 } : undefined}
                  transition={{ duration: 1.5, delay: datasetIndex * 0.2 }}
                />
              )}
              
              {/* 线条 */}
              {dataset.data.length > 1 && (
                <motion.path
                  d={path}
                  fill="none"
                  stroke={dataset.color}
                  strokeWidth="2"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  initial={animated ? { pathLength: 0 } : undefined}
                  animate={animated ? { pathLength: 1 } : undefined}
                  transition={{ duration: 1.5, delay: datasetIndex * 0.2 }}
                />
              )}
              
              {/* 数据点 */}
              {dataset.data.map((point, pointIndex) => {
                const x = dataset.data.length > 1 
                  ? (pointIndex / (dataset.data.length - 1)) * 100 
                  : 50
                const y = ((maxValue - point.value) / range) * 80 + 10
                
                return (
                  <motion.circle
                    key={pointIndex}
                    cx={x}
                    cy={y}
                    r="1.5"
                    fill={dataset.color}
                    initial={animated ? { opacity: 0 } : undefined}
                    animate={animated ? { opacity: 1 } : undefined}
                    transition={{ 
                      duration: 0.3, 
                      delay: animated ? 1.5 + pointIndex * 0.1 : 0 
                    }}
                  />
                )
              })}
            </g>
          )
        })}
      </svg>
      
      {/* Y轴标签 */}
      <div className="absolute left-0 top-0 h-full flex flex-col justify-between text-xs text-gray-500 -ml-8">
        <span>{maxValue.toFixed(0)}</span>
        <span>{((maxValue + minValue) / 2).toFixed(0)}</span>
        <span>{minValue.toFixed(0)}</span>
      </div>
    </div>
  )
}

/**
 * 📊 简单柱状图组件
 */
const SimpleBarChart: React.FC<{
  data: BarChartData
  height: number
  animated: boolean
}> = ({ data, height, animated }) => {
  // 检查是否有数据
  const hasData = data.labels.length > 0 && data.datasets.some(dataset => dataset.data.length > 0)
  
  if (!hasData) {
    return (
      <div className="relative flex items-center justify-center" style={{ height }}>
        <div className="text-center text-gray-400">
          <svg className="w-16 h-16 mx-auto mb-2 opacity-50" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
          </svg>
          <p className="text-sm">暂无数据</p>
        </div>
      </div>
    )
  }
  
  const allValues = data.datasets.flatMap(dataset => dataset.data)
  const maxValue = Math.max(...allValues, 1) // 至少为1避免除零

  return (
    <div className="flex items-end justify-between h-full space-x-1" style={{ height }}>
      {data.labels.map((label, index) => (
        <div key={index} className="flex-1 flex flex-col items-center">
          <div className="flex-1 flex items-end justify-center w-full">
            {data.datasets.map((dataset, datasetIndex) => {
              const value = dataset.data[index] || 0
              const heightPercent = maxValue > 0 ? (value / maxValue) * 100 : 0
              const backgroundColor = dataset.backgroundColor[index] || dataset.backgroundColor[0]
              
              return (
                <motion.div
                  key={datasetIndex}
                  className="flex-1 mx-0.5 rounded-t-sm"
                  style={{ backgroundColor }}
                  initial={animated ? { height: 0 } : { height: `${heightPercent}%` }}
                  animate={{ height: `${heightPercent}%` }}
                  transition={{ 
                    duration: 0.8, 
                    delay: animated ? index * 0.1 : 0,
                    ease: "easeOut"
                  }}
                />
              )
            })}
          </div>
          <div className="text-xs text-gray-600 mt-2 text-center truncate w-full">
            {label}
          </div>
        </div>
      ))}
    </div>
  )
}

/**
 * 🥧 简单饼图组件
 */
const SimplePieChart: React.FC<{
  data: PieChartData
  height: number
  animated: boolean
  isDoughnut?: boolean
}> = ({ data, height, animated, isDoughnut = false }) => {
  // 检查是否有数据
  const hasData = data.data.length > 0 && data.data.some(item => item.value > 0)
  
  if (!hasData) {
    return (
      <div className="relative flex items-center justify-center" style={{ height }}>
        <div className="text-center text-gray-400">
          <svg className="w-16 h-16 mx-auto mb-2 opacity-50" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 3.055A9.001 9.001 0 1020.945 13H11V3.055z" />
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20.488 9H15V3.512A9.025 9.025 0 0120.488 9z" />
          </svg>
          <p className="text-sm">暂无数据</p>
        </div>
      </div>
    )
  }
  
  const total = data.data.reduce((sum, item) => sum + item.value, 0)
  if (total === 0) {
    return (
      <div className="relative flex items-center justify-center" style={{ height }}>
        <div className="text-center text-gray-400">
          <p className="text-sm">暂无数据</p>
        </div>
      </div>
    )
  }
  
  let currentAngle = -90 // 从顶部开始

  const radius = 40
  const innerRadius = isDoughnut ? 20 : 0
  const centerX = 50
  const centerY = 50

  // 生成路径
  const generatePath = (startAngle: number, endAngle: number, outerRadius: number, innerRadius: number) => {
    const startAngleRad = (startAngle * Math.PI) / 180
    const endAngleRad = (endAngle * Math.PI) / 180
    
    const x1 = centerX + outerRadius * Math.cos(startAngleRad)
    const y1 = centerY + outerRadius * Math.sin(startAngleRad)
    const x2 = centerX + outerRadius * Math.cos(endAngleRad)
    const y2 = centerY + outerRadius * Math.sin(endAngleRad)
    
    const largeArcFlag = endAngle - startAngle <= 180 ? "0" : "1"
    
    if (innerRadius === 0) {
      // 饼图
      return `M ${centerX} ${centerY} L ${x1} ${y1} A ${outerRadius} ${outerRadius} 0 ${largeArcFlag} 1 ${x2} ${y2} Z`
    } else {
      // 环形图
      const x3 = centerX + innerRadius * Math.cos(endAngleRad)
      const y3 = centerY + innerRadius * Math.sin(endAngleRad)
      const x4 = centerX + innerRadius * Math.cos(startAngleRad)
      const y4 = centerY + innerRadius * Math.sin(startAngleRad)
      
      return `M ${x1} ${y1} A ${outerRadius} ${outerRadius} 0 ${largeArcFlag} 1 ${x2} ${y2} L ${x3} ${y3} A ${innerRadius} ${innerRadius} 0 ${largeArcFlag} 0 ${x4} ${y4} Z`
    }
  }

  return (
    <div className="relative flex items-center justify-center" style={{ height }}>
      <svg viewBox="0 0 100 100" className="w-full h-full max-w-xs max-h-xs">
        {data.data.map((item, index) => {
          if (item.value === 0) return null
          
          const angle = (item.value / total) * 360
          const startAngle = currentAngle
          const endAngle = currentAngle + angle
          
          currentAngle += angle
          
          const path = generatePath(startAngle, endAngle, radius, innerRadius)
          const color = item.color || `hsl(${(index * 360) / data.data.length}, 70%, 60%)`
          
          return (
            <motion.path
              key={index}
              d={path}
              fill={color}
              stroke="white"
              strokeWidth="0.5"
              initial={animated ? { pathLength: 0, opacity: 0 } : undefined}
              animate={animated ? { pathLength: 1, opacity: 1 } : undefined}
              transition={{ 
                duration: 0.8, 
                delay: animated ? index * 0.1 : 0,
                ease: "easeOut"
              }}
            />
          )
        })}
      </svg>
      
      {/* 中心文本 */}
      {isDoughnut && data.centerText && (
        <div className="absolute inset-0 flex items-center justify-center">
          <div className="text-center">
            <div className="text-lg font-bold text-gray-800">{data.centerText}</div>
          </div>
        </div>
      )}
    </div>
  )
}

/**
 * 📊 主图表组件
 */
export const GlassChart: React.FC<GlassChartProps> = ({
  type,
  data,
  title,
  height = 300,
  className = '',
  showLegend = true,
  showGrid = true,
  animated = true
}) => {
  const renderChart = () => {
    switch (type) {
      case 'line':
        return (
          <SimpleLineChart
            data={data as LineChartData}
            height={height - (title ? 40 : 0) - (showLegend ? 40 : 0)}
            showGrid={showGrid}
            animated={animated}
          />
        )
      case 'bar':
        return (
          <SimpleBarChart
            data={data as BarChartData}
            height={height - (title ? 40 : 0) - (showLegend ? 40 : 0)}
            animated={animated}
          />
        )
      case 'pie':
        return (
          <SimplePieChart
            data={data as PieChartData}
            height={height - (title ? 40 : 0) - (showLegend ? 40 : 0)}
            animated={animated}
            isDoughnut={false}
          />
        )
      case 'doughnut':
        return (
          <SimplePieChart
            data={data as PieChartData}
            height={height - (title ? 40 : 0) - (showLegend ? 40 : 0)}
            animated={animated}
            isDoughnut={true}
          />
        )
      default:
        return <div>不支持的图表类型</div>
    }
  }

  const renderLegend = () => {
    if (!showLegend) return null

    let legendItems: { label: string; color: string }[] = []

    if (type === 'line') {
      const lineData = data as LineChartData
      legendItems = lineData.datasets.map(dataset => ({
        label: dataset.label,
        color: dataset.color
      }))
    } else if (type === 'bar') {
      const barData = data as BarChartData
      legendItems = barData.datasets.map((dataset) => ({
        label: dataset.label,
        color: dataset.backgroundColor[0] || '#3B82F6'
      }))
    } else if (type === 'pie' || type === 'doughnut') {
      const pieData = data as PieChartData
      legendItems = pieData.data.map((item, index) => ({
        label: item.label,
        color: item.color || `hsl(${(index * 360) / pieData.data.length}, 70%, 60%)`
      }))
    }

    return (
      <div className="flex flex-wrap justify-center gap-4 mt-4">
        {legendItems.map((item, index) => (
          <div key={index} className="flex items-center space-x-2">
            <div
              className="w-3 h-3 rounded-full"
              style={{ backgroundColor: item.color }}
            />
            <span className="text-sm text-gray-600">{item.label}</span>
          </div>
        ))}
      </div>
    )
  }

  return (
    <div className={`bg-white/25 backdrop-blur-sm rounded-xl border border-white/20 p-6 ${className}`}>
      {title && (
        <h3 className="text-lg font-semibold text-gray-800 mb-4 text-center">
          {title}
        </h3>
      )}
      
      <div className="relative">
        {renderChart()}
      </div>
      
      {renderLegend()}
    </div>
  )
}

export default GlassChart
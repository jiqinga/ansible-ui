import React, { useState } from 'react'
import { motion } from 'framer-motion'
import { cn } from '@/utils'

interface TableColumn<T = any> {
  key: string
  title: string
  dataIndex?: string
  width?: string | number
  align?: 'left' | 'center' | 'right'
  sortable?: boolean
  render?: (value: any, record: T, index: number) => React.ReactNode
  className?: string
}

interface GlassTableProps<T = any> {
  columns: TableColumn<T>[]
  data: T[]
  loading?: boolean
  empty?: React.ReactNode
  size?: 'sm' | 'md' | 'lg'
  striped?: boolean
  hoverable?: boolean
  bordered?: boolean
  sticky?: boolean
  pagination?: {
    current: number
    pageSize: number
    total: number
    onChange: (page: number, pageSize: number) => void
  }
  rowKey?: string | ((record: T) => string)
  onRow?: (record: T, index: number) => {
    onClick?: () => void
    onDoubleClick?: () => void
    className?: string
  }
  className?: string
  containerClassName?: string
}

type SortOrder = 'asc' | 'desc' | null

/**
 * 🎨 玻璃态表格组件
 * 
 * 功能：
 * - 排序支持
 * - 分页支持
 * - 加载状态
 * - 行点击事件
 * - 响应式设计
 */
const GlassTable = <T extends Record<string, any>>({
  columns,
  data,
  loading = false,
  empty,
  size = 'md',
  striped = false,
  hoverable = true,
  bordered = true,
  sticky = false,
  pagination,
  rowKey = 'id',
  onRow,
  className,
  containerClassName,
}: GlassTableProps<T>) => {
  const [sortColumn, setSortColumn] = useState<string | null>(null)
  const [sortOrder, setSortOrder] = useState<SortOrder>(null)

  // 🎨 尺寸样式映射
  const sizeStyles = {
    sm: 'text-sm',
    md: 'text-base',
    lg: 'text-lg',
  }

  const cellPaddingStyles = {
    sm: 'px-3 py-2',
    md: 'px-4 py-3',
    lg: 'px-6 py-4',
  }

  // 🎨 表格样式类
  const tableClasses = cn(
    'w-full',
    sizeStyles[size],
    className
  )

  // 🎨 容器样式类
  const containerClasses = cn(
    'bg-white/15 backdrop-blur-glass border border-white/20 rounded-glass overflow-hidden',
    bordered && 'border',
    containerClassName
  )

  // 🎨 获取行键
  const getRowKey = (record: T, index: number): string => {
    if (typeof rowKey === 'function') {
      return rowKey(record)
    }
    return record[rowKey] || index.toString()
  }

  // 🎨 获取单元格值
  const getCellValue = (record: T, column: TableColumn<T>) => {
    if (column.render) {
      const index = data.indexOf(record)
      return column.render(
        column.dataIndex ? record[column.dataIndex] : record,
        record,
        index
      )
    }
    return column.dataIndex ? record[column.dataIndex] : ''
  }

  // 🔄 处理排序
  const handleSort = (column: TableColumn<T>) => {
    if (!column.sortable) return

    let newSortOrder: SortOrder = 'asc'
    
    if (sortColumn === column.key) {
      if (sortOrder === 'asc') {
        newSortOrder = 'desc'
      } else if (sortOrder === 'desc') {
        newSortOrder = null
      }
    }

    setSortColumn(newSortOrder ? column.key : null)
    setSortOrder(newSortOrder)
  }

  // 📊 排序数据
  const sortedData = React.useMemo(() => {
    if (!sortColumn || !sortOrder) return data

    const column = columns.find(col => col.key === sortColumn)
    if (!column || !column.dataIndex) return data

    return [...data].sort((a, b) => {
      const aValue = a[column.dataIndex!]
      const bValue = b[column.dataIndex!]

      if (aValue === bValue) return 0

      const comparison = aValue > bValue ? 1 : -1
      return sortOrder === 'asc' ? comparison : -comparison
    })
  }, [data, sortColumn, sortOrder, columns])

  // 🎨 排序图标
  const SortIcon = ({ column }: { column: TableColumn<T> }) => {
    if (!column.sortable) return null

    const isActive = sortColumn === column.key
    
    return (
      <span className="ml-2 inline-flex flex-col">
        <motion.svg
          className={cn(
            'w-3 h-3 -mb-1',
            isActive && sortOrder === 'asc' 
              ? 'text-glass-text-accent' 
              : 'text-glass-text-secondary/50'
          )}
          fill="currentColor"
          viewBox="0 0 20 20"
          animate={{ scale: isActive && sortOrder === 'asc' ? 1.2 : 1 }}
        >
          <path fillRule="evenodd" d="M14.707 12.707a1 1 0 01-1.414 0L10 9.414l-3.293 3.293a1 1 0 01-1.414-1.414l4-4a1 1 0 011.414 0l4 4a1 1 0 010 1.414z" clipRule="evenodd" />
        </motion.svg>
        <motion.svg
          className={cn(
            'w-3 h-3',
            isActive && sortOrder === 'desc' 
              ? 'text-glass-text-accent' 
              : 'text-glass-text-secondary/50'
          )}
          fill="currentColor"
          viewBox="0 0 20 20"
          animate={{ scale: isActive && sortOrder === 'desc' ? 1.2 : 1 }}
        >
          <path fillRule="evenodd" d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z" clipRule="evenodd" />
        </motion.svg>
      </span>
    )
  }

  // 🎨 加载动画
  const LoadingSpinner = () => (
    <div className="flex justify-center items-center py-12">
      <motion.div
        className="w-8 h-8 border-2 border-glass-text-accent border-t-transparent rounded-full"
        animate={{ rotate: 360 }}
        transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
      />
      <span className="ml-3 text-glass-text-secondary">加载中...</span>
    </div>
  )

  // 🎨 空状态
  const EmptyState = () => (
    <div className="flex flex-col items-center justify-center py-12 text-glass-text-secondary">
      <svg className="w-16 h-16 mb-4 opacity-50" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
      </svg>
      {empty || <span>暂无数据</span>}
    </div>
  )

  return (
    <div className={containerClasses}>
      {/* 📊 表格容器 */}
      <div className="overflow-x-auto">
        <table className={tableClasses}>
          {/* 📋 表头 */}
          <thead className={cn(
            'bg-white/10 border-b border-white/10',
            sticky && 'sticky top-0 z-10'
          )}>
            <tr>
              {columns.map((column) => (
                <th
                  key={column.key}
                  className={cn(
                    cellPaddingStyles[size],
                    'font-semibold text-glass-text-primary',
                    `text-${column.align || 'left'}`,
                    column.sortable && 'cursor-pointer hover:bg-white/5 transition-colors',
                    column.className
                  )}
                  style={{ width: column.width }}
                  onClick={() => handleSort(column)}
                >
                  <div className="flex items-center justify-between">
                    <span>{column.title}</span>
                    <SortIcon column={column} />
                  </div>
                </th>
              ))}
            </tr>
          </thead>

          {/* 📄 表体 */}
          <tbody>
            {loading ? (
              <tr>
                <td colSpan={columns.length}>
                  <LoadingSpinner />
                </td>
              </tr>
            ) : sortedData.length === 0 ? (
              <tr>
                <td colSpan={columns.length}>
                  <EmptyState />
                </td>
              </tr>
            ) : (
              sortedData.map((record, index) => {
                const rowProps = onRow?.(record, index) || {}
                const key = getRowKey(record, index)
                
                return (
                  <motion.tr
                    key={key}
                    className={cn(
                      'border-b border-white/5 transition-colors',
                      striped && index % 2 === 1 && 'bg-white/5',
                      hoverable && 'hover:bg-white/10',
                      rowProps.onClick && 'cursor-pointer',
                      rowProps.className
                    )}
                    onClick={rowProps.onClick}
                    onDoubleClick={rowProps.onDoubleClick}
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.2, delay: index * 0.05 }}
                    whileHover={hoverable ? { x: 2 } : {}}
                  >
                    {columns.map((column) => (
                      <td
                        key={column.key}
                        className={cn(
                          cellPaddingStyles[size],
                          'text-glass-text-primary',
                          `text-${column.align || 'left'}`,
                          column.className
                        )}
                        style={{ width: column.width }}
                      >
                        {getCellValue(record, column)}
                      </td>
                    ))}
                  </motion.tr>
                )
              })
            )}
          </tbody>
        </table>
      </div>

      {/* 📄 分页 */}
      {pagination && (
        <div className="flex items-center justify-between px-6 py-4 border-t border-white/10">
          <div className="text-sm text-glass-text-secondary">
            共 {pagination.total} 条记录
          </div>
          
          <div className="flex items-center gap-2">
            <motion.button
              className="px-3 py-1 text-sm bg-white/10 hover:bg-white/20 
                       border border-white/20 rounded-glass-sm transition-colors
                       disabled:opacity-50 disabled:cursor-not-allowed"
              disabled={pagination.current <= 1}
              onClick={() => pagination.onChange(pagination.current - 1, pagination.pageSize)}
              whileHover={{ x: -2 }}
              whileTap={{ x: 0 }}
            >
              上一页
            </motion.button>
            
            <span className="px-3 py-1 text-sm text-glass-text-primary">
              {pagination.current} / {Math.ceil(pagination.total / pagination.pageSize)}
            </span>
            
            <motion.button
              className="px-3 py-1 text-sm bg-white/10 hover:bg-white/20 
                       border border-white/20 rounded-glass-sm transition-colors
                       disabled:opacity-50 disabled:cursor-not-allowed"
              disabled={pagination.current >= Math.ceil(pagination.total / pagination.pageSize)}
              onClick={() => pagination.onChange(pagination.current + 1, pagination.pageSize)}
              whileHover={{ x: 2 }}
              whileTap={{ x: 0 }}
            >
              下一页
            </motion.button>
          </div>
        </div>
      )}
    </div>
  )
}

export default GlassTable
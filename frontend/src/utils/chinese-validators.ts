/**
 * 🇨🇳 中文验证工具
 * 
 * 提供中文环境下的表单验证和错误消息
 */

/**
 * 📧 邮箱验证
 * @param email 邮箱地址
 * @returns 验证结果和中文错误消息
 */
export const validateEmail = (email: string): { isValid: boolean; message: string } => {
  if (!email) {
    return { isValid: false, message: '请输入邮箱地址' }
  }
  
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
  if (!emailRegex.test(email)) {
    return { isValid: false, message: '请输入有效的邮箱地址' }
  }
  
  return { isValid: true, message: '' }
}

/**
 * 📱 手机号验证（中国大陆）
 * @param phone 手机号码
 * @returns 验证结果和中文错误消息
 */
export const validatePhone = (phone: string): { isValid: boolean; message: string } => {
  if (!phone) {
    return { isValid: false, message: '请输入手机号码' }
  }
  
  // 中国大陆手机号正则表达式
  const phoneRegex = /^1[3-9]\d{9}$/
  if (!phoneRegex.test(phone)) {
    return { isValid: false, message: '请输入有效的手机号码' }
  }
  
  return { isValid: true, message: '' }
}

/**
 * 🔒 密码强度验证
 * @param password 密码
 * @param minLength 最小长度
 * @returns 验证结果和中文错误消息
 */
export const validatePassword = (
  password: string, 
  minLength: number = 8
): { isValid: boolean; message: string; strength: 'weak' | 'medium' | 'strong' } => {
  if (!password) {
    return { isValid: false, message: '请输入密码', strength: 'weak' }
  }
  
  if (password.length < minLength) {
    return { 
      isValid: false, 
      message: `密码长度至少需要 ${minLength} 位`, 
      strength: 'weak' 
    }
  }
  
  let strength: 'weak' | 'medium' | 'strong' = 'weak'
  let strengthScore = 0
  
  // 检查密码复杂度
  if (/[a-z]/.test(password)) strengthScore++ // 小写字母
  if (/[A-Z]/.test(password)) strengthScore++ // 大写字母
  if (/\d/.test(password)) strengthScore++    // 数字
  if (/[!@#$%^&*(),.?":{}|<>]/.test(password)) strengthScore++ // 特殊字符
  
  if (strengthScore >= 3) {
    strength = 'strong'
  } else if (strengthScore >= 2) {
    strength = 'medium'
  }
  
  if (strength === 'weak') {
    return { 
      isValid: false, 
      message: '密码强度太弱，请包含大小写字母、数字和特殊字符', 
      strength 
    }
  }
  
  return { isValid: true, message: '', strength }
}

/**
 * 🆔 身份证号验证（中国大陆）
 * @param idCard 身份证号
 * @returns 验证结果和中文错误消息
 */
export const validateIdCard = (idCard: string): { isValid: boolean; message: string } => {
  if (!idCard) {
    return { isValid: false, message: '请输入身份证号码' }
  }
  
  // 18位身份证号正则表达式
  const idCardRegex = /^[1-9]\d{5}(18|19|20)\d{2}((0[1-9])|(1[0-2]))(([0-2][1-9])|10|20|30|31)\d{3}[0-9Xx]$/
  
  if (!idCardRegex.test(idCard)) {
    return { isValid: false, message: '请输入有效的身份证号码' }
  }
  
  // 验证校验码
  const weights = [7, 9, 10, 5, 8, 4, 2, 1, 6, 3, 7, 9, 10, 5, 8, 4, 2]
  const checkCodes = ['1', '0', 'X', '9', '8', '7', '6', '5', '4', '3', '2']
  
  let sum = 0
  for (let i = 0; i < 17; i++) {
    sum += parseInt(idCard[i]) * weights[i]
  }
  
  const checkCode = checkCodes[sum % 11]
  if (checkCode !== idCard[17].toUpperCase()) {
    return { isValid: false, message: '身份证号码校验失败' }
  }
  
  return { isValid: true, message: '' }
}

/**
 * 🌐 IP地址验证
 * @param ip IP地址
 * @returns 验证结果和中文错误消息
 */
export const validateIP = (ip: string): { isValid: boolean; message: string } => {
  if (!ip) {
    return { isValid: false, message: '请输入IP地址' }
  }
  
  // IPv4 正则表达式
  const ipv4Regex = /^((25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$/
  
  if (!ipv4Regex.test(ip)) {
    return { isValid: false, message: '请输入有效的IP地址' }
  }
  
  return { isValid: true, message: '' }
}

/**
 * 🔌 端口号验证
 * @param port 端口号
 * @returns 验证结果和中文错误消息
 */
export const validatePort = (port: string | number): { isValid: boolean; message: string } => {
  if (!port && port !== 0) {
    return { isValid: false, message: '请输入端口号' }
  }
  
  const portNum = typeof port === 'string' ? parseInt(port, 10) : port
  
  if (isNaN(portNum)) {
    return { isValid: false, message: '端口号必须是数字' }
  }
  
  if (portNum < 1 || portNum > 65535) {
    return { isValid: false, message: '端口号必须在 1-65535 之间' }
  }
  
  return { isValid: true, message: '' }
}

/**
 * 📝 用户名验证
 * @param username 用户名
 * @param minLength 最小长度
 * @param maxLength 最大长度
 * @returns 验证结果和中文错误消息
 */
export const validateUsername = (
  username: string,
  minLength: number = 3,
  maxLength: number = 20
): { isValid: boolean; message: string } => {
  if (!username) {
    return { isValid: false, message: '请输入用户名' }
  }
  
  if (username.length < minLength) {
    return { isValid: false, message: `用户名长度至少需要 ${minLength} 位` }
  }
  
  if (username.length > maxLength) {
    return { isValid: false, message: `用户名长度不能超过 ${maxLength} 位` }
  }
  
  // 用户名只能包含字母、数字、下划线和中文
  const usernameRegex = /^[\u4e00-\u9fa5a-zA-Z0-9_]+$/
  if (!usernameRegex.test(username)) {
    return { isValid: false, message: '用户名只能包含中文、字母、数字和下划线' }
  }
  
  return { isValid: true, message: '' }
}

/**
 * 🌐 URL验证
 * @param url URL地址
 * @returns 验证结果和中文错误消息
 */
export const validateURL = (url: string): { isValid: boolean; message: string } => {
  if (!url) {
    return { isValid: false, message: '请输入URL地址' }
  }
  
  try {
    new URL(url)
    return { isValid: true, message: '' }
  } catch {
    return { isValid: false, message: '请输入有效的URL地址' }
  }
}

/**
 * 📄 文件名验证
 * @param filename 文件名
 * @returns 验证结果和中文错误消息
 */
export const validateFilename = (filename: string): { isValid: boolean; message: string } => {
  if (!filename) {
    return { isValid: false, message: '请输入文件名' }
  }
  
  // Windows和Linux都不允许的字符
  const invalidChars = /[<>:"/\\|?*]/
  if (invalidChars.test(filename)) {
    return { isValid: false, message: '文件名不能包含以下字符: < > : " / \\ | ? *' }
  }
  
  // 检查文件名长度
  if (filename.length > 255) {
    return { isValid: false, message: '文件名长度不能超过255个字符' }
  }
  
  // 检查是否为保留名称（Windows）
  const reservedNames = ['CON', 'PRN', 'AUX', 'NUL', 'COM1', 'COM2', 'COM3', 'COM4', 'COM5', 'COM6', 'COM7', 'COM8', 'COM9', 'LPT1', 'LPT2', 'LPT3', 'LPT4', 'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9']
  if (reservedNames.includes(filename.toUpperCase())) {
    return { isValid: false, message: '文件名不能使用系统保留名称' }
  }
  
  return { isValid: true, message: '' }
}

/**
 * 🔢 数字范围验证
 * @param value 数值
 * @param min 最小值
 * @param max 最大值
 * @returns 验证结果和中文错误消息
 */
export const validateNumberRange = (
  value: string | number,
  min?: number,
  max?: number
): { isValid: boolean; message: string } => {
  if (value === '' || value === null || value === undefined) {
    return { isValid: false, message: '请输入数值' }
  }
  
  const num = typeof value === 'string' ? parseFloat(value) : value
  
  if (isNaN(num)) {
    return { isValid: false, message: '请输入有效的数值' }
  }
  
  if (min !== undefined && num < min) {
    return { isValid: false, message: `数值不能小于 ${min}` }
  }
  
  if (max !== undefined && num > max) {
    return { isValid: false, message: `数值不能大于 ${max}` }
  }
  
  return { isValid: true, message: '' }
}

/**
 * 📝 必填字段验证
 * @param value 字段值
 * @param fieldName 字段名称
 * @returns 验证结果和中文错误消息
 */
export const validateRequired = (
  value: any,
  fieldName: string = '此字段'
): { isValid: boolean; message: string } => {
  if (value === null || value === undefined || value === '') {
    return { isValid: false, message: `${fieldName}不能为空` }
  }
  
  if (Array.isArray(value) && value.length === 0) {
    return { isValid: false, message: `请至少选择一个${fieldName}` }
  }
  
  return { isValid: true, message: '' }
}

/**
 * 📏 字符串长度验证
 * @param value 字符串值
 * @param minLength 最小长度
 * @param maxLength 最大长度
 * @param fieldName 字段名称
 * @returns 验证结果和中文错误消息
 */
export const validateLength = (
  value: string,
  minLength?: number,
  maxLength?: number,
  fieldName: string = '此字段'
): { isValid: boolean; message: string } => {
  if (!value) {
    return { isValid: false, message: `请输入${fieldName}` }
  }
  
  if (minLength !== undefined && value.length < minLength) {
    return { isValid: false, message: `${fieldName}长度至少需要 ${minLength} 位` }
  }
  
  if (maxLength !== undefined && value.length > maxLength) {
    return { isValid: false, message: `${fieldName}长度不能超过 ${maxLength} 位` }
  }
  
  return { isValid: true, message: '' }
}

/**
 * 🔄 确认密码验证
 * @param password 密码
 * @param confirmPassword 确认密码
 * @returns 验证结果和中文错误消息
 */
export const validatePasswordConfirm = (
  password: string,
  confirmPassword: string
): { isValid: boolean; message: string } => {
  if (!confirmPassword) {
    return { isValid: false, message: '请确认密码' }
  }
  
  if (password !== confirmPassword) {
    return { isValid: false, message: '两次输入的密码不一致' }
  }
  
  return { isValid: true, message: '' }
}

/**
 * 📅 日期验证
 * @param date 日期字符串
 * @param format 日期格式
 * @returns 验证结果和中文错误消息
 */
export const validateDate = (
  date: string,
  // format: string = 'YYYY-MM-DD' // 暂时不使用
): { isValid: boolean; message: string } => {
  if (!date) {
    return { isValid: false, message: '请选择日期' }
  }
  
  const dateObj = new Date(date)
  if (isNaN(dateObj.getTime())) {
    return { isValid: false, message: '请输入有效的日期' }
  }
  
  return { isValid: true, message: '' }
}

/**
 * 🎯 综合表单验证
 * @param formData 表单数据
 * @param rules 验证规则
 * @returns 验证结果
 */
export interface ValidationRule {
  required?: boolean
  minLength?: number
  maxLength?: number
  min?: number
  max?: number
  pattern?: RegExp
  custom?: (value: any) => { isValid: boolean; message: string }
  fieldName?: string
}

export interface ValidationRules {
  [key: string]: ValidationRule
}

export interface ValidationResult {
  isValid: boolean
  errors: { [key: string]: string }
}

export const validateForm = (
  formData: { [key: string]: any },
  rules: ValidationRules
): ValidationResult => {
  const errors: { [key: string]: string } = {}
  
  for (const [field, rule] of Object.entries(rules)) {
    const value = formData[field]
    const fieldName = rule.fieldName || field
    
    // 必填验证
    if (rule.required) {
      const requiredResult = validateRequired(value, fieldName)
      if (!requiredResult.isValid) {
        errors[field] = requiredResult.message
        continue
      }
    }
    
    // 如果字段为空且不是必填，跳过其他验证
    if (!value && !rule.required) {
      continue
    }
    
    // 长度验证
    if (typeof value === 'string' && (rule.minLength || rule.maxLength)) {
      const lengthResult = validateLength(value, rule.minLength, rule.maxLength, fieldName)
      if (!lengthResult.isValid) {
        errors[field] = lengthResult.message
        continue
      }
    }
    
    // 数值范围验证
    if (typeof value === 'number' && (rule.min !== undefined || rule.max !== undefined)) {
      const rangeResult = validateNumberRange(value, rule.min, rule.max)
      if (!rangeResult.isValid) {
        errors[field] = rangeResult.message
        continue
      }
    }
    
    // 正则表达式验证
    if (rule.pattern && typeof value === 'string') {
      if (!rule.pattern.test(value)) {
        errors[field] = `${fieldName}格式不正确`
        continue
      }
    }
    
    // 自定义验证
    if (rule.custom) {
      const customResult = rule.custom(value)
      if (!customResult.isValid) {
        errors[field] = customResult.message
        continue
      }
    }
  }
  
  return {
    isValid: Object.keys(errors).length === 0,
    errors
  }
}
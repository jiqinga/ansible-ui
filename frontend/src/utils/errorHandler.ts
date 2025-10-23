/**
 * 🛠️ 错误处理工具函数
 */

/**
 * 从API错误响应中提取错误信息
 * 
 * 支持多种错误响应格式：
 * 1. 统一错误格式: { error: { message: "..." } }
 * 2. 旧格式: { detail: "..." }
 * 3. 直接错误对象: { message: "..." }
 * 
 * @param err - 错误对象
 * @param defaultMessage - 默认错误信息
 * @returns 提取的错误信息
 */
export function extractErrorMessage(err: any, defaultMessage: string = '操作失败'): string {
  // 尝试从统一错误格式中提取
  if (err.response?.data?.error?.message) {
    return err.response.data.error.message;
  }
  
  // 尝试从旧格式中提取
  if (err.response?.data?.detail) {
    return err.response.data.detail;
  }
  
  // 尝试从错误对象中提取
  if (err.message) {
    return err.message;
  }
  
  // 返回默认信息
  return defaultMessage;
}

/**
 * 从API错误响应中提取详细错误信息
 * 
 * @param err - 错误对象
 * @returns 错误详情对象
 */
export function extractErrorDetails(err: any): {
  message: string;
  code?: string;
  details?: any;
  statusCode?: number;
} {
  const statusCode = err.response?.status;
  
  // 统一错误格式
  if (err.response?.data?.error) {
    const errorData = err.response.data.error;
    return {
      message: errorData.message || '操作失败',
      code: errorData.code,
      details: errorData.details,
      statusCode,
    };
  }
  
  // 旧格式
  if (err.response?.data?.detail) {
    return {
      message: err.response.data.detail,
      statusCode,
    };
  }
  
  // 默认
  return {
    message: err.message || '操作失败',
    statusCode,
  };
}

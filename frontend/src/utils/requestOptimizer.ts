/**
 * 请求优化工具
 * 
 * 提供请求防抖、缓存和批量处理功能
 */

interface CacheEntry<T> {
  data: T;
  timestamp: number;
  ttl: number;
}

interface PendingRequest<T> {
  promise: Promise<T>;
  timestamp: number;
}

/**
 * 请求缓存管理器
 */
class RequestCache {
  private cache: Map<string, CacheEntry<any>> = new Map();
  private pendingRequests: Map<string, PendingRequest<any>> = new Map();
  
  /**
   * 获取缓存数据
   */
  get<T>(key: string): T | null {
    const entry = this.cache.get(key);
    if (!entry) return null;
    
    const now = Date.now();
    if (now - entry.timestamp > entry.ttl) {
      this.cache.delete(key);
      return null;
    }
    
    return entry.data;
  }
  
  /**
   * 设置缓存数据
   */
  set<T>(key: string, data: T, ttl: number = 60000): void {
    this.cache.set(key, {
      data,
      timestamp: Date.now(),
      ttl
    });
  }
  
  /**
   * 清除缓存
   */
  clear(key?: string): void {
    if (key) {
      this.cache.delete(key);
    } else {
      this.cache.clear();
    }
  }
  
  /**
   * 获取或创建待处理请求
   */
  getPendingRequest<T>(key: string): Promise<T> | null {
    const pending = this.pendingRequests.get(key);
    if (!pending) return null;
    
    // 如果请求超过10秒，认为已失效
    const now = Date.now();
    if (now - pending.timestamp > 10000) {
      this.pendingRequests.delete(key);
      return null;
    }
    
    return pending.promise;
  }
  
  /**
   * 设置待处理请求
   */
  setPendingRequest<T>(key: string, promise: Promise<T>): void {
    this.pendingRequests.set(key, {
      promise,
      timestamp: Date.now()
    });
    
    // 请求完成后清除
    promise.finally(() => {
      this.pendingRequests.delete(key);
    });
  }
  
  /**
   * 清理过期缓存
   */
  cleanup(): void {
    const now = Date.now();
    
    // 清理过期缓存
    for (const [key, entry] of this.cache.entries()) {
      if (now - entry.timestamp > entry.ttl) {
        this.cache.delete(key);
      }
    }
    
    // 清理超时的待处理请求
    for (const [key, pending] of this.pendingRequests.entries()) {
      if (now - pending.timestamp > 10000) {
        this.pendingRequests.delete(key);
      }
    }
  }
}

// 全局缓存实例
const requestCache = new RequestCache();

// 定期清理缓存
setInterval(() => {
  requestCache.cleanup();
}, 60000); // 每分钟清理一次

/**
 * 防抖函数
 */
export function debounce<T extends (...args: any[]) => any>(
  func: T,
  wait: number = 300
): (...args: Parameters<T>) => void {
  let timeout: NodeJS.Timeout | null = null;
  
  return function(this: any, ...args: Parameters<T>) {
    const context = this;
    
    if (timeout) {
      clearTimeout(timeout);
    }
    
    timeout = setTimeout(() => {
      func.apply(context, args);
    }, wait);
  };
}

/**
 * 节流函数
 */
export function throttle<T extends (...args: any[]) => any>(
  func: T,
  wait: number = 300
): (...args: Parameters<T>) => void {
  let timeout: NodeJS.Timeout | null = null;
  let previous = 0;
  
  return function(this: any, ...args: Parameters<T>) {
    const context = this;
    const now = Date.now();
    
    if (!previous) previous = now;
    
    const remaining = wait - (now - previous);
    
    if (remaining <= 0 || remaining > wait) {
      if (timeout) {
        clearTimeout(timeout);
        timeout = null;
      }
      previous = now;
      func.apply(context, args);
    } else if (!timeout) {
      timeout = setTimeout(() => {
        previous = Date.now();
        timeout = null;
        func.apply(context, args);
      }, remaining);
    }
  };
}

/**
 * 带缓存的请求包装器
 */
export async function cachedRequest<T>(
  key: string,
  requestFn: () => Promise<T>,
  ttl: number = 60000
): Promise<T> {
  // 检查缓存
  const cached = requestCache.get<T>(key);
  if (cached !== null) {
    console.log(`✅ 缓存命中: ${key}`);
    return cached;
  }
  
  // 检查是否有相同的待处理请求
  const pending = requestCache.getPendingRequest<T>(key);
  if (pending) {
    console.log(`⏳ 复用待处理请求: ${key}`);
    return pending;
  }
  
  // 创建新请求
  console.log(`🔄 发起新请求: ${key}`);
  const promise = requestFn();
  requestCache.setPendingRequest(key, promise);
  
  try {
    const data = await promise;
    requestCache.set(key, data, ttl);
    return data;
  } catch (error) {
    // 请求失败不缓存
    throw error;
  }
}

/**
 * 批量请求合并器
 */
export class BatchRequestManager<K, V> {
  private queue: Map<K, Array<(value: V) => void>> = new Map();
  private timer: NodeJS.Timeout | null = null;
  private batchFn: (keys: K[]) => Promise<Map<K, V>>;
  private wait: number;
  
  constructor(batchFn: (keys: K[]) => Promise<Map<K, V>>, wait: number = 50) {
    this.batchFn = batchFn;
    this.wait = wait;
  }
  
  /**
   * 添加请求到批处理队列
   */
  request(key: K): Promise<V> {
    return new Promise((resolve) => {
      const callbacks = this.queue.get(key) || [];
      callbacks.push(resolve);
      this.queue.set(key, callbacks);
      
      // 设置批处理定时器
      if (!this.timer) {
        this.timer = setTimeout(() => {
          this.flush();
        }, this.wait);
      }
    });
  }
  
  /**
   * 执行批处理
   */
  private async flush(): Promise<void> {
    if (this.timer) {
      clearTimeout(this.timer);
      this.timer = null;
    }
    
    if (this.queue.size === 0) return;
    
    const keys = Array.from(this.queue.keys());
    const queue = new Map(this.queue);
    this.queue.clear();
    
    try {
      const results = await this.batchFn(keys);
      
      // 分发结果
      for (const [key, callbacks] of queue.entries()) {
        const value = results.get(key);
        if (value !== undefined) {
          callbacks.forEach(callback => callback(value));
        }
      }
    } catch (error) {
      console.error('批处理请求失败:', error);
    }
  }
}

/**
 * 请求重试包装器
 */
export async function retryRequest<T>(
  requestFn: () => Promise<T>,
  maxRetries: number = 3,
  delay: number = 1000
): Promise<T> {
  let lastError: Error | null = null;
  
  for (let i = 0; i < maxRetries; i++) {
    try {
      return await requestFn();
    } catch (error) {
      lastError = error as Error;
      
      if (i < maxRetries - 1) {
        console.log(`请求失败，${delay}ms后重试 (${i + 1}/${maxRetries})`);
        await new Promise(resolve => setTimeout(resolve, delay));
        delay *= 2; // 指数退避
      }
    }
  }
  
  throw lastError;
}

/**
 * 清除所有缓存
 */
export function clearAllCache(): void {
  requestCache.clear();
}

/**
 * 清除指定缓存
 */
export function clearCache(key: string): void {
  requestCache.clear(key);
}

export default {
  debounce,
  throttle,
  cachedRequest,
  BatchRequestManager,
  retryRequest,
  clearAllCache,
  clearCache
};

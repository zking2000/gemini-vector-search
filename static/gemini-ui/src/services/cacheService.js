/**
 * 缓存服务 - 用于缓存API响应结果，减少重复请求
 */

// 缓存对象，格式: { key: { data: any, timestamp: number } }
const cache = {};

// 缓存有效期（毫秒）
const DEFAULT_TTL = 5 * 60 * 1000; // 5分钟

/**
 * 设置缓存
 * @param {string} key - 缓存键
 * @param {*} data - 要缓存的数据
 * @param {number} ttl - 缓存有效期（毫秒）
 */
const setCache = (key, data, ttl = DEFAULT_TTL) => {
  cache[key] = {
    data,
    timestamp: Date.now(),
    ttl
  };
};

/**
 * 获取缓存
 * @param {string} key - 缓存键
 * @returns {*} 缓存的数据或null
 */
const getCache = (key) => {
  const cacheItem = cache[key];
  
  // 如果没有缓存项或缓存已过期，返回null
  if (!cacheItem || Date.now() - cacheItem.timestamp > cacheItem.ttl) {
    return null;
  }
  
  return cacheItem.data;
};

/**
 * 清除特定缓存项
 * @param {string} key - 缓存键
 */
const clearCache = (key) => {
  if (key in cache) {
    delete cache[key];
  }
};

/**
 * 清除所有缓存
 */
const clearAllCache = () => {
  Object.keys(cache).forEach(key => delete cache[key]);
};

/**
 * 清除包含特定前缀的所有缓存项
 * @param {string} prefix - 缓存键前缀
 */
const clearCacheByPrefix = (prefix) => {
  Object.keys(cache).forEach(key => {
    if (key.startsWith(prefix)) {
      delete cache[key];
    }
  });
};

export default {
  setCache,
  getCache,
  clearCache,
  clearAllCache,
  clearCacheByPrefix
}; 
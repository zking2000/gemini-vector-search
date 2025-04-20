/**
 * API服务
 */
import axios from 'axios';
import cacheService from './cacheService';

// 创建axios实例
const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json'
  }
});

// 响应拦截器 - 处理错误
apiClient.interceptors.response.use(
  response => response,
  error => {
    // 统一处理错误
    const errorMessage = error.response?.data?.detail || error.message || '未知错误';
    console.error('API错误:', errorMessage);
    
    return Promise.reject(error);
  }
);

/**
 * 发送GET请求（支持缓存）
 * @param {string} url - API路径
 * @param {Object} params - URL参数
 * @param {boolean} useCache - 是否使用缓存
 * @param {number} cacheTTL - 缓存有效期（毫秒）
 * @returns {Promise<any>} 响应数据
 */
const get = async (url, params = {}, useCache = false, cacheTTL) => {
  // 构建缓存键
  const cacheKey = `get:${url}:${JSON.stringify(params)}`;
  
  // 如果启用缓存，尝试从缓存获取数据
  if (useCache) {
    const cachedData = cacheService.getCache(cacheKey);
    if (cachedData) {
      return cachedData;
    }
  }
  
  // 发送请求
  const response = await apiClient.get(url, { params });
  
  // 如果启用缓存，将结果存入缓存
  if (useCache) {
    cacheService.setCache(cacheKey, response.data, cacheTTL);
  }
  
  return response.data;
};

/**
 * 发送POST请求
 * @param {string} url - API路径
 * @param {Object} data - 请求体数据
 * @param {Object} config - axios配置
 * @returns {Promise<any>} 响应数据
 */
const post = async (url, data = {}, config = {}) => {
  const response = await apiClient.post(url, data, config);
  return response.data;
};

/**
 * 发送PUT请求
 * @param {string} url - API路径
 * @param {Object} data - 请求体数据
 * @returns {Promise<any>} 响应数据
 */
const put = async (url, data = {}) => {
  const response = await apiClient.put(url, data);
  return response.data;
};

/**
 * 发送DELETE请求
 * @param {string} url - API路径
 * @param {Object} params - URL参数
 * @returns {Promise<any>} 响应数据
 */
const del = async (url, params = {}) => {
  const response = await apiClient.delete(url, { params });
  return response.data;
};

/**
 * 上传文件
 * @param {string} url - API路径
 * @param {FormData} formData - 包含文件的FormData
 * @param {Function} onProgress - 进度回调
 * @returns {Promise<any>} 响应数据
 */
const uploadFile = async (url, formData, onProgress) => {
  const response = await apiClient.post(url, formData, {
    headers: {
      'Content-Type': 'multipart/form-data'
    },
    onUploadProgress: progressEvent => {
      if (onProgress) {
        const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total);
        onProgress(percentCompleted);
      }
    }
  });
  
  return response.data;
};

// 在修改数据后清除相关缓存
const invalidateCache = (prefix) => {
  cacheService.clearCacheByPrefix(prefix);
};

export default {
  get,
  post,
  put,
  del,
  uploadFile,
  invalidateCache
}; 
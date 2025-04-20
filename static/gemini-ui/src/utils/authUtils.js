/**
 * 认证工具函数 - 提供认证相关的公共逻辑
 */
import { DEFAULTS } from '../constants';

/**
 * 从环境变量获取凭据对象
 * @returns {Object} 包含用户名和密码的对象
 */
export const getCredentialsFromEnv = () => {
  try {
    // 读取环境变量中的JSON格式凭据
    const credentialsStr = import.meta.env.VITE_AUTH_CREDENTIALS;
    
    if (credentialsStr) {
      // 尝试直接解析JSON字符串
      try {
        const credentials = JSON.parse(credentialsStr);
        return credentials;
      } catch (parseError) {
        // JSON解析失败，尝试替代方法
        console.error('JSON解析失败，尝试替代方法:', parseError);
        try {
          // 使用eval作为备选方案（通常应避免）
          // eslint-disable-next-line no-eval
          const credentials = eval(`(${credentialsStr})`);
          console.log('使用替代方法解析成功');
          return credentials;
        } catch (evalError) {
          console.error('替代解析方法也失败:', evalError);
        }
      }
    }
  } catch (error) {
    console.error('获取认证信息失败:', error);
  }
  
  // 默认凭据作为回退方案
  console.warn('使用默认凭据');
  return DEFAULTS.CREDENTIALS;
};

/**
 * 获取可用用户名列表
 * @returns {string[]} 用户名数组
 */
export const getAvailableUsernames = () => {
  const credentials = getCredentialsFromEnv();
  return Object.keys(credentials);
};

/**
 * 验证用户凭据
 * @param {string} username 用户名
 * @param {string} password 密码
 * @returns {boolean} 验证是否成功
 */
export const validateCredentials = (username, password) => {
  const credentials = getCredentialsFromEnv();
  return credentials[username] === password;
};

/**
 * 获取API基础URL
 * @returns {string} API基础URL
 */
export const getApiBaseUrl = () => {
  return import.meta.env.VITE_API_BASE_URL || DEFAULTS.API_BASE_URL;
};

/**
 * 获取应用标题
 * @returns {string} 应用标题
 */
export const getAppTitle = () => {
  return import.meta.env.VITE_APP_TITLE || DEFAULTS.APP_TITLE;
}; 
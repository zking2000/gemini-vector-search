import React, { createContext, useState, useContext, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { validateCredentials } from '../utils/authUtils';
import { STORAGE_KEYS } from '../constants';

const AuthContext = createContext(null);

// 从环境变量加载认证信息
const getCredentials = () => {
  try {
    // 读取环境变量中的JSON格式凭据
    const credentialsStr = import.meta.env.VITE_AUTH_CREDENTIALS;
    
    if (credentialsStr) {
      // 直接解析JSON字符串，不需要特殊处理
      try {
        const credentials = JSON.parse(credentialsStr);
        console.log('可用用户列表:', Object.keys(credentials));
        return credentials;
      } catch (parseError) {
        // 如果JSON解析失败，尝试将字符串作为对象计算
        console.error('JSON解析失败，尝试替代方法:', parseError);
        try {
          // 使用非标准的eval方法（在正常情况下应避免）
          // eslint-disable-next-line no-eval
          const credentials = eval(`(${credentialsStr})`);
          console.log('使用替代方法解析成功，可用用户列表:', Object.keys(credentials));
          return credentials;
        } catch (evalError) {
          console.error('替代解析方法也失败:', evalError);
        }
      }
    }
  } catch (error) {
    console.error('获取认证信息失败:', error);
  }
  
  // 如果环境变量不存在或解析失败，使用默认凭据
  console.warn('使用默认凭据');
  return {
    admin: 'Pa$$w0rd',
    user1: '123456',
    user2: 'password123'
  };
};

// 获取认证信息
const credentials = getCredentials();

export const AuthProvider = ({ children }) => {
  const { t } = useTranslation();
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  // 初始化时检查localStorage中是否有登录信息
  useEffect(() => {
    const storedUser = localStorage.getItem(STORAGE_KEYS.USER);
    if (storedUser) {
      try {
        setUser(JSON.parse(storedUser));
      } catch (e) {
        console.error('解析存储的用户信息失败:', e);
        localStorage.removeItem(STORAGE_KEYS.USER);
      }
    }
    setLoading(false);
  }, []);

  const login = (username, password) => {
    setError('');
    console.log('尝试登录:', username);
    
    // 验证用户凭据
    if (validateCredentials(username, password)) {
      console.log('登录成功');
      const userData = { username };
      setUser(userData);
      localStorage.setItem(STORAGE_KEYS.USER, JSON.stringify(userData));
      
      // 存储API认证信息
      localStorage.setItem(STORAGE_KEYS.API_USERNAME, username);
      localStorage.setItem(STORAGE_KEYS.API_PASSWORD, password);
      
      return true;
    } else {
      console.log('登录失败，密码不匹配');
      setError(t('auth.invalidCredentials'));
      return false;
    }
  };

  const logout = () => {
    setUser(null);
    localStorage.removeItem(STORAGE_KEYS.USER);
    localStorage.removeItem(STORAGE_KEYS.API_USERNAME);
    localStorage.removeItem(STORAGE_KEYS.API_PASSWORD);
  };

  const authContextValue = {
    user,
    loading,
    error,
    login,
    logout,
    isAuthenticated: !!user,
  };

  return (
    <AuthContext.Provider value={authContextValue}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}; 
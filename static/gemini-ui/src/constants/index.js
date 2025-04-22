/**
 * 应用常量
 */

// 本地存储键
export const STORAGE_KEYS = {
  USER: 'user',
  API_USERNAME: 'api_username',
  API_PASSWORD: 'api_password'
};

// API路径
export const API_PATHS = {
  HEALTH: '/api/v1/health',
  DOCUMENTS: '/api/v1/documents',
  EMBEDDING: '/api/v1/embedding',
  UPLOAD_PDF: '/api/v1/upload-pdf',
  QUERY: '/api/v1/query',
  COMPLETION: '/api/v1/completion',
  INTEGRATION: '/api/v1/integration',
};

// 路由路径
export const ROUTES = {
  HOME: '/',
  LOGIN: '/login',
  DOCUMENTS: '/documents',
  SEARCH: '/search',
  UPLOAD: '/upload',
  ASSISTANT: '/assistant',
  LOGIN_CHECK: '/login-check'
};

// 默认值
export const DEFAULTS = {
  API_BASE_URL: 'http://localhost:8000',
  APP_TITLE: 'Smart RAG Platform',
  CREDENTIALS: {
    admin: 'Pa$$w0rd',
    user1: '123456',
    user2: 'password123'
  }
}; 
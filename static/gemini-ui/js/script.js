// 全局变量和常量
const API_BASE_URL = window.location.origin;
const API_ROUTES = {
  auth: {
    login: '/api/v1/auth/login'
  },
  documents: {
    list: '/api/v1/documents',
    get: (id) => `/api/v1/documents/${id}`,
    delete: (id) => `/api/v1/documents/${id}`,
    upload: '/api/v1/upload-pdf',
    clear: '/api/v1/clear-alloydb'
  },
  chat: {
    integration: '/api/v1/integration',
    completion: '/api/v1/completion',
  },
  health: '/api/v1/health',
  dbStatus: '/api/v1/database-status'
};

// DOM 元素引用
const elements = {
  loadingIndicator: document.getElementById('loading-indicator'),
  authContainer: document.getElementById('auth-container'),
  appContainer: document.getElementById('app-container'),
  loginForm: document.getElementById('login-form'),
  logoutButton: document.getElementById('logout-button'),
  navItems: document.querySelectorAll('nav a'),
  pages: document.querySelectorAll('.page'),
  documentsList: document.getElementById('documents-list'),
  documentSearchInput: document.getElementById('document-search'),
  documentSearchButton: document.getElementById('search-button'),
  clearDbButton: document.getElementById('clear-db-button'),
  uploadForm: document.getElementById('upload-form'),
  fileInput: document.getElementById('file-input'),
  uploadContainer: document.getElementById('upload-container'),
  clearExistingCheckbox: document.getElementById('clear-existing'),
  chatForm: document.getElementById('chat-form'),
  chatInput: document.getElementById('chat-input'),
  chatMessages: document.getElementById('chat-messages'),
  modalDocumentDetails: document.getElementById('modal-document-details'),
  modalClose: document.querySelector('.modal-close'),
  alertsContainer: document.getElementById('alerts-container')
};

// 工具函数
function showLoading(message = '加载中...') {
  const loadingText = document.querySelector('.loading-text');
  if (loadingText) loadingText.textContent = message;
  elements.loadingIndicator.style.display = 'flex';
}

function hideLoading() {
  elements.loadingIndicator.style.display = 'none';
}

function showAlert(message, type = 'info', duration = 3000) {
  const alert = document.createElement('div');
  alert.className = `alert alert-${type}`;
  
  const icon = document.createElement('i');
  icon.className = `alert-icon fas fa-${type === 'success' ? 'check-circle' : type === 'error' ? 'exclamation-circle' : 'info-circle'}`;
  
  alert.appendChild(icon);
  alert.appendChild(document.createTextNode(' ' + message));
  
  elements.alertsContainer.appendChild(alert);
  
  setTimeout(() => {
    alert.style.opacity = '0';
    setTimeout(() => {
      elements.alertsContainer.removeChild(alert);
    }, 300);
  }, duration);
}

function navigateTo(pageId) {
  elements.navItems.forEach(item => {
    if (item.getAttribute('data-target') === pageId) {
      item.classList.add('active');
    } else {
      item.classList.remove('active');
    }
  });
  
  elements.pages.forEach(page => {
    if (page.id === pageId) {
      page.classList.add('active');
    } else {
      page.classList.remove('active');
    }
  });
  
  // 特定页面加载数据
  if (pageId === 'documents-page') {
    loadDocuments();
  }
}

function formatDate(dateString) {
  if (!dateString) return '未知日期';
  const date = new Date(dateString);
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  });
}

function truncateText(text, maxLength = 100) {
  if (!text || text.length <= maxLength) return text;
  return text.substring(0, maxLength) + '...';
}

// 认证相关功能
function checkAuth() {
  const credentials = getStoredCredentials();
  if (credentials) {
    showAppUI();
    // 验证凭据是否有效
    fetchWithAuth(API_ROUTES.health)
      .then(response => {
        if (!response.ok) {
          logout();
        }
      })
      .catch(() => logout());
  } else {
    showAuthUI();
  }
}

function login(username, password) {
  showLoading('登录中...');
  
  fetch(API_BASE_URL + API_ROUTES.dbStatus)
    .then(response => response.json())
    .then(data => {
      hideLoading();
      if (data.status === 'ok') {
        storeCredentials(username, password);
        showAppUI();
        navigateTo('chat-page');
        showAlert('登录成功', 'success');
      } else {
        showAlert('数据库连接失败，请稍后重试', 'error');
      }
    })
    .catch(error => {
      hideLoading();
      showAlert('连接服务器失败: ' + error.message, 'error');
    });
}

function logout() {
  clearStoredCredentials();
  showAuthUI();
}

function storeCredentials(username, password) {
  const credentials = btoa(`${username}:${password}`);
  localStorage.setItem('gemini_credentials', credentials);
}

function getStoredCredentials() {
  return localStorage.getItem('gemini_credentials');
}

function clearStoredCredentials() {
  localStorage.removeItem('gemini_credentials');
}

function showAuthUI() {
  elements.authContainer.style.display = 'flex';
  elements.appContainer.style.display = 'none';
}

function showAppUI() {
  elements.authContainer.style.display = 'none';
  elements.appContainer.style.display = 'flex';
}

// API 调用函数
async function fetchWithAuth(url, options = {}) {
  const credentials = getStoredCredentials();
  
  if (!credentials) {
    showAuthUI();
    throw new Error('未授权');
  }
  
  const headers = new Headers(options.headers || {});
  headers.append('Authorization', `Basic ${credentials}`);
  
  const config = {
    ...options,
    headers
  };
  
  try {
    const response = await fetch(API_BASE_URL + url, config);
    
    if (response.status === 401) {
      logout();
      throw new Error('授权失败');
    }
    
    return response;
  } catch (error) {
    console.error('API 请求错误:', error);
    showAlert('请求失败: ' + error.message, 'error');
    throw error;
  }
}

// 文档管理功能
async function loadDocuments(searchTerm = '') {
  showLoading('加载文档列表...');
  
  try {
    const url = searchTerm 
      ? `${API_ROUTES.documents.list}?search=${encodeURIComponent(searchTerm)}` 
      : API_ROUTES.documents.list;
    
    const response = await fetchWithAuth(url);
    const data = await response.json();
    
    renderDocumentsList(data.documents || []);
    hideLoading();
  } catch (error) {
    hideLoading();
    showAlert('加载文档失败', 'error');
  }
}

function renderDocumentsList(documents) {
  if (!elements.documentsList) return;
  
  elements.documentsList.innerHTML = '';
  
  if (documents.length === 0) {
    elements.documentsList.innerHTML = '<div class="empty-state">没有找到文档，请上传新文档。</div>';
    return;
  }
  
  documents.forEach(doc => {
    const docElement = document.createElement('div');
    docElement.className = 'document-item';
    
    let docTitle = doc.title || '未命名文档';
    if (doc.metadata && typeof doc.metadata === 'object' && doc.metadata.filename) {
      docTitle = doc.metadata.filename;
    }
    
    docElement.innerHTML = `
      <div class="document-icon" style="writing-mode: horizontal-tb !important; display: inline-block;">
        <i class="fas fa-file-pdf" style="writing-mode: horizontal-tb !important;"></i>
      </div>
      <div class="document-info" style="writing-mode: horizontal-tb !important; display: inline-block;">
        <div class="document-title" style="writing-mode: horizontal-tb !important; text-orientation: mixed !important; direction: ltr !important; display: block; white-space: nowrap;">${docTitle}</div>
        <div class="document-meta" style="writing-mode: horizontal-tb !important; text-orientation: mixed !important; direction: ltr !important; display: block;">
          <span style="writing-mode: horizontal-tb !important; display: block;">文档ID: ${doc.id}</span>
          <span style="writing-mode: horizontal-tb !important; display: block;">上传时间: ${formatDate(doc.created_at)}</span>
          <span style="writing-mode: horizontal-tb !important; display: block;">大小: ${doc.metadata && doc.metadata.size ? formatFileSize(doc.metadata.size) : '未知'}</span>
        </div>
      </div>
      <div class="document-actions" style="writing-mode: horizontal-tb !important; display: inline-block;">
        <button class="btn btn-text btn-icon view-document" data-id="${doc.id}" title="查看详情" style="writing-mode: horizontal-tb !important;">
          <i class="fas fa-eye" style="writing-mode: horizontal-tb !important;"></i>
        </button>
        <button class="btn btn-text btn-icon delete-document" data-id="${doc.id}" title="删除文档" style="writing-mode: horizontal-tb !important;">
          <i class="fas fa-trash" style="writing-mode: horizontal-tb !important;"></i>
        </button>
      </div>
    `;
    
    elements.documentsList.appendChild(docElement);
    
    // 添加事件监听器
    docElement.querySelector('.view-document').addEventListener('click', () => viewDocument(doc.id));
    docElement.querySelector('.delete-document').addEventListener('click', () => deleteDocument(doc.id));
  });
}

function formatFileSize(bytes) {
  if (!bytes) return '未知';
  const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
  if (bytes === 0) return '0 Byte';
  const i = parseInt(Math.floor(Math.log(bytes) / Math.log(1024)));
  return Math.round(bytes / Math.pow(1024, i), 2) + ' ' + sizes[i];
}

async function viewDocument(docId) {
  showLoading('加载文档详情...');
  
  try {
    const response = await fetchWithAuth(API_ROUTES.documents.get(docId));
    const document = await response.json();
    
    showDocumentDetails(document);
    hideLoading();
  } catch (error) {
    hideLoading();
    showAlert('加载文档详情失败', 'error');
  }
}

function showDocumentDetails(document) {
  const modal = elements.modalDocumentDetails;
  if (!modal) return;
  
  let docTitle = document.title || '未命名文档';
  let metadata = '';
  
  if (document.metadata) {
    try {
      const metaObj = typeof document.metadata === 'string' 
        ? JSON.parse(document.metadata) 
        : document.metadata;
      
      if (metaObj.filename) {
        docTitle = metaObj.filename;
      }
      
      metadata = `
        <div><strong>文件名:</strong> ${metaObj.filename || '未知'}</div>
        <div><strong>文件大小:</strong> ${formatFileSize(metaObj.size)}</div>
        <div><strong>页数:</strong> ${metaObj.pages || '未知'}</div>
        <div><strong>上传时间:</strong> ${formatDate(document.created_at)}</div>
      `;
    } catch (e) {
      metadata = `<div>元数据格式错误</div>`;
    }
  }
  
  modal.querySelector('.modal-title').textContent = docTitle;
  modal.querySelector('.modal-body').innerHTML = `
    <div class="document-detail">
      <h4>文档元数据</h4>
      <div class="document-metadata">
        ${metadata}
      </div>
      <h4>文档ID</h4>
      <div>${document.id}</div>
    </div>
  `;
  
  modal.style.display = 'flex';
}

async function deleteDocument(docId) {
  if (!confirm('确定要删除这个文档吗？此操作不可逆。')) {
    return;
  }
  
  showLoading('删除文档...');
  
  try {
    const response = await fetchWithAuth(API_ROUTES.documents.delete(docId), {
      method: 'DELETE'
    });
    
    if (response.ok) {
      hideLoading();
      showAlert('文档已成功删除', 'success');
      loadDocuments(); // 重新加载文档列表
    } else {
      const error = await response.json();
      throw new Error(error.detail || '删除失败');
    }
  } catch (error) {
    hideLoading();
    showAlert('删除文档失败: ' + error.message, 'error');
  }
}

// 清空数据库
function clearDatabase() {
  if (!confirm('确定要清空数据库吗？此操作将删除所有文档和嵌入，且无法恢复！')) return;
  
  showLoading();
  
  fetchWithAuth(`${API_ROUTES.documents.clear}?confirmation=confirm_clear_alloydb`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    }
  })
  .then(response => {
    if (response.ok) {
      return response.json();
    }
    throw new Error(`服务器响应错误: ${response.status}`);
  })
  .then(data => {
    showAlert('数据库已成功清空', 'success');
    // 重新加载文档列表
    loadDocuments();
  })
  .catch(error => {
    console.error('清空数据库时出错:', error);
    showAlert(`清空数据库失败: ${error.message}`, 'error');
  })
  .finally(hideLoading);
}

// 文档上传功能
function setupFileUpload() {
  if (elements.uploadContainer) {
    elements.uploadContainer.addEventListener('click', () => {
      elements.fileInput.click();
    });
  }
  
  if (elements.fileInput) {
    elements.fileInput.addEventListener('change', (e) => {
      if (e.target.files.length > 0) {
        const fileName = e.target.files[0].name;
        document.querySelector('.upload-text p').textContent = `已选择: ${fileName}`;
      }
    });
  }
}

async function uploadDocument(formData) {
  showLoading('上传文档中...');
  
  try {
    // 添加清除现有文档的选项
    if (elements.clearExistingCheckbox && elements.clearExistingCheckbox.checked) {
      formData.append('clear_existing', 'true');
    }
    
    const response = await fetchWithAuth(API_ROUTES.documents.upload, {
      method: 'POST',
      body: formData
    });
    
    const result = await response.json();
    
    hideLoading();
    
    if (response.ok) {
      showAlert('文档上传成功', 'success');
      // 重置表单
      if (elements.uploadForm) {
        elements.uploadForm.reset();
        document.querySelector('.upload-text p').textContent = '支持PDF格式，单文件最大20MB';
      }
      return result;
    } else {
      throw new Error(result.detail || '上传失败');
    }
  } catch (error) {
    hideLoading();
    showAlert('上传文档失败: ' + error.message, 'error');
    throw error;
  }
}

// 聊天功能
function renderMessage(content, isUser = false) {
  const messageDiv = document.createElement('div');
  messageDiv.className = `message message-${isUser ? 'user' : 'ai'}`;
  
  // 处理可能的换行符
  const formattedContent = content.replace(/\n/g, '<br>');
  messageDiv.innerHTML = formattedContent;
  
  elements.chatMessages.appendChild(messageDiv);
  elements.chatMessages.scrollTop = elements.chatMessages.scrollHeight;
}

async function sendChatMessage(message) {
  renderMessage(message, true);
  
  showLoading('思考中...');
  
  try {
    const response = await fetchWithAuth(API_ROUTES.chat.integration, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        prompt: message,
        context_query: message,
        use_context: true,
        max_context_docs: 10
      }),
      params: {
        debug: true
      }
    });
    
    const result = await response.json();
    hideLoading();
    
    if (response.ok && result.completion) {
      // 创建增强的回复内容
      let enhancedContent = result.completion;
      
      // 如果有调试信息和文档片段，添加引用信息
      if (result.debug_info && result.debug_info.document_snippets && result.debug_info.document_snippets.length > 0) {
        enhancedContent += '<hr style="margin: 15px 0; border-top: 1px dashed #ccc;">';
        enhancedContent += '<details class="document-reference" style="font-size: 0.9em; color: #666; writing-mode: horizontal-tb !important;">';
        enhancedContent += '<summary style="cursor: pointer; margin-bottom: 5px; writing-mode: horizontal-tb !important;"><b>参考文档</b> (点击展开)</summary>';
        
        result.debug_info.document_snippets.forEach((doc, index) => {
          const source = doc.source || `文档片段 #${index+1}`;
          const similarityPercentage = doc.similarity ? `${Math.round(doc.similarity * 100)}%` : '未知';
          const contentPreview = doc.content.substring(0, 100) + (doc.content.length > 100 ? '...' : '');
          
          enhancedContent += `<div class="document-card" style="writing-mode: horizontal-tb !important; display: flex !important; flex-direction: row !important;">`;
          enhancedContent += `<div class="document-info" style="display: flex !important; flex-direction: column !important; writing-mode: horizontal-tb !important;">
            <div class="document-header" style="width: 100%; display: flex !important; flex-direction: row !important; writing-mode: horizontal-tb !important;">
              <span class="document-title" style="display: inline-block !important; writing-mode: horizontal-tb !important; text-orientation: mixed !important; direction: ltr !important; max-width: 200px !important; overflow: hidden !important; text-overflow: ellipsis !important; white-space: nowrap !important;">${source}</span>
              <span class="similarity-badge" style="display: inline-block !important; writing-mode: horizontal-tb !important;">相似度: ${similarityPercentage}</span>
            </div>
            <div class="document-content" style="display: block !important; writing-mode: horizontal-tb !important;">${contentPreview}</div>
          </div>`;
          enhancedContent += `</div>`;
        });
        
        enhancedContent += '</details>';
      }
      
      renderMessage(enhancedContent);
    } else {
      renderMessage('抱歉，无法处理您的请求。请稍后再试。');
    }
  } catch (error) {
    hideLoading();
    showAlert('发送消息失败: ' + error.message, 'error');
    renderMessage('抱歉，我无法处理您的请求。请稍后再试。');
  }
}

// 事件监听器设置
function setupEventListeners() {
  // 导航事件
  elements.navItems.forEach(item => {
    item.addEventListener('click', (e) => {
      e.preventDefault();
      const targetPage = item.getAttribute('data-target');
      if (targetPage) {
        navigateTo(targetPage);
      }
    });
  });
  
  // 登录表单
  if (elements.loginForm) {
    elements.loginForm.addEventListener('submit', (e) => {
      e.preventDefault();
      const username = document.getElementById('username').value;
      const password = document.getElementById('password').value;
      login(username, password);
    });
  }
  
  // 登出按钮
  if (elements.logoutButton) {
    elements.logoutButton.addEventListener('click', (e) => {
      e.preventDefault();
      logout();
    });
  }
  
  // 文档搜索
  if (elements.documentSearchButton) {
    elements.documentSearchButton.addEventListener('click', () => {
      const searchTerm = elements.documentSearchInput.value.trim();
      loadDocuments(searchTerm);
    });
  }
  
  if (elements.documentSearchInput) {
    elements.documentSearchInput.addEventListener('keypress', (e) => {
      if (e.key === 'Enter') {
        const searchTerm = elements.documentSearchInput.value.trim();
        loadDocuments(searchTerm);
      }
    });
  }
  
  // 清空数据库
  if (elements.clearDbButton) {
    elements.clearDbButton.addEventListener('click', clearDatabase);
  }
  
  // 文档上传
  if (elements.uploadForm) {
    elements.uploadForm.addEventListener('submit', (e) => {
      e.preventDefault();
      
      const fileInput = document.getElementById('file-input');
      if (!fileInput.files || fileInput.files.length === 0) {
        showAlert('请选择一个文件上传', 'error');
        return;
      }
      
      const formData = new FormData();
      formData.append('file', fileInput.files[0]);
      
      uploadDocument(formData)
        .then(() => {
          navigateTo('documents-page'); // 上传成功后切换到文档页面
        })
        .catch(error => console.error('上传错误:', error));
    });
  }
  
  // 模态框关闭
  if (elements.modalClose) {
    elements.modalClose.addEventListener('click', () => {
      elements.modalDocumentDetails.style.display = 'none';
    });
    
    window.addEventListener('click', (e) => {
      if (e.target === elements.modalDocumentDetails) {
        elements.modalDocumentDetails.style.display = 'none';
      }
    });
  }
  
  // 聊天发送
  if (elements.chatForm) {
    elements.chatForm.addEventListener('submit', (e) => {
      e.preventDefault();
      
      const message = elements.chatInput.value.trim();
      if (!message) return;
      
      elements.chatInput.value = '';
      sendChatMessage(message);
    });
  }
}

// 应用初始化
function initApp() {
  // 检查认证状态
  checkAuth();
  
  // 设置事件监听器
  setupEventListeners();
  
  // 设置文件上传
  setupFileUpload();
  
  // 默认导航到聊天页面
  navigateTo('chat-page');
}

// 当DOM加载完成后初始化应用
document.addEventListener('DOMContentLoaded', initApp);
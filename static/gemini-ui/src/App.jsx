import React from 'react';
import { Routes, Route } from 'react-router-dom';
import { ConfigProvider } from 'antd';
import { AuthProvider } from './context/AuthContext';
import Login from './pages/Login';
import AppLayout from './components/AppLayout';
import PrivateRoute from './components/PrivateRoute';

// 导入页面组件
import Home from './pages/Home';
import DocumentList from './pages/DocumentList';
import QueryAssistant from './pages/QueryAssistant';
import UploadDocument from './pages/UploadDocument';
import DocumentSearch from './pages/DocumentSearch';

// 导入全局样式
import './index.css';

// 全局样式覆盖 - 强制所有元素水平显示
const globalStyles = `
  * {
    writing-mode: horizontal-tb !important;
    text-orientation: mixed !important;
    direction: ltr !important;
  }
  
  .ant-typography, 
  .ant-list-item-meta-title, 
  .ant-list-item-meta-description,
  .document-title,
  .document-content,
  .reference-item,
  .ant-badge-count,
  .document-reference *,
  .ant-list-item *,
  .ant-list-item-meta *,
  .ant-tooltip *,
  .ant-card * {
    writing-mode: horizontal-tb !important;
    text-orientation: mixed !important;
    word-break: break-word !important;
    text-align: left !important;
  }
  
  /* 专门处理Ant Design列表项标题 */
  .ant-list-item-meta-title {
    display: block !important;
  }
  
  /* 强制文档标题水平显示 */
  .document-card * {
    writing-mode: horizontal-tb !important;
    text-orientation: mixed !important;
  }
  
  /* 强制处理所有ID和数字显示 */
  [class*="id-"], 
  [class*="ID-"],
  div:contains("ID:"),
  span:contains("ID:") {
    writing-mode: horizontal-tb !important;
    text-orientation: mixed !important;
    direction: ltr !important;
  }
`;

// 主应用组件
const App = () => {
  return (
    <ConfigProvider
      theme={{
        token: {
          colorPrimary: '#1677ff',
        },
      }}
    >
      <style>{globalStyles}</style>
      <AuthProvider>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route 
            path="/*" 
            element={
              <PrivateRoute>
                <AppLayout />
              </PrivateRoute>
            } 
          />
        </Routes>
      </AuthProvider>
    </ConfigProvider>
  );
};

export default App; 
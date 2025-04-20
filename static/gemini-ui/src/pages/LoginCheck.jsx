import React, { useEffect, useState } from 'react';
import { Card, Typography, List, Button } from 'antd';
import axios from 'axios';
import { useAuth } from '../context/AuthContext';
import { getAvailableUsernames, getApiBaseUrl } from '../utils/authUtils';
import { STORAGE_KEYS, API_PATHS } from '../constants';

const { Title, Paragraph, Text } = Typography;

const LoginCheck = () => {
  const { user, isAuthenticated } = useAuth();
  const [apiStatus, setApiStatus] = useState({ tested: false, success: false, error: null });
  const [availableUsers, setAvailableUsers] = useState([]);
  
  useEffect(() => {
    // 获取可用用户列表
    setAvailableUsers(getAvailableUsernames());
  }, []);
  
  const testApiConnection = async () => {
    try {
      // 获取API基础URL
      const apiBaseUrl = getApiBaseUrl();
      
      // 测试API连接
      const response = await axios.get(
        `${apiBaseUrl}${API_PATHS.HEALTH}`
      );
      
      setApiStatus({
        tested: true,
        success: true,
        data: response.data
      });
    } catch (error) {
      setApiStatus({
        tested: true,
        success: false,
        error: error.message,
        details: error.response?.data
      });
    }
  };
  
  return (
    <Card title="登录状态检查">
      <Title level={3}>前端登录状态</Title>
      <List
        bordered
        dataSource={[
          { label: "已登录", value: isAuthenticated ? "是" : "否" },
          { label: "用户信息", value: user ? JSON.stringify(user) : "未登录" }
        ]}
        renderItem={item => (
          <List.Item>
            <Text strong>{item.label}:</Text> {item.value}
          </List.Item>
        )}
      />
      
      <Title level={3} style={{ marginTop: 20 }}>API测试</Title>
      <Button type="primary" onClick={testApiConnection} style={{ marginBottom: 16 }}>
        测试API连接
      </Button>
      
      {apiStatus.tested && (
        <Card type={apiStatus.success ? "success" : "error"} style={{ marginTop: 16 }}>
          <Paragraph>
            状态: {apiStatus.success ? "成功" : "失败"}
          </Paragraph>
          {apiStatus.success ? (
            <Paragraph>
              API响应: {JSON.stringify(apiStatus.data)}
            </Paragraph>
          ) : (
            <Paragraph>
              错误: {apiStatus.error}
              {apiStatus.details && (
                <div>
                  详情: {JSON.stringify(apiStatus.details)}
                </div>
              )}
            </Paragraph>
          )}
        </Card>
      )}
    </Card>
  );
};

export default LoginCheck; 
import React, { useState, useEffect } from 'react';
import { Form, Input, Button, Card, Typography, Alert, Checkbox, message } from 'antd';
import { UserOutlined, LockOutlined } from '@ant-design/icons';
import { useNavigate, useLocation } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { useAuth } from '../context/AuthContext';
import { getAvailableUsernames } from '../utils/authUtils';
import LanguageSwitcher from '../components/LanguageSwitcher';

const { Title, Paragraph } = Typography;

const Login = () => {
  const { t } = useTranslation();
  const { login, isAuthenticated, error } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [loading, setLoading] = useState(false);
  const [availableUsers, setAvailableUsers] = useState([]);

  // 获取用户想要访问的原始URL，如果没有则默认为首页
  const from = location.state?.from || '/';

  // 加载可用用户列表
  useEffect(() => {
    setAvailableUsers(getAvailableUsernames());
  }, []);

  useEffect(() => {
    // 如果已经登录，直接跳转到目标页面
    if (isAuthenticated) {
      navigate(from, { replace: true });
    }
  }, [isAuthenticated, navigate, from]);

  const onFinish = async (values) => {
    setLoading(true);
    const { username, password } = values;

    try {
      const success = login(username, password);
      if (success) {
        message.success(t('auth.welcomeBack'));
        navigate(from, { replace: true });
      }
    } catch (error) {
      console.error('登录失败:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ 
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      minHeight: '100vh',
      background: '#f0f2f5',
      padding: '0 20px'
    }}>
      <div style={{ position: 'absolute', top: 20, right: 20 }}>
        <LanguageSwitcher />
      </div>
      
      <Card 
        style={{ 
          width: '100%', 
          maxWidth: 400,
          boxShadow: '0 4px 12px rgba(0, 0, 0, 0.1)'
        }}
        bordered={false}
      >
        <div style={{ textAlign: 'center', marginBottom: 24 }}>
          <Title level={2} style={{ marginBottom: 8 }}>{t('auth.loginTitle')}</Title>
          <Paragraph type="secondary">{t('auth.loginSubtitle')}</Paragraph>
        </div>

        {error && (
          <Alert 
            message={error}
            type="error"
            showIcon
            style={{ marginBottom: 24 }}
          />
        )}

        <Form
          name="login"
          initialValues={{ remember: true }}
          onFinish={onFinish}
          size="large"
          layout="vertical"
        >
          <Form.Item
            name="username"
            rules={[{ required: true, message: t('auth.usernameRequired') }]}
          >
            <Input 
              prefix={<UserOutlined />} 
              placeholder={t('auth.username')} 
              autoComplete="username"
            />
          </Form.Item>

          <Form.Item
            name="password"
            rules={[{ required: true, message: t('auth.passwordRequired') }]}
          >
            <Input.Password 
              prefix={<LockOutlined />} 
              placeholder={t('auth.password')} 
              autoComplete="current-password"
            />
          </Form.Item>

          <Form.Item>
            <Form.Item name="remember" valuePropName="checked" noStyle>
              <Checkbox>{t('auth.rememberMe')}</Checkbox>
            </Form.Item>
          </Form.Item>

          <Form.Item>
            <Button 
              type="primary" 
              htmlType="submit" 
              style={{ width: '100%' }}
              loading={loading}
            >
              {t('auth.loginButton')}
            </Button>
          </Form.Item>
        </Form>
      </Card>
    </div>
  );
};

export default Login; 
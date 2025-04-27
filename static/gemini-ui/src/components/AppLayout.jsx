import React, { useEffect } from 'react';
import { Routes, Route, Link, useLocation } from 'react-router-dom';
import { Layout, Menu, theme, Dropdown, Avatar, Space, Button, Popconfirm } from 'antd';
import { 
  HomeOutlined, 
  FileSearchOutlined, 
  UploadOutlined, 
  QuestionCircleOutlined,
  DatabaseOutlined,
  UserOutlined,
  LogoutOutlined,
  BarChartOutlined
} from '@ant-design/icons';
import { useTranslation } from 'react-i18next';
import './MenuStyles.css'; // 引入自定义样式

// 语言切换组件
import LanguageSwitcher from './LanguageSwitcher';
import { useAuth } from '../context/AuthContext';

// 页面组件
import Home from '../pages/Home';
import DocumentSearch from '../pages/DocumentSearch';
import UploadDocument from '../pages/UploadDocument';
import QueryAssistant from '../pages/QueryAssistant';
import DocumentList from '../pages/DocumentList';
import LoginCheck from '../pages/LoginCheck';
import StrategyEvaluation from '../pages/StrategyEvaluation';

const { Header, Content, Footer } = Layout;

// 主应用布局组件
const AppLayout = () => {
  const { t } = useTranslation();
  const { user, logout } = useAuth();
  const location = useLocation();
  
  const {
    token: { colorBgContainer, borderRadiusLG },
  } = theme.useToken();

  // 根据当前路径确定选中的菜单项
  const getSelectedKey = () => {
    const path = location.pathname;
    if (path === '/') return '1';
    if (path.includes('/assistant')) return '4';
    if (path.includes('/upload')) return '3';
    if (path.includes('/documents')) return '2';
    if (path.includes('/strategy-evaluation')) return '5';
    return '1';
  };

  // 用户菜单项
  const userMenuItems = [
    {
      key: 'profile',
      icon: <UserOutlined />,
      label: user?.username,
    },
    {
      key: 'logout',
      icon: <LogoutOutlined />,
      label: (
        <Popconfirm
          title={t('auth.logoutConfirm')}
          onConfirm={logout}
          okText={t('common.confirm')}
          cancelText={t('common.cancel')}
        >
          {t('auth.logout')}
        </Popconfirm>
      ),
    }
  ];

  return (
    <Layout>
      <Header
        style={{
          position: 'sticky',
          top: 0,
          zIndex: 1,
          width: '100%',
          display: 'flex',
          alignItems: 'center',
          paddingLeft: '10px',
          paddingRight: '10px',
          overflow: 'visible'
        }}
      >
        <div className="logo" style={{ color: '#fff', fontWeight: 'bold', fontSize: '16px', marginRight: '15px', whiteSpace: 'nowrap' }}>
          {t('home.title')}
        </div>
        <Menu
          theme="dark"
          mode="horizontal"
          selectedKeys={[getSelectedKey()]}
          style={{
            flex: 1,
            minWidth: '600px',
            padding: '0 5px',
            gap: '0'
          }}
          items={[
            {
              key: '1',
              icon: <HomeOutlined />,
              label: <Link to="/" style={{ whiteSpace: 'nowrap', padding: '0 2px' }}>{t('nav.home')}</Link>,
            },
            {
              key: '4',
              icon: <QuestionCircleOutlined />,
              label: <Link to="/assistant" style={{ whiteSpace: 'nowrap', padding: '0 2px' }}>{t('nav.queryAssistant')}</Link>,
            },
            {
              key: '3',
              icon: <UploadOutlined />,
              label: <Link to="/upload" style={{ whiteSpace: 'nowrap', padding: '0 2px' }}>{t('nav.uploadDocument')}</Link>,
            },
            {
              key: '2',
              icon: <DatabaseOutlined />,
              label: <Link to="/documents" style={{ whiteSpace: 'nowrap', padding: '0 2px' }}>{t('nav.documentList')}</Link>,
            },
            {
              key: '5',
              icon: <BarChartOutlined />,
              label: <Link to="/strategy-evaluation" style={{ whiteSpace: 'nowrap', padding: '0 2px' }}>{t('nav.strategyEvaluation')}</Link>,
            }
          ]}
        />
        <div style={{ marginLeft: 'auto', display: 'flex', alignItems: 'center' }}>
          <LanguageSwitcher />
          <Dropdown 
            menu={{ items: userMenuItems }} 
            placement="bottomRight"
            arrow
          >
            <Button type="text" style={{ color: '#fff', marginLeft: 16 }}>
              <Space>
                <Avatar size="small" icon={<UserOutlined />} />
                {user?.username}
              </Space>
            </Button>
          </Dropdown>
        </div>
      </Header>
      <Content
        style={{
          padding: '0 50px',
        }}
      >
        <div
          style={{
            padding: 24,
            minHeight: 'calc(100vh - 180px)',
            background: colorBgContainer,
            borderRadius: borderRadiusLG,
            marginTop: 16,
          }}
        >
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/documents" element={<DocumentList />} />
            <Route path="/upload" element={<UploadDocument />} />
            <Route path="/assistant" element={<QueryAssistant />} />
            <Route path="/login-check" element={<LoginCheck />} />
            <Route path="/strategy-evaluation" element={<StrategyEvaluation />} />
          </Routes>
        </div>
      </Content>
      <Footer
        style={{
          textAlign: 'center',
        }}
      >
        {t('footer.copyright', { year: new Date().getFullYear() })}
      </Footer>
    </Layout>
  );
};

export default AppLayout; 
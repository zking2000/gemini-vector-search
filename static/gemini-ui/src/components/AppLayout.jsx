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
  LogoutOutlined
} from '@ant-design/icons';
import { useTranslation } from 'react-i18next';

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
    if (path.includes('/assistant')) return '5';
    if (path.includes('/upload')) return '4';
    if (path.includes('/documents')) return '2';
    if (path.includes('/search')) return '3';
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
        }}
      >
        <div className="logo" style={{ color: '#fff', fontWeight: 'bold', fontSize: '18px', marginRight: '30px' }}>
          {t('home.title')}
        </div>
        <Menu
          theme="dark"
          mode="horizontal"
          selectedKeys={[getSelectedKey()]}
          items={[
            {
              key: '1',
              icon: <HomeOutlined />,
              label: <Link to="/">{t('nav.home')}</Link>,
            },
            {
              key: '5',
              icon: <QuestionCircleOutlined />,
              label: <Link to="/assistant">{t('nav.queryAssistant')}</Link>,
            },
            {
              key: '4',
              icon: <UploadOutlined />,
              label: <Link to="/upload">{t('nav.uploadDocument')}</Link>,
            },
            {
              key: '2',
              icon: <DatabaseOutlined />,
              label: <Link to="/documents">{t('nav.documentList')}</Link>,
            },
            {
              key: '3',
              icon: <FileSearchOutlined />,
              label: <Link to="/search">{t('nav.documentSearch')}</Link>,
            },
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
            <Route path="/search" element={<DocumentSearch />} />
            <Route path="/upload" element={<UploadDocument />} />
            <Route path="/assistant" element={<QueryAssistant />} />
            <Route path="/login-check" element={<LoginCheck />} />
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
import React, { useState, useEffect } from 'react';
import { Row, Col, Card, Statistic, Button, Typography, Spin } from 'antd';
import { 
  FileTextOutlined, 
  SearchOutlined, 
  DatabaseOutlined, 
  RobotOutlined 
} from '@ant-design/icons';
import { Link } from 'react-router-dom';
import axios from 'axios';
import { useTranslation } from 'react-i18next';

const { Title, Paragraph } = Typography;

const Home = () => {
  const { t } = useTranslation();
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState({
    totalDocuments: 0,
    totalChunks: 0,
    lastUpdated: t('common.loading')
  });

  useEffect(() => {
    // 获取系统状态数据
    const fetchStats = async () => {
      try {
        const response = await axios.get('/api/v1/database-status');
        setStats({
          totalDocuments: response.data.total_sources || 0,
          totalChunks: response.data.total_documents || 0,
          lastUpdated: response.data.last_updated || t('common.noData')
        });
      } catch (error) {
        console.error('获取统计数据失败:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchStats();
  }, [t]);

  return (
    <div>
      <div style={{ textAlign: 'center', marginBottom: 40 }}>
        <Title level={2}>{t('home.title')}</Title>
        <Paragraph style={{ fontSize: 16 }}>
          {t('home.subtitle')}
        </Paragraph>
      </div>

      <Spin spinning={loading}>
        <Row gutter={[16, 16]}>
          <Col xs={24} sm={12} md={8}>
            <Card bordered={false} hoverable>
              <Statistic
                title={t('home.statsDocuments')}
                value={stats.totalDocuments}
                prefix={<FileTextOutlined />}
              />
            </Card>
          </Col>
          <Col xs={24} sm={12} md={8}>
            <Card bordered={false} hoverable>
              <Statistic
                title={t('home.statsChunks')}
                value={stats.totalChunks}
                prefix={<DatabaseOutlined />}
              />
            </Card>
          </Col>
          <Col xs={24} sm={12} md={8}>
            <Card bordered={false} hoverable>
              <Statistic
                title={t('home.statsUpdated')}
                value={stats.lastUpdated}
                prefix={<RobotOutlined />}
              />
            </Card>
          </Col>
        </Row>
      </Spin>

      <div style={{ marginTop: 40 }}>
        <Row gutter={[16, 16]}>
          <Col xs={24} sm={12} md={12}>
            <Card 
              title={t('home.cardSearchTitle')} 
              bordered={false} 
              hoverable 
              extra={<Link to="/search"><Button type="primary" icon={<SearchOutlined />}>{t('home.cardSearchBtn')}</Button></Link>}
            >
              <p>{t('home.cardSearchDesc')}</p>
            </Card>
          </Col>
          <Col xs={24} sm={12} md={12}>
            <Card 
              title={t('home.cardUploadTitle')} 
              bordered={false} 
              hoverable 
              extra={<Link to="/upload"><Button type="primary" icon={<SearchOutlined />}>{t('home.cardUploadBtn')}</Button></Link>}
            >
              <p>{t('home.cardUploadDesc')}</p>
            </Card>
          </Col>
          <Col xs={24} md={24}>
            <Card 
              title={t('home.cardAssistantTitle')} 
              bordered={false} 
              hoverable 
              extra={<Link to="/assistant"><Button type="primary" icon={<RobotOutlined />}>{t('home.cardAssistantBtn')}</Button></Link>}
            >
              <p>{t('home.cardAssistantDesc')}</p>
            </Card>
          </Col>
        </Row>
      </div>
    </div>
  );
};

export default Home; 
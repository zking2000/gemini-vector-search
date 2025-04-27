import React, { useState, useEffect } from 'react';
import { Row, Col, Card, Statistic, Typography, Spin } from 'antd';
import { 
  FileTextOutlined, 
  DatabaseOutlined, 
  RobotOutlined
} from '@ant-design/icons';
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
        // 获取数据库连接状态
        const dbStatusResponse = await axios.get('/api/v1/database-status');
        
        // 获取文档数量
        const docsResponse = await axios.get('/api/v1/documents', {
          params: { limit: 1, offset: 0 }
        });
        
        // 组合两个接口的数据
        setStats({
          totalDocuments: docsResponse.data.total || 0,
          totalChunks: docsResponse.data.documents?.length > 0 ? docsResponse.data.total * 3 : 0, // 估算文本块数量
          lastUpdated: dbStatusResponse.data.timestamp ? 
                       new Date(dbStatusResponse.data.timestamp).toLocaleString() : 
                       t('common.noData')
        });
      } catch (error) {
        console.error('获取统计数据失败:', error);
        setStats({
          totalDocuments: 0,
          totalChunks: 0,
          lastUpdated: t('common.noData')
        });
      } finally {
        setLoading(false);
      }
    };

    fetchStats();
  }, [t]);

  return (
    <div style={{ maxWidth: 1200, margin: '0 auto', padding: '40px 24px' }}>
      <div style={{ 
        textAlign: 'center', 
        marginBottom: 60,
        padding: '40px 0'
      }}>
        <Title 
          level={1} 
          style={{ 
            marginBottom: 24,
            fontSize: '3.5rem',
            fontWeight: 600,
            background: 'linear-gradient(135deg, #1890ff 0%, #722ed1 100%)',
            WebkitBackgroundClip: 'text',
            WebkitTextFillColor: 'transparent',
            letterSpacing: '-0.02em'
          }}
        >
          {t('home.title')}
        </Title>
        <Paragraph style={{ 
          fontSize: '1.25rem', 
          color: '#666',
          maxWidth: 800,
          margin: '0 auto',
          lineHeight: 1.6,
          fontWeight: 400
        }}>
          {t('home.subtitle')}
        </Paragraph>
      </div>

      <Spin spinning={loading}>
        <Row gutter={[32, 32]}>
          <Col xs={24} sm={12} md={8}>
            <Card 
              bordered={false} 
              hoverable 
              style={{ 
                height: '100%',
                boxShadow: '0 2px 8px rgba(0,0,0,0.06)',
                borderRadius: 8
              }}
            >
              <Statistic
                title={t('home.statsDocuments')}
                value={stats.totalDocuments}
                prefix={<FileTextOutlined style={{ color: '#1890ff' }} />}
                valueStyle={{ 
                  color: '#1890ff',
                  fontSize: 28,
                  fontWeight: 500
                }}
              />
            </Card>
          </Col>
          <Col xs={24} sm={12} md={8}>
            <Card 
              bordered={false} 
              hoverable 
              style={{ 
                height: '100%',
                boxShadow: '0 2px 8px rgba(0,0,0,0.06)',
                borderRadius: 8
              }}
            >
              <Statistic
                title={t('home.statsChunks')}
                value={stats.totalChunks}
                prefix={<DatabaseOutlined style={{ color: '#52c41a' }} />}
                valueStyle={{ 
                  color: '#52c41a',
                  fontSize: 28,
                  fontWeight: 500
                }}
              />
            </Card>
          </Col>
          <Col xs={24} sm={12} md={8}>
            <Card 
              bordered={false} 
              hoverable 
              style={{ 
                height: '100%',
                boxShadow: '0 2px 8px rgba(0,0,0,0.06)',
                borderRadius: 8
              }}
            >
              <Statistic
                title={t('home.statsUpdated')}
                value={stats.lastUpdated}
                prefix={<RobotOutlined style={{ color: '#722ed1' }} />}
                valueStyle={{ 
                  color: '#722ed1',
                  fontSize: 28,
                  fontWeight: 500
                }}
              />
            </Card>
          </Col>
        </Row>
      </Spin>
    </div>
  );
};

export default Home; 
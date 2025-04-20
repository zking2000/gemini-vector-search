import React, { useState } from 'react';
import { Input, Card, Button, List, Avatar, Spin, Typography, Row, Col, Select, Slider, Space, Alert, Empty } from 'antd';
import { SearchOutlined, FileTextOutlined } from '@ant-design/icons';
import axios from 'axios';

const { Search } = Input;
const { Title, Paragraph, Text } = Typography;
const { Option } = Select;

const DocumentSearch = () => {
  const [searchResults, setSearchResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [summary, setSummary] = useState('');
  const [query, setQuery] = useState('');
  const [resultsCount, setResultsCount] = useState(5);
  const [sources, setSources] = useState([]);
  const [selectedSource, setSelectedSource] = useState('all');
  const [errorMessage, setErrorMessage] = useState('');

  const fetchSources = async () => {
    try {
      const response = await axios.get('/api/v1/documents/sources');
      setSources(response.data.sources || []);
    } catch (error) {
      console.error('获取文档来源失败:', error);
    }
  };

  // 初始加载时获取文档来源列表
  React.useEffect(() => {
    fetchSources();
  }, []);

  const handleSearch = async (value) => {
    if (!value || value.trim() === '') {
      setErrorMessage('请输入搜索内容');
      return;
    }

    setQuery(value);
    setLoading(true);
    setSearchResults([]);
    setSummary('');
    setErrorMessage('');

    try {
      // 构建URL和参数
      let url = '/api/v1/query';
      let params = {};
      if (selectedSource && selectedSource !== 'all') {
        params.source_filter = selectedSource;
      }

      const response = await axios.post(url, {
        query: value,
        limit: resultsCount
      }, { params });

      if (response.data.results && response.data.results.length > 0) {
        setSearchResults(response.data.results);
        if (response.data.summary) {
          setSummary(response.data.summary);
        }
      } else {
        setSearchResults([]);
        setSummary('');
      }
    } catch (error) {
      console.error('搜索失败:', error);
      setErrorMessage('搜索失败，请稍后重试');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <Card title="文档搜索" bordered={false}>
        <Space direction="vertical" size="large" style={{ width: '100%' }}>
          <Row gutter={16}>
            <Col xs={24} sm={24} md={16}>
              <Search
                placeholder="输入搜索内容..."
                allowClear
                enterButton={<><SearchOutlined /> 搜索</>}
                size="large"
                onSearch={handleSearch}
                loading={loading}
              />
            </Col>
            <Col xs={24} sm={12} md={4}>
              <Select
                style={{ width: '100%' }}
                placeholder="选择文档来源"
                defaultValue="all"
                onChange={(value) => setSelectedSource(value)}
              >
                <Option value="all" style={{writingMode: 'horizontal-tb', textOrientation: 'mixed'}}>所有来源</Option>
                {sources.map((source) => (
                  <Option key={source} value={source} style={{writingMode: 'horizontal-tb', textOrientation: 'mixed'}}>
                    {source}
                  </Option>
                ))}
              </Select>
            </Col>
            <Col xs={24} sm={12} md={4}>
              <span>结果数量: {resultsCount}</span>
              <Slider
                min={1}
                max={20}
                defaultValue={5}
                onChange={(value) => setResultsCount(value)}
              />
            </Col>
          </Row>

          {errorMessage && (
            <Alert message={errorMessage} type="error" showIcon />
          )}

          {loading ? (
            <div style={{ textAlign: 'center', padding: '20px 0' }}>
              <Spin tip="搜索中..." />
            </div>
          ) : (
            <>
              {summary && (
                <Card type="inner" title="搜索结果摘要">
                  <Paragraph>{summary}</Paragraph>
                </Card>
              )}

              {searchResults.length > 0 ? (
                <List
                  itemLayout="vertical"
                  dataSource={searchResults}
                  renderItem={(item, index) => (
                    <List.Item
                      key={item.id || index}
                      extra={
                        item.similarity ? (
                          <div style={{writingMode: 'horizontal-tb', textOrientation: 'mixed', direction: 'ltr'}}>
                            <Text type="secondary" style={{writingMode: 'horizontal-tb'}}>相似度:</Text>
                            <Text strong style={{writingMode: 'horizontal-tb'}}> {(item.similarity * 100).toFixed(1)}%</Text>
                          </div>
                        ) : null
                      }
                    >
                      <List.Item.Meta
                        avatar={
                          <div style={{display: 'inline-block', writingMode: 'horizontal-tb', width: '32px', height: '32px', lineHeight: '32px', textAlign: 'center'}}>
                            <Avatar icon={<FileTextOutlined style={{writingMode: 'horizontal-tb'}} />} style={{writingMode: 'horizontal-tb'}} />
                          </div>
                        }
                        title={
                          <Space style={{display: 'flex', writingMode: 'horizontal-tb'}}>
                            <Text strong style={{display: 'inline-block', writingMode: 'horizontal-tb', textOrientation: 'mixed', direction: 'ltr'}}>来源: {item.metadata?.source || '未知'}</Text>
                            {item.metadata?.page && <Text type="secondary" style={{display: 'inline-block', writingMode: 'horizontal-tb'}}>页码: {item.metadata.page}</Text>}
                          </Space>
                        }
                        description={<Text style={{display: 'inline-block', writingMode: 'horizontal-tb', textOrientation: 'mixed', direction: 'ltr'}}>ID: {item.id}</Text>}
                      />
                      <div 
                        style={{ 
                          backgroundColor: '#f6f8fa', 
                          padding: 16, 
                          borderRadius: 4, 
                          marginTop: 12,
                          writingMode: 'horizontal-tb',
                          textOrientation: 'mixed',
                          direction: 'ltr'
                        }}
                      >
                        <Paragraph ellipsis={{ rows: 3, expandable: true, symbol: '展开' }} style={{writingMode: 'horizontal-tb', textOrientation: 'mixed', direction: 'ltr'}}>
                          {item.content}
                        </Paragraph>
                      </div>
                    </List.Item>
                  )}
                />
              ) : (
                query && !loading && (
                  <Empty description="未找到相关文档" />
                )
              )}
            </>
          )}
        </Space>
      </Card>
    </div>
  );
};

export default DocumentSearch; 
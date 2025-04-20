import React, { useState, useRef, useEffect } from 'react';
import { Input, Button, Card, Spin, Typography, Select, Switch, Space, Divider, List, Avatar, Empty, Alert, Badge } from 'antd';
import { SendOutlined, RobotOutlined, UserOutlined, FileTextOutlined, DeleteOutlined, InfoCircleOutlined } from '@ant-design/icons';
import axios from 'axios';

const { TextArea } = Input;
const { Title, Paragraph, Text } = Typography;
const { Option } = Select;

const QueryAssistant = () => {
  const [loading, setLoading] = useState(false);
  const [prompt, setPrompt] = useState('');
  const [conversations, setConversations] = useState([]);
  const [sources, setSources] = useState([]);
  const [selectedSource, setSelectedSource] = useState('all');
  const [useContext, setUseContext] = useState(true);
  const [maxContextDocs, setMaxContextDocs] = useState(5);
  const [forceUseDocuments, setForceUseDocuments] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');
  const bottomRef = useRef(null);

  // 获取文档来源列表
  useEffect(() => {
    const fetchSources = async () => {
      try {
        const response = await axios.get('/api/v1/documents/sources');
        setSources(response.data.sources || []);
      } catch (error) {
        console.error('获取文档来源失败:', error);
      }
    };

    fetchSources();
  }, []);

  // 自动滚动到底部
  useEffect(() => {
    if (bottomRef.current) {
      bottomRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [conversations]);

  const handleSend = async () => {
    if (!prompt.trim()) {
      return;
    }

    // 添加用户问题到对话列表
    const userMessage = {
      role: 'user',
      content: prompt,
      timestamp: new Date().toISOString()
    };
    
    setConversations(prev => [...prev, userMessage]);
    setLoading(true);
    setErrorMessage('');
    
    // 保存问题并清空输入框
    const questionText = prompt;
    setPrompt('');

    try {
      // 发送请求
      const response = await axios.post('/api/v1/integration', {
        prompt: questionText,
        use_context: useContext,
        context_query: useContext ? questionText : null,
        max_context_docs: maxContextDocs,
        source_filter: selectedSource !== 'all' ? selectedSource : null
      }, {
        params: {
          debug: true,
          force_use_documents: forceUseDocuments
        }
      });

      // 添加AI回复和引用文档(如果有)
      const aiMessage = {
        role: 'assistant',
        content: response.data.completion || '抱歉，无法生成回答',
        timestamp: new Date().toISOString(),
      };

      if (response.data.debug_info && response.data.debug_info.document_snippets) {
        aiMessage.contextDocuments = response.data.debug_info.document_snippets;
      }

      setConversations(prev => [...prev, aiMessage]);
    } catch (error) {
      console.error('获取回答失败:', error);
      setErrorMessage('获取回答失败，请稍后重试');
      
      // 添加错误消息
      setConversations(prev => [
        ...prev, 
        {
          role: 'system',
          content: '获取回答失败，请稍后重试',
          isError: true,
          timestamp: new Date().toISOString()
        }
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const clearConversation = () => {
    setConversations([]);
  };

  const renderMessage = (message) => {
    const isUser = message.role === 'user';
    const isSystem = message.role === 'system';

    if (isSystem) {
      return (
        <Alert 
          message={message.content}
          type={message.isError ? "error" : "info"}
          showIcon
          style={{ marginBottom: 16 }}
        />
      );
    }

    return (
      <div
        style={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: isUser ? 'flex-end' : 'flex-start',
          marginBottom: 16
        }}
      >
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            marginBottom: 8
          }}
        >
          <Avatar
            icon={isUser ? <UserOutlined /> : <RobotOutlined />}
            style={{ 
              backgroundColor: isUser ? '#1890ff' : '#52c41a',
              marginRight: isUser ? 0 : 8,
              marginLeft: isUser ? 8 : 0
            }}
          />
          <Text type="secondary" style={{ fontSize: 12 }}>
            {new Date(message.timestamp).toLocaleTimeString()}
          </Text>
        </div>

        <div
          style={{
            maxWidth: '80%',
            padding: 16,
            borderRadius: 8,
            backgroundColor: isUser ? '#e6f7ff' : '#f6ffed',
            textAlign: isUser ? 'right' : 'left',
          }}
        >
          <Paragraph 
            style={{ whiteSpace: 'pre-wrap', margin: 0 }}
          >
            {message.content}
          </Paragraph>
        </div>

        {message.contextDocuments && message.contextDocuments.length > 0 && (
          <div style={{ marginTop: 8, maxWidth: '80%' }} className="document-reference">
            <Text type="secondary" style={{ fontSize: 12, writingMode: 'horizontal-tb', display: 'block' }}>
              <InfoCircleOutlined /> 参考文档:
            </Text>
            <List
              size="small"
              dataSource={message.contextDocuments.slice(0, 3)}
              renderItem={(doc, index) => (
                <List.Item className="reference-item" 
                  style={{
                    display: 'block',
                    writingMode: 'horizontal-tb',
                    textOrientation: 'mixed'
                  }}
                >
                  <div style={{ display: 'flex', flexDirection: 'row', alignItems: 'flex-start', writingMode: 'horizontal-tb' }}>
                    <Avatar icon={<FileTextOutlined />} style={{ backgroundColor: '#faad14', marginRight: '8px', flexShrink: 0 }} />
                    <div style={{ flex: 1, minWidth: 0 }}>
                      <div className="document-header" style={{width: '100%', display: 'flex', flexDirection: 'row', justifyContent: 'space-between', writingMode: 'horizontal-tb'}}>
                        <div className="document-title" style={{
                          display: 'inline-block', 
                          writingMode: 'horizontal-tb',
                          textOrientation: 'mixed',
                          direction: 'ltr',
                          fontWeight: 'bold',
                          overflow: 'hidden',
                          textOverflow: 'ellipsis',
                          marginRight: '8px',
                          maxWidth: '200px',
                          whiteSpace: 'nowrap'
                        }}>
                          {doc.source || (doc.metadata?.source || doc.metadata?.pdf_filename || `文档片段 #${index+1}`)}
                        </div>
                        {doc.similarity && 
                          <div className="similarity-badge" style={{
                            display: 'inline-block',
                            writingMode: 'horizontal-tb',
                            backgroundColor: '#e6f7ff',
                            padding: '2px 6px',
                            borderRadius: '10px',
                            fontSize: '0.8em',
                            whiteSpace: 'nowrap'
                          }}>
                            相似度: {(doc.similarity * 100).toFixed(0)}%
                          </div>
                        }
                      </div>
                      <div className="document-content" style={{
                        display: 'block',
                        writingMode: 'horizontal-tb',
                        textOrientation: 'mixed',
                        color: '#666',
                        fontSize: '12px'
                      }}>
                        {doc.content.substring(0, 100)}...
                      </div>
                    </div>
                  </div>
                </List.Item>
              )}
            />
            {message.contextDocuments.length > 3 && (
              <Text type="secondary" style={{ fontSize: 12, display: 'block', textAlign: 'center' }}>
                还有 {message.contextDocuments.length - 3} 个参考文档
              </Text>
            )}
          </div>
        )}
      </div>
    );
  };

  return (
    <div className="query-assistant-container">
      <Card 
        title={<Title level={4}>智能查询助手</Title>}
        extra={
          <Button 
            type="text" 
            icon={<DeleteOutlined />} 
            onClick={clearConversation}
          >
            清空对话
          </Button>
        }
        bordered={false}
        style={{ width: '100%', height: 'calc(100vh - 160px)' }}
      >
        <div style={{ marginBottom: 16 }}>
          <Space align="center" style={{ marginBottom: 16 }}>
            <Select
              style={{ width: 200 }}
              value={selectedSource}
              onChange={setSelectedSource}
              placeholder="选择文档来源"
            >
              <Option value="all" style={{writingMode: 'horizontal-tb', textOrientation: 'mixed'}}>所有文档</Option>
              {sources.map(source => (
                <Option key={source} value={source} style={{writingMode: 'horizontal-tb', textOrientation: 'mixed'}}>{source}</Option>
              ))}
            </Select>
            
            <Text>文档上下文:</Text>
            <Switch 
              checked={useContext} 
              onChange={setUseContext} 
              checkedChildren="开启"
              unCheckedChildren="关闭"
            />
            
            <Text>强制使用文档:</Text>
            <Switch 
              checked={forceUseDocuments} 
              onChange={setForceUseDocuments} 
              checkedChildren="开启"
              unCheckedChildren="关闭"
              disabled={!useContext}
            />
            
            {useContext && (
              <>
                <Text>最大引用文档数:</Text>
                <Select 
                  style={{ width: 80 }} 
                  value={maxContextDocs} 
                  onChange={setMaxContextDocs}
                >
                  {[3, 5, 10, 15, 20].map(num => (
                    <Option key={num} value={num}>{num}</Option>
                  ))}
                </Select>
              </>
            )}
          </Space>
        </div>

        <div
          style={{
            height: 'calc(100vh - 380px)',
            minHeight: '300px',
            overflowY: 'auto',
            padding: '0 12px',
            border: '1px solid #f0f0f0',
            borderRadius: 6,
            backgroundColor: '#fafafa',
          }}
        >
          {conversations.length > 0 ? (
            <div style={{ padding: '16px 0' }}>
              {conversations.map((message, index) => (
                <React.Fragment key={index}>
                  {renderMessage(message)}
                </React.Fragment>
              ))}
              <div ref={bottomRef} />
            </div>
          ) : (
            <Empty
              image={Empty.PRESENTED_IMAGE_SIMPLE}
              description="开始与AI助手对话"
              style={{ margin: '60px 0' }}
            />
          )}
        </div>

        <div
          style={{
            display: 'flex',
            alignItems: 'flex-end',
          }}
        >
          <TextArea
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="输入问题..."
            autoSize={{ minRows: 2, maxRows: 6 }}
            style={{ 
              borderRadius: '8px 0 0 8px', 
              resize: 'none',
              width: 'calc(100% - 50px)',
            }}
            disabled={loading}
          />
          <Button
            type="primary"
            icon={<SendOutlined />}
            onClick={handleSend}
            loading={loading}
            style={{ 
              height: '54px',
              borderRadius: '0 8px 8px 0',
              width: '50px',
            }}
            disabled={!prompt.trim()}
          />
        </div>

        {loading && (
          <div style={{ textAlign: 'center' }}>
            <Spin tip="思考中..." />
          </div>
        )}
      </Card>
    </div>
  );
};

export default QueryAssistant; 
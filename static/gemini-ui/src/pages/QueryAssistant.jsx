import React, { useState, useRef, useEffect } from 'react';
import { Input, Button, Card, Spin, Typography, Select, Switch, Space, Divider, List, Avatar, Empty, Alert, Badge, Dropdown, Modal, message } from 'antd';
import { SendOutlined, RobotOutlined, UserOutlined, FileTextOutlined, DeleteOutlined, InfoCircleOutlined, DownloadOutlined, UploadOutlined, MoreOutlined } from '@ant-design/icons';
import axios from 'axios';
import { saveAs } from 'file-saver';
import { useTranslation } from 'react-i18next';

const { TextArea } = Input;
const { Title, Paragraph, Text } = Typography;
const { Option } = Select;

const QueryAssistant = () => {
  const { t } = useTranslation();
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

  // 加载本地存储中的对话历史
  useEffect(() => {
    try {
      const savedConversations = localStorage.getItem('assistantConversations');
      if (savedConversations) {
        setConversations(JSON.parse(savedConversations));
      }
      
      // 从localStorage加载其他设置
      const savedSettings = localStorage.getItem('assistantSettings');
      if (savedSettings) {
        const settings = JSON.parse(savedSettings);
        if (settings.selectedSource) setSelectedSource(settings.selectedSource);
        if (settings.useContext !== undefined) setUseContext(settings.useContext);
        if (settings.maxContextDocs) setMaxContextDocs(settings.maxContextDocs);
        if (settings.forceUseDocuments !== undefined) setForceUseDocuments(settings.forceUseDocuments);
      }
    } catch (error) {
      console.error('加载对话历史失败:', error);
    }
  }, []);

  // 保存对话到本地存储
  useEffect(() => {
    try {
      if (conversations.length > 0) {
        // 如果对话太多，保留最近的50条
        const conversationsToSave = conversations.length > 50 
          ? conversations.slice(-50) 
          : conversations;
        
        localStorage.setItem('assistantConversations', JSON.stringify(conversationsToSave));
      }
    } catch (error) {
      console.error('保存对话历史失败:', error);
      // 如果是存储空间不足的错误，尝试只保存最近的10条对话
      if (error instanceof DOMException && error.name === 'QuotaExceededError') {
        try {
          const reducedConversations = conversations.slice(-10);
          localStorage.setItem('assistantConversations', JSON.stringify(reducedConversations));
          
          // 显示提示消息
          setConversations(prev => [
            ...prev,
            {
              role: 'system',
              content: '由于浏览器存储空间限制，只保留了最近10条对话记录',
              isError: false,
              timestamp: new Date().toISOString()
            }
          ]);
        } catch (e) {
          console.error('即使减少对话量也无法保存:', e);
        }
      }
    }
  }, [conversations]);

  // 保存设置到本地存储
  useEffect(() => {
    try {
      const settings = {
        selectedSource,
        useContext,
        maxContextDocs,
        forceUseDocuments
      };
      localStorage.setItem('assistantSettings', JSON.stringify(settings));
    } catch (error) {
      console.error('保存设置失败:', error);
    }
  }, [selectedSource, useContext, maxContextDocs, forceUseDocuments]);

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
    // 清除本地存储中的对话历史
    localStorage.removeItem('assistantConversations');
  };

  // 导出对话历史
  const exportConversations = () => {
    try {
      if (conversations.length === 0) {
        message.warning('没有对话可导出');
        return;
      }

      const exportData = {
        conversations,
        settings: {
          selectedSource,
          useContext,
          maxContextDocs,
          forceUseDocuments
        },
        exportDate: new Date().toISOString()
      };

      const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' });
      const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
      saveAs(blob, `对话记录_${timestamp}.json`);
      message.success('对话导出成功');
    } catch (error) {
      console.error('导出对话失败:', error);
      message.error('导出对话失败');
    }
  };

  // 导入对话控制
  const [importModalVisible, setImportModalVisible] = useState(false);
  const fileInputRef = useRef(null);

  const showImportModal = () => {
    setImportModalVisible(true);
  };

  const handleImport = () => {
    if (fileInputRef.current) {
      fileInputRef.current.click();
    }
  };

  const handleFileChange = (event) => {
    const file = event.target.files[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = (e) => {
      try {
        const importedData = JSON.parse(e.target.result);
        
        if (Array.isArray(importedData.conversations)) {
          setConversations(importedData.conversations);
          
          // 导入设置
          if (importedData.settings) {
            if (importedData.settings.selectedSource) setSelectedSource(importedData.settings.selectedSource);
            if (importedData.settings.useContext !== undefined) setUseContext(importedData.settings.useContext);
            if (importedData.settings.maxContextDocs) setMaxContextDocs(importedData.settings.maxContextDocs);
            if (importedData.settings.forceUseDocuments !== undefined) setForceUseDocuments(importedData.settings.forceUseDocuments);
          }
          
          message.success('对话导入成功');
        } else {
          message.error('导入的文件格式不正确');
        }
      } catch (error) {
        console.error('导入对话失败:', error);
        message.error('导入对话失败，文件格式不正确');
      }
      
      // 重置文件输入
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
      setImportModalVisible(false);
    };
    
    reader.readAsText(file);
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
            maxWidth: '70%',
            padding: 16,
            borderRadius: 8,
            backgroundColor: isUser ? '#e6f7ff' : '#f6ffed',
            textAlign: isUser ? 'right' : 'left',
            wordWrap: 'break-word',
            overflowWrap: 'break-word',
          }}
        >
          <Paragraph 
            style={{ whiteSpace: 'pre-wrap', margin: 0 }}
          >
            {message.content}
          </Paragraph>
        </div>

        {message.contextDocuments && message.contextDocuments.length > 0 && (
          <div style={{ marginTop: 8, maxWidth: '70%', overflowWrap: 'break-word', wordWrap: 'break-word' }} className="document-reference">
            <Text type="secondary" style={{ fontSize: 12, writingMode: 'horizontal-tb', display: 'block' }}>
              <InfoCircleOutlined /> {t('queryAssistant.referenceDocument')}:
            </Text>
            <List
              size="small"
              dataSource={message.contextDocuments.slice(0, 3)}
              renderItem={(doc, index) => (
                <List.Item className="reference-item" 
                  style={{
                    display: 'block',
                    writingMode: 'horizontal-tb',
                    textOrientation: 'mixed',
                    wordWrap: 'break-word',
                    overflowWrap: 'break-word'
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
                          maxWidth: '150px',
                          whiteSpace: 'nowrap'
                        }}>
                          {doc.source || (doc.metadata?.source || doc.metadata?.pdf_filename || `${t('queryAssistant.documentFragment')} #${index+1}`)}
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
                {t('queryAssistant.additionalDocuments', { count: message.contextDocuments.length - 3 })}
              </Text>
            )}
          </div>
        )}
      </div>
    );
  };

  return (
    <div className="query-assistant-container" style={{ 
      position: 'relative',
      minHeight: '100%',
      width: '100%',
      display: 'flex',
      flexDirection: 'column'
    }}>
      <Card 
        title={<Title level={4}>{t('queryAssistant.title')}</Title>}
        extra={
          <Space>
            <Dropdown
              menu={{
                items: [
                  {
                    key: '1',
                    icon: <DeleteOutlined />,
                    label: t('queryAssistant.clearChat'),
                    onClick: clearConversation
                  },
                  {
                    key: '2',
                    icon: <DownloadOutlined />,
                    label: t('common.download'),
                    onClick: exportConversations
                  },
                  {
                    key: '3',
                    icon: <UploadOutlined />,
                    label: t('common.upload'),
                    onClick: showImportModal
                  }
                ]
              }}
              placement="bottomRight"
            >
              <Button type="text" icon={<MoreOutlined />}>{t('common.more')}</Button>
            </Dropdown>
          </Space>
        }
        bordered={false}
        style={{ 
          width: '100%', 
          height: 'auto',
          flex: 1,
          display: 'flex',
          flexDirection: 'column',
          overflow: 'auto'
        }}
        bodyStyle={{
          flex: 1,
          display: 'flex',
          flexDirection: 'column',
          overflow: 'hidden'
        }}
      >
        <div style={{ 
          marginBottom: 16,
          flexWrap: 'wrap',
          display: 'flex'
        }}>
          <Space align="center" style={{ 
            marginBottom: 16,
            flexWrap: 'wrap'
          }}>
            <Select
              style={{ width: 200 }}
              value={selectedSource}
              onChange={setSelectedSource}
              placeholder={t('queryAssistant.sourceSelect')}
            >
              <Option value="all" style={{writingMode: 'horizontal-tb', textOrientation: 'mixed'}}>{t('queryAssistant.allSources')}</Option>
              {sources.map(source => (
                <Option key={source} value={source} style={{writingMode: 'horizontal-tb', textOrientation: 'mixed'}}>{source}</Option>
              ))}
            </Select>
            
            <Text>{t('queryAssistant.useContext')}:</Text>
            <Switch 
              checked={useContext} 
              onChange={setUseContext} 
              checkedChildren={t('common.on')}
              unCheckedChildren={t('common.off')}
            />
            
            <Text>{t('queryAssistant.forceUseDocuments')}:</Text>
            <Switch 
              checked={forceUseDocuments} 
              onChange={setForceUseDocuments} 
              checkedChildren={t('common.on')}
              unCheckedChildren={t('common.off')}
              disabled={!useContext}
            />
            
            {useContext && (
              <>
                <Text>{t('queryAssistant.maxContextDocs')}:</Text>
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
            height: 'auto',
            flex: 1,
            overflowY: 'auto',
            padding: '0 12px',
            border: '1px solid #f0f0f0',
            borderRadius: 6,
            backgroundColor: '#fafafa',
            position: 'relative',
            width: '100%',
            marginBottom: '16px'
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
              description={t('queryAssistant.startChat')}
              style={{ margin: '60px 0' }}
            />
          )}
        </div>

        <div
          style={{
            display: 'flex',
            alignItems: 'flex-end',
            marginTop: '16px',
            width: '100%',
            position: 'relative'
          }}
        >
          <TextArea
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={t('queryAssistant.inputPlaceholder')}
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
              flexShrink: 0
            }}
            disabled={!prompt.trim()}
          />
        </div>

        {loading && (
          <div style={{ textAlign: 'center' }}>
            <Spin tip={t('queryAssistant.thinking')} />
          </div>
        )}
      </Card>

      {/* 导入对话的模态框 */}
      <Modal
        title={t('queryAssistant.importDialog.title')}
        open={importModalVisible}
        onCancel={() => setImportModalVisible(false)}
        footer={[
          <Button key="cancel" onClick={() => setImportModalVisible(false)}>
            {t('common.cancel')}
          </Button>,
          <Button key="import" type="primary" onClick={handleImport}>
            {t('queryAssistant.importDialog.selectFile')}
          </Button>
        ]}
      >
        <p>{t('queryAssistant.importDialog.description')}</p>
        <p>{t('queryAssistant.importDialog.warning')}</p>
        <input
          type="file"
          ref={fileInputRef}
          onChange={handleFileChange}
          accept=".json"
          style={{ display: 'none' }}
        />
      </Modal>
    </div>
  );
};

export default QueryAssistant; 
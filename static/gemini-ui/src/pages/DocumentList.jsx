import React, { useState, useEffect } from 'react';
import { Table, Input, Card, Button, message, Popconfirm, Tooltip, Tag, Space, Modal, Typography } from 'antd';
import { SearchOutlined, DeleteOutlined, EyeOutlined } from '@ant-design/icons';
import axios from 'axios';
import { useTranslation } from 'react-i18next';

const { Search } = Input;
const { Text } = Typography;

const DocumentList = () => {
  const { t } = useTranslation();
  const [documents, setDocuments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedDocument, setSelectedDocument] = useState(null);
  const [isModalVisible, setIsModalVisible] = useState(false);
  const [pagination, setPagination] = useState({
    current: 1,
    pageSize: 20,
    total: 0,
    showSizeChanger: true,
    pageSizeOptions: ['10', '20', '50', '100'],
    showTotal: (total) => t('documentList.totalRecords', { total })
  });
  const [searchTerm, setSearchTerm] = useState('');

  const fetchDocuments = async (page = 1, limit = 20, source = '') => {
    setLoading(true);
    try {
      const response = await axios.get(`/api/v1/documents`, {
        params: {
          offset: (page - 1) * limit,
          limit,
          source
        }
      });
      
      setDocuments(response.data.documents || []);
      setPagination(prev => ({
        ...prev,
        current: page,
        pageSize: limit,
        total: response.data.total || 0
      }));
    } catch (error) {
      console.error(t('documentList.fetchError'), error);
      message.error(t('documentList.fetchError'));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDocuments(pagination.current, pagination.pageSize, searchTerm);
  }, []);

  const handleTableChange = (newPagination) => {
    setPagination(newPagination);
    fetchDocuments(newPagination.current, newPagination.pageSize, searchTerm);
  };

  const handleSearch = (value) => {
    setSearchTerm(value);
    fetchDocuments(1, pagination.pageSize, value);
  };

  const handleDelete = async (id) => {
    try {
      await axios.delete(`/api/v1/documents/${id}`);
      message.success(t('documentList.deleteSuccess'));
      fetchDocuments(pagination.current, pagination.pageSize, searchTerm);
    } catch (error) {
      console.error(t('documentList.deleteError'), error);
      message.error(t('documentList.deleteError'));
    }
  };

  const handleViewDetails = (record) => {
    setSelectedDocument(record);
    setIsModalVisible(true);
  };

  const handleModalClose = () => {
    setIsModalVisible(false);
    setSelectedDocument(null);
  };

  const columns = [
    {
      title: 'ID',
      dataIndex: 'id',
      key: 'id',
      width: 80,
    },
    {
      title: t('documentList.source'),
      dataIndex: 'metadata',
      key: 'source',
      render: (metadata) => (
        <span style={{display: 'inline-block', writingMode: 'horizontal-tb', textOrientation: 'mixed', direction: 'ltr'}}>
          {metadata?.source || t('common.unknown')}
        </span>
      ),
    },
    {
      title: t('documentList.contentPreview'),
      dataIndex: 'content',
      key: 'content',
      render: (text) => {
        const preview = text ? (text.length > 100 ? `${text.substring(0, 100)}...` : text) : t('documentList.noContent');
        return (
          <Tooltip title={text}>
            <span>{preview}</span>
          </Tooltip>
        );
      },
    },
    {
      title: t('documentList.strategy'),
      dataIndex: 'metadata',
      key: 'chunking_strategy',
      width: 100,
      render: (metadata) => {
        const strategy = metadata?.chunking_strategy || 'fixed_size';
        const color = strategy === 'intelligent' ? 'green' : 'blue';
        return <Tag color={color}>{strategy}</Tag>;
      },
    },
    {
      title: t('documentList.time'),
      dataIndex: 'created_at',
      key: 'created_at',
      width: 170,
      render: (text) => text ? new Date(text).toLocaleString() : t('common.unknown'),
    },
    {
      title: t('documentList.actions'),
      key: 'action',
      width: 120,
      render: (_, record) => (
        <Space>
          <Tooltip title={t('common.view')}>
            <Button 
              icon={<EyeOutlined />} 
              size="small" 
              onClick={() => handleViewDetails(record)}
            />
          </Tooltip>
          <Popconfirm
            title={t('documentList.deleteConfirm')}
            onConfirm={() => handleDelete(record.id)}
            okText={t('common.confirm')}
            cancelText={t('common.cancel')}
          >
            <Tooltip title={t('common.delete')}>
              <Button icon={<DeleteOutlined />} danger size="small" />
            </Tooltip>
          </Popconfirm>
        </Space>
      ),
    },
  ];

  return (
    <div>
      <Card title={t('documentList.title')} bordered={false}>
        <Search 
          placeholder={t('documentList.searchPlaceholder')}
          onSearch={handleSearch} 
          enterButton={<><SearchOutlined />{t('common.search')}</>}
          allowClear
          style={{ marginBottom: 20 }}
        />
        <Table
          columns={columns}
          dataSource={documents}
          rowKey="id"
          pagination={pagination}
          loading={loading}
          onChange={handleTableChange}
        />
      </Card>

      <Modal
        title={t('documentList.documentDetails')}
        open={isModalVisible}
        onCancel={handleModalClose}
        footer={[
          <Button key="close" onClick={handleModalClose}>
            Close
          </Button>
        ]}
        width={800}
      >
        {selectedDocument && (
          <div>
            <p><Text strong>{t('documentList.documentId')}:</Text> {selectedDocument.id}</p>
            <p><Text strong>{t('documentList.source')}:</Text> {selectedDocument.metadata?.source || t('common.unknown')}</p>
            <p><Text strong>{t('documentList.strategy')}:</Text> {selectedDocument.metadata?.chunking_strategy || 'fixed_size'}</p>
            <p><Text strong>{t('documentList.time')}:</Text> {selectedDocument.created_at ? new Date(selectedDocument.created_at).toLocaleString() : t('common.unknown')}</p>
            <div style={{ marginTop: 16 }}>
              <Text strong>{t('documentList.content')}:</Text>
              <div style={{ 
                marginTop: 8, 
                padding: 12, 
                backgroundColor: '#f5f5f5', 
                borderRadius: 4,
                maxHeight: '400px',
                overflowY: 'auto'
              }}>
                <Text>{selectedDocument.content}</Text>
              </div>
            </div>
          </div>
        )}
      </Modal>
    </div>
  );
};

export default DocumentList; 
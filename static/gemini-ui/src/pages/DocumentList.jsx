import React, { useState, useEffect } from 'react';
import { Table, Input, Card, Button, message, Popconfirm, Tooltip, Tag, Space } from 'antd';
import { SearchOutlined, DeleteOutlined, EyeOutlined } from '@ant-design/icons';
import axios from 'axios';

const { Search } = Input;

const DocumentList = () => {
  const [documents, setDocuments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [pagination, setPagination] = useState({
    current: 1,
    pageSize: 10,
    total: 0
  });
  const [searchTerm, setSearchTerm] = useState('');

  const fetchDocuments = async (page = 1, limit = 10, source = '') => {
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
      setPagination({
        ...pagination,
        current: page,
        total: response.data.total || 0
      });
    } catch (error) {
      console.error('获取文档列表失败:', error);
      message.error('获取文档列表失败，请稍后重试');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDocuments(pagination.current, pagination.pageSize, searchTerm);
  }, []);

  const handleTableChange = (pagination) => {
    fetchDocuments(pagination.current, pagination.pageSize, searchTerm);
  };

  const handleSearch = (value) => {
    setSearchTerm(value);
    fetchDocuments(1, pagination.pageSize, value);
  };

  const handleDelete = async (id) => {
    try {
      await axios.delete(`/api/v1/documents/${id}`);
      message.success('文档删除成功');
      fetchDocuments(pagination.current, pagination.pageSize, searchTerm);
    } catch (error) {
      console.error('删除文档失败:', error);
      message.error('删除文档失败，请稍后重试');
    }
  };

  const columns = [
    {
      title: 'ID',
      dataIndex: 'id',
      key: 'id',
      width: 80,
    },
    {
      title: '来源',
      dataIndex: 'metadata',
      key: 'source',
      render: (metadata) => (
        <span style={{display: 'inline-block', writingMode: 'horizontal-tb', textOrientation: 'mixed', direction: 'ltr'}}>
          {metadata?.source || '未知来源'}
        </span>
      ),
    },
    {
      title: '内容预览',
      dataIndex: 'content',
      key: 'content',
      render: (text) => {
        const preview = text ? (text.length > 100 ? `${text.substring(0, 100)}...` : text) : '无内容';
        return (
          <Tooltip title={text}>
            <span>{preview}</span>
          </Tooltip>
        );
      },
    },
    {
      title: '类型',
      dataIndex: 'metadata',
      key: 'type',
      width: 100,
      render: (metadata) => <Tag color="blue">{metadata?.type || 'text'}</Tag>,
    },
    {
      title: '时间',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 170,
      render: (text) => text ? new Date(text).toLocaleString() : '未知',
    },
    {
      title: '操作',
      key: 'action',
      width: 120,
      render: (_, record) => (
        <Space>
          <Button 
            icon={<EyeOutlined />} 
            size="small" 
            onClick={() => {
              // 查看文档详情
              message.info(`文档ID: ${record.id}`);
            }}
          />
          <Popconfirm
            title="确定要删除此文档吗？"
            onConfirm={() => handleDelete(record.id)}
            okText="确定"
            cancelText="取消"
          >
            <Button icon={<DeleteOutlined />} danger size="small" />
          </Popconfirm>
        </Space>
      ),
    },
  ];

  return (
    <div>
      <Card title="文档列表" bordered={false}>
        <Search 
          placeholder="搜索文档来源..." 
          onSearch={handleSearch} 
          enterButton={<><SearchOutlined />搜索</>}
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
    </div>
  );
};

export default DocumentList; 
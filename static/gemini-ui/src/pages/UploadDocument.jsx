import React, { useState } from 'react';
import { Upload, Card, Button, Form, Input, Switch, Slider, message, Space, Typography, Alert, Progress, Row, Col, Radio } from 'antd';
import { UploadOutlined, FileTextOutlined, InboxOutlined } from '@ant-design/icons';
import axios from 'axios';
import { useTranslation } from 'react-i18next';

const { Dragger } = Upload;
const { TextArea } = Input;
const { Title, Paragraph, Text } = Typography;

const UploadDocument = () => {
  const { t } = useTranslation();
  const [form] = Form.useForm();
  const [uploadType, setUploadType] = useState('pdf');
  const [useIntelligentChunking, setUseIntelligentChunking] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [uploadResult, setUploadResult] = useState(null);
  const [errorMessage, setErrorMessage] = useState('');

  const handleUpload = async (values) => {
    if (uploadType === 'text' && !values.content) {
      setErrorMessage(t('uploadDocument.inputRequired'));
      return;
    }

    setUploading(true);
    setUploadProgress(0);
    setErrorMessage('');
    setUploadResult(null);

    try {
      if (uploadType === 'text') {
        // 上传文本
        const response = await axios.post('/api/v1/documents', {
          content: values.content,
          metadata: {
            source: values.source || t('common.unknown'),
            type: 'text',
            author: values.author || t('common.unknown')
          }
        });
        
        setUploadResult({
          success: true,
          message: t('uploadDocument.uploadSuccess'),
          documentId: response.data.id
        });
        
        form.resetFields();
      }
    } catch (error) {
      console.error('上传失败:', error);
      setErrorMessage(t('uploadDocument.uploadFailed'));
      setUploadResult({
        success: false,
        message: t('uploadDocument.uploadFailed') + ': ' + (error.response?.data?.detail || error.message)
      });
    } finally {
      setUploading(false);
      setUploadProgress(100);
    }
  };

  const uploadProps = {
    name: 'file',
    multiple: false,
    action: `/api/v1/upload-pdf`,
    data: {
      chunking_strategy: useIntelligentChunking ? 'intelligent' : 'fixed_size',
      chunk_size: form.getFieldValue('chunkSize') || 1000,
      overlap: form.getFieldValue('overlap') || 200,
    },
    headers: {
      // 这里可以添加授权头信息
    },
    beforeUpload: (file) => {
      const isPDF = file.type === 'application/pdf';
      if (!isPDF) {
        message.error(t('uploadDocument.fileTypeError'));
      }
      return isPDF || Upload.LIST_IGNORE;
    },
    onChange: (info) => {
      if (info.file.status === 'uploading') {
        setUploading(true);
        // 模拟上传进度
        let percent = info.file.percent || 0;
        setUploadProgress(Math.floor(percent));
      }
      if (info.file.status === 'done') {
        setUploading(false);
        setUploadProgress(100);
        message.success(`${info.file.name} ${t('uploadDocument.uploadSuccess')}`);
        setUploadResult({
          success: true,
          message: t('uploadDocument.uploadSuccess'),
          fileInfo: info.file.response
        });
      } else if (info.file.status === 'error') {
        setUploading(false);
        setUploadProgress(0);
        message.error(`${info.file.name} ${t('uploadDocument.uploadFailed')}`);
        setErrorMessage(`${t('uploadDocument.uploadFailed')}: ${info.file.response?.detail || t('uploadDocument.uploadFailed')}`);
      }
    },
  };

  return (
    <div>
      <Card title={t('uploadDocument.title')} bordered={false}>
        <Space direction="vertical" size="large" style={{ width: '100%' }}>
          <Row gutter={16}>
            <Col span={24}>
              <Radio.Group
                value={uploadType}
                onChange={(e) => setUploadType(e.target.value)}
                style={{ marginBottom: 20 }}
              >
                <Radio.Button value="pdf">{t('uploadDocument.tabPdf')}</Radio.Button>
                <Radio.Button value="text">{t('uploadDocument.tabText')}</Radio.Button>
              </Radio.Group>
            </Col>
          </Row>

          {uploadType === 'pdf' ? (
            <>
              <Form form={form} layout="vertical">
                <Form.Item
                  label={t('uploadDocument.intelligentChunking')}
                  name="useIntelligentChunking"
                  valuePropName="checked"
                  initialValue={true}
                >
                  <Switch
                    checkedChildren={t('uploadDocument.smartChunking')}
                    unCheckedChildren={t('uploadDocument.fixedChunking')}
                    defaultChecked
                    onChange={(checked) => setUseIntelligentChunking(checked)}
                  />
                </Form.Item>

                {!useIntelligentChunking && (
                  <>
                    <Form.Item
                      label={t('uploadDocument.chunkSize')}
                      name="chunkSize"
                      initialValue={1000}
                      rules={[{ required: true, message: t('uploadDocument.chunkSizeRequired') }]}
                    >
                      <Slider
                        min={100}
                        max={5000}
                        step={100}
                        marks={{
                          100: <span style={{ display: 'inline-block', width: '40px', textAlign: 'center' }}>100</span>,
                          1000: <span style={{ display: 'inline-block', width: '40px', textAlign: 'center' }}>1000</span>,
                          2000: <span style={{ display: 'inline-block', width: '40px', textAlign: 'center' }}>2000</span>,
                          3000: <span style={{ display: 'inline-block', width: '40px', textAlign: 'center' }}>3000</span>,
                          4000: <span style={{ display: 'inline-block', width: '40px', textAlign: 'center' }}>4000</span>,
                          5000: <span style={{ display: 'inline-block', width: '40px', textAlign: 'center' }}>5000</span>
                        }}
                        tooltip={{
                          formatter: (value) => `${value} ${t('uploadDocument.chars')}`
                        }}
                        style={{ 
                          margin: '0 12px',
                          width: 'calc(100% - 24px)'
                        }}
                        railStyle={{
                          backgroundColor: '#f0f0f0'
                        }}
                        trackStyle={{
                          backgroundColor: '#1890ff'
                        }}
                        handleStyle={{
                          borderColor: '#1890ff',
                          backgroundColor: '#fff'
                        }}
                        dotStyle={{
                          borderColor: '#1890ff'
                        }}
                      />
                    </Form.Item>

                    <Form.Item
                      label={t('uploadDocument.overlapSize')}
                      name="overlapSize"
                      initialValue={200}
                      rules={[{ required: true, message: t('uploadDocument.overlapSizeRequired') }]}
                    >
                      <Slider
                        min={0}
                        max={500}
                        step={50}
                        marks={{
                          0: <span style={{ display: 'inline-block', width: '40px', textAlign: 'center' }}>0</span>,
                          100: <span style={{ display: 'inline-block', width: '40px', textAlign: 'center' }}>100</span>,
                          200: <span style={{ display: 'inline-block', width: '40px', textAlign: 'center' }}>200</span>,
                          300: <span style={{ display: 'inline-block', width: '40px', textAlign: 'center' }}>300</span>,
                          400: <span style={{ display: 'inline-block', width: '40px', textAlign: 'center' }}>400</span>,
                          500: <span style={{ display: 'inline-block', width: '40px', textAlign: 'center' }}>500</span>
                        }}
                        tooltip={{
                          formatter: (value) => `${value} ${t('uploadDocument.chars')}`
                        }}
                        style={{ 
                          margin: '0 12px',
                          width: 'calc(100% - 24px)'
                        }}
                        railStyle={{
                          backgroundColor: '#f0f0f0'
                        }}
                        trackStyle={{
                          backgroundColor: '#1890ff'
                        }}
                        handleStyle={{
                          borderColor: '#1890ff',
                          backgroundColor: '#fff'
                        }}
                        dotStyle={{
                          borderColor: '#1890ff'
                        }}
                      />
                    </Form.Item>
                  </>
                )}

                <Form.Item>
                  <Dragger {...uploadProps} disabled={uploading}>
                    <p className="ant-upload-drag-icon">
                      <InboxOutlined />
                    </p>
                    <p className="ant-upload-text">{t('uploadDocument.dragText')}</p>
                    <p className="ant-upload-hint">
                      {t('uploadDocument.dropHint')}
                    </p>
                  </Dragger>
                </Form.Item>
              </Form>
            </>
          ) : (
            <Form form={form} layout="vertical" onFinish={handleUpload}>
              <Form.Item
                label={t('uploadDocument.textAreaLabel')}
                name="content"
                rules={[{ required: true, message: t('uploadDocument.inputRequired') }]}
              >
                <TextArea rows={6} placeholder={t('uploadDocument.textAreaPlaceholder')} />
              </Form.Item>
              <Form.Item
                label={<span style={{display: 'inline-block', writingMode: 'horizontal-tb'}}>{t('uploadDocument.sourceLabel')}</span>}
                name="source"
              >
                <Input placeholder={t('uploadDocument.sourcePlaceholder')} style={{writingMode: 'horizontal-tb'}} />
              </Form.Item>
              <Form.Item
                label={t('uploadDocument.authorLabel')}
                name="author"
              >
                <Input placeholder={t('uploadDocument.authorPlaceholder')} />
              </Form.Item>
              <Form.Item>
                <Button
                  type="primary"
                  icon={<FileTextOutlined />}
                  loading={uploading}
                  onClick={() => form.submit()}
                >
                  {t('uploadDocument.addTextBtn')}
                </Button>
              </Form.Item>
            </Form>
          )}

          {uploading && (
            <Progress percent={uploadProgress} status="active" />
          )}

          {errorMessage && (
            <Alert message={errorMessage} type="error" showIcon />
          )}

          {uploadResult && uploadResult.success && (
            <Alert
              message={t('uploadDocument.uploadSuccess')}
              description={
                <div>
                  <p>{uploadResult.message}</p>
                  {uploadResult.documentId && <p>{t('uploadDocument.documentId')}: {uploadResult.documentId}</p>}
                  {uploadResult.fileInfo && (
                    <>
                      <p>{t('uploadDocument.fileInfoTitle')}: {uploadResult.fileInfo.filename}</p>
                      <p>{t('uploadDocument.chunksProcessed')}: {uploadResult.fileInfo.chunks_processed}</p>
                    </>
                  )}
                </div>
              }
              type="success"
              showIcon
            />
          )}
        </Space>
      </Card>
    </div>
  );
};

export default UploadDocument; 
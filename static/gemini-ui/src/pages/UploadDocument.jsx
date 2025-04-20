import React, { useState } from 'react';
import { Upload, Card, Button, Form, Input, Switch, Slider, message, Space, Typography, Alert, Progress, Row, Col, Radio } from 'antd';
import { UploadOutlined, FileTextOutlined, InboxOutlined } from '@ant-design/icons';
import axios from 'axios';

const { Dragger } = Upload;
const { TextArea } = Input;
const { Title, Paragraph, Text } = Typography;

const UploadDocument = () => {
  const [form] = Form.useForm();
  const [uploadType, setUploadType] = useState('pdf');
  const [useIntelligentChunking, setUseIntelligentChunking] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [uploadResult, setUploadResult] = useState(null);
  const [errorMessage, setErrorMessage] = useState('');

  const handleUpload = async (values) => {
    if (uploadType === 'text' && !values.content) {
      setErrorMessage('请输入文本内容');
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
            source: values.source || '手动输入',
            type: 'text',
            author: values.author || '未知'
          }
        });
        
        setUploadResult({
          success: true,
          message: '文本添加成功',
          documentId: response.data.id
        });
        
        form.resetFields();
      }
    } catch (error) {
      console.error('上传失败:', error);
      setErrorMessage('上传失败，请稍后重试');
      setUploadResult({
        success: false,
        message: '上传失败: ' + (error.response?.data?.detail || error.message)
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
      use_intelligent_chunking: useIntelligentChunking,
      chunk_size: form.getFieldValue('chunkSize') || 1000,
      overlap: form.getFieldValue('overlap') || 200,
    },
    headers: {
      // 这里可以添加授权头信息
    },
    beforeUpload: (file) => {
      const isPDF = file.type === 'application/pdf';
      if (!isPDF) {
        message.error('只能上传PDF文件!');
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
        message.success(`${info.file.name} 上传成功`);
        setUploadResult({
          success: true,
          message: '文件上传成功',
          fileInfo: info.file.response
        });
      } else if (info.file.status === 'error') {
        setUploading(false);
        setUploadProgress(0);
        message.error(`${info.file.name} 上传失败`);
        setErrorMessage(`上传失败: ${info.file.response?.detail || '请检查文件格式或网络连接'}`);
      }
    },
  };

  return (
    <div>
      <Card title="上传文档" bordered={false}>
        <Space direction="vertical" size="large" style={{ width: '100%' }}>
          <Row gutter={16}>
            <Col span={24}>
              <Radio.Group
                value={uploadType}
                onChange={(e) => setUploadType(e.target.value)}
                style={{ marginBottom: 20 }}
              >
                <Radio.Button value="pdf">上传PDF文件</Radio.Button>
                <Radio.Button value="text">输入文本内容</Radio.Button>
              </Radio.Group>
            </Col>
          </Row>

          {uploadType === 'pdf' ? (
            <>
              <Form form={form} layout="vertical">
                <Form.Item
                  label="智能分块设置"
                  name="useIntelligentChunking"
                  valuePropName="checked"
                  initialValue={true}
                >
                  <Switch
                    checkedChildren="智能分块"
                    unCheckedChildren="固定分块"
                    defaultChecked
                    onChange={(checked) => setUseIntelligentChunking(checked)}
                  />
                </Form.Item>

                {!useIntelligentChunking && (
                  <>
                    <Form.Item
                      label="分块大小"
                      name="chunkSize"
                      initialValue={1000}
                    >
                      <Slider min={100} max={3000} marks={{
                        500: '500',
                        1000: '1000',
                        2000: '2000',
                        3000: '3000',
                      }} />
                    </Form.Item>
                    <Form.Item
                      label="重叠大小"
                      name="overlap"
                      initialValue={200}
                    >
                      <Slider min={0} max={500} marks={{
                        0: '0',
                        100: '100',
                        300: '300',
                        500: '500',
                      }} />
                    </Form.Item>
                  </>
                )}

                <Form.Item>
                  <Dragger {...uploadProps} disabled={uploading}>
                    <p className="ant-upload-drag-icon">
                      <InboxOutlined />
                    </p>
                    <p className="ant-upload-text">点击或拖拽文件到此区域上传</p>
                    <p className="ant-upload-hint">
                      仅支持PDF文件，系统将自动处理并创建向量索引
                    </p>
                  </Dragger>
                </Form.Item>
              </Form>
            </>
          ) : (
            <Form form={form} layout="vertical" onFinish={handleUpload}>
              <Form.Item
                label="文本内容"
                name="content"
                rules={[{ required: true, message: '请输入文本内容' }]}
              >
                <TextArea rows={6} placeholder="请输入要添加的文本内容..." />
              </Form.Item>
              <Form.Item
                label={<span style={{display: 'inline-block', writingMode: 'horizontal-tb'}}>来源</span>}
                name="source"
              >
                <Input placeholder="文档来源(可选)" style={{writingMode: 'horizontal-tb'}} />
              </Form.Item>
              <Form.Item
                label="作者"
                name="author"
              >
                <Input placeholder="作者(可选)" />
              </Form.Item>
              <Form.Item>
                <Button
                  type="primary"
                  icon={<FileTextOutlined />}
                  loading={uploading}
                  onClick={() => form.submit()}
                >
                  添加文本
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
              message="上传成功"
              description={
                <div>
                  <p>{uploadResult.message}</p>
                  {uploadResult.documentId && <p>文档ID: {uploadResult.documentId}</p>}
                  {uploadResult.fileInfo && (
                    <>
                      <p>文件名: {uploadResult.fileInfo.filename}</p>
                      <p>处理的文本块数: {uploadResult.fileInfo.chunks_processed}</p>
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
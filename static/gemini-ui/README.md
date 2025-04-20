# Gemini向量搜索系统前端

这是一个基于React和Ant Design的前端应用，用于与Gemini向量搜索API进行交互。

## 功能特点

- 简洁美观的用户界面
- 文档管理和搜索功能
- PDF文件上传和处理
- 基于文档内容的智能问答
- 响应式设计，适配不同设备

## 技术栈

- React 18
- React Router 6
- Ant Design 5
- Axios
- Vite

## 安装与运行

### 安装依赖

```bash
cd static/gemini-ui
npm install
```

### 开发模式运行

```bash
npm start
```

### 构建生产版本

```bash
npm run build
```

构建后的文件将生成在`dist`目录下，可以部署到任何静态文件服务器。

## 开发说明

### 目录结构

```
gemini-ui/
├── src/
│   ├── pages/            # 页面组件
│   │   ├── Home.jsx      # 首页
│   │   ├── DocumentList.jsx  # 文档列表页
│   │   ├── DocumentSearch.jsx  # 文档搜索页
│   │   ├── UploadDocument.jsx  # 文档上传页
│   │   └── QueryAssistant.jsx  # 智能问答页
│   ├── App.jsx           # 主应用组件
│   ├── main.jsx          # 应用入口
│   └── index.css         # 全局样式
├── public/               # 静态资源
├── index.html            # HTML模板
└── vite.config.js        # Vite配置
```

### API集成

前端应用默认通过代理方式与后端API通信，在开发模式下会将`/api`路径下的请求代理到`http://localhost:8000`。

在生产环境中，需要确保API端点可访问，或者修改请求路径。

## 使用说明

### 智能问答

在"智能问答"页面，您可以：

1. 选择要查询的文档来源
2. 切换是否使用文档上下文（使用向量搜索）
3. 调整最大参考文档数量
4. 提交问题并获取AI回答

### 文档管理

在"文档列表"页面，您可以：

1. 浏览所有已上传的文档
2. 搜索特定来源的文档
3. 查看文档详情和删除文档

### 文档搜索

在"文档搜索"页面，您可以：

1. 输入关键词搜索相关文档
2. 按文档来源筛选搜索结果
3. 调整返回的结果数量
4. 查看搜索结果摘要和详细内容

### 文档上传

在"上传文档"页面，您可以：

1. 上传PDF文件或直接输入文本内容
2. 配置智能分块选项
3. 添加文档元数据信息

## 许可证

© 2023 版权所有 
export default {
  // 公共部分
  common: {
    loading: '加载中...',
    search: '搜索',
    cancel: '取消',
    confirm: '确认',
    delete: '删除',
    edit: '编辑',
    save: '保存',
    view: '查看',
    upload: '上传',
    download: '下载',
    success: '成功',
    failed: '失败',
    unknown: '未知',
    noData: '暂无数据',
    back: '返回',
    more: '更多',
    on: '开启',
    off: '关闭'
  },
  
  // 认证相关
  auth: {
    login: '登录',
    logout: '退出登录',
    username: '用户名',
    password: '密码',
    rememberMe: '记住我',
    loginButton: '登录',
    welcomeBack: '欢迎回来',
    loginTitle: 'Smart RAG Platform',
    loginSubtitle: '请输入您的账号信息',
    invalidCredentials: '用户名或密码错误',
    logoutConfirm: '确定要退出登录吗？',
    loginRequired: '请先登录',
    usernameRequired: '请输入用户名',
    passwordRequired: '请输入密码',
    availableUsers: '可用用户名',
  },
  
  // 导航菜单
  nav: {
    home: '首页',
    documentList: '文档列表',
    uploadDocument: '上传文档',
    queryAssistant: '查询助手',
    strategyEvaluation: '策略评估'
  },
  
  // 首页
  home: {
    title: 'Smart RAG Platform',
    subtitle: '基于Google Gemini 2.5 Pro模型的智能文档检索与问答系统',
    statsDocuments: '文档总数',
    statsChunks: '文本块总数',
    statsUpdated: '最近更新',
    cardSearchTitle: '搜索文档',
    cardSearchDesc: '使用向量搜索技术在已有文档中查找相关信息，支持语义搜索和相似度排序。',
    cardSearchBtn: '开始搜索',
    cardUploadTitle: '上传文档',
    cardUploadDesc: '上传PDF文档，系统将自动处理并生成向量表示，支持智能分段。',
    cardUploadBtn: '上传文档',
    cardAssistantTitle: '智能问答',
    cardAssistantDesc: '针对已有文档提出问题，系统会基于文档内容生成回答，支持复杂查询和上下文理解。',
    cardAssistantBtn: '开始对话',
  },
  
  // 文档列表页面
  documentList: {
    title: '文档列表',
    empty: '暂无文档',
    upload: '上传文档',
    search: '搜索文档',
    source: '来源',
    createdAt: '创建时间',
    actions: '操作',
    delete: '删除',
    deleteConfirm: '确定要删除这个文档吗？',
    deleteSuccess: '文档删除成功',
    deleteError: '文档删除失败',
    chunkingStrategy: {
      fixed_size: '固定分块',
      intelligent: '智能分块'
    }
  },
  
  // 文档搜索页面
  documentSearch: {
    title: '文档搜索',
    searchPlaceholder: '输入搜索内容...',
    sourceSelect: '选择文档来源',
    allSources: '所有来源',
    resultsCount: '结果数量',
    noResultsFound: '未找到相关文档',
    searchError: '搜索失败，请稍后重试',
    inputRequired: '请输入搜索内容',
    summary: '搜索结果摘要',
    searchingText: '搜索中...',
    similarity: '相似度',
    source: '来源',
    page: '页码',
    expand: '展开',
  },
  
  // 上传文档页面
  uploadDocument: {
    title: '上传文档',
    tabPdf: '上传PDF文件',
    tabText: '输入文本内容',
    intelligentChunking: '智能分块设置',
    smartChunking: '智能分块',
    fixedChunking: '固定分块',
    chunkSize: '分块大小',
    overlapSize: '重叠大小',
    dragText: '点击或拖拽文件到此区域上传',
    dropHint: '仅支持PDF文件，系统将自动处理并创建向量索引',
    textAreaLabel: '文本内容',
    textAreaPlaceholder: '请输入要添加的文本内容...',
    sourceLabel: '来源',
    sourcePlaceholder: '文档来源(可选)',
    authorLabel: '作者',
    authorPlaceholder: '作者(可选)',
    addTextBtn: '添加文本',
    uploadSuccess: '上传成功',
    uploadFailed: '上传失败，请稍后重试',
    inputRequired: '请输入文本内容',
    fileTypeError: '只能上传PDF文件!',
    processingText: '文件处理中...',
    fileInfoTitle: '文件信息',
    documentId: '文档ID',
    fileName: '文件名',
    chunksProcessed: '处理的文本块数',
  },
  
  // 智能问答页面
  queryAssistant: {
    title: '智能问答',
    sourceSelect: '文档来源',
    allSources: '所有文档',
    useContext: '使用文档上下文',
    noContext: '仅使用模型知识',
    maxContextDocs: '最大引用文档数',
    clearChat: '清空对话',
    inputPlaceholder: '输入问题...',
    thinking: '思考中...',
    contextDocsLabel: '参考文档',
    moreContextDocs: '还有 {count} 个参考文档',
    startChat: '开始与AI助手对话',
    errorFetch: '获取回答失败，请稍后重试',
    forceUseDocuments: '强制使用文档',
    referenceDocument: '参考文档',
    documentFragment: '文档片段',
    additionalDocuments: '还有 {count} 个参考文档',
    importDialog: {
      title: '导入对话记录',
      selectFile: '选择文件',
      description: '请选择之前导出的对话记录文件（JSON格式）。',
      warning: '注意：导入将会替换当前的对话记录。'
    }
  },
  
  // 页脚
  footer: {
    copyright: 'Smart RAG Platform ©{year} 由Google Gemini 2.5提供支持',
  }
}; 
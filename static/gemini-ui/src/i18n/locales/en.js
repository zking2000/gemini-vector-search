export default {
  // Common
  common: {
    loading: 'Loading...',
    search: 'Search',
    cancel: 'Cancel',
    confirm: 'Confirm',
    delete: 'Delete',
    edit: 'Edit',
    save: 'Save',
    view: 'View',
    upload: 'Upload',
    download: 'Download',
    success: 'Success',
    failed: 'Failed',
    unknown: 'Unknown',
    noData: 'No data available',
    back: 'Back',
    more: 'More',
    on: 'On',
    off: 'Off'
  },
  
  // Authentication
  auth: {
    login: 'Login',
    logout: 'Logout',
    username: 'Username',
    password: 'Password',
    rememberMe: 'Remember me',
    loginButton: 'Login',
    welcomeBack: 'Welcome Back',
    loginTitle: 'Smart RAG Platform',
    loginSubtitle: 'Please enter your credentials',
    invalidCredentials: 'Invalid username or password',
    logoutConfirm: 'Are you sure you want to log out?',
    loginRequired: 'Please login first',
    usernameRequired: 'Please input your username',
    passwordRequired: 'Please input your password',
    availableUsers: 'Available users',
  },
  
  // Navigation
  nav: {
    home: 'Home',
    documentList: 'Document List',
    uploadDocument: 'Upload Document',
    queryAssistant: 'Query Assistant',
    strategyEvaluation: 'Strategy Evaluation'
  },
  
  // Home page
  home: {
    title: 'Smart RAG Platform',
    subtitle: 'Intelligent Document Retrieval and Q&A System based on Google Gemini 2.5 Pro',
    statsDocuments: 'Total Documents',
    statsChunks: 'Total Text Chunks',
    statsUpdated: 'Last Updated',
    cardSearchTitle: 'Search Documents',
    cardSearchDesc: 'Find relevant information in existing documents using vector search technology, supporting semantic search and similarity ranking.',
    cardSearchBtn: 'Start Search',
    cardUploadTitle: 'Upload Documents',
    cardUploadDesc: 'Upload PDF documents, the system will automatically process and generate vector representations, supporting intelligent chunking.',
    cardUploadBtn: 'Upload Document',
    cardAssistantTitle: 'AI Assistant',
    cardAssistantDesc: 'Ask questions about your documents, the system will generate answers based on document content, supporting complex queries and context understanding.',
    cardAssistantBtn: 'Start Conversation',
  },
  
  // Document list page
  documentList: {
    title: 'Document List',
    empty: 'No documents',
    upload: 'Upload Document',
    search: 'Search Documents',
    source: 'Source',
    createdAt: 'Created At',
    actions: 'Actions',
    delete: 'Delete',
    deleteConfirm: 'Are you sure you want to delete this document?',
    deleteSuccess: 'Document deleted successfully',
    deleteError: 'Failed to delete document',
    chunkingStrategy: {
      fixed_size: 'Fixed Chunking',
      intelligent: 'Intelligent Chunking'
    }
  },
  
  // Document search page
  documentSearch: {
    title: 'Document Search',
    searchPlaceholder: 'Enter search content...',
    sourceSelect: 'Select document source',
    allSources: 'All sources',
    resultsCount: 'Result count',
    noResultsFound: 'No related documents found',
    searchError: 'Search failed, please try again later',
    inputRequired: 'Please enter search content',
    summary: 'Search Results Summary',
    searchingText: 'Searching...',
    similarity: 'Similarity',
    source: 'Source',
    page: 'Page',
    expand: 'Expand',
  },
  
  // Upload document page
  uploadDocument: {
    title: 'Upload Document',
    tabPdf: 'Upload PDF File',
    tabText: 'Input Text Content',
    intelligentChunking: 'Intelligent Chunking Settings',
    smartChunking: 'Smart Chunking',
    fixedChunking: 'Fixed Chunking',
    chunkSize: 'Chunk Size',
    overlapSize: 'Overlap Size',
    dragText: 'Click or drag file to this area to upload',
    dropHint: 'Only PDF files are supported, the system will automatically process and create vector index',
    textAreaLabel: 'Text Content',
    textAreaPlaceholder: 'Please enter the text content to add...',
    sourceLabel: 'Source',
    sourcePlaceholder: 'Document source (optional)',
    authorLabel: 'Author',
    authorPlaceholder: 'Author (optional)',
    addTextBtn: 'Add Text',
    uploadSuccess: 'Upload Successful',
    uploadFailed: 'Upload failed, please try again later',
    inputRequired: 'Please enter text content',
    fileTypeError: 'Only PDF files can be uploaded!',
    processingText: 'Processing file...',
    fileInfoTitle: 'File Information',
    documentId: 'Document ID',
    fileName: 'File Name',
    chunksProcessed: 'Processed Text Chunks',
  },
  
  // Query assistant page
  queryAssistant: {
    title: 'AI Assistant',
    sourceSelect: 'Document Source',
    allSources: 'All Documents',
    useContext: 'Use Document Context',
    noContext: 'Use Model Knowledge Only',
    maxContextDocs: 'Max Reference Docs',
    clearChat: 'Clear Chat',
    inputPlaceholder: 'Enter your question...',
    thinking: 'Thinking...',
    contextDocsLabel: 'Reference Documents',
    moreContextDocs: '{count} more reference documents',
    startChat: 'Start chatting with AI Assistant',
    errorFetch: 'Failed to get answer, please try again later',
    forceUseDocuments: 'Force Use Documents',
    referenceDocument: 'Reference Documents',
    documentFragment: 'Document Fragment',
    additionalDocuments: '{count} more reference documents',
    importDialog: {
      title: 'Import Chat History',
      selectFile: 'Select File',
      description: 'Please select a previously exported chat history file (JSON format).',
      warning: 'Note: Importing will replace the current chat history.'
    }
  },
  
  // Footer
  footer: {
    copyright: 'Smart RAG Platform ©{year} Powered by Google Gemini 2.5',
  }
}; 
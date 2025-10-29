import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 30000
})

// 请求拦截器
api.interceptors.request.use(
  config => {
    return config
  },
  error => {
    return Promise.reject(error)
  }
)

// 响应拦截器
api.interceptors.response.use(
  response => {
    return response.data
  },
  error => {
    console.error('API Error:', error)
    return Promise.reject(error)
  }
)

export const apiService = {
  // 内容相关
  getContentList: () => api.get('/content/list/'),
  getContentDetail: (id) => api.get(`/content/${id}/`),
  deleteContent: (id) => api.delete(`/content/${id}/`),
  
  // 生成相关
  uploadPdf: (file, onProgress) => {
    const formData = new FormData()
    formData.append('file', file)
    return api.post('/generate/upload/', formData, {
      onUploadProgress: onProgress
    })
  },
  generateFromUrl: (url) => api.post('/generate/url/', { url }),
  generateFromText: (text) => api.post('/generate/text/', { question: text }),
  
  // 其他
  getIndexImages: () => api.get('/index/images/'),
  searchPapers: (query) => api.get('/search/', { params: { q: query } }),
  proxyPdf: (url, onProgress) => api.get('/proxy/pdf/', {
    params: { url },
    responseType: 'blob',
    onDownloadProgress: onProgress
  }),
  
  // 词云
  extractWordcloud: (pdfUrl) => api.post('/wordcloud/extract/', { pdf_url: pdfUrl }),
  
  // AI模型配置
  getAIConfig: () => api.get('/ai/config/'),
  saveAIConfig: (config) => api.post('/ai/config/', config),
  getAIOptions: () => api.get('/ai/options/'),
  
  // 翻译和聊天
  translateText: (text, targetLang) => api.post('/translate/', { text, target_lang: targetLang }),
  chatWithText: (messages, contextText) => api.post('/chat/', { messages, context_text: contextText }),
  
  // 流式翻译和聊天（返回EventSource URL）
  getTranslateStreamUrl: () => '/api/translate/stream/',
  getChatStreamUrl: () => '/api/chat/stream/',
  
  // 会话管理
  getSessions: () => api.get('/sessions/'),
  getSession: (sessionId) => api.get(`/sessions/${sessionId}/`),
  createSession: (data) => api.post('/sessions/', data),
  deleteSession: (sessionId) => api.delete(`/sessions/${sessionId}/`)
}

export default api

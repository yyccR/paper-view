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
  extractWordcloud: (pdfUrl) => api.post('/wordcloud/extract/', { pdf_url: pdfUrl })
}

export default api

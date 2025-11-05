<template>
  <div class="workspace-container">
    <Sidebar 
      @toggle-home="handleHomeToggle"
      @toggle-space="handleSpaceToggle"
      @toggle-ai="handleAIToggle"
      @toggle-subscribe="handleSubscribeToggle"
      @toggle-notification="handleNotificationToggle"
      @toggle-user="handleUserToggle"
    />
    
    <!-- 可视化模板边栏 - 组件化 -->
    <TemplateSidebar
      :active="showTemplatePanel"
      :thumbnails="thumbnails"
      :selectedTemplate="selectedTemplate"
      :hoveredTemplate="hoveredTemplate"
      :tooltipPosition="tooltipPosition"
      :getLabel="getLabel"
      :getDescription="getDescription"
      @select-template="selectTemplate"
      @hover-template="handleTemplateHover"
      @leave-template="handleTemplateLeave"
    />
    
    <!-- 遮罩层 - AI面板不显示遮罩 -->
    <div 
      v-if="showNotificationPanel || showUserPanel" 
      class="overlay" 
      @click="closeAllPanels"
    ></div>

    <!-- 通知面板 - 组件化 -->
    <NotificationPanel
      :active="showNotificationPanel"
      :chatSessions="chatSessions"
      :formatTime="formatTime"
      @close="handleNotificationClose"
      @open-session="openSession"
      @delete-session="deleteSession"
    />

    <!-- 用户面板 - 组件化 -->
    <UserPanel :active="showUserPanel" />

    <!-- 翻译聊天面板 -->
    <TranslateChat 
      v-model="showTranslateChat"
      :selectedText="selectionText"
      :targetLang="selectedLang"
      :mode="chatMode"
      :paperTitle="selectedPaperTitle"
      :sessionId="currentOpenSessionId"
      :sessionMessages="currentSessionMessages"
      @sessionClosed="handleSessionClosed"
      @widthChanged="handleChatPanelWidthChange"
    />

    <!-- AI模型配置面板 - 组件化 -->
    <AIConfigPanel
      :active="showAIPanel"
      :aiProviders="aiProviders"
      :expandedProviders="expandedProviders"
      :currentAIConfig="currentAIConfig"
      :showCustomModelForm="showCustomModelForm"
      :customModel="customModel"
      :isCustomModelValid="isCustomModelValid"
      @close="showAIPanel = false"
      @toggle-provider="toggleProvider"
      @select-model="(p) => selectModel(p.provider, p.model)"
      @toggle-custom-form="toggleCustomModelForm"
      @save-custom-model="saveCustomModel"
      @reset-custom-model="resetCustomModelForm"
    />

    <!-- 主工作区 -->
    <main class="workspace" :style="workspaceStyle">
      <!-- 顶部搜索区域（仅在上传文件预览或未预览时显示） -->
      <div class="workspace-header" v-show="!showPdfPreview || isUploadedFile">
        <div class="search-wrapper">
          <button class="upload-btn" @click="triggerFileUpload" :title="$t('workspace.uploadPdf')">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
              <path d="M12 15V3M12 3L8 7M12 3L16 7" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
              <path d="M2 17L2 19C2 20.1046 2.89543 21 4 21L20 21C21.1046 21 22 20.1046 22 19V17" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
            </svg>
          </button>
          <input 
            type="text" 
            class="search-input" 
            v-model="searchQuery"
            @keypress.enter="handleSearch"
            :placeholder="$t('workspace.searchPlaceholder')"
          >
          <button class="search-btn" @click="handleSearch" :disabled="isSearching">
            <svg v-if="!isSearching" width="20" height="20" viewBox="0 0 24 24" fill="none">
              <path d="M21 21L15 15M17 10C17 13.866 13.866 17 10 17C6.13401 17 3 13.866 3 10C3 6.13401 6.13401 3 10 3C13.866 3 17 6.13401 17 10Z" 
                    stroke="currentColor" 
                    stroke-width="2" 
                    stroke-linecap="round"/>
            </svg>
            <div v-else class="search-spinner"></div>
          </button>
        </div>
      </div>

      <!-- 文件预览区域 - 组件化 -->
      <PdfPreviewSection
        :visible="showPdfPreview"
        :showVisualization="showVisualization"
        :pdfExpanded="pdfExpanded"
        :isDownloading="isDownloading"
        :downloadProgress="downloadProgress"
        :downloadError="downloadError"
        :currentFileType="currentFileType"
        :useIframeFallback="useIframeFallback"
        :viewerSrc="viewerSrc"
        :pdfBlobUrl="pdfBlobUrl"
        :selectedPaperTitle="selectedPaperTitle"
        :filePreviewContent="filePreviewContent"
        :excelData="excelData"
        :currentExcelSheet="currentExcelSheet"
        @close-preview="closePdfPreview"
        @viewer-loaded="onChildViewerLoaded"
        @register-pdf-container="(el) => (pdfContainer.value = el)"
        @register-preview-content="(el) => (previewContent.value = el)"
        @set-excel-sheet="(idx) => (currentExcelSheet.value = idx)"
      />

      <!-- 文本选择操作浮层 -->
      <SelectionActions
        :visible="showSelectionActions"
        :position="selectionPos"
        :selectionText="selectionText"
        :selectedLang="selectedLang"
        :langCodes="langCodes"
        :showLangMenu="showLangMenu"
        @mousedown="onToolbarMouseDown"
        @translate="handleTranslate"
        @ask="handleAsk"
        @copy="handleCopy"
        @toggle-lang-menu="toggleLangMenu"
        @select-lang="selectLang"
      />

      <!-- 可视化结果区域 - 组件化 -->
      <VisualizationSection
        :visible="showVisualization"
        :visualizationData="visualizationData"
        :wordCloudData="wordCloudData"
        :vosviewerData="vosviewerData"
        :densityData="densityData"
        @back-to-pdf="backToPdfPreview"
      />

      <!-- 内容展示区域 -->
      <div class="content-section" v-show="!showPdfPreview">
        <!-- 欢迎界面 -->
        <div class="welcome-view" v-if="currentView === 'welcome'">
          <div class="welcome-icon">
            <svg width="80" height="80" viewBox="0 0 24 24" fill="none">
              <path d="M13 2L3 14H12L11 22L21 10H12L13 2Z" stroke="currentColor" stroke-width="2" stroke-linejoin="round"/>
            </svg>
          </div>
          <h2>{{ $t('workspace.welcome.title') }}</h2>
          <p>{{ $t('workspace.welcome.subtitle') }}</p>
        </div>

        <!-- 搜索结果列表 - 组件化 -->
        <SearchResults
          v-if="currentView === 'search'"
          :results="paginatedResults"
          :total="allResults.length"
          :currentPage="currentPage"
          :totalPages="totalPages"
          :pageButtons="pageButtons"
          :startItem="startItem"
          :endItem="endItem"
          @select-paper="selectPaper"
          @goto-page="goToPage"
        />
      </div>
    </main>

    <!-- 隐藏的文件上传输入 -->
    <input type="file" ref="fileInput" accept=".pdf,.doc,.docx,.xls,.xlsx,.csv,.txt" style="display: none;" @change="handleFileUpload">
    
    <!-- 文件上传Loading弹窗 - 组件化 -->
    <UploadProgressModal :visible="showUploadModal" :progress="uploadProgress" />
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, nextTick, watch } from 'vue'
import { useRoute } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { apiService } from '@/api'
// removed unused: isURL
import Sidebar from '@/components/Sidebar.vue'
import TranslateChat from '@/components/TranslateChatNew.vue'
import { parseBibTeX, convertToConnectedPapersFormat } from '@/utils/bibParser'
import NotificationPanel from '@/components/workspace/NotificationPanel.vue'
import UserPanel from '@/components/workspace/UserPanel.vue'
import AIConfigPanel from '@/components/workspace/AIConfigPanel.vue'
import SelectionActions from '@/components/workspace/SelectionActions.vue'
import VisualizationSection from '@/components/workspace/VisualizationSection.vue'
import SearchResults from '@/components/workspace/SearchResults.vue'
import UploadProgressModal from '@/components/workspace/UploadProgressModal.vue'
import TemplateSidebar from '@/components/workspace/TemplateSidebar.vue'
import PdfPreviewSection from '@/components/workspace/PdfPreviewSection.vue'

const { t } = useI18n()

const route = useRoute()

const showNotificationPanel = ref(false)
const showUserPanel = ref(false)
const showAIPanel = ref(false)
const showTemplatePanel = ref(true) // 默认显示模板面板
const searchQuery = ref('')
const currentView = ref('welcome')
const isSearching = ref(false)
const thumbnails = ref([])
// 根据图片文件名获取标签（使用 i18n）
const getLabel = (imageName) => {
  const key = imageName.replace('.png', '')
  return t(`workspace.templates.${key}`, imageName.replace('.png', ''))
}

// 子组件 iframe 加载完成回调：桥接到原有逻辑
const onChildViewerLoaded = (frameEl) => {
  try {
    viewerFrame.value = frameEl
  } catch (e) {}
  onViewerLoaded()
}

// 根据图片文件名获取描述（使用 i18n）
const getDescription = (imageName) => {
  const key = imageName.replace('.png', '')
  return t(`workspace.templates.descriptions.${key}`, '')
}

// 悬浮状态
const hoveredTemplate = ref(null)
const tooltipPosition = ref(null)
// removed: was used for old sidebar DOM refs

// AI模型配置相关
const aiProviders = ref({})
const expandedProviders = ref(new Set())
const currentAIConfig = ref(null)
const showCustomModelForm = ref(false)
const customModel = ref({
  provider: '',
  modelName: '',
  apiBase: '',
  apiKey: '',
  description: ''
})

// 文本选择浮层状态
const previewContent = ref(null)
const selectionText = ref('')
const selectionPos = ref({ top: 0, left: 0 })
const showSelectionActions = ref(false)
const interactingToolbar = ref(false)
const showLangMenu = ref(false)
const langCodes = ref(['zh', 'en', 'ja', 'ko', 'es'])
const selectedLang = ref('zh')
const showTranslateChat = ref(false)
const chatMode = ref('translate') // 'translate' or 'chat'
const chatSessions = ref([]) // 会话历史
const currentOpenSessionId = ref(null) // 当前打开的会话ID
const currentSessionMessages = ref([]) // 当前会话的消息列表
const chatPanelWidth = ref(280) // 聊天面板宽度

// 文件预览相关
const currentFileType = ref('pdf') // 当前文件类型: pdf, word, excel, text
const filePreviewContent = ref('') // 文件预览内容（Word/TXT）
const excelData = ref(null) // Excel 数据
const currentExcelSheet = ref(0) // 当前 Excel Sheet 索引
const isUploadedFile = ref(false) // 是否是上传的文件（区分于论文预览）
// 文件上传loading弹窗
const showUploadModal = ref(false)
const uploadProgress = ref(0)

// 模板侧边栏固定宽度（需与 CSS `.template-sidebar` 的宽度保持一致）
const TEMPLATE_SIDEBAR_WIDTH = 280

// moved to PdfPreviewSection

// moved to UploadProgressModal

const getViewportClampedPos = (baseTop, baseLeft, selWidth) => {
  const margin = 8
  const toolbarWidth = 240
  const toolbarHeight = 36
  // baseTop/baseLeft 已是相对视口的坐标
  let top = Math.max(0, baseTop - margin - toolbarHeight)
  let left = baseLeft + Math.max(0, (selWidth - toolbarWidth) / 2)
  // 视口边界约束（基于视口，不考虑页面滚动）
  const minLeft = margin
  const maxLeft = window.innerWidth - toolbarWidth - margin
  if (left < minLeft) left = minLeft
  if (left > maxLeft) left = maxLeft
  return { top, left }
}

const updateSelectionFromWindow = (doc) => {
  try {
    const sel = doc.getSelection ? doc.getSelection() : window.getSelection()
    if (!sel || sel.isCollapsed) {
      // 若正在与工具条交互或语言菜单打开，则不隐藏
      if (!(interactingToolbar.value || showLangMenu.value)) {
        selectionText.value = ''
        showSelectionActions.value = false
      }
      return
    }
    const text = sel.toString().trim()
    if (!text) {
      if (!(interactingToolbar.value || showLangMenu.value)) {
        selectionText.value = ''
        showSelectionActions.value = false
      }
      return
    }
    const range = sel.rangeCount > 0 ? sel.getRangeAt(0) : null
    if (!range) return
    
    // 检查选中的文本是否在PDF文档区域内
    const isInPdfArea = () => {
      // 如果doc不是主文档（即在iframe内），直接允许
      if (doc !== window.document) {
        return true
      }
      
      // 如果是在主文档，检查选中文本的容器元素
      let container = range.commonAncestorContainer
      if (container.nodeType === Node.TEXT_NODE) {
        container = container.parentElement
      }
      
      // 检查是否在.pdf-viewer, .pdf-canvas-container或.preview-content区域内
      if (container && container.closest) {
        return !!(container.closest('.pdf-viewer') || 
                 container.closest('.pdf-canvas-container') || 
                 container.closest('.preview-content'))
      }
      
      return false
    }
    
    // 如果不在PDF文档区域内，不显示弹窗
    if (!isInPdfArea()) {
      if (!(interactingToolbar.value || showLangMenu.value)) {
        selectionText.value = ''
        showSelectionActions.value = false
      }
      return
    }
    
    const rect = range.getBoundingClientRect()
    if (!rect || (rect.width === 0 && rect.height === 0)) return
    selectionText.value = text
    // 计算页面坐标：区分主文档与iframe文档
    const frameEl = doc.defaultView && doc.defaultView.frameElement
    if (frameEl) {
      const iframeRect = frameEl.getBoundingClientRect()
      const baseTop = iframeRect.top + rect.top
      const baseLeft = iframeRect.left + rect.left
      selectionPos.value = getViewportClampedPos(baseTop, baseLeft, rect.width)
    } else {
      selectionPos.value = getViewportClampedPos(rect.top, rect.left, rect.width)
    }
    showSelectionActions.value = true
  } catch (e) {
    // ignore
  }
}

const clearSelectionActions = () => {
  selectionText.value = ''
  showSelectionActions.value = false
  showLangMenu.value = false
  interactingToolbar.value = false
}

const handleCopy = async () => {
  try {
    await navigator.clipboard.writeText(selectionText.value)
  } catch (e) {
    // fallback
    const ta = document.createElement('textarea')
    ta.value = selectionText.value
    document.body.appendChild(ta)
    ta.select()
    document.execCommand('copy')
    document.body.removeChild(ta)
  }
  clearSelectionActions()
}

const handleTranslate = () => {
  // 清空历史会话数据，开始新对话
  currentOpenSessionId.value = null
  currentSessionMessages.value = []
  
  // 如果面板已打开且是翻译模式，临时切换模式来触发新翻译
  if (showTranslateChat.value && chatMode.value === 'translate') {
    chatMode.value = 'chat'
    nextTick(() => {
      chatMode.value = 'translate'
    })
  } else {
    // 打开翻译模式的聊天面板
    chatMode.value = 'translate'
    showTranslateChat.value = true
  }
  // 不清除选择文本，保持浮层可见直到面板打开后
  setTimeout(() => {
    clearSelectionActions()
  }, 100)
}

const handleAsk = () => {
  // 清空历史会话数据，开始新对话
  currentOpenSessionId.value = null
  currentSessionMessages.value = []
  
  // 打开聊天模式的面板
  chatMode.value = 'chat'
  showTranslateChat.value = true
  setTimeout(() => {
    clearSelectionActions()
  }, 100)
}

const toggleLangMenu = () => {
  showLangMenu.value = !showLangMenu.value
}

const selectLang = (code) => {
  selectedLang.value = code
  showLangMenu.value = false
}

// 当点击工具条时，保持浮层可见（避免selectionchange导致隐藏）
const onToolbarMouseDown = () => {
  interactingToolbar.value = true
}

// 选择事件绑定与清理
let detachters = []
const attachSelectionListenersTo = (doc) => {
  if (!doc) return
  const onMouseUp = () => setTimeout(() => updateSelectionFromWindow(doc), 0)
  const onKeyUp = () => setTimeout(() => updateSelectionFromWindow(doc), 0)
  const onSelectionChange = () => setTimeout(() => updateSelectionFromWindow(doc), 0)
  const onMouseDown = (e) => {
    const target = e.target
    if (!(target && target.closest && target.closest('.selection-actions'))) {
      // 点击到其他地方时，先隐藏
      clearSelectionActions()
    }
  }
  doc.addEventListener('mouseup', onMouseUp)
  doc.addEventListener('keyup', onKeyUp)
  doc.addEventListener('selectionchange', onSelectionChange)
  doc.addEventListener('mousedown', onMouseDown)
  const onScroll = () => clearSelectionActions()
  const onResize = () => clearSelectionActions()
  window.addEventListener('scroll', onScroll, true)
  window.addEventListener('resize', onResize)
  detachters.push(() => {
    try {
      doc.removeEventListener('mouseup', onMouseUp)
      doc.removeEventListener('keyup', onKeyUp)
      doc.removeEventListener('selectionchange', onSelectionChange)
      doc.removeEventListener('mousedown', onMouseDown)
      window.removeEventListener('scroll', onScroll, true)
      window.removeEventListener('resize', onResize)
    } catch {}
  })
}

// 处理模板悬浮事件
const handleTemplateHover = (index, event) => {
  hoveredTemplate.value = index
  const target = event.currentTarget
  const rect = target.getBoundingClientRect()
  
  // tooltip尺寸估算（与CSS中的尺寸对应）
  const tooltipHeight = 260 // 大约高度：标题+图片160px+描述+padding
  const tooltipWidth = 280
  
  // 计算初始位置：在元素右侧，垂直居中
  let top = rect.top + rect.height / 2
  let left = rect.right + 12
  
  // 检查是否超出视口底部
  const viewportHeight = window.innerHeight
  const halfTooltipHeight = tooltipHeight / 2
  
  if (top + halfTooltipHeight > viewportHeight) {
    // 超出底部，调整为底部对齐
    top = viewportHeight - tooltipHeight - 10 // 10px底部边距
  } else if (top - halfTooltipHeight < 0) {
    // 超出顶部，调整为顶部对齐
    top = 10 // 10px顶部边距
  }
  
  // 检查是否超出视口右侧
  const viewportWidth = window.innerWidth
  if (left + tooltipWidth > viewportWidth) {
    // 超出右侧，显示在元素左侧
    left = rect.left - tooltipWidth - 12
  }
  
  tooltipPosition.value = {
    top: top,
    left: left,
    transform: (top === rect.top + rect.height / 2) ? 'translateY(-50%)' : 'none'
  }
}

// 处理鼠标离开事件
const handleTemplateLeave = () => {
  hoveredTemplate.value = null
  tooltipPosition.value = null
}

// 新增状态
const selectedTemplate = ref(null)
const selectedPaperTitle = ref('')
const showPdfPreview = ref(false)
const showVisualization = ref(false)
const isProcessing = ref(false)
const visualizationImage = ref('')
const visualizationData = ref(null)
const wordCloudData = ref([])
const vosviewerData = ref(null)
const densityData = ref(null)
const pdfExpanded = ref(false)
const currentPdfUrl = ref('')
// 跟踪已加载的可视化模板
const loadedVisualizations = ref([])
// PDF 下载与预览
const isDownloading = ref(false)
const downloadProgress = ref(0)
const downloadError = ref('') // PDF下载错误信息
// PDF.js 渲染相关 / 专用viewer
const pdfContainer = ref(null)
// inline pdf.js rendering related states moved to child; keep only what is still used
const pdfBlobUrl = ref('')
const useIframeFallback = ref(false)
const viewerSrc = ref('')
const viewerFrame = ref(null)

const allResults = ref([])
const currentPage = ref(1)
const itemsPerPage = 10
const fileInput = ref(null)

const totalPages = computed(() => Math.ceil(allResults.value.length / itemsPerPage))
const startItem = computed(() => (currentPage.value - 1) * itemsPerPage + 1)
const endItem = computed(() => Math.min(currentPage.value * itemsPerPage, allResults.value.length))

const paginatedResults = computed(() => {
  const start = (currentPage.value - 1) * itemsPerPage
  return allResults.value.slice(start, start + itemsPerPage)
})

const pageButtons = computed(() => {
  const maxButtons = 5
  let start = Math.max(1, currentPage.value - Math.floor(maxButtons / 2))
  let end = Math.min(totalPages.value, start + maxButtons - 1)
  if (end - start < maxButtons - 1) {
    start = Math.max(1, end - maxButtons + 1)
  }
  return Array.from({ length: end - start + 1 }, (_, i) => start + i)
})

const loadThumbnails = async () => {
  try {
    const data = await apiService.getIndexImages()
    if (data.images) {
      thumbnails.value = data.images
    }
  } catch (error) {
    console.error('加载缩略图失败:', error)
  }
}

const handleSearch = async () => {
  const query = searchQuery.value.trim()
  if (!query || isSearching.value) return

  isSearching.value = true
  currentView.value = 'search'
  try {
    const data = await apiService.searchPapers(query)
    const results = Array.isArray(data?.results) ? data.results : []
    allResults.value = results.map(r => ({
      title: r.title,
      authors: r.authors,
      abstract: r.abstract,
      year: r.year,
      citations: r.citations || 0,
      url: r.url,
      pdf_url: r.pdf_url
    }))
  } catch (error) {
    console.error('搜索失败:', error)
    allResults.value = []
  } finally {
    isSearching.value = false
  }
  currentPage.value = 1
}

const generateMockResults = (query) => {
  const mockResults = []
  for (let i = 1; i <= 20; i++) {
    mockResults.push({
      title: `关于"${query}"的研究论文 ${i}`,
      authors: 'Zhang Wei, Li Ming, Wang Fang',
      abstract: '这是一篇关于人工智能和机器学习的研究论文。本文探讨了深度学习在自然语言处理中的应用。',
      year: 2020 + (i % 5),
      citations: Math.floor(Math.random() * 100)
    })
  }
  return mockResults
}

const goToPage = (page) => {
  if (page < 1 || page > totalPages.value || page === currentPage.value) return
  currentPage.value = page
}

const triggerFileUpload = () => {
  fileInput.value.click()
}

const handleFileUpload = async (event) => {
  const file = event.target.files[0]
  if (!file) return
  
  // 验证文件类型
  const allowedExtensions = ['.pdf', '.doc', '.docx', '.xls', '.xlsx', '.csv', '.txt']
  const fileExtension = '.' + file.name.split('.').pop().toLowerCase()
  
  if (!allowedExtensions.includes(fileExtension)) {
    alert('不支持的文件类型。支持的格式：PDF, Word, Excel, CSV, TXT')
    return
  }
  
  // 显示上传弹窗
  showUploadModal.value = true
  uploadProgress.value = 0
  
  try {
    // 上传文件
    const response = await apiService.uploadFile(file, (progressEvent) => {
      if (progressEvent.total) {
        uploadProgress.value = Math.round((progressEvent.loaded * 100) / progressEvent.total)
      }
    })
    
    if (response.success) {
      // 上传成功，关闭弹窗，加载预览
      showUploadModal.value = false
      await loadFilePreview(response)
    } else {
      showUploadModal.value = false
      alert('上传失败：' + (response.error || '未知错误'))
    }
  } catch (error) {
    console.error('Upload error:', error)
    showUploadModal.value = false
    alert('上传失败，请重试')
  }
  
  // 清空 input
  event.target.value = ''
}

// 加载文件预览
const loadFilePreview = async (fileInfo) => {
  try {
    currentFileType.value = fileInfo.file_type
    selectedPaperTitle.value = fileInfo.filename
    showPdfPreview.value = true
    showVisualization.value = false
    isUploadedFile.value = false // 文件预览时也隐藏搜索框
    
    if (fileInfo.file_type === 'pdf') {
      // PDF: 使用 iframe 预览
      const previewUrl = `/api/files/preview/${fileInfo.file_id}/`
      viewerSrc.value = `/pdf-viewer.html?file=${encodeURIComponent(previewUrl)}&name=${encodeURIComponent(fileInfo.filename)}`
      useIframeFallback.value = true
      isDownloading.value = false
    } else {
      // 其他文件类型：调用 API 获取预览内容
      const response = await apiService.previewFile(fileInfo.file_id)
      
      if (response.success || response.file_type) {
        if (fileInfo.file_type === 'text' || fileInfo.file_type === 'word') {
          filePreviewContent.value = response.content
        } else if (fileInfo.file_type === 'excel') {
          excelData.value = response.data
          currentExcelSheet.value = 0
        }
      } else {
        alert('预览失败：' + (response.error || '未知错误'))
      }
      isDownloading.value = false
    }
  } catch (error) {
    console.error('Preview error:', error)
    alert('预览失败')
    isDownloading.value = false
  }
}

// 加载从首页上传的文件
const loadUploadedFile = async () => {
  const uploadedFileInfo = sessionStorage.getItem('uploadedFileInfo')
  if (uploadedFileInfo) {
    try {
      const fileInfo = JSON.parse(uploadedFileInfo)
      sessionStorage.removeItem('uploadedFileInfo')
      await loadFilePreview(fileInfo)
    } catch (error) {
      console.error('Load uploaded file error:', error)
    }
  }
}

const selectTemplate = (index) => {
  selectedTemplate.value = index
  const imageName = thumbnails.value[index]
  const templateName = getLabel(imageName)
  console.log('选中模板:', templateName)
  // 通知内置viewer启用"应用可视化"按钮
  if (viewerFrame.value && viewerFrame.value.contentWindow) {
    viewerFrame.value.contentWindow.postMessage({ type: 'set-apply-enabled', enabled: true }, '*')
  }
}

const selectPaper = async (paper) => {
  selectedPaperTitle.value = paper.title
  currentPdfUrl.value = paper.pdf_url
  showPdfPreview.value = true
  showVisualization.value = false
  visualizationData.value = null
  wordCloudData.value = []
  vosviewerData.value = null
  densityData.value = null
  loadedVisualizations.value = []
  pdfBlobUrl.value = ''
  isDownloading.value = true
  downloadProgress.value = 0
  downloadError.value = '' // 清空错误
  useIframeFallback.value = false
  isUploadedFile.value = false // 论文预览时隐藏搜索框
  currentFileType.value = 'pdf' // 确保文件类型设置为PDF
  // 清空非PDF文件的预览内容
  filePreviewContent.value = ''
  excelData.value = null
  currentExcelSheet.value = 0
  try {
    const resp = await apiService.proxyPdf(paper.pdf_url, (e) => {
      if (e && e.total) {
        downloadProgress.value = Math.min(100, Math.round((e.loaded / e.total) * 100))
      }
    })
    // Axios 已返回 Blob
    const blob = resp
    // 创建blob URL
    pdfBlobUrl.value = URL.createObjectURL(blob)
    // 解析文件名用于下载（取原pdf链接最后一段）
    let name = 'document.pdf'
    try {
      if (paper.pdf_url) {
        const u = new URL(paper.pdf_url)
        const seg = u.pathname.split('/').filter(Boolean).pop() || 'document'
        name = seg.endsWith('.pdf') ? seg : `${seg}.pdf`
      }
    } catch (e) {}
    // 使用内置viewer页面进行阅读器式预览（携带name参数）
    viewerSrc.value = `/pdf-viewer.html?file=${encodeURIComponent(pdfBlobUrl.value)}&name=${encodeURIComponent(name)}`
    useIframeFallback.value = true
  } catch (err) {
    console.error('PDF下载失败:', err)
    downloadError.value = 'PDF下载失败，请检查网络连接或稍后重试'
  } finally {
    isDownloading.value = false
  }
}

const onViewerLoaded = () => {
  // iframe加载完成后，设置初始状态
  if (viewerFrame.value && viewerFrame.value.contentWindow) {
    // 设置应用按钮可用状态
    const enabled = selectedTemplate.value !== null
    viewerFrame.value.contentWindow.postMessage({ type: 'set-apply-enabled', enabled }, '*')
    
    // 如果有已加载的可视化，显示返回按钮
    if (loadedVisualizations.value.length > 0) {
      const vizButtons = loadedVisualizations.value.map(v => ({
        id: v.id,
        name: v.templateName
      }))
      viewerFrame.value.contentWindow.postMessage({ 
        type: 'show-viz-buttons', 
        buttons: vizButtons 
      }, '*')
    }
    // 绑定选择监听到内置PDF viewer文档
    try {
      const doc = viewerFrame.value.contentDocument || viewerFrame.value.contentWindow.document
      attachSelectionListenersTo(doc)
    } catch (e) {
      // ignore cross-origin or timing issues
    }
  }
}

const closePdfPreview = () => {
  showPdfPreview.value = false
  showVisualization.value = false
  visualizationData.value = null
  vosviewerData.value = null
  densityData.value = null
  pdfExpanded.value = false
  // 清空已加载的可视化记录
  loadedVisualizations.value = []
  // 释放blob URL
  if (pdfBlobUrl.value) {
    URL.revokeObjectURL(pdfBlobUrl.value)
    pdfBlobUrl.value = ''
  }
  // 清空pdf容器
  if (pdfContainer.value) {
    pdfContainer.value.innerHTML = ''
  }
  viewerSrc.value = ''
  // 重置文件预览状态
  isUploadedFile.value = false
  currentFileType.value = 'pdf' // 重置文件类型为默认值
  filePreviewContent.value = ''
  excelData.value = null
  currentExcelSheet.value = 0
}

const applyVisualization = async () => {
  if (selectedTemplate.value === null) {
    console.error('请先选择一个模板')
    return
  }

  const imageName = thumbnails.value[selectedTemplate.value]
  const templateKey = imageName.replace('.png', '')
  const templateName = getLabel(imageName)
  
  // 使用模板key判断是否为词云图，避免受语言切换影响
  if (templateKey === 'wordcloud') {
    if (!currentPdfUrl.value) {
      alert(t('workspace.visualization.noPdfLoaded'))
      return
    }
    
    isProcessing.value = true
    
    try {
      // 调用后端API提取词云数据
      const response = await apiService.extractWordcloud(currentPdfUrl.value)
      
      if (response.success && response.data) {
        wordCloudData.value = response.data
        visualizationData.value = null
        vosviewerData.value = null
        densityData.value = null
        
        // 记录已加载的可视化
        const vizId = `${selectedTemplate.value}-${Date.now()}`
        if (!loadedVisualizations.value.find(v => v.templateIndex === selectedTemplate.value)) {
          loadedVisualizations.value.push({
            id: vizId,
            templateIndex: selectedTemplate.value,
            templateName: templateName,
            data: wordCloudData.value
          })
        }
        
        // 显示可视化
        showVisualization.value = true
        pdfExpanded.value = false
        
        await nextTick()
      } else {
        throw new Error(response.error || t('workspace.visualization.loadFailed'))
      }
    } catch (error) {
      console.error('词云生成失败:', error)
      alert(t('workspace.visualization.wordcloudFailed'))
    } finally {
      isProcessing.value = false
    }
  } else if (templateKey === 'connected_paper') {
    isProcessing.value = true
    
    try {
      // 加载BIB文件
      const response = await fetch('/assets/bib/ConnectedPapers-for-Qwen3-Technical-Report.bib')
      const bibContent = await response.text()
      
      // 解析BIB文件
      const papers = parseBibTeX(bibContent)
      console.log('解析出', papers.length, '篇论文')
      
      // 转换为ConnectedPapers格式
      visualizationData.value = convertToConnectedPapersFormat(papers)
      wordCloudData.value = []
      vosviewerData.value = null
      densityData.value = null
      console.log('可视化数据:', visualizationData.value)
      console.log('节点数量:', visualizationData.value.nodes.length)
      console.log('边数量:', visualizationData.value.edges.length)
      
      // 记录已加载的可视化
      const vizId = `${selectedTemplate.value}-${Date.now()}`
      if (!loadedVisualizations.value.find(v => v.templateIndex === selectedTemplate.value)) {
        loadedVisualizations.value.push({
          id: vizId,
          templateIndex: selectedTemplate.value,
          templateName: templateName,
          data: visualizationData.value
        })
      }
      
      // 显示可视化
      showVisualization.value = true
      pdfExpanded.value = false
      
      // 等待DOM更新后再次触发渲染
      await nextTick()
      
    } catch (error) {
      console.error('可视化失败:', error)
      alert(t('workspace.visualization.loadFailed'))
    } finally {
      isProcessing.value = false
    }
  } else if (templateKey === 'citation_network') {
    isProcessing.value = true
    
    try {
      // 加载 VOSviewer 网络数据
      const response = await fetch('/assets/bib/VOSviewer-network.json')
      const networkData = await response.json()
      
      console.log('VOSviewer 网络数据加载成功')
      console.log('节点数量:', networkData.network?.items?.length || 0)
      console.log('连接数量:', networkData.network?.links?.length || 0)
      
      // 设置 VOSviewer 数据
      vosviewerData.value = networkData
      visualizationData.value = null
      wordCloudData.value = []
      densityData.value = null
      
      // 记录已加载的可视化
      const vizId = `${selectedTemplate.value}-${Date.now()}`
      if (!loadedVisualizations.value.find(v => v.templateIndex === selectedTemplate.value)) {
        loadedVisualizations.value.push({
          id: vizId,
          templateIndex: selectedTemplate.value,
          templateName: templateName,
          data: vosviewerData.value
        })
      }
      
      // 显示可视化
      showVisualization.value = true
      pdfExpanded.value = false
      
      await nextTick()
      
    } catch (error) {
      console.error('加载 VOSviewer 数据失败:', error)
      alert(t('workspace.visualization.loadFailed'))
    } finally {
      isProcessing.value = false
    }
  } else if (templateKey === 'heatmap') {
    isProcessing.value = true
    
    try {
      // 加载 VOSviewer 网络数据用于密度可视化
      const response = await fetch('/assets/bib/VOSviewer-network.json')
      const networkData = await response.json()
      
      console.log('加载密度可视化数据成功')
      console.log('节点数量:', networkData.network?.items?.length || 0)
      
      // 设置密度数据
      densityData.value = networkData
      visualizationData.value = null
      wordCloudData.value = []
      vosviewerData.value = null
      
      // 记录已加载的可视化
      const vizId = `${selectedTemplate.value}-${Date.now()}`
      if (!loadedVisualizations.value.find(v => v.templateIndex === selectedTemplate.value)) {
        loadedVisualizations.value.push({
          id: vizId,
          templateIndex: selectedTemplate.value,
          templateName: templateName,
          data: densityData.value
        })
      }
      
      // 显示可视化
      showVisualization.value = true
      pdfExpanded.value = false
      
      await nextTick()
      
    } catch (error) {
      console.error('加载密度可视化数据失败:', error)
      alert(t('workspace.visualization.loadFailed'))
    } finally {
      isProcessing.value = false
    }
  } else {
    // 其他模板使用原有逻辑
    isProcessing.value = true
    await new Promise(resolve => setTimeout(resolve, 2000))
    visualizationImage.value = '/assets/index_images/visualization_sample.png'
    
    // 记录已加载的可视化
    const vizId = `${selectedTemplate.value}-${Date.now()}`
    if (!loadedVisualizations.value.find(v => v.templateIndex === selectedTemplate.value)) {
      loadedVisualizations.value.push({
        id: vizId,
        templateIndex: selectedTemplate.value,
        templateName: templateName,
        data: null
      })
    }
    
    showVisualization.value = true
    isProcessing.value = false
  }
  
  // 通知内置viewer处理完成，恢复按钮，并隐藏返回可视化按钮
  if (viewerFrame.value && viewerFrame.value.contentWindow) {
    viewerFrame.value.contentWindow.postMessage({ type: 'apply-visualization-done' }, '*')
    viewerFrame.value.contentWindow.postMessage({ type: 'hide-viz-buttons' }, '*')
  }
}

const togglePdfExpand = () => {
  pdfExpanded.value = !pdfExpanded.value
}

const backToPdfPreview = () => {
  // 关闭可视化，返回PDF预览（保留可视化数据）
  showVisualization.value = false
  pdfExpanded.value = false
  
  // 通知 pdf-viewer 显示返回可视化的按钮
  if (viewerFrame.value && viewerFrame.value.contentWindow) {
    const vizButtons = loadedVisualizations.value.map(v => ({
      id: v.id,
      name: v.templateName
    }))
    viewerFrame.value.contentWindow.postMessage({ 
      type: 'show-viz-buttons', 
      buttons: vizButtons 
    }, '*')
  }
}

const returnToVisualization = (vizId) => {
  // 返回可视化界面
  if (vizId) {
    // 如果指定了 vizId，加载对应的可视化
    const viz = loadedVisualizations.value.find(v => v.id === vizId)
    if (viz && viz.data) {
      // 判断数据类型
      if (Array.isArray(viz.data) && viz.data.length > 0 && viz.data[0].word) {
        // 词云数据
        wordCloudData.value = viz.data
        visualizationData.value = null
        vosviewerData.value = null
        densityData.value = null
      } else if (viz.data.network && viz.data.network.items) {
        // 检查是否为密度可视化或VOSviewer网络数据
        // 根据templateName区分（heatmap对应密度可视化）
        const imageName = thumbnails.value[viz.templateIndex]
        const templateKey = imageName?.replace('.png', '')
        
        if (templateKey === 'heatmap') {
          // 密度可视化数据
          densityData.value = viz.data
          visualizationData.value = null
          wordCloudData.value = []
          vosviewerData.value = null
        } else {
          // VOSviewer 网络数据
          vosviewerData.value = viz.data
          visualizationData.value = null
          wordCloudData.value = []
          densityData.value = null
        }
      } else {
        // 关系图数据
        visualizationData.value = viz.data
        wordCloudData.value = []
        vosviewerData.value = null
        densityData.value = null
      }
    }
  }
  showVisualization.value = true
  
  // 通知 pdf-viewer 隐藏返回可视化的按钮
  if (viewerFrame.value && viewerFrame.value.contentWindow) {
    viewerFrame.value.contentWindow.postMessage({ 
      type: 'hide-viz-buttons'
    }, '*')
  }
}

const closeAllPanels = () => {
  showNotificationPanel.value = false
  showUserPanel.value = false
  showAIPanel.value = false
  // 关闭所有面板后，显示主页面板
  showTemplatePanel.value = true
}

// 处理各个按钮的点击事件
const handleHomeToggle = () => {
  showTemplatePanel.value = true
  showAIPanel.value = false
  showNotificationPanel.value = false
  showUserPanel.value = false
}

const handleSpaceToggle = () => {
  // 暂时没有space面板，关闭其他所有面板
  closeAllPanels()
}

const handleAIToggle = () => {
  showAIPanel.value = true
  showTemplatePanel.value = false
  showNotificationPanel.value = false
  showUserPanel.value = false
}

const handleSubscribeToggle = () => {
  // 暂时没有subscribe面板，关闭其他所有面板
  closeAllPanels()
}

const handleNotificationToggle = () => {
  showNotificationPanel.value = true
  showAIPanel.value = false
  showTemplatePanel.value = false
  showUserPanel.value = false
  // 关闭聊天窗口
  showTranslateChat.value = false
  // 刷新会话列表
  loadChatSessions()
}

const handleUserToggle = () => {
  showUserPanel.value = true
  showAIPanel.value = false
  showTemplatePanel.value = false
  showNotificationPanel.value = false
}

const handleNotificationClose = () => {
  showNotificationPanel.value = false
  // 关闭通知面板后，显示主页面板
  showTemplatePanel.value = true
}

const handleChatPanelWidthChange = (width) => {
  chatPanelWidth.value = width
}

// 防守式：面板打开后以 DOM 实际宽度为准，避免偶发的旧值导致间隙
watch(showTranslateChat, (val) => {
  if (val) {
    nextTick(() => {
      try {
        const el = document.querySelector('.translate-chat-panel.active') || document.querySelector('.translate-chat-panel')
        if (el) {
          const w = Math.round(el.getBoundingClientRect().width)
          if (w && w !== chatPanelWidth.value) {
            chatPanelWidth.value = w
          }
        }
      } catch {}
    })
  }
})

// 计算主工作区的样式
const workspaceStyle = computed(() => {
  // 模板侧边栏隐藏时需要补偿其宽度，避免主工作区左移到固定面板下方
  const templateMargin = showTemplatePanel.value ? 0 : TEMPLATE_SIDEBAR_WIDTH
  
  // 聊天面板打开时，如果宽度超过模板侧边栏，需要额外让出空间
  const chatMargin = showTranslateChat.value 
    ? Math.max(0, chatPanelWidth.value - TEMPLATE_SIDEBAR_WIDTH) 
    : 0
  
  const totalMargin = templateMargin + chatMargin
  
  return {
    marginLeft: `${totalMargin}px`,
    transition: 'margin-left 0.3s ease'
  }
})

// AI模型配置相关方法
const loadAIOptions = async () => {
  try {
    const response = await apiService.getAIOptions()
    if (response.success) {
      aiProviders.value = response.data
    }
  } catch (error) {
    console.error('加载AI模型选项失败:', error)
  }
}

const loadCurrentAIConfig = async () => {
  try {
    const response = await apiService.getAIConfig()
    if (response.success && response.data) {
      currentAIConfig.value = response.data
    }
  } catch (error) {
    console.error('加载当前AI配置失败:', error)
  }
}

const toggleProvider = (providerKey) => {
  const next = new Set(expandedProviders.value)
  if (next.has(providerKey)) {
    next.delete(providerKey)
  } else {
    next.add(providerKey)
  }
  expandedProviders.value = next
}

const isModelSelected = (provider, modelId) => {
  return currentAIConfig.value && 
         currentAIConfig.value.provider === provider && 
         currentAIConfig.value.model_name === modelId
}

const selectModel = async (provider, model) => {
  try {
    // 从aiProviders中获取api_base和api_key
    const providerData = aiProviders.value[provider]
    const config = {
      provider: provider,
      model_name: model.id,
      api_base: providerData?.api_base || '',
      api_key: providerData?.api_key || ''
    }
    
    const response = await apiService.saveAIConfig(config)
    if (response.success) {
      currentAIConfig.value = response.data
      console.log('AI模型配置已保存:', response.data)
    }
  } catch (error) {
    console.error('保存AI配置失败:', error)
    alert(t('aiConfig.saveFailed'))
  }
}

const handleLogoError = (e) => {
  // Logo加载失败时使用默认图标
  e.target.style.display = 'none'
}

// 获取提供商显示名称
const getProviderDisplayName = (provider) => {
  const names = {
    'gpt': 'GPT',
    'claude': 'Claude',
    'qwen': '通义千问',
    'doubao': '豆包',
    'gemini': 'Gemini'
  }
  return names[provider] || provider
}

// 检查提供商是否有选中的模型
const hasSelectedModel = (provider) => {
  return currentAIConfig.value && currentAIConfig.value.provider === provider
}

// 自定义模型相关方法
const isCustomModelValid = computed(() => {
  return customModel.value.provider.trim() !== '' && 
         customModel.value.modelName.trim() !== ''
})

const toggleCustomModelForm = () => {
  showCustomModelForm.value = !showCustomModelForm.value
}

const saveCustomModel = async () => {
  if (!isCustomModelValid.value) {
    alert(t('aiConfig.customModel.validationError'))
    return
  }
  
  try {
    const config = {
      provider: customModel.value.provider.trim(),
      model_name: customModel.value.modelName.trim(),
      api_base: customModel.value.apiBase.trim(),
      api_key: customModel.value.apiKey.trim()
    }
    
    const response = await apiService.saveAIConfig(config)
    if (response.success) {
      currentAIConfig.value = response.data
      alert(t('aiConfig.customModel.saveSuccess'))
      resetCustomModelForm()
      showCustomModelForm.value = false
    }
  } catch (error) {
    console.error('保存自定义模型失败:', error)
    alert(t('aiConfig.customModel.saveFailed'))
  }
}

const resetCustomModelForm = () => {
  customModel.value = {
    provider: '',
    modelName: '',
    apiBase: '',
    apiKey: '',
    description: ''
  }
}

// 会话管理相关
const loadChatSessions = async () => {
  try {
    const response = await apiService.getSessions()
    if (response.success) {
      chatSessions.value = response.data
    }
  } catch (error) {
    console.error('加载会话列表失败:', error)
  }
}

const handleSessionClosed = (sessionId) => {
  // 会话关闭时，刷新会话列表
  loadChatSessions()
}

const openSession = async (sessionId) => {
  try {
    // 加载会话详情
    const response = await apiService.getSession(sessionId)
    if (response.success) {
      const session = response.data.session
      const sessionMessages = response.data.messages
      
      console.log('加载会话:', session.title, sessionMessages.length, '条消息')
      
      // 设置会话数据
      currentOpenSessionId.value = sessionId
      currentSessionMessages.value = sessionMessages
      selectedPaperTitle.value = session.paper_title || session.title
      chatMode.value = session.session_type === 'translate' ? 'translate' : 'chat'
      
      // 打开聊天面板
      showTranslateChat.value = true
      
      // 关闭通知面板
      showNotificationPanel.value = false
    }
  } catch (error) {
    console.error('加载会话失败:', error)
    // 即使加载失败，也打开聊天面板
    currentOpenSessionId.value = null
    currentSessionMessages.value = []
    showTranslateChat.value = true
    showNotificationPanel.value = false
  }
}

const deleteSession = async (sessionId) => {
  if (!confirm(t('workspace.notification.confirmDelete'))) {
    return
  }
  
  try {
    const response = await apiService.deleteSession(sessionId)
    if (response.success) {
      // 从列表中移除
      chatSessions.value = chatSessions.value.filter(s => s.id !== sessionId)
    }
  } catch (error) {
    console.error('删除会话失败:', error)
    alert(t('workspace.notification.deleteFailed'))
  }
}

const formatTime = (dateString) => {
  if (!dateString) return ''
  const date = new Date(dateString)
  const now = new Date()
  const diff = now - date
  const minutes = Math.floor(diff / 60000)
  const hours = Math.floor(diff / 3600000)
  const days = Math.floor(diff / 86400000)
  
  if (minutes < 1) return t('workspace.notification.time.justNow')
  if (minutes < 60) return t('workspace.notification.time.minutesAgo', { count: minutes })
  if (hours < 24) return t('workspace.notification.time.hoursAgo', { count: hours })
  if (days < 7) return t('workspace.notification.time.daysAgo', { count: days })
  return date.toLocaleDateString(t('common.locale'), { month: 'short', day: 'numeric' })
}

onMounted(() => {
  loadThumbnails()
  loadAIOptions()
  loadCurrentAIConfig()
  loadChatSessions() // 加载会话历史
  // 监听主文档选择
  attachSelectionListenersTo(document)
  
  // 检查是否有从首页上传的文件
  loadUploadedFile()
  
  const query = route.query.q || route.query.url
  if (query) {
    searchQuery.value = query
    handleSearch()
  }
  // 监听内置viewer返回消息
  const onMessage = (e) => {
    if (e && e.data && e.data.type === 'close-pdf') {
      closePdfPreview()
    }
    if (e && e.data && e.data.type === 'apply-visualization') {
      applyVisualization()
      return
    }
    if (e && e.data && e.data.type === 'return-to-visualization') {
      returnToVisualization(e.data.vizId)
    }
  }
  window.addEventListener('message', onMessage)
  // 保存到实例上以便卸载
  messageListenerRef.value = onMessage
})

const messageListenerRef = ref(null)

onUnmounted(() => {
  if (messageListenerRef.value) {
    window.removeEventListener('message', messageListenerRef.value)
  }
})

// removed: inline pdf.js renderer (now handled in PdfPreviewSection)
</script>

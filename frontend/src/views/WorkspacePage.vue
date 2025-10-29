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
    
    <!-- 可视化模板边栏 - 固定在导航栏右边 -->
    <aside class="template-sidebar" :class="{ active: showTemplatePanel }">
      <div class="template-header">
        <h3>{{ $t('workspace.templates.title') }}</h3>
      </div>
      <div class="template-grid">
        <div 
          v-for="(image, index) in thumbnails" 
          :key="index" 
          class="template-item" 
          :class="{ active: selectedTemplate === index }"
          @click="selectTemplate(index)"
          @mouseenter="handleTemplateHover(index, $event)"
          @mouseleave="handleTemplateLeave"
          ref="templateItems"
        >
          <img :src="`/assets/index_images/${image}`" :alt="`模板 ${index + 1}`" class="template-image">
          <span class="template-label">{{ getLabel(image) }}</span>
        </div>
      </div>
    </aside>
    
    <!-- 悬浮提示框 - 使用Teleport渲染到body -->
    <Teleport to="body">
      <div 
        v-if="hoveredTemplate !== null && tooltipPosition" 
        class="template-tooltip-portal"
        :style="{ 
          top: tooltipPosition.top + 'px', 
          left: tooltipPosition.left + 'px',
          transform: tooltipPosition.transform 
        }"
      >
        <div class="tooltip-content">
          <h4 class="tooltip-title">{{ getLabel(thumbnails[hoveredTemplate]) }}</h4>
          <div class="tooltip-image-wrapper">
            <img :src="`/assets/index_images/${thumbnails[hoveredTemplate]}`" :alt="getLabel(thumbnails[hoveredTemplate])" class="tooltip-image">
          </div>
          <p class="tooltip-description">{{ getDescription(thumbnails[hoveredTemplate]) }}</p>
        </div>
      </div>
    </Teleport>
    
    <!-- 遮罩层 - AI面板不显示遮罩 -->
    <div 
      v-if="showNotificationPanel || showUserPanel" 
      class="overlay" 
      @click="closeAllPanels"
    ></div>

    <!-- 通知面板 - 显示聊天会话历史 -->
    <div class="notification-panel" :class="{ active: showNotificationPanel }">
      <div class="notification-header">
        <h3>{{ $t('workspace.notification.title') }}</h3>
        <button class="close-btn" @click="showNotificationPanel = false">&times;</button>
      </div>
      <div class="notification-list">
        <div 
          v-for="session in chatSessions" 
          :key="session.id"
          class="session-item"
          @click="openSession(session.id)"
        >
          <div class="session-icon">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none">
              <path d="M21 15C21 15.5304 20.7893 16.0391 20.4142 16.4142C20.0391 16.7893 19.5304 17 19 17H7L3 21V5C3 4.46957 3.21071 3.96086 3.58579 3.58579C3.96086 3.21071 4.46957 3 5 3H19C19.5304 3 20.0391 3.21071 20.4142 3.58579C20.7893 3.96086 21 4.46957 21 5V15Z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
          </div>
          <div class="session-content">
            <p class="session-title">{{ session.title }}</p>
            <div class="session-meta">
              <span class="session-type" :class="`type-${session.session_type}`">
                {{ session.session_type === 'translate' ? '翻译' : '对话' }}
              </span>
              <span class="session-count">{{ session.message_count }} 条消息</span>
            </div>
            <span class="session-time">{{ formatTime(session.last_message_at || session.created_at) }}</span>
          </div>
        </div>
        <div v-if="chatSessions.length === 0" class="empty-state">
          <p>{{ $t('workspace.notification.noSessions') }}</p>
        </div>
      </div>
    </div>

    <!-- 用户面板 -->
    <div class="user-panel" :class="{ active: showUserPanel }">
      <div class="user-info">
        <img src="/default-avatar.svg" alt="用户头像" class="user-avatar">
        <div class="user-details">
          <h4>{{ $t('workspace.user.guestUser') }}</h4>
          <p>{{ $t('workspace.user.notLoggedIn') }}</p>
        </div>
      </div>
      <div class="user-menu">
        <a href="#profile" class="menu-item">{{ $t('workspace.user.profile') }}</a>
        <a href="#settings" class="menu-item">{{ $t('workspace.user.settings') }}</a>
        <div class="menu-divider"></div>
        <a href="#login" class="menu-item">{{ $t('workspace.user.login') }}</a>
      </div>
    </div>

    <!-- 翻译聊天面板 -->
    <TranslateChat 
      v-model="showTranslateChat"
      :selectedText="selectionText"
      :targetLang="selectedLang"
      :mode="chatMode"
      :paperTitle="selectedPaperTitle"
      @sessionClosed="handleSessionClosed"
    />

    <!-- AI模型配置面板 -->
    <div class="ai-config-panel" :class="{ active: showAIPanel }">
      <div class="ai-config-header">
        <h3>{{ $t('aiConfig.title') }}</h3>
        <button class="close-btn" @click="showAIPanel = false">&times;</button>
      </div>
      <div class="ai-config-content">
        <!-- 当前选中的模型 -->
        <div v-if="currentAIConfig" class="current-model-info">
          <div class="info-row">
            <div class="info-label">{{ $t('aiConfig.currentModel') }}</div>
            <div class="current-badge">Active</div>
          </div>
          <div class="info-value">
            <span class="provider-tag">{{ getProviderDisplayName(currentAIConfig.provider) }}</span>
            <span class="model-tag">{{ currentAIConfig.model_name }}</span>
          </div>
        </div>
        
        <!-- 模型提供商列表 -->
        <div class="ai-providers-grid">
          <div 
            v-for="(provider, key) in aiProviders" 
            :key="key"
            class="provider-card"
            :class="{ 
              expanded: expandedProviders.has(key),
              'has-selected': hasSelectedModel(key)
            }"
          >
            <div class="provider-header" @click="toggleProvider(key)">
              <div class="provider-info">
                <div class="provider-logo">
                  <img :src="`/assets/logos/${provider.logo}.png`" :alt="provider.name" @error="handleLogoError">
                </div>
                <div class="provider-details">
                  <span class="provider-name">{{ provider.name }}</span>
                  <span class="model-count">{{ provider.models.length }} {{ $t('aiConfig.models') }}</span>
                </div>
              </div>
              <div class="provider-actions">
                <span v-if="hasSelectedModel(key)" class="active-indicator">●</span>
                <svg class="expand-icon" :class="{ rotated: expandedProviders.has(key) }" width="20" height="20" viewBox="0 0 24 24" fill="none">
                  <path d="M6 9L12 15L18 9" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
              </div>
            </div>
            
            <!-- 模型列表：添加向下展开过渡动画 -->
            <transition name="expand-down">
            <div v-show="expandedProviders.has(key)" class="models-list">
              <div 
                v-for="model in provider.models" 
                :key="model.id"
                class="model-item"
                @click="selectModel(key, model)"
                :class="{ selected: isModelSelected(key, model.id) }"
              >
                <div class="model-info">
                  <div class="model-name">
                    {{ model.name }}
                  </div>
                  <div class="model-description">{{ model.description }}</div>
                </div>
                <div v-if="isModelSelected(key, model.id)" class="selected-badge">✓</div>
              </div>
            </div>
            </transition>
          </div>
          
          <!-- 自定义新增模型卡片 -->
          <div class="provider-card custom-model-card" :class="{ expanded: showCustomModelForm }">
            <div class="provider-header" @click="toggleCustomModelForm">
              <div class="provider-info">
                <div class="provider-logo custom-logo">
                  <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
                    <path d="M12 5V19M5 12H19" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
                  </svg>
                </div>
                <div class="provider-details">
                  <span class="provider-name">{{ $t('aiConfig.customModel.title') }}</span>
                  <span class="model-count">{{ $t('aiConfig.customModel.subtitle') }}</span>
                </div>
              </div>
              <div class="provider-actions">
                <svg class="expand-icon" :class="{ rotated: showCustomModelForm }" width="20" height="20" viewBox="0 0 24 24" fill="none">
                  <path d="M6 9L12 15L18 9" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
              </div>
            </div>
            
            <!-- 自定义模型表单 -->
            <div v-if="showCustomModelForm" class="custom-model-form">
              <div class="form-group">
                <label>{{ $t('aiConfig.customModel.providerName') }}</label>
                <input 
                  v-model="customModel.provider" 
                  type="text" 
                  :placeholder="$t('aiConfig.customModel.providerPlaceholder')"
                  class="form-input"
                />
              </div>
              
              <div class="form-group">
                <label>{{ $t('aiConfig.customModel.modelName') }}</label>
                <input 
                  v-model="customModel.modelName" 
                  type="text" 
                  :placeholder="$t('aiConfig.customModel.modelPlaceholder')"
                  class="form-input"
                />
              </div>
              
              <div class="form-group">
                <label>{{ $t('aiConfig.customModel.apiBase') }}</label>
                <input 
                  v-model="customModel.apiBase" 
                  type="text" 
                  :placeholder="$t('aiConfig.customModel.apiBasePlaceholder')"
                  class="form-input"
                />
              </div>
              
              <div class="form-group">
                <label>{{ $t('aiConfig.customModel.apiKey') }}</label>
                <input 
                  v-model="customModel.apiKey" 
                  type="password" 
                  :placeholder="$t('aiConfig.customModel.apiKeyPlaceholder')"
                  class="form-input"
                />
              </div>
              
              <div class="form-group">
                <label>{{ $t('aiConfig.customModel.description') }}</label>
                <textarea 
                  v-model="customModel.description" 
                  :placeholder="$t('aiConfig.customModel.descriptionPlaceholder')"
                  class="form-textarea"
                  rows="2"
                ></textarea>
              </div>
              
              <div class="form-actions">
                <button @click="saveCustomModel" class="btn-primary" :disabled="!isCustomModelValid">
                  {{ $t('aiConfig.customModel.save') }}
                </button>
                <button @click="resetCustomModelForm" class="btn-secondary">
                  {{ $t('aiConfig.customModel.reset') }}
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 主工作区 -->
    <main class="workspace">
      <!-- 顶部搜索区域 -->
      <div class="workspace-header" v-show="!showPdfPreview">
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

      <!-- PDF预览区域 -->
      <div class="pdf-preview-section" v-if="showPdfPreview" :class="{ 'pdf-collapsed': showVisualization && !pdfExpanded }">
        <!-- PDF内容区域 -->
        <div class="preview-content" :class="{ 'pdf-expanded': pdfExpanded }" ref="previewContent">
          <!-- 圆形进度加载 -->
          <div v-if="isDownloading" class="pdf-loading">
            <div class="circle-wrapper">
              <svg class="progress-ring" width="120" height="120">
                <circle class="progress-ring__background" stroke="#ecf0f1" stroke-width="10" fill="transparent" r="52" cx="60" cy="60" />
                <circle class="progress-ring__progress" :stroke="progressColor" stroke-width="10" fill="transparent" r="52" cx="60" cy="60"
                        :style="{ strokeDasharray: circumference, strokeDashoffset: dashOffset }" stroke-linecap="round" />
              </svg>
              <div class="progress-text">{{ downloadProgress }}%</div>
            </div>
          </div>

          <!-- PDF.js 画布预览 -->
          <div v-if="!showVisualization" class="pdf-viewer" style="width:100%; height:100%; overflow: auto;">
            <template v-if="!useIframeFallback">
              <div ref="pdfContainer" class="pdf-canvas-container"></div>
              <p v-if="!isDownloading && !pdfBlobUrl" style="color:#95a5a6;">准备预览PDF...</p>
            </template>
            <template v-else>
              <iframe v-if="viewerSrc" ref="viewerFrame" :src="viewerSrc" @load="onViewerLoaded" style="border:none; width:100%; height:100%;"></iframe>
              <p v-else style="color:#95a5a6;">准备预览PDF...</p>
            </template>
          </div>
        </div>
      </div>

      <!-- 文本选择操作浮层 -->
      <Teleport to="body">
        <div 
          v-if="showSelectionActions && selectionText"
          class="selection-actions"
          :style="{ top: selectionPos.top + 'px', left: selectionPos.left + 'px' }"
          @mousedown.stop="onToolbarMouseDown"
        >
          <button class="sel-btn" @click="handleTranslate" :title="$t('selection.translate')">
            {{ $t('selection.translate') }}
          </button>
          <div class="lang-selector" @click.stop>
            <button class="lang-btn" @click="toggleLangMenu" :title="$t('selection.language')">
              {{ $t(`selection.lang.${selectedLang}`) }}
              <svg class="chevron" width="12" height="12" viewBox="0 0 24 24"><path d="M6 9l6 6 6-6" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>
            </button>
            <ul v-if="showLangMenu" class="lang-menu">
              <li 
                v-for="code in langCodes" 
                :key="code" 
                :class="{ active: code === selectedLang }"
                @click="selectLang(code)"
              >{{ $t(`selection.lang.${code}`) }}</li>
            </ul>
          </div>
          <button class="sel-btn" @click="handleAsk" :title="$t('selection.ask')">
            {{ $t('selection.ask') }}
          </button>
          <button class="sel-btn" @click="handleCopy" :title="$t('selection.copy')">
            {{ $t('selection.copy') }}
          </button>
        </div>
      </Teleport>

      <!-- 可视化结果区域 -->
      <div class="visualization-section" v-if="showVisualization">
        <!-- 右上角按钮组 -->
        <div class="viz-controls">
          <button class="viz-btn back-to-pdf-btn" @click="backToPdfPreview" :title="$t('workspace.pdf.backToPaper')">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
              <path d="M14 2H6C4.9 2 4 2.9 4 4V20C4 21.1 4.9 22 6 22H18C19.1 22 20 21.1 20 20V8L14 2Z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
              <path d="M14 2V8H20" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
            <span class="btn-text">{{ $t('workspace.pdf.backToPaper') }}</span>
          </button>
        </div>
        
        <!-- 可视化图表，直接填充整个区域 -->
        <div class="visualization-content">
          <ConnectedPapersGraph 
            v-if="visualizationData && visualizationData.nodes"
            :papers="visualizationData.nodes"
            :edges="visualizationData.edges"
            :mainPaper="visualizationData.mainPaper"
          />
          <WordCloudHeatmap 
            v-if="wordCloudData && wordCloudData.length > 0"
            :wordData="wordCloudData"
          />
        </div>
      </div>

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

        <!-- 搜索结果列表 -->
        <div class="search-results" v-if="currentView === 'search'">
          <h3 class="results-title">{{ $t('workspace.searchResults.title') }}</h3>
          <div class="results-list">
            <div 
              v-for="result in paginatedResults" 
              :key="result.title" 
              class="result-item"
              @click="selectPaper(result)"
            >
              <h3 class="result-title">{{ result.title }}</h3>
              <p class="result-authors">{{ result.authors }}</p>
              <p class="result-abstract">{{ result.abstract }}</p>
              <div class="result-meta">
                <span>{{ $t('workspace.searchResults.year', { year: result.year }) }}</span>
                <span>{{ $t('workspace.searchResults.citations', { count: result.citations }) }}</span>
              </div>
            </div>
          </div>
          <!-- 分页 -->
          <div class="pagination" v-if="totalPages > 1">
            <span class="pagination-info">{{ $t('workspace.pagination.showing') }} {{ startItem }}-{{ endItem }} {{ $t('workspace.pagination.of') }} {{ $t('workspace.pagination.total', { total: allResults.length }) }}</span>
            <button class="pagination-btn" @click="goToPage(1)" :disabled="currentPage === 1">{{ $t('workspace.pagination.first') }}</button>
            <button class="pagination-btn" @click="goToPage(currentPage - 1)" :disabled="currentPage === 1">{{ $t('workspace.pagination.previous') }}</button>
            <div class="pagination-pages">
              <button 
                v-for="page in pageButtons" 
                :key="page"
                class="pagination-btn" 
                :class="{ active: page === currentPage }"
                @click="goToPage(page)"
              >
                {{ page }}
              </button>
            </div>
            <button class="pagination-btn" @click="goToPage(currentPage + 1)" :disabled="currentPage === totalPages">{{ $t('workspace.pagination.next') }}</button>
            <button class="pagination-btn" @click="goToPage(totalPages)" :disabled="currentPage === totalPages">{{ $t('workspace.pagination.last') }}</button>
          </div>
        </div>
      </div>
    </main>

    <!-- 隐藏的文件上传输入 -->
    <input type="file" ref="fileInput" accept=".pdf" style="display: none;" @change="handleFileUpload">
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue'
import { useRoute } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { apiService } from '@/api'
import { isURL } from '@/utils/helpers'
import Sidebar from '@/components/Sidebar.vue'
import ConnectedPapersGraph from '@/components/ConnectedPapersGraph.vue'
import WordCloudHeatmap from '@/components/WordCloudHeatmap.vue'
import TranslateChat from '@/components/TranslateChatNew.vue'
import { parseBibTeX, convertToConnectedPapersFormat } from '@/utils/bibParser'

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

// 根据图片文件名获取描述（使用 i18n）
const getDescription = (imageName) => {
  const key = imageName.replace('.png', '')
  return t(`workspace.templates.descriptions.${key}`, '')
}

// 悬浮状态
const hoveredTemplate = ref(null)
const tooltipPosition = ref(null)
const templateItems = ref([])

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
  // 打开翻译模式的聊天面板
  chatMode.value = 'translate'
  showTranslateChat.value = true
  // 不清除选择文本，保持浮层可见直到面板打开后
  setTimeout(() => {
    clearSelectionActions()
  }, 100)
}

const handleAsk = () => {
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
const pdfExpanded = ref(false)
const currentPdfUrl = ref('')
// 跟踪已加载的可视化模板
const loadedVisualizations = ref([])
// PDF 下载与预览
const isDownloading = ref(false)
const downloadProgress = ref(0)
const pdfBlobUrl = ref('')
// PDF.js 渲染相关 / 专用viewer
const pdfContainer = ref(null)
const pdfDocRef = ref(null)
const pdfLibRef = ref(null)
const isRendering = ref(false)
const maxRenderPages = 8
const useIframeFallback = ref(false)
const viewerSrc = ref('')
const viewerFrame = ref(null)
// 圆形进度参数
const radius = 52
const circumferenceVal = 2 * Math.PI * radius
const circumference = `${circumferenceVal}px`
const progressColor = '#3498db'
const dashOffset = computed(() => {
  const pct = Math.max(0, Math.min(100, downloadProgress.value))
  const val = circumferenceVal - (pct / 100) * circumferenceVal
  return `${val}px`
})

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

const handleFileUpload = (event) => {
  const file = event.target.files[0]
  if (file && file.type === 'application/pdf') {
    console.log('已选择文件:', file.name)
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
  loadedVisualizations.value = []
  pdfBlobUrl.value = ''
  isDownloading.value = true
  downloadProgress.value = 0
  useIframeFallback.value = false
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
      // 判断是词云数据还是关系图数据
      if (Array.isArray(viz.data) && viz.data.length > 0 && viz.data[0].word) {
        // 词云数据
        wordCloudData.value = viz.data
        visualizationData.value = null
      } else {
        // 关系图数据
        visualizationData.value = viz.data
        wordCloudData.value = []
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
  showTemplatePanel.value = false
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
}

const handleUserToggle = () => {
  showUserPanel.value = true
  showAIPanel.value = false
  showTemplatePanel.value = false
  showNotificationPanel.value = false
}

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
      
      // 设置会话信息（后续可以传递给TranslateChat组件）
      console.log('加载会话:', session.title, sessionMessages.length, '条消息')
      
      // TODO: 需要扩展TranslateChat组件以支持加载历史会话
      // 目前先打开空白聊天面板
      showTranslateChat.value = true
      chatMode.value = session.session_type === 'translate' ? 'translate' : 'chat'
      
      // 关闭通知面板
      showNotificationPanel.value = false
    }
  } catch (error) {
    console.error('加载会话失败:', error)
    // 即使加载失败，也打开聊天面板
    showTranslateChat.value = true
    showNotificationPanel.value = false
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
  
  if (minutes < 1) return '刚刚'
  if (minutes < 60) return `${minutes}分钟前`
  if (hours < 24) return `${hours}小时前`
  if (days < 7) return `${days}天前`
  return date.toLocaleDateString('zh-CN', { month: 'short', day: 'numeric' })
}

onMounted(() => {
  loadThumbnails()
  loadAIOptions()
  loadCurrentAIConfig()
  loadChatSessions() // 加载会话历史
  // 监听主文档选择
  attachSelectionListenersTo(document)
  
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

// 初始化并渲染 PDF 到画布
const initPdfViewer = async () => {
  try {
    if (!pdfBlobUrl.value) return
    isRendering.value = true
    // 动态加载 pdf.js（使用CDN ESM）
    if (!pdfLibRef.value) {
      let pdfjsLib = null
      try {
        pdfjsLib = await import('https://cdn.jsdelivr.net/npm/pdfjs-dist@4.10.38/build/pdf.min.mjs')
      } catch (e1) {
        try {
          pdfjsLib = await import('https://unpkg.com/pdfjs-dist@4.10.38/build/pdf.min.mjs')
        } catch (e2) {
          console.error('加载pdf.js失败，切换iframe回退', e1, e2)
          useIframeFallback.value = true
          return
        }
      }
      pdfjsLib.GlobalWorkerOptions.workerSrc = 'https://cdn.jsdelivr.net/npm/pdfjs-dist@4.10.38/build/pdf.worker.min.mjs'
      pdfLibRef.value = pdfjsLib
    }
    const pdfjsLib = pdfLibRef.value
    // 确保容器存在，否则回退到 iframe
    if (!pdfContainer.value) {
      useIframeFallback.value = true
      return
    }
    // 将 blob URL 转为 ArrayBuffer
    const buf = await fetch(pdfBlobUrl.value).then(r => r.arrayBuffer())
    const loadingTask = pdfjsLib.getDocument({ data: buf })
    const pdf = await loadingTask.promise
    pdfDocRef.value = pdf
    // 清空容器并渲染前 maxRenderPages 页
    pdfContainer.value.innerHTML = ''
    const pagesToRender = Math.min(pdf.numPages, maxRenderPages)
    for (let pageNum = 1; pageNum <= pagesToRender; pageNum++) {
      const page = await pdf.getPage(pageNum)
      const viewport = page.getViewport({ scale: 1.25 })
      const canvas = document.createElement('canvas')
      const context = canvas.getContext('2d')
      canvas.width = viewport.width
      canvas.height = viewport.height
      canvas.style.display = 'block'
      canvas.style.margin = '12px auto'
      canvas.style.boxShadow = '0 2px 8px rgba(0,0,0,0.08)'
      pdfContainer.value.appendChild(canvas)
      await page.render({ canvasContext: context, viewport }).promise
    }
    // 如果页数较多，给出提示
    if (pdf.numPages > maxRenderPages) {
      const tip = document.createElement('div')
      tip.textContent = `已显示前 ${maxRenderPages} 页，共 ${pdf.numPages} 页`
      tip.style.textAlign = 'center'
      tip.style.color = '#7f8c8d'
      tip.style.margin = '8px 0 16px'
      pdfContainer.value.appendChild(tip)
    }
  } catch (e) {
    console.error('PDF渲染失败，切换iframe回退:', e)
    useIframeFallback.value = true
  } finally {
    isRendering.value = false
  }
}
</script>

<style scoped>
/* 预览容器内的加载样式 */
.pdf-loading {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
}
.circle-wrapper {
  position: relative;
  width: 140px;
  height: 140px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}
.progress-ring {
  transform: rotate(-90deg);
}
.progress-ring__background,
.progress-ring__progress {
  transition: stroke-dashoffset 0.2s ease;
}
.progress-text {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -60%);
  font-size: 20px;
  font-weight: 600;
  color: #2c3e50;
}
.progress-subtext {
  position: absolute;
  top: calc(50% + 28px);
  left: 50%;
  transform: translateX(-50%);
  font-size: 12px;
  color: #7f8c8d;
}
.pdf-canvas-container {
  max-width: 1100px;
  margin: 0 auto;
  padding: 16px 0 24px;
}
</style>

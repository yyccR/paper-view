<template>
  <div class="translate-chat-panel" :class="{ active: modelValue }">
    <!-- 头部 -->
    <div class="chat-header">
      <div class="header-title" @mouseenter="handleTitleHover" @mouseleave="showTitleTooltip = false" ref="titleRef">
        <h3>{{ truncatedTitle }}</h3>
      </div>
      <div class="header-actions">
        <button class="icon-btn" @click="createNewSession" :title="$t('translateChat.newChat')">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none">
            <path d="M12 5V19M5 12H19" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
          </svg>
        </button>
        <button class="close-btn" @click="close">&times;</button>
      </div>
    </div>
    
    <!-- 消息区域 -->
    <div class="chat-messages" ref="messagesContainer">
      <div 
        v-for="(msg, index) in messages" 
        :key="`msg-${index}-${msg.timestamp}`"
        class="message-row"
        :class="{ 'ai-row': msg.role === 'assistant', 'user-row': msg.role === 'user' }"
      >
        <div v-if="msg.role === 'assistant'" class="message-avatar">
          <img :src="aiLogo" alt="AI" class="ai-logo">
        </div>
        <div class="message-bubble" :class="[`${msg.role}-bubble`, { 'error-bubble': msg.isError, 'streaming': msg.streaming }]">
          {{ msg.content }}<span v-if="msg.streaming" class="cursor">|</span>
        </div>
      </div>
    </div>
    
    <!-- 输入区域 -->
    <div class="chat-input-area">
      <textarea 
        v-model="inputText" 
        :placeholder="$t('translateChat.inputPlaceholder')"
        @keydown.enter.exact.prevent="sendMessage"
        @keydown.enter.shift.exact="() => {}"
        @input="autoResize"
        ref="inputArea"
        rows="1"
        class="chat-input"
      ></textarea>
      <button 
        class="send-btn" 
        @click="sendMessage"
        :disabled="!inputText.trim() || isLoading"
      >
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none">
          <path d="M22 2L11 13M22 2L15 22L11 13M22 2L2 9L11 13" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
      </button>
    </div>
    
    <!-- 悬浯tooltip，使用Teleport移到body避免被裁剪 -->
    <Teleport to="body">
      <div v-if="showTitleTooltip && isTitleTruncated" class="title-tooltip" :style="tooltipStyle">
        {{ fullTitle }}
      </div>
    </Teleport>
  </div>
</template>

<script setup>
import { ref, computed, watch, nextTick, onUnmounted } from 'vue'
import { apiService } from '@/api'

const props = defineProps({
  modelValue: Boolean,
  selectedText: {
    type: String,
    default: ''
  },
  mode: {
    type: String,
    default: 'translate' // 'translate' or 'chat'
  },
  targetLang: {
    type: String,
    default: 'zh'
  },
  paperTitle: {
    type: String,
    default: ''
  }
})

const emit = defineEmits(['update:modelValue', 'sessionClosed'])

const messages = ref([])
const inputText = ref('')
const isLoading = ref(false)
const messagesContainer = ref(null)
const inputArea = ref(null)
const currentAIConfig = ref(null)
const showTitleTooltip = ref(false)
const titleRef = ref(null)
const tooltipStyle = ref({})
const currentSessionId = ref(null)
const lastTranslatedText = ref('')  // 记录上次翻译的文本
let eventSource = null

// 标题处理
const fullTitle = computed(() => props.paperTitle || '新对话')
const truncatedTitle = computed(() => {
  const title = fullTitle.value
  if (title.length > 20) {
    return title.substring(0, 20) + '...'
  }
  return title
})
const isTitleTruncated = computed(() => fullTitle.value.length > 20)

// 处理标题悬停
const handleTitleHover = () => {
  if (!isTitleTruncated.value) return
  
  showTitleTooltip.value = true
  
  // 计算tooltip位置
  nextTick(() => {
    if (titleRef.value) {
      const rect = titleRef.value.getBoundingClientRect()
      tooltipStyle.value = {
        position: 'fixed',
        top: `${rect.bottom + 8}px`,
        left: `${rect.left}px`,
        zIndex: 1001
      }
    }
  })
}

// 获取当前AI配置
const loadAIConfig = async () => {
  try {
    const response = await apiService.getAIConfig()
    if (response.success && response.data) {
      currentAIConfig.value = response.data
    }
  } catch (error) {
    console.error('Failed to load AI config:', error)
  }
}

// AI Logo
const aiLogo = computed(() => {
  if (currentAIConfig.value && currentAIConfig.value.provider) {
    return `/assets/logos/${currentAIConfig.value.provider}.png`
  }
  return '/assets/logos/openai.png'
})

const close = () => {
  // 关闭EventSource
  if (eventSource) {
    eventSource.close()
    eventSource = null
  }
  
  // 通知父组件会话已关闭
  if (currentSessionId.value) {
    emit('sessionClosed', currentSessionId.value)
  }
  
  emit('update:modelValue', false)
}

const scrollToBottom = () => {
  nextTick(() => {
    if (messagesContainer.value) {
      messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
    }
  })
}

const autoResize = () => {
  if (inputArea.value) {
    inputArea.value.style.height = 'auto'
    inputArea.value.style.height = Math.min(inputArea.value.scrollHeight, 120) + 'px'
  }
}

const createNewSession = () => {
  messages.value = []
  currentSessionId.value = null
  inputText.value = ''
  if (eventSource) {
    eventSource.close()
    eventSource = null
  }
}

// 流式发送消息
const sendMessageStream = async (userMessage, isTranslate = false) => {
  isLoading.value = true
  
  try {
    const url = isTranslate ? apiService.getTranslateStreamUrl() : apiService.getChatStreamUrl()
    
    const payload = isTranslate ? {
      text: userMessage,
      target_lang: props.targetLang,
      session_id: currentSessionId.value,
      paper_title: props.paperTitle
    } : {
      messages: messages.value.filter(m => m.role !== 'system').map(m => ({ role: m.role, content: m.content })),
      context_text: props.selectedText,
      session_id: currentSessionId.value,
      paper_title: props.paperTitle
    }
    
    // 使用fetch发送POST请求，然后读取流
    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(payload)
    })
    
    if (!response.ok) {
      // 尝试读取错误响应体
      let errorMessage = `HTTP ${response.status}: ${response.statusText}`
      try {
        const errorData = await response.json()
        if (errorData.error) {
          errorMessage = errorData.error
        } else if (errorData.detail) {
          errorMessage = errorData.detail
        } else if (errorData.message) {
          errorMessage = errorData.message
        }
      } catch (e) {
        // 无法解析JSON，使用默认错误消息
        console.error('无法解析错误响应:', e)
      }
      throw new Error(errorMessage)
    }
    
    const reader = response.body.getReader()
    const decoder = new TextDecoder()
    let streamError = null
    
    // 直接在messages数组中创建一条消息，然后实时更新
    const messageIndex = messages.value.length
    messages.value.push({
      role: 'assistant',
      content: '',
      timestamp: new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' }),
      streaming: true  // 标记为流式输出中
    })
    
    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      
      const chunk = decoder.decode(value)
      const lines = chunk.split('\n')
      
      for (const line of lines) {
        if (line.startsWith('data: ')) {
          const data = line.slice(6)
          try {
            const json = JSON.parse(data)
            
            if (json.type === 'chunk') {
              // 直接更新messages中的消息内容
              messages.value[messageIndex].content += json.content
              scrollToBottom()
            } else if (json.type === 'done') {
              // 流式完成，移除streaming标记
              messages.value[messageIndex].streaming = false
              currentSessionId.value = json.session_id
              scrollToBottom()
            } else if (json.type === 'error') {
              // 保存错误信息并跳出循环
              streamError = json.error
              // 删除正在流式输出的消息
              messages.value.splice(messageIndex, 1)
              break
            }
          } catch (e) {
            console.error('Parse error:', e)
          }
        }
      }
      
      // 如果遇到错误，跳出外层循环
      if (streamError) {
        break
      }
    }
    
    // 如果有流式错误，抛出异常让外层catch处理
    if (streamError) {
      throw new Error(streamError)
    }
    
  } catch (error) {
    console.error('Stream error:', error)
    
    // 构建详细的错误信息
    let errorMessage = '请求失败'
    if (error.message) {
      errorMessage = error.message
    }
    
    // 如果是网络错误
    if (error.name === 'TypeError' && error.message.includes('fetch')) {
      errorMessage = '网络连接失败，请检查网络连接和后端服务是否正常运行'
    }
    
    messages.value.push({
      role: 'assistant',
      content: `❌ 错误: ${errorMessage}\n\n请检查：\n1. AI配置是否正确\n2. 后端服务是否正常运行\n3. 网络连接是否正常`,
      timestamp: new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' }),
      isError: true  // 标记为错误消息
    })
  } finally {
    isLoading.value = false
    await nextTick()
    scrollToBottom()
  }
}

const sendMessage = async () => {
  const text = inputText.value.trim()
  if (!text || isLoading.value) return
  
  // 添加用户消息
  messages.value.push({
    role: 'user',
    content: text,
    timestamp: new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
  })
  
  inputText.value = ''
  autoResize()
  scrollToBottom()
  
  // 流式发送
  await sendMessageStream(text, false)
}

// 初始化翻译或聊天
const initTranslation = async () => {
  if (props.mode === 'translate' && props.selectedText) {
    // 翻译模式：自动流式翻译
    await sendMessageStream(props.selectedText, true)
  } else if (props.mode === 'chat' && props.selectedText) {
    // 聊天模式：显示欢迎消息
    messages.value.push({
      role: 'assistant',
      content: `我看到你选择了以下文本：\n\n"${props.selectedText}"\n\n请问有什么可以帮助你的？`,
      timestamp: new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
    })
    scrollToBottom()
  }
}

// 监听面板打开和模式变化
watch([() => props.modelValue, () => props.mode, () => props.selectedText], 
  ([newModelValue, newMode, newSelectedText], [oldModelValue, oldMode]) => {
    // 只在以下情况触发：
    // 1. 面板从关闭到打开（用户点击翻译按钮）
    // 2. 面板已打开但模式变为'translate'（从聊天切换到翻译）
    const panelJustOpened = newModelValue && !oldModelValue
    const modeChangedToTranslate = newModelValue && newMode === 'translate' && oldMode !== 'translate'
    
    if (panelJustOpened || modeChangedToTranslate) {
      // 翻译模式：直接追加翻译，不清空历史
      if (newMode === 'translate' && newSelectedText) {
        loadAIConfig().then(() => {
          initTranslation()
          lastTranslatedText.value = newSelectedText
        })
      } else if (newMode === 'chat') {
        // 聊天模式不自动翻译
        if (panelJustOpened) {
          loadAIConfig().then(() => {
            initTranslation()
          })
        }
      }
    }
  },
  { deep: false }
)

onUnmounted(() => {
  if (eventSource) {
    eventSource.close()
  }
})
</script>

<style scoped>
.translate-chat-panel {
  position: fixed;
  left: 70px;
  top: 0;
  width: 280px;
  height: 100vh;
  background: white;
  box-shadow: 2px 0 20px rgba(0, 0, 0, 0.1);
  transform: translateX(-100%);
  transition: transform 0.3s ease;
  z-index: 96;
  display: flex;
  flex-direction: column;
}

.translate-chat-panel.active {
  transform: translateX(0);
}

.chat-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px;
  border-bottom: 1px solid #ecf0f1;
  background: #f8f9fa;
  gap: 8px;
}

.header-title {
  flex: 1;
  position: relative;
  overflow: hidden;
}

.header-title h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: #2c3e50;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.header-title:hover h3 {
  color: #3498db;
}

/* 标题tooltip */
.title-tooltip {
  background: white;
  color: #2c3e50;
  padding: 12px 16px;
  border-radius: 8px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.15);
  border: 1px solid #ecf0f1;
  min-width: 200px;
  max-width: 400px;
  word-wrap: break-word;
  font-size: 14px;
  line-height: 1.5;
  animation: tooltipFadeIn 0.2s ease;
  pointer-events: none;
}

@keyframes tooltipFadeIn {
  from {
    opacity: 0;
    transform: translateY(-4px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.header-actions {
  display: flex;
  gap: 4px;
  align-items: center;
}

.icon-btn {
  background: none;
  border: none;
  padding: 6px;
  cursor: pointer;
  border-radius: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #7f8c8d;
  transition: all 0.2s;
}

.icon-btn:hover {
  background: rgba(0, 0, 0, 0.05);
  color: #3498db;
}

.close-btn {
  background: none;
  border: none;
  font-size: 28px;
  line-height: 1;
  color: #7f8c8d;
  cursor: pointer;
  padding: 0;
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 4px;
  transition: all 0.2s;
}

.close-btn:hover {
  background: rgba(0, 0, 0, 0.05);
  color: #2c3e50;
}

.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.message-row {
  display: flex;
  gap: 8px;
  animation: slideIn 0.2s ease;
}

@keyframes slideIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.ai-row {
  align-items: flex-start;
  justify-content: flex-start;
}

.user-row {
  align-items: flex-end;
  justify-content: flex-end;
}

.message-avatar {
  flex-shrink: 0;
  width: 28px;
  height: 28px;
  border-radius: 50%;
  overflow: hidden;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 5px;
}

.ai-logo {
  width: 100%;
  height: 100%;
  object-fit: contain;
  filter: brightness(0) invert(1);
}

.message-bubble {
  max-width: calc(100% - 36px);
  padding: 10px 14px;
  border-radius: 12px;
  word-wrap: break-word;
  white-space: pre-wrap;
  line-height: 1.5;
  font-size: 14px;
}

.ai-bubble,
.assistant-bubble {
  background: #f8f9fa;
  color: #2c3e50;
  border: 1px solid #ecf0f1;
  border-top-left-radius: 4px;
}

.user-bubble {
  background: #3498db;
  color: white;
  border-top-right-radius: 4px;
  margin-left: auto;
}

.error-bubble {
  background: #ff4757 !important;
  color: white !important;
  border: 1px solid #ee5a6f !important;
  font-weight: 500;
}

.streaming {
  position: relative;
}

.cursor {
  display: inline-block;
  animation: blink 1s infinite;
  margin-left: 2px;
}

@keyframes blink {
  0%, 50% { opacity: 1; }
  51%, 100% { opacity: 0; }
}

.chat-input-area {
  display: flex;
  gap: 8px;
  padding: 12px 16px;
  border-top: 1px solid #ecf0f1;
  background: #f8f9fa;
  align-items: flex-end;
}

.chat-input {
  flex: 1;
  padding: 10px 12px;
  border: 1px solid #dfe6e9;
  border-radius: 8px;
  font-size: 14px;
  font-family: inherit;
  resize: none;
  transition: border-color 0.2s;
  background: white;
  color: #2c3e50;
  min-height: 38px;
  max-height: 120px;
  line-height: 1.4;
}

.chat-input:focus {
  outline: none;
  border-color: #3498db;
}

.send-btn {
  flex-shrink: 0;
  width: 38px;
  height: 38px;
  border-radius: 8px;
  border: none;
  background: #3498db;
  color: white;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
}

.send-btn:hover:not(:disabled) {
  background: #2980b9;
  transform: translateY(-1px);
}

.send-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* 滚动条样式 */
.chat-messages::-webkit-scrollbar {
  width: 4px;
}

.chat-messages::-webkit-scrollbar-track {
  background: transparent;
}

.chat-messages::-webkit-scrollbar-thumb {
  background: rgba(0, 0, 0, 0.2);
  border-radius: 2px;
}

.chat-messages::-webkit-scrollbar-thumb:hover {
  background: rgba(0, 0, 0, 0.3);
}

</style>

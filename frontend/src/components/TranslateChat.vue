<template>
  <div class="translate-chat-panel" :class="{ active: modelValue }">
    <div class="chat-header">
      <h3>{{ mode === 'translate' ? $t('translateChat.title') : $t('translateChat.chatTitle') }}</h3>
      <button class="close-btn" @click="close">&times;</button>
    </div>
    
    <div class="chat-messages" ref="messagesContainer">
      <div 
        v-for="(msg, index) in messages" 
        :key="index"
        class="message-item"
        :class="{ 'ai-message': msg.role === 'assistant', 'user-message': msg.role === 'user' }"
      >
        <div v-if="msg.role === 'assistant'" class="message-avatar">
          <img :src="aiLogo" alt="AI" class="ai-logo">
        </div>
        <div class="message-content">
          <div class="message-text" :class="{ 'error-text': msg.isError }">{{ msg.content }}</div>
          <div class="message-time">{{ msg.timestamp }}</div>
        </div>
      </div>
      
      <!-- 加载中的提示 -->
      <div v-if="isLoading" class="message-item ai-message">
        <div class="message-avatar">
          <img :src="aiLogo" alt="AI" class="ai-logo">
        </div>
        <div class="message-content">
          <div class="message-text loading-dots">
            <span></span><span></span><span></span>
          </div>
        </div>
      </div>
    </div>
    
    <div class="chat-input-area">
      <textarea 
        v-model="inputText" 
        :placeholder="$t('translateChat.inputPlaceholder')"
        @keydown.enter.exact.prevent="sendMessage"
        @keydown.enter.shift.exact="() => {}"
        rows="2"
        class="chat-input"
      ></textarea>
      <button 
        class="send-btn" 
        @click="sendMessage"
        :disabled="!inputText.trim() || isLoading"
      >
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
          <path d="M22 2L11 13M22 2L15 22L11 13M22 2L2 9L11 13" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, nextTick } from 'vue'
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
  }
})

const emit = defineEmits(['update:modelValue'])

const messages = ref([])
const inputText = ref('')
const isLoading = ref(false)
const messagesContainer = ref(null)
const currentAIConfig = ref(null)

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

// AI Logo - 使用配置的AI模型logo
const aiLogo = computed(() => {
  if (currentAIConfig.value) {
    // 优先使用logo字段，如果没有则使用provider
    const logoName = currentAIConfig.value.logo || currentAIConfig.value.provider || 'openai'
    return `/assets/logos/${logoName}.png`
  }
  // 默认使用通用AI图标
  return '/assets/logos/openai.png'
})

const close = () => {
  emit('update:modelValue', false)
}

const formatTime = () => {
  const now = new Date()
  return now.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
}

const scrollToBottom = () => {
  nextTick(() => {
    if (messagesContainer.value) {
      messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
    }
  })
}

const sendMessage = async () => {
  const text = inputText.value.trim()
  if (!text || isLoading.value) return
  
  // 添加用户消息
  messages.value.push({
    role: 'user',
    content: text,
    timestamp: formatTime()
  })
  
  inputText.value = ''
  scrollToBottom()
  isLoading.value = true
  
  try {
    if (props.mode === 'translate' && messages.value.length === 1) {
      // 如果是翻译模式且是第一条消息，使用翻译API
      const response = await apiService.translateText(props.selectedText, props.targetLang)
      
      if (response.success) {
        messages.value.push({
          role: 'assistant',
          content: response.data.translated_text,
          timestamp: formatTime()
        })
      } else {
        throw new Error(response.error || 'Translation failed')
      }
    } else {
      // 使用聊天API
      const chatMessages = messages.value.map(msg => ({
        role: msg.role === 'assistant' ? 'assistant' : 'user',
        content: msg.content
      }))
      
      const response = await apiService.chatWithText(
        chatMessages,
        props.selectedText
      )
      
      if (response.success) {
        messages.value.push({
          role: 'assistant',
          content: response.data.response,
          timestamp: formatTime()
        })
      } else {
        throw new Error(response.error || 'Chat failed')
      }
    }
  } catch (error) {
    console.error('Error:', error)
    
    // 构建详细的错误信息
    let errorMessage = '请求失败'
    if (error.response && error.response.data) {
      // Axios错误响应
      if (error.response.data.error) {
        errorMessage = error.response.data.error
      } else if (error.response.data.detail) {
        errorMessage = error.response.data.detail
      } else if (error.response.data.message) {
        errorMessage = error.response.data.message
      } else {
        errorMessage = `HTTP ${error.response.status}: ${error.response.statusText}`
      }
    } else if (error.message) {
      errorMessage = error.message
    }
    
    // 如果是网络错误
    if (error.code === 'ERR_NETWORK' || error.message.includes('Network Error')) {
      errorMessage = '网络连接失败，请检查网络连接和后端服务是否正常运行'
    }
    
    messages.value.push({
      role: 'assistant',
      content: `❌ 错误: ${errorMessage}\n\n请检查：\n1. AI配置是否正确\n2. 后端服务是否正常运行\n3. 网络连接是否正常`,
      timestamp: formatTime(),
      isError: true
    })
  } finally {
    isLoading.value = false
    scrollToBottom()
  }
}

// 初始化翻译或聊天
const initTranslation = async () => {
  if (props.mode === 'translate' && props.selectedText) {
    // 翻译模式：自动翻译选中的文本
    isLoading.value = true
    
    try {
      const response = await apiService.translateText(props.selectedText, props.targetLang)
      
      if (response.success) {
        messages.value.push({
          role: 'assistant',
          content: response.data.translated_text,
          timestamp: formatTime()
        })
      } else {
        throw new Error(response.error || 'Translation failed')
      }
    } catch (error) {
      console.error('Translation error:', error)
      
      // 构建详细的错误信息
      let errorMessage = '翻译失败'
      if (error.response && error.response.data) {
        if (error.response.data.error) {
          errorMessage = error.response.data.error
        } else if (error.response.data.detail) {
          errorMessage = error.response.data.detail
        } else if (error.response.data.message) {
          errorMessage = error.response.data.message
        } else {
          errorMessage = `HTTP ${error.response.status}: ${error.response.statusText}`
        }
      } else if (error.message) {
        errorMessage = error.message
      }
      
      if (error.code === 'ERR_NETWORK' || error.message.includes('Network Error')) {
        errorMessage = '网络连接失败，请检查网络连接和后端服务是否正常运行'
      }
      
      messages.value.push({
        role: 'assistant',
        content: `❌ 错误: ${errorMessage}\n\n请检查：\n1. AI配置是否正确\n2. 后端服务是否正常运行\n3. 网络连接是否正常`,
        timestamp: formatTime(),
        isError: true
      })
    } finally {
      isLoading.value = false
      scrollToBottom()
    }
  } else if (props.mode === 'chat' && props.selectedText) {
    // 聊天模式：显示欢迎消息和选中的文本
    messages.value.push({
      role: 'assistant',
      content: `我看到你选择了以下文本：\n\n"${props.selectedText}"\n\n请问有什么可以帮助你的？`,
      timestamp: formatTime()
    })
    scrollToBottom()
  }
}

// 监听面板打开
watch(() => props.modelValue, (newVal) => {
  if (newVal) {
    // 面板打开时，清空之前的消息并初始化
    messages.value = []
    inputText.value = ''
    loadAIConfig().then(() => {
      initTranslation()
    })
  }
})
</script>

<style scoped>
.translate-chat-panel {
  position: fixed;
  left: 70px;
  top: 0;
  width: 380px;
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
  padding: 20px;
  border-bottom: 1px solid #ecf0f1;
  background: #f8f9fa;
}

.chat-header h3 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: #2c3e50;
}

.close-btn {
  background: none;
  border: none;
  font-size: 32px;
  line-height: 1;
  color: #7f8c8d;
  cursor: pointer;
  padding: 0;
  width: 32px;
  height: 32px;
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
  padding: 24px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.message-item {
  display: flex;
  gap: 12px;
  animation: slideIn 0.3s ease;
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

.ai-message {
  align-items: flex-start;
}

.user-message {
  flex-direction: row-reverse;
}

.message-avatar {
  flex-shrink: 0;
  width: 36px;
  height: 36px;
  border-radius: 50%;
  overflow: hidden;
  background: #ffffff;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 6px;
  border: 1px solid #ecf0f1;
}

.ai-logo {
  width: 100%;
  height: 100%;
  object-fit: contain;
}

.message-content {
  flex: 1;
  max-width: calc(100% - 48px);
}

.message-text {
  padding: 12px 16px;
  border-radius: 12px;
  word-wrap: break-word;
  white-space: pre-wrap;
  line-height: 1.6;
}

.ai-message .message-text {
  background: #f8f9fa;
  color: #2c3e50;
  border: 1px solid #ecf0f1;
}

.user-message .message-text {
  background: #3498db;
  color: white;
  margin-left: auto;
}

.error-text {
  background: #ff4757 !important;
  color: white !important;
  border: 1px solid #ee5a6f !important;
  font-weight: 500;
}

.message-time {
  font-size: 11px;
  color: #7f8c8d;
  margin-top: 4px;
  padding: 0 4px;
}

.user-message .message-time {
  text-align: right;
}

.loading-dots {
  display: flex;
  gap: 4px;
  padding: 12px 16px;
}

.loading-dots span {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #7f8c8d;
  animation: bounce 1.4s infinite ease-in-out both;
}

.loading-dots span:nth-child(1) {
  animation-delay: -0.32s;
}

.loading-dots span:nth-child(2) {
  animation-delay: -0.16s;
}

@keyframes bounce {
  0%, 80%, 100% {
    transform: scale(0);
  }
  40% {
    transform: scale(1);
  }
}

.chat-input-area {
  display: flex;
  gap: 12px;
  padding: 16px 20px;
  border-top: 1px solid #ecf0f1;
  background: #f8f9fa;
}

.chat-input {
  flex: 1;
  padding: 12px 16px;
  border: 1px solid #dfe6e9;
  border-radius: 8px;
  font-size: 14px;
  font-family: inherit;
  resize: none;
  transition: border-color 0.2s;
  background: white;
  color: #2c3e50;
}

.chat-input:focus {
  outline: none;
  border-color: #3498db;
}

.send-btn {
  flex-shrink: 0;
  width: 44px;
  height: 44px;
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
  width: 6px;
}

.chat-messages::-webkit-scrollbar-track {
  background: transparent;
}

.chat-messages::-webkit-scrollbar-thumb {
  background: rgba(0, 0, 0, 0.2);
  border-radius: 3px;
}

.chat-messages::-webkit-scrollbar-thumb:hover {
  background: rgba(0, 0, 0, 0.3);
}
</style>

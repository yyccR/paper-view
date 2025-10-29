<template>
  <div class="translate-chat-panel" :class="{ active: modelValue }">
    <!-- 头部 -->
    <div class="chat-header">
      <div class="header-title" @click="showFullTitle = true">
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
        <div class="message-bubble" :class="`${msg.role}-bubble`">
          {{ msg.content }}
        </div>
      </div>
      
      <!-- 流式输入中的消息 -->
      <div v-if="streamingMessage" class="message-row ai-row" key="streaming-message">
        <div class="message-avatar">
          <img :src="aiLogo" alt="AI" class="ai-logo">
        </div>
        <div class="message-bubble ai-bubble streaming">
          {{ streamingMessage }}<span class="cursor">|</span>
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
    
    <!-- 全标题弹窗 -->
    <Teleport to="body">
      <div v-if="showFullTitle" class="title-modal" @click="showFullTitle = false">
        <div class="title-modal-content" @click.stop>
          <h4>{{ fullTitle }}</h4>
          <button @click="showFullTitle = false" class="modal-close-btn">{{ $t('common.close') }}</button>
        </div>
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
const showFullTitle = ref(false)
const streamingMessage = ref('')
const currentSessionId = ref(null)
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
  streamingMessage.value = ''
  inputText.value = ''
  if (eventSource) {
    eventSource.close()
    eventSource = null
  }
}

// 流式发送消息
const sendMessageStream = async (userMessage, isTranslate = false) => {
  isLoading.value = true
  streamingMessage.value = ''
  
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
      throw new Error(`HTTP error! status: ${response.status}`)
    }
    
    const reader = response.body.getReader()
    const decoder = new TextDecoder()
    let fullContent = ''
    
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
              streamingMessage.value += json.content
              fullContent += json.content
              scrollToBottom()
            } else if (json.type === 'done') {
              // 流式完成，添加到消息列表（使用累积的完整内容）
              if (fullContent) {
                messages.value.push({
                  role: 'assistant',
                  content: fullContent,
                  timestamp: new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
                })
                currentSessionId.value = json.session_id
                
                // 等待DOM更新后再清空流式消息，避免闪烁
                await nextTick()
                // 额外延迟确保渲染完成
                setTimeout(() => {
                  streamingMessage.value = ''
                  scrollToBottom()
                }, 50)
                fullContent = '' // 重置累积内容
              }
            } else if (json.type === 'error') {
              throw new Error(json.error)
            }
          } catch (e) {
            console.error('Parse error:', e)
          }
        }
      }
    }
    
  } catch (error) {
    console.error('Stream error:', error)
    messages.value.push({
      role: 'assistant',
      content: `错误: ${error.message || '请求失败，请检查AI配置'}`,
      timestamp: new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
    })
    // 等待DOM更新后再清空
    await nextTick()
    streamingMessage.value = ''
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

// 监听面板打开
watch(() => props.modelValue, (newVal) => {
  if (newVal) {
    messages.value = []
    inputText.value = ''
    currentSessionId.value = null
    streamingMessage.value = ''
    loadAIConfig().then(() => {
      initTranslation()
    })
  }
})

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
  cursor: pointer;
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

.ai-bubble {
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

/* 标题弹窗 */
.title-modal {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  animation: fadeIn 0.2s ease;
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

.title-modal-content {
  background: white;
  padding: 24px;
  border-radius: 12px;
  max-width: 500px;
  width: 90%;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.2);
  animation: slideUp 0.3s ease;
}

@keyframes slideUp {
  from {
    transform: translateY(20px);
    opacity: 0;
  }
  to {
    transform: translateY(0);
    opacity: 1;
  }
}

.title-modal-content h4 {
  margin: 0 0 16px 0;
  color: #2c3e50;
  font-size: 16px;
  line-height: 1.6;
  word-break: break-word;
}

.modal-close-btn {
  background: #3498db;
  color: white;
  border: none;
  padding: 8px 16px;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
  transition: background 0.2s;
}

.modal-close-btn:hover {
  background: #2980b9;
}
</style>

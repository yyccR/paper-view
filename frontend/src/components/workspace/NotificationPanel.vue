<template>
  <div class="notification-panel" :class="{ active: active }">
    <div class="notification-header">
      <h3>{{ $t('workspace.notification.title') }}</h3>
      <button class="close-btn" @click="$emit('close')">&times;</button>
    </div>
    <div class="notification-list">
      <div 
        v-for="session in chatSessions" 
        :key="session.id"
        class="session-item"
        @click="$emit('open-session', session.id)"
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
              {{ $t(`workspace.notification.sessionType.${session.session_type}`) }}
            </span>
            <span class="session-count">{{ $t('workspace.notification.messageCount', { count: session.message_count }) }}</span>
          </div>
          <span class="session-time">{{ formatTime(session.last_message_at || session.created_at) }}</span>
        </div>
        <button 
          class="delete-session-btn" 
          @click.stop="$emit('delete-session', session.id)"
          :title="$t('workspace.notification.deleteSession')"
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
            <path d="M18 6L6 18M6 6L18 18" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
        </button>
      </div>
      <div v-if="chatSessions.length === 0" class="empty-state">
        <p>{{ $t('workspace.notification.noSessions') }}</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { toRefs } from 'vue'

const props = defineProps({
  active: { type: Boolean, default: false },
  chatSessions: { type: Array, default: () => [] },
  // 传入父组件的时间格式化函数，避免在子组件复制逻辑
  formatTime: { type: Function, required: true }
})
const { active, chatSessions, formatTime } = toRefs(props)
</script>

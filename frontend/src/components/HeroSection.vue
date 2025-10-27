<template>
  <section class="hero">
    <div class="hero-content">
      <h1 class="hero-title">{{ $t('hero.title') }}</h1>
      
      <!-- 中间区域 -->
      <div class="hero-middle"></div>
      
      <!-- 底部搜索框 -->
      <div class="search-section">
        <div class="search-wrapper">
          <button class="upload-btn" @click="$emit('upload')" :title="$t('hero.uploadTitle')">
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
            :placeholder="$t('hero.searchPlaceholder')"
          >
          <button class="search-btn" @click="handleSearch">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
              <path d="M21 21L15 15M17 10C17 13.866 13.866 17 10 17C6.13401 17 3 13.866 3 10C3 6.13401 6.13401 3 10 3C13.866 3 17 6.13401 17 10Z" 
                    stroke="currentColor" 
                    stroke-width="2" 
                    stroke-linecap="round"/>
            </svg>
          </button>
        </div>
        
        <!-- 进度提示 -->
        <div class="progress-section" v-if="showProgress">
          <div class="progress-bar">
            <div class="progress-fill" :style="{ width: `${progress}%` }"></div>
          </div>
          <p class="progress-text">{{ progressText }}</p>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup>
import { ref } from 'vue'

const props = defineProps({
  showProgress: Boolean,
  progress: Number,
  progressText: String,
  displayImages: Array
})

const emit = defineEmits(['search', 'upload'])

const searchQuery = ref('')

const handleSearch = () => {
  if (searchQuery.value.trim()) {
    emit('search', searchQuery.value.trim())
  }
}
</script>

<style scoped>
/* Hero样式已在全局CSS中定义 */
</style>

<template>
  <div class="modal" :class="{ active: modelValue }" @click="handleOutsideClick">
    <div class="modal-content" @click.stop>
      <span class="modal-close" @click="close">&times;</span>
      <div id="paperDetail">
        <h2 style="margin-bottom: 24px;">{{ paper.title }}</h2>
        <div style="color: var(--text-gray); margin-bottom: 32px;" v-if="paper.summary">
          <p v-for="(s, index) in paper.summary" :key="index" style="margin-bottom: 12px;">
            {{ s }}
          </p>
        </div>
        <div v-if="paper.images && paper.images.length">
          <img 
            v-for="(img, index) in paper.images" 
            :key="index"
            :src="`/api/content/image/?path=${img}`" 
            alt="内容图片" 
            style="width: 100%; border-radius: 12px; margin-bottom: 16px;"
          >
        </div>
        <button 
          class="btn-secondary" 
          @click="$emit('delete', paper.id)" 
          style="background: rgba(255, 59, 48, 0.2); border-color: rgba(255, 59, 48, 0.4);"
        >
          {{ $t('paperModal.deleteContent') }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
const props = defineProps({
  modelValue: Boolean,
  paper: {
    type: Object,
    required: true
  }
})

const emit = defineEmits(['update:modelValue', 'delete'])

const close = () => {
  emit('update:modelValue', false)
}

const handleOutsideClick = (e) => {
  if (e.target === e.currentTarget) {
    close()
  }
}
</script>

<style scoped>
/* Modal样式已在全局CSS中定义 */
</style>

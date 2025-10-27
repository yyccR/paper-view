<template>
  <div class="paper-card fade-in" @click="$emit('click')">
    <h3>{{ paper.title }}</h3>
    <div class="paper-meta">
      <span>{{ $t('paperCard.date', { date: paper.date }) }}</span>
      <span>{{ $t('paperCard.imageCount', { count: paper.image_count }) }}</span>
    </div>
    <div v-if="paper.images && paper.images.length" class="paper-images">
      <img 
        v-for="(img, index) in paper.images.slice(0, 3)" 
        :key="index"
        :src="`/api/content/image/?path=${img}`" 
        alt="预览图"
      >
    </div>
  </div>
</template>

<script setup>
defineProps({
  paper: {
    type: Object,
    required: true
  }
})

defineEmits(['click'])
</script>

<style scoped>
/* Paper card样式已在全局CSS中定义 */
</style>

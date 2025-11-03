<template>
  <aside class="template-sidebar" :class="{ active }">
    <div class="template-header">
      <h3>{{ $t('workspace.templates.title') }}</h3>
    </div>
    <div class="template-grid">
      <div 
        v-for="(image, index) in thumbnails" 
        :key="index" 
        class="template-item" 
        :class="{ active: selectedTemplate === index }"
        @click="$emit('select-template', index)"
        @mouseenter="$emit('hover-template', index, $event)"
        @mouseleave="$emit('leave-template')"
      >
        <img :src="`/assets/index_images/${image}`" :alt="`模板 ${index + 1}`" class="template-image">
        <span class="template-label">{{ getLabel(image) }}</span>
      </div>
    </div>
  </aside>

  <!-- 悬浮提示框 - Teleport 到 body -->
  <Teleport to="body">
    <div 
      v-if="hoveredTemplate !== null && tooltipPosition" 
      class="template-tooltip-portal"
      :style="{ top: tooltipPosition.top + 'px', left: tooltipPosition.left + 'px', transform: tooltipPosition.transform }"
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
</template>

<script setup>
const props = defineProps({
  active: { type: Boolean, default: false },
  thumbnails: { type: Array, default: () => [] },
  selectedTemplate: { type: Number, default: null },
  hoveredTemplate: { type: Number, default: null },
  tooltipPosition: { type: Object, default: null },
  getLabel: { type: Function, required: true },
  getDescription: { type: Function, required: true }
})
const emit = defineEmits(['select-template','hover-template','leave-template'])
</script>

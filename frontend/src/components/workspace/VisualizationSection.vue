<template>
  <div class="visualization-section" v-if="visible">
    <div class="viz-controls">
      <button class="viz-btn back-to-pdf-btn" @click="$emit('back-to-pdf')" :title="$t('workspace.pdf.backToPaper')">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
          <path d="M14 2H6C4.9 2 4 2.9 4 4V20C4 21.1 4.9 22 6 22H18C19.1 22 20 21.1 20 20V8L14 2Z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
          <path d="M14 2V8H20" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
        <span class="btn-text">{{ $t('workspace.pdf.backToPaper') }}</span>
      </button>
    </div>
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
      <CitationNetwork
        v-if="vosviewerData && vosviewerData.network"
        :networkData="vosviewerData"
      />
      <DensityVisualization
        v-if="densityData && densityData.network"
        :networkData="densityData"
      />
    </div>
  </div>
</template>
<script setup>
import ConnectedPapersGraph from '@/components/ConnectedPapersGraph.vue'
import WordCloudHeatmap from '@/components/WordCloudHeatmap.vue'
import CitationNetwork from '@/components/CitationNetwork.vue'
import DensityVisualization from '@/components/DensityVisualization.vue'

const props = defineProps({
  visible: { type: Boolean, default: false },
  visualizationData: { type: Object, default: null },
  wordCloudData: { type: Array, default: () => [] },
  vosviewerData: { type: Object, default: null },
  densityData: { type: Object, default: null }
})
const emit = defineEmits(['back-to-pdf'])
</script>

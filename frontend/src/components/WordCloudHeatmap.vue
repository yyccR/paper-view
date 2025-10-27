<template>
  <div class="wordcloud-container">
    <!-- 简化的缩放控制 - 右下角 -->
    <div class="zoom-controls">
      <button @click="zoomIn" class="zoom-btn" :title="$t('wordcloud.zoomIn')">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
          <path d="M12 5V19M5 12H19" stroke="currentColor" stroke-width="2"/>
        </svg>
      </button>
      <button @click="zoomOut" class="zoom-btn" :title="$t('wordcloud.zoomOut')">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
          <path d="M5 12H19" stroke="currentColor" stroke-width="2"/>
        </svg>
      </button>
      <button @click="resetZoom" class="zoom-btn" :title="$t('wordcloud.reset')">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
          <path d="M3 12a9 9 0 0 1 9-9 9.75 9.75 0 0 1 6.74 2.74L21 8M21 12a9 9 0 0 1-9 9 9.75 9.75 0 0 1-6.74-2.74L3 16" stroke="currentColor" stroke-width="2"/>
        </svg>
      </button>
    </div>
    
    <!-- SVG画布 -->
    <div ref="chartContainer" class="chart-container">
      <svg ref="svg" class="wordcloud-svg"></svg>
    </div>
    
    <!-- 悬停提示 -->
    <div ref="tooltip" class="wordcloud-tooltip" v-show="tooltipVisible">
      <div class="tooltip-word">{{ tooltipData.word }}</div>
      <div class="tooltip-freq">{{ $t('wordcloud.frequency') }}: {{ tooltipData.frequency }}</div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch, nextTick } from 'vue'
import { useI18n } from 'vue-i18n'
import * as d3 from 'd3'

const { t } = useI18n()

const props = defineProps({
  wordData: {
    type: Array,
    required: true,
    default: () => []
  }
})

const chartContainer = ref(null)
const svg = ref(null)
const tooltip = ref(null)
const tooltipVisible = ref(false)
const tooltipData = ref({ word: '', frequency: 0 })

let d3Svg = null
let simulation = null
let zoom = null
let currentTransform = d3.zoomIdentity

// 获取基于频率的颜色（蓝色热力图风格）
const getHeatmapColor = (frequency, maxFrequency) => {
  // 计算归一化的频率 (0-1)
  const normalized = frequency / maxFrequency
  
  // 使用蓝色系，通过透明度和饱和度表现热力
  // 高频：深蓝色，不透明
  // 低频：浅蓝色，半透明
  const opacity = 0.3 + (normalized * 0.7) // 0.3 到 1.0
  const saturation = 40 + (normalized * 60) // 40% 到 100%
  const lightness = 65 - (normalized * 30) // 65% 到 35%
  
  return {
    fill: `hsla(210, ${saturation}%, ${lightness}%, ${opacity})`,
    stroke: `hsl(210, ${saturation}%, ${Math.max(20, lightness - 20)}%)`,
    opacity: opacity
  }
}

const initializeChart = () => {
  if (!chartContainer.value || !svg.value) return
  
  const width = chartContainer.value.clientWidth
  const height = chartContainer.value.clientHeight
  
  // 清空现有内容
  d3.select(svg.value).selectAll('*').remove()
  
  // 创建SVG
  d3Svg = d3.select(svg.value)
    .attr('width', width)
    .attr('height', height)
  
  // 添加缩放功能
  zoom = d3.zoom()
    .scaleExtent([0.5, 5])
    .on('zoom', (event) => {
      currentTransform = event.transform
      g.attr('transform', event.transform)
    })
  
  d3Svg.call(zoom)
  
  // 创建主容器组
  const g = d3Svg.append('g')
    .attr('class', 'main-group')
  
  // 准备数据
  const maxFreq = Math.max(...props.wordData.map(d => d.frequency))
  const nodes = props.wordData.map((d, i) => {
    const fontSize = 12 + (d.frequency / maxFreq) * 36 // 12px 到 48px
    // 更精确的文本边界估算
    const textWidth = d.word.length * fontSize * 0.5  // 进一步减小宽度系数
    const textHeight = fontSize
    return {
      id: i,
      word: d.word,
      frequency: d.frequency,
      fontSize: fontSize,
      width: textWidth,
      height: textHeight,
      radius: Math.max(textWidth, textHeight) / 2.2  // 缩小碰撞圆，除以2.2而不是2，并移除额外的+4
    }
  })
  
  // 创建力导向模拟（更紧凑的参数）
  simulation = d3.forceSimulation(nodes)
    .force('charge', d3.forceManyBody().strength(-150))  // 进一步减小斥力
    .force('center', d3.forceCenter(width / 2, height / 2))
    .force('collision', d3.forceCollide().radius(d => d.radius + 1).strength(0.9))  // 碰撞间距只+1px，强度0.9
    .force('x', d3.forceX(width / 2).strength(0.3))  // 进一步增加中心引力
    .force('y', d3.forceY(height / 2).strength(0.3))
  
  // 直接创建文字标签（无背景圆圈）
  const labels = g.selectAll('.word-label')
    .data(nodes)
    .enter()
    .append('text')
    .attr('class', 'word-label')
    .attr('text-anchor', 'middle')
    .attr('dominant-baseline', 'middle')
    .style('font-size', d => `${d.fontSize}px`)
    .style('font-weight', d => {
      // 高频词更粗
      const normalized = d.frequency / maxFreq
      return normalized > 0.7 ? '800' : normalized > 0.4 ? '700' : '600'
    })
    .style('fill', d => {
      const color = getHeatmapColor(d.frequency, maxFreq)
      return color.stroke // 使用更深的颜色作为文字颜色
    })
    .style('opacity', d => {
      const color = getHeatmapColor(d.frequency, maxFreq)
      return color.opacity
    })
    .style('cursor', 'pointer')
    .style('user-select', 'none')
    .style('transition', 'all 0.3s ease')
    .text(d => d.word)
  
  // 添加交互效果
  labels
    .on('mouseover', function(event, d) {
      d3.select(this)
        .transition()
        .duration(200)
        .style('opacity', 1)
        .style('font-size', `${d.fontSize * 1.1}px`)  // 减小悬停放大倍数
        .style('font-weight', '900')
      
      // 显示提示框
      tooltipData.value = {
        word: d.word,
        frequency: d.frequency
      }
      tooltipVisible.value = true
      
      const tooltipEl = tooltip.value
      if (tooltipEl) {
        tooltipEl.style.left = `${event.pageX + 10}px`
        tooltipEl.style.top = `${event.pageY - 40}px`
      }
    })
    .on('mouseout', function(event, d) {
      const color = getHeatmapColor(d.frequency, maxFreq)
      d3.select(this)
        .transition()
        .duration(200)
        .style('opacity', color.opacity)
        .style('font-size', `${d.fontSize}px`)
        .style('font-weight', d => {
          const normalized = d.frequency / maxFreq
          return normalized > 0.7 ? '800' : normalized > 0.4 ? '700' : '600'
        })
      
      tooltipVisible.value = false
    })
    .on('mousemove', function(event) {
      const tooltipEl = tooltip.value
      if (tooltipEl) {
        tooltipEl.style.left = `${event.pageX + 10}px`
        tooltipEl.style.top = `${event.pageY - 40}px`
      }
    })
  
  // 拖拽功能
  const drag = d3.drag()
    .on('start', dragstarted)
    .on('drag', dragged)
    .on('end', dragended)
  
  labels.call(drag)
  
  function dragstarted(event, d) {
    if (!event.active) simulation.alphaTarget(0.3).restart()
    d.fx = d.x
    d.fy = d.y
  }
  
  function dragged(event, d) {
    d.fx = event.x
    d.fy = event.y
  }
  
  function dragended(event, d) {
    if (!event.active) simulation.alphaTarget(0)
    d.fx = null
    d.fy = null
  }
  
  // 更新位置
  simulation.on('tick', () => {
    labels
      .attr('x', d => d.x)
      .attr('y', d => d.y)
  })
}

const zoomIn = () => {
  if (d3Svg && zoom) {
    d3Svg.transition()
      .duration(300)
      .call(zoom.scaleBy, 1.3)
  }
}

const zoomOut = () => {
  if (d3Svg && zoom) {
    d3Svg.transition()
      .duration(300)
      .call(zoom.scaleBy, 0.7)
  }
}

const resetZoom = () => {
  if (d3Svg && zoom) {
    d3Svg.transition()
      .duration(500)
      .call(zoom.transform, d3.zoomIdentity)
  }
}

const handleResize = () => {
  initializeChart()
}

onMounted(() => {
  nextTick(() => {
    initializeChart()
    window.addEventListener('resize', handleResize)
  })
})

onUnmounted(() => {
  if (simulation) {
    simulation.stop()
  }
  window.removeEventListener('resize', handleResize)
})

watch(() => props.wordData, () => {
  nextTick(() => {
    initializeChart()
  })
}, { deep: true })
</script>

<style scoped>
.wordcloud-container {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
  position: relative;
  overflow: hidden;
}

/* 缩放控制 - 右下角浮动 */
.zoom-controls {
  position: absolute;
  bottom: 24px;
  right: 24px;
  display: flex;
  flex-direction: column;
  gap: 8px;
  z-index: 100;
  background: rgba(255, 255, 255, 0.95);
  padding: 8px;
  border-radius: 8px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.15);
}

.zoom-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  border: none;
  background: white;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s;
  color: #495057;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.zoom-btn:hover {
  background: #3498db;
  color: white;
  transform: scale(1.05);
  box-shadow: 0 2px 6px rgba(52, 152, 219, 0.3);
}

.zoom-btn:active {
  transform: scale(0.95);
}

.chart-container {
  flex: 1;
  position: relative;
  overflow: hidden;
}

.wordcloud-svg {
  width: 100%;
  height: 100%;
  display: block;
}

.wordcloud-tooltip {
  position: fixed;
  background: linear-gradient(135deg, rgba(52, 152, 219, 0.95), rgba(41, 128, 185, 0.95));
  color: white;
  padding: 10px 16px;
  border-radius: 8px;
  pointer-events: none;
  z-index: 1000;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.2);
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen',
    'Ubuntu', 'Cantarell', 'Fira Sans', 'Droid Sans', 'Helvetica Neue',
    sans-serif;
  border: 1px solid rgba(255, 255, 255, 0.2);
}

.tooltip-word {
  font-size: 18px;
  font-weight: bold;
  margin-bottom: 4px;
  letter-spacing: 0.5px;
}

.tooltip-freq {
  font-size: 13px;
  color: rgba(255, 255, 255, 0.9);
  font-weight: 500;
}

/* D3元素样式 */
:deep(.word-label) {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen',
    'Ubuntu', 'Cantarell', 'Fira Sans', 'Droid Sans', 'Helvetica Neue',
    sans-serif;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
}
</style>

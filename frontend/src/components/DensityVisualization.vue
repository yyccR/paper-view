<template>
  <div class="density-visualization">
    <!-- 控制面板 -->
    <div class="density-controls">
      <div class="control-group">
        <label>{{ $t('densityViz.kernelSize') }}:</label>
        <input type="range" v-model.number="kernelSize" min="20" max="100" step="5" @input="updateDensity" />
        <span>{{ kernelSize }}</span>
      </div>
      <div class="control-group">
        <label>{{ $t('densityViz.resolution') }}:</label>
        <select v-model.number="resolution" @change="updateDensity">
          <option :value="1">{{ $t('densityViz.resolutionHigh') }}</option>
          <option :value="2">{{ $t('densityViz.resolutionMedium') }}</option>
          <option :value="3">{{ $t('densityViz.resolutionLow') }}</option>
        </select>
      </div>
      <div class="control-group">
        <label>
          <input type="checkbox" v-model="showLabels" @change="render" />
          {{ $t('densityViz.showLabels') }}
        </label>
      </div>
      <div class="control-group">
        <button @click="resetView" class="reset-btn">{{ $t('densityViz.reset') }}</button>
      </div>
    </div>

    <!-- Canvas画布 -->
    <div class="canvas-wrapper" ref="canvasWrapper">
      <canvas ref="canvas" @mousedown="onMouseDown" @mousemove="onMouseMove" @mouseup="onMouseUp" @wheel="onWheel"></canvas>
      
      <!-- 悬浮信息 -->
      <div class="hover-info" v-if="hoveredNode" :style="{ left: hoverInfoX + 'px', top: hoverInfoY + 'px' }">
        <div class="info-title">{{ hoveredNode.label }}</div>
        <div class="info-row">{{ $t('densityViz.citations') }}: <strong>{{ hoveredNode.weights?.Citations || 0 }}</strong></div>
        <div class="info-row">{{ $t('densityViz.avgCitations') }}: <strong>{{ hoveredNode.scores?.['Avg. citations']?.toFixed(1) || 'N/A' }}</strong></div>
      </div>
    </div>

    <!-- 颜色图例 -->
    <div class="color-legend">
      <div class="legend-title">{{ $t('densityViz.density') }}</div>
      <div class="legend-gradient"></div>
      <div class="legend-labels">
        <span>{{ $t('densityViz.low') }}</span>
        <span>{{ $t('densityViz.high') }}</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch, nextTick } from 'vue'
import { useI18n } from 'vue-i18n'

const { t } = useI18n()

const props = defineProps({
  networkData: {
    type: Object,
    required: true
  }
})

const canvas = ref(null)
const canvasWrapper = ref(null)
const ctx = ref(null)
const hoveredNode = ref(null)
const hoverInfoX = ref(0)
const hoverInfoY = ref(0)

// 控制参数
const kernelSize = ref(50) // 高斯核大小
const resolution = ref(2) // 密度计算分辨率（1=高, 2=中, 3=低）
const showLabels = ref(true) // 是否显示标签

// 视图状态
const viewState = ref({
  offsetX: 0,
  offsetY: 0,
  scale: 1,
  baseScale: 1,
  isDragging: false,
  dragStartX: 0,
  dragStartY: 0,
  dragStartOffsetX: 0,
  dragStartOffsetY: 0
})

// 节点数据
const nodes = ref([])
const densityMap = ref(null)
const densityWidth = ref(0)
const densityHeight = ref(0)

// VOSviewer风格的颜色映射（蓝色→绿色→黄色→红色）
const getDensityColor = (density) => {
  // density: 0-1之间的归一化值
  const colors = [
    { pos: 0.0, r: 0, g: 0, b: 255 },      // 深蓝色 (低密度)
    { pos: 0.25, r: 0, g: 255, b: 255 },   // 青色
    { pos: 0.5, r: 0, g: 255, b: 0 },      // 绿色
    { pos: 0.75, r: 255, g: 255, b: 0 },   // 黄色
    { pos: 1.0, r: 255, g: 0, b: 0 }       // 红色 (高密度)
  ]
  
  // 找到对应的颜色区间
  for (let i = 0; i < colors.length - 1; i++) {
    if (density >= colors[i].pos && density <= colors[i + 1].pos) {
      const t = (density - colors[i].pos) / (colors[i + 1].pos - colors[i].pos)
      const r = Math.round(colors[i].r + t * (colors[i + 1].r - colors[i].r))
      const g = Math.round(colors[i].g + t * (colors[i + 1].g - colors[i].g))
      const b = Math.round(colors[i].b + t * (colors[i + 1].b - colors[i].b))
      return { r, g, b }
    }
  }
  return { r: 255, g: 0, b: 0 }
}

// 高斯核函数
const gaussianKernel = (distance, sigma) => {
  return Math.exp(-(distance * distance) / (2 * sigma * sigma))
}

// 计算密度图
const calculateDensityMap = () => {
  if (!canvas.value || nodes.value.length === 0) return
  
  const width = canvas.value.width
  const height = canvas.value.height
  const step = resolution.value // 采样步长
  
  densityWidth.value = Math.ceil(width / step)
  densityHeight.value = Math.ceil(height / step)
  
  const map = new Float32Array(densityWidth.value * densityHeight.value)
  const sigma = kernelSize.value
  
  // 计算每个采样点的密度
  for (let y = 0; y < densityHeight.value; y++) {
    for (let x = 0; x < densityWidth.value; x++) {
      const screenX = x * step
      const screenY = y * step
      let density = 0
      
      // 计算所有节点对该点的密度贡献
      nodes.value.forEach(node => {
        const dx = screenX - node.screenX
        const dy = screenY - node.screenY
        const distance = Math.sqrt(dx * dx + dy * dy)
        
        // 使用节点权重（引用数）作为密度权重
        const weight = Math.sqrt((node.weights?.Citations || 0) + (node.weights?.Documents || 1))
        density += weight * gaussianKernel(distance, sigma)
      })
      
      map[y * densityWidth.value + x] = density
    }
  }
  
  // 归一化密度值
  let maxDensity = 0
  for (let i = 0; i < map.length; i++) {
    if (map[i] > maxDensity) maxDensity = map[i]
  }
  
  if (maxDensity > 0) {
    for (let i = 0; i < map.length; i++) {
      map[i] /= maxDensity
    }
  }
  
  densityMap.value = map
}

const initCanvas = () => {
  if (!canvas.value || !canvasWrapper.value) return
  
  const wrapper = canvasWrapper.value
  canvas.value.width = wrapper.clientWidth
  canvas.value.height = wrapper.clientHeight
  ctx.value = canvas.value.getContext('2d')
  
  // 解析网络数据
  if (props.networkData?.network?.items) {
    nodes.value = props.networkData.network.items.map(item => ({
      ...item,
      screenX: 0,
      screenY: 0
    }))
  }
  
  // 计算坐标范围并居中
  if (nodes.value.length > 0) {
    const xCoords = nodes.value.map(n => n.x)
    const yCoords = nodes.value.map(n => n.y)
    const minX = Math.min(...xCoords)
    const maxX = Math.max(...xCoords)
    const minY = Math.min(...yCoords)
    const maxY = Math.max(...yCoords)
    
    const dataWidth = maxX - minX
    const dataHeight = maxY - minY
    
    // 计算合适的缩放比例
    const padding = 100
    const scaleX = (canvas.value.width - padding * 2) / dataWidth
    const scaleY = (canvas.value.height - padding * 2) / dataHeight
    viewState.value.scale = Math.min(scaleX, scaleY, 800)
    viewState.value.baseScale = viewState.value.scale
    
    // 居中偏移
    viewState.value.offsetX = canvas.value.width / 2
    viewState.value.offsetY = canvas.value.height / 2
  }
  
  updateDensity()
}

const worldToScreen = (x, y) => {
  const { offsetX, offsetY, scale } = viewState.value
  return {
    x: x * scale + offsetX,
    y: y * scale + offsetY
  }
}

const screenToWorld = (x, y) => {
  const { offsetX, offsetY, scale } = viewState.value
  return {
    x: (x - offsetX) / scale,
    y: (y - offsetY) / scale
  }
}

const updateDensity = () => {
  // 更新节点屏幕坐标
  nodes.value.forEach(node => {
    const screen = worldToScreen(node.x, node.y)
    node.screenX = screen.x
    node.screenY = screen.y
  })
  
  // 重新计算密度图
  calculateDensityMap()
  render()
}

const render = () => {
  if (!ctx.value || !canvas.value) return
  
  const context = ctx.value
  const width = canvas.value.width
  const height = canvas.value.height
  
  // 清空画布
  context.clearRect(0, 0, width, height)
  
  // 绘制密度热力图
  if (densityMap.value) {
    const imageData = context.createImageData(width, height)
    const data = imageData.data
    
    const step = resolution.value
    
    for (let y = 0; y < height; y++) {
      for (let x = 0; x < width; x++) {
        const mapX = Math.floor(x / step)
        const mapY = Math.floor(y / step)
        
        if (mapX < densityWidth.value && mapY < densityHeight.value) {
          const density = densityMap.value[mapY * densityWidth.value + mapX]
          const color = getDensityColor(density)
          
          const idx = (y * width + x) * 4
          data[idx] = color.r
          data[idx + 1] = color.g
          data[idx + 2] = color.b
          data[idx + 3] = 255 * 0.7 // 透明度
        }
      }
    }
    
    context.putImageData(imageData, 0, 0)
  }
  
  // 绘制节点（小圆点）
  nodes.value.forEach(node => {
    const size = 3
    context.fillStyle = 'rgba(255, 255, 255, 0.8)'
    context.strokeStyle = 'rgba(50, 50, 50, 0.6)'
    context.lineWidth = 1
    
    context.beginPath()
    context.arc(node.screenX, node.screenY, size, 0, Math.PI * 2)
    context.fill()
    context.stroke()
  })
  
  // 绘制标签
  if (showLabels.value) {
    context.textAlign = 'center'
    context.textBaseline = 'middle'
    context.font = '11px Arial, sans-serif'
    context.fillStyle = 'rgba(0, 0, 0, 0.8)'
    context.strokeStyle = 'rgba(255, 255, 255, 0.8)'
    context.lineWidth = 3
    
    nodes.value.forEach(node => {
      const label = node.label || ''
      // 先描边再填充，形成描边效果
      context.strokeText(label, node.screenX, node.screenY - 8)
      context.fillText(label, node.screenX, node.screenY - 8)
    })
  }
  
  // 高亮悬浮节点
  if (hoveredNode.value) {
    const node = hoveredNode.value
    const size = 5
    context.fillStyle = 'rgba(255, 255, 0, 0.9)'
    context.strokeStyle = 'rgba(255, 100, 0, 1)'
    context.lineWidth = 2
    
    context.beginPath()
    context.arc(node.screenX, node.screenY, size, 0, Math.PI * 2)
    context.fill()
    context.stroke()
  }
}

const getNodeAtPosition = (x, y) => {
  const threshold = 10
  for (let i = nodes.value.length - 1; i >= 0; i--) {
    const node = nodes.value[i]
    const dx = x - node.screenX
    const dy = y - node.screenY
    const distance = Math.sqrt(dx * dx + dy * dy)
    if (distance <= threshold) {
      return node
    }
  }
  return null
}

const onMouseDown = (e) => {
  const rect = canvas.value.getBoundingClientRect()
  const x = e.clientX - rect.left
  const y = e.clientY - rect.top
  
  const node = getNodeAtPosition(x, y)
  if (node) {
    return
  }
  
  // 开始拖拽画布
  viewState.value.isDragging = true
  viewState.value.dragStartX = e.clientX
  viewState.value.dragStartY = e.clientY
  viewState.value.dragStartOffsetX = viewState.value.offsetX
  viewState.value.dragStartOffsetY = viewState.value.offsetY
}

const onMouseMove = (e) => {
  const rect = canvas.value.getBoundingClientRect()
  const x = e.clientX - rect.left
  const y = e.clientY - rect.top
  
  if (viewState.value.isDragging) {
    const dx = e.clientX - viewState.value.dragStartX
    const dy = e.clientY - viewState.value.dragStartY
    
    viewState.value.offsetX = viewState.value.dragStartOffsetX + dx
    viewState.value.offsetY = viewState.value.dragStartOffsetY + dy
    
    updateDensity()
  } else {
    const node = getNodeAtPosition(x, y)
    if (node !== hoveredNode.value) {
      hoveredNode.value = node
      canvas.value.style.cursor = node ? 'pointer' : 'move'
      
      if (node) {
        hoverInfoX.value = canvas.value.width - 220
        hoverInfoY.value = canvas.value.height - 120
      }
      
      render()
    }
  }
}

const onMouseUp = () => {
  viewState.value.isDragging = false
}

const onWheel = (e) => {
  e.preventDefault()
  
  const rect = canvas.value.getBoundingClientRect()
  const mouseX = e.clientX - rect.left
  const mouseY = e.clientY - rect.top
  
  const worldBefore = screenToWorld(mouseX, mouseY)
  
  const scaleFactor = e.deltaY < 0 ? 1.1 : 0.9
  viewState.value.scale *= scaleFactor
  viewState.value.scale = Math.max(100, Math.min(3000, viewState.value.scale))
  
  const worldAfter = screenToWorld(mouseX, mouseY)
  
  viewState.value.offsetX += (worldAfter.x - worldBefore.x) * viewState.value.scale
  viewState.value.offsetY += (worldAfter.y - worldBefore.y) * viewState.value.scale
  
  updateDensity()
}

const resetView = () => {
  if (nodes.value.length > 0) {
    const xCoords = nodes.value.map(n => n.x)
    const yCoords = nodes.value.map(n => n.y)
    const minX = Math.min(...xCoords)
    const maxX = Math.max(...xCoords)
    const minY = Math.min(...yCoords)
    const maxY = Math.max(...yCoords)
    
    const dataWidth = maxX - minX
    const dataHeight = maxY - minY
    
    const padding = 100
    const scaleX = (canvas.value.width - padding * 2) / dataWidth
    const scaleY = (canvas.value.height - padding * 2) / dataHeight
    viewState.value.scale = Math.min(scaleX, scaleY, 800)
    viewState.value.baseScale = viewState.value.scale
    
    viewState.value.offsetX = canvas.value.width / 2
    viewState.value.offsetY = canvas.value.height / 2
  }
  
  updateDensity()
}

const handleResize = () => {
  if (canvas.value && canvasWrapper.value) {
    canvas.value.width = canvasWrapper.value.clientWidth
    canvas.value.height = canvasWrapper.value.clientHeight
    updateDensity()
  }
}

onMounted(() => {
  nextTick(() => {
    initCanvas()
    window.addEventListener('resize', handleResize)
  })
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
})

watch(() => props.networkData, () => {
  nextTick(() => {
    initCanvas()
  })
}, { deep: true })
</script>

<style scoped>
.density-visualization {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  background: #fafafa;
  position: relative;
}

.density-controls {
  display: flex;
  gap: 20px;
  padding: 12px 20px;
  background: rgba(255, 255, 255, 0.95);
  border-bottom: 1px solid #e0e0e0;
  align-items: center;
  flex-wrap: wrap;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
}

.control-group {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  color: #333;
}

.control-group label {
  font-weight: 500;
  white-space: nowrap;
}

.control-group input[type="range"] {
  width: 120px;
}

.control-group select {
  padding: 4px 8px;
  border: 1px solid #ddd;
  border-radius: 4px;
  background: white;
  font-size: 13px;
}

.control-group input[type="checkbox"] {
  width: 16px;
  height: 16px;
  cursor: pointer;
}

.reset-btn {
  padding: 6px 16px;
  background: #3498db;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 13px;
  font-weight: 500;
  transition: background 0.2s;
}

.reset-btn:hover {
  background: #2980b9;
}

.canvas-wrapper {
  flex: 1;
  position: relative;
  overflow: hidden;
}

.canvas-wrapper canvas {
  display: block;
  cursor: move;
  background: white;
}

.hover-info {
  position: absolute;
  background: rgba(255, 255, 255, 0.95);
  border: 1px solid #ddd;
  border-radius: 6px;
  padding: 8px 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
  pointer-events: none;
  z-index: 1000;
  min-width: 200px;
  backdrop-filter: blur(8px);
}

.info-title {
  font-size: 13px;
  font-weight: 600;
  color: #333;
  margin-bottom: 6px;
}

.info-row {
  font-size: 11px;
  color: #666;
  margin: 2px 0;
}

.info-row strong {
  color: #333;
  font-weight: 600;
}

.color-legend {
  position: absolute;
  bottom: 20px;
  right: 20px;
  background: rgba(255, 255, 255, 0.95);
  border: 1px solid #ddd;
  border-radius: 6px;
  padding: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
  backdrop-filter: blur(8px);
  min-width: 150px;
}

.legend-title {
  font-size: 12px;
  font-weight: 600;
  color: #333;
  margin-bottom: 8px;
  text-align: center;
}

.legend-gradient {
  height: 20px;
  background: linear-gradient(to right, 
    rgb(0, 0, 255),      /* 蓝色 */
    rgb(0, 255, 255),    /* 青色 */
    rgb(0, 255, 0),      /* 绿色 */
    rgb(255, 255, 0),    /* 黄色 */
    rgb(255, 0, 0)       /* 红色 */
  );
  border-radius: 3px;
  margin-bottom: 6px;
}

.legend-labels {
  display: flex;
  justify-content: space-between;
  font-size: 11px;
  color: #666;
}
</style>

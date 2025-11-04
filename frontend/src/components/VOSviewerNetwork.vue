<template>
  <div class="vosviewer-network">
    <div class="network-controls">
      <div class="control-group">
        <label>{{ $t('wordcloud.zoom') }}</label>
        <div class="zoom-controls">
          <button @click="zoomIn" class="control-btn">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
              <path d="M12 5V19M5 12H19" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
            </svg>
          </button>
          <button @click="zoomOut" class="control-btn">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
              <path d="M5 12H19" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
            </svg>
          </button>
          <button @click="resetView" class="control-btn">
            {{ $t('wordcloud.reset') }}
          </button>
        </div>
      </div>
      
      <div class="info-panel" v-if="selectedNode || hoveredNode">
        <h4>{{ (selectedNode || hoveredNode).label }}</h4>
        <div class="node-stats">
          <div class="stat-item">
            <span class="stat-label">Documents:</span>
            <span class="stat-value">{{ (selectedNode || hoveredNode).weights?.Documents || 0 }}</span>
          </div>
          <div class="stat-item">
            <span class="stat-label">Citations:</span>
            <span class="stat-value">{{ (selectedNode || hoveredNode).weights?.Citations || 0 }}</span>
          </div>
          <div class="stat-item">
            <span class="stat-label">Avg. Citations:</span>
            <span class="stat-value">{{ (selectedNode || hoveredNode).scores?.['Avg. citations']?.toFixed(1) || 'N/A' }}</span>
          </div>
          <div class="stat-item">
            <span class="stat-label">Avg. Year:</span>
            <span class="stat-value">{{ (selectedNode || hoveredNode).scores?.['Avg. pub. year']?.toFixed(0) || 'N/A' }}</span>
          </div>
          <div class="stat-item">
            <span class="stat-label">Cluster:</span>
            <span class="stat-value" :style="{ color: getClusterColor((selectedNode || hoveredNode).cluster) }">
              #{{ (selectedNode || hoveredNode).cluster }}
            </span>
          </div>
        </div>
      </div>
    </div>
    
    <div class="network-canvas-wrapper" ref="canvasWrapper">
      <canvas ref="canvas" @mousedown="onMouseDown" @mousemove="onMouseMove" @mouseup="onMouseUp" @wheel="onWheel"></canvas>
    </div>
    
    <div class="legend">
      <div class="legend-title">Clusters</div>
      <div class="legend-items">
        <div v-for="cluster in uniqueClusters" :key="cluster" class="legend-item">
          <span class="legend-color" :style="{ backgroundColor: getClusterColor(cluster) }"></span>
          <span class="legend-label">Cluster {{ cluster }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, computed, watch, nextTick } from 'vue'

const props = defineProps({
  networkData: {
    type: Object,
    required: true
  }
})

const canvas = ref(null)
const canvasWrapper = ref(null)
const ctx = ref(null)
const selectedNode = ref(null)
const hoveredNode = ref(null)

// 视图状态
const viewState = ref({
  offsetX: 0,
  offsetY: 0,
  scale: 1,
  isDragging: false,
  dragStartX: 0,
  dragStartY: 0,
  dragStartOffsetX: 0,
  dragStartOffsetY: 0
})

// 节点和链接数据
const nodes = ref([])
const links = ref([])
const nodeConnections = ref(new Map()) // 存储每个节点的连接关系

// 簇的颜色映射
const clusterColors = [
  '#E57373', '#F06292', '#BA68C8', '#9575CD', '#7986CB',
  '#64B5F6', '#4FC3F7', '#4DD0E1', '#4DB6AC', '#81C784',
  '#AED581', '#DCE775', '#FFD54F', '#FFB74D', '#FF8A65',
  '#A1887F', '#90A4AE', '#78909C', '#EF5350', '#EC407A',
  '#AB47BC', '#7E57C2', '#5C6BC0', '#42A5F5', '#29B6F6'
]

const uniqueClusters = computed(() => {
  const clusters = new Set(nodes.value.map(n => n.cluster))
  return Array.from(clusters).sort((a, b) => a - b)
})

const getClusterColor = (cluster) => {
  return clusterColors[cluster % clusterColors.length]
}

const hexToRgba = (hex, alpha) => {
  // 将十六进制颜色转换为 RGBA
  const r = parseInt(hex.slice(1, 3), 16)
  const g = parseInt(hex.slice(3, 5), 16)
  const b = parseInt(hex.slice(5, 7), 16)
  return `rgba(${r}, ${g}, ${b}, ${alpha})`
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
  
  if (props.networkData?.network?.links) {
    links.value = props.networkData.network.links
    
    // 构建节点连接关系映射
    const connections = new Map()
    links.value.forEach(link => {
      if (!connections.has(link.source_id)) {
        connections.set(link.source_id, new Set())
      }
      if (!connections.has(link.target_id)) {
        connections.set(link.target_id, new Set())
      }
      connections.get(link.source_id).add(link.target_id)
      connections.get(link.target_id).add(link.source_id)
    })
    nodeConnections.value = connections
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
    const centerX = (minX + maxX) / 2
    const centerY = (minY + maxY) / 2
    
    // 计算合适的缩放比例
    const padding = 100
    const scaleX = (canvas.value.width - padding * 2) / dataWidth
    const scaleY = (canvas.value.height - padding * 2) / dataHeight
    viewState.value.scale = Math.min(scaleX, scaleY, 1000) // 限制最大缩放
    
    // 居中偏移
    viewState.value.offsetX = canvas.value.width / 2
    viewState.value.offsetY = canvas.value.height / 2
  }
  
  render()
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

const render = () => {
  if (!ctx.value || !canvas.value) return
  
  const context = ctx.value
  context.clearRect(0, 0, canvas.value.width, canvas.value.height)
  
  // 绘制背景
  context.fillStyle = '#fafafa'
  context.fillRect(0, 0, canvas.value.width, canvas.value.height)
  
  // 更新节点屏幕坐标
  nodes.value.forEach(node => {
    const screen = worldToScreen(node.x, node.y)
    node.screenX = screen.x
    node.screenY = screen.y
  })
  
  // 绘制链接（曲线）
  if (links.value.length > 0) {
    links.value.forEach(link => {
      const source = nodes.value.find(n => n.id === link.source_id)
      const target = nodes.value.find(n => n.id === link.target_id)
      if (source && target) {
        // 判断是否应该高亮这条连接
        const isHighlighted = hoveredNode.value && 
          (source.id === hoveredNode.value.id || target.id === hoveredNode.value.id)
        
        // 根据连接强度设置透明度
        const strength = link.strength || 1
        const baseOpacity = isHighlighted ? 0.6 : 0.15
        const opacity = Math.min(baseOpacity * strength, 0.8)
        
        context.strokeStyle = isHighlighted 
          ? `rgba(100, 100, 100, ${opacity})`
          : `rgba(180, 180, 180, ${opacity})`
        context.lineWidth = isHighlighted ? 2 : 1
        
        // 绘制贝塞尔曲线
        const dx = target.screenX - source.screenX
        const dy = target.screenY - source.screenY
        const distance = Math.sqrt(dx * dx + dy * dy)
        
        // 控制点偏移（产生曲线效果）
        const curvature = 0.2 // 曲率系数
        const offsetX = -dy * curvature * (distance / 100)
        const offsetY = dx * curvature * (distance / 100)
        
        const cpX = (source.screenX + target.screenX) / 2 + offsetX
        const cpY = (source.screenY + target.screenY) / 2 + offsetY
        
        context.beginPath()
        context.moveTo(source.screenX, source.screenY)
        context.quadraticCurveTo(cpX, cpY, target.screenX, target.screenY)
        context.stroke()
      }
    })
  }
  
  // 绘制节点
  nodes.value.forEach(node => {
    // 根据引用数和文档数计算节点大小
    const citations = node.weights?.Citations || 0
    const documents = node.weights?.Documents || 1
    const size = Math.sqrt(citations + documents * 10) * 2 + 6
    
    const color = getClusterColor(node.cluster)
    
    // 判断节点是否应该高亮或变暗
    let opacity = 0.7 // 默认透明度
    let isHighlighted = false
    
    if (hoveredNode.value) {
      if (node.id === hoveredNode.value.id) {
        // 当前悬浮节点
        opacity = 1
        isHighlighted = true
      } else if (nodeConnections.value.get(hoveredNode.value.id)?.has(node.id)) {
        // 相关节点
        opacity = 0.8
        isHighlighted = true
      } else {
        // 不相关节点变暗
        opacity = 0.15
      }
    }
    
    // 节点圆圈外部光晕（高亮时）
    if (isHighlighted) {
      const gradient = context.createRadialGradient(
        node.screenX, node.screenY, 0,
        node.screenX, node.screenY, size + 8
      )
      gradient.addColorStop(0, `${color}00`)
      gradient.addColorStop(0.5, `${color}40`)
      gradient.addColorStop(1, `${color}00`)
      context.fillStyle = gradient
      context.beginPath()
      context.arc(node.screenX, node.screenY, size + 8, 0, Math.PI * 2)
      context.fill()
    }
    
    // 节点圆圈 - 带透明度
    const rgbaColor = hexToRgba(color, opacity)
    context.fillStyle = rgbaColor
    context.beginPath()
    context.arc(node.screenX, node.screenY, size, 0, Math.PI * 2)
    context.fill()
    
    // 节点边框（高亮时更明显）
    if (isHighlighted) {
      context.strokeStyle = color
      context.lineWidth = 2
      context.beginPath()
      context.arc(node.screenX, node.screenY, size, 0, Math.PI * 2)
      context.stroke()
    }
    
    // 高亮选中节点
    if (selectedNode.value && selectedNode.value.id === node.id) {
      context.strokeStyle = '#333'
      context.lineWidth = 3
      context.beginPath()
      context.arc(node.screenX, node.screenY, size + 3, 0, Math.PI * 2)
      context.stroke()
    }
    
    // 节点标签 - 显示较大节点、悬浮节点或选中节点的标签
    const showLabel = size > 10 || 
      (hoveredNode.value && node.id === hoveredNode.value.id) ||
      (selectedNode.value && selectedNode.value.id === node.id)
    
    if (showLabel && viewState.value.scale > 400) {
      context.fillStyle = isHighlighted ? '#000' : '#666'
      context.font = isHighlighted ? 'bold 12px Arial' : '11px Arial'
      context.textAlign = 'center'
      context.textBaseline = 'top'
      
      // 文字背景（提高可读性）
      if (isHighlighted) {
        const textWidth = context.measureText(node.label).width
        context.fillStyle = 'rgba(255, 255, 255, 0.9)'
        context.fillRect(
          node.screenX - textWidth / 2 - 4,
          node.screenY + size + 6,
          textWidth + 8,
          16
        )
        context.fillStyle = '#000'
      }
      
      context.fillText(node.label, node.screenX, node.screenY + size + 8)
    }
  })
}

const getNodeAtPosition = (x, y) => {
  // 从后向前遍历（后绘制的在上层）
  for (let i = nodes.value.length - 1; i >= 0; i--) {
    const node = nodes.value[i]
    const citations = node.weights?.Citations || 0
    const documents = node.weights?.Documents || 1
    const size = Math.sqrt(citations + documents * 10) * 2 + 6
    const dx = x - node.screenX
    const dy = y - node.screenY
    const distance = Math.sqrt(dx * dx + dy * dy)
    if (distance <= size + 2) { // 增加一点容差
      return node
    }
  }
  return null
}

const onMouseDown = (e) => {
  const rect = canvas.value.getBoundingClientRect()
  const x = e.clientX - rect.left
  const y = e.clientY - rect.top
  
  // 检查是否点击了节点
  const node = getNodeAtPosition(x, y)
  if (node) {
    selectedNode.value = node
    render()
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
    
    render()
  } else {
    // 检测鼠标悬浮的节点
    const node = getNodeAtPosition(x, y)
    if (node !== hoveredNode.value) {
      hoveredNode.value = node
      canvas.value.style.cursor = node ? 'pointer' : 'move'
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
  
  // 计算缩放前的世界坐标
  const worldBefore = screenToWorld(mouseX, mouseY)
  
  // 更新缩放
  const scaleFactor = e.deltaY < 0 ? 1.1 : 0.9
  viewState.value.scale *= scaleFactor
  viewState.value.scale = Math.max(100, Math.min(3000, viewState.value.scale))
  
  // 计算缩放后的世界坐标
  const worldAfter = screenToWorld(mouseX, mouseY)
  
  // 调整偏移以保持鼠标位置不变
  viewState.value.offsetX += (worldAfter.x - worldBefore.x) * viewState.value.scale
  viewState.value.offsetY += (worldAfter.y - worldBefore.y) * viewState.value.scale
  
  render()
}

const zoomIn = () => {
  viewState.value.scale *= 1.2
  viewState.value.scale = Math.min(3000, viewState.value.scale)
  render()
}

const zoomOut = () => {
  viewState.value.scale *= 0.8
  viewState.value.scale = Math.max(100, viewState.value.scale)
  render()
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
    viewState.value.scale = Math.min(scaleX, scaleY, 1000)
    
    viewState.value.offsetX = canvas.value.width / 2
    viewState.value.offsetY = canvas.value.height / 2
  }
  selectedNode.value = null
  render()
}

const handleResize = () => {
  if (canvas.value && canvasWrapper.value) {
    canvas.value.width = canvasWrapper.value.clientWidth
    canvas.value.height = canvasWrapper.value.clientHeight
    render()
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
.vosviewer-network {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  background: #fafafa;
  position: relative;
}

.network-controls {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  padding: 15px 20px;
  background: white;
  border-bottom: 1px solid #e0e0e0;
  gap: 20px;
  flex-wrap: wrap;
}

.control-group {
  display: flex;
  align-items: center;
  gap: 10px;
}

.control-group label {
  font-size: 14px;
  font-weight: 500;
  color: #555;
}

.zoom-controls {
  display: flex;
  gap: 5px;
}

.control-btn {
  padding: 6px 12px;
  border: 1px solid #ddd;
  background: white;
  border-radius: 4px;
  cursor: pointer;
  font-size: 13px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
}

.control-btn:hover {
  background: #f5f5f5;
  border-color: #999;
}

.control-btn svg {
  display: block;
}

.info-panel {
  flex: 1;
  padding: 10px 15px;
  background: #f8f9fa;
  border-radius: 6px;
  min-width: 250px;
  max-width: 400px;
}

.info-panel h4 {
  margin: 0 0 10px 0;
  font-size: 15px;
  font-weight: 600;
  color: #333;
}

.node-stats {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
}

.stat-item {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.stat-label {
  font-size: 11px;
  color: #666;
  font-weight: 500;
}

.stat-value {
  font-size: 14px;
  font-weight: 600;
  color: #333;
}

.network-canvas-wrapper {
  flex: 1;
  position: relative;
  overflow: hidden;
}

.network-canvas-wrapper canvas {
  display: block;
  cursor: move;
  background: linear-gradient(to bottom, #fafafa 0%, #f5f5f5 100%);
}

.legend {
  position: absolute;
  top: 80px;
  right: 20px;
  background: rgba(255, 255, 255, 0.95);
  border-radius: 8px;
  padding: 12px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.15);
  max-height: 400px;
  overflow-y: auto;
  backdrop-filter: blur(10px);
}

.legend-title {
  font-size: 13px;
  font-weight: 600;
  color: #333;
  margin-bottom: 8px;
}

.legend-items {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  color: #555;
}

.legend-color {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  flex-shrink: 0;
}

.legend-label {
  white-space: nowrap;
}
</style>

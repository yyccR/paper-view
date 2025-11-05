<template>
  <div class="citation-network">
    <div class="network-canvas-wrapper" ref="canvasWrapper">
      <canvas ref="canvas" @mousedown="onMouseDown" @mousemove="onMouseMove" @mouseup="onMouseUp" @wheel="onWheel"></canvas>
      
      <div class="hover-info" v-if="hoveredNode" :style="{ left: hoverInfoX + 'px', top: hoverInfoY + 'px' }">
        <div class="info-title">{{ hoveredNode.label }}</div>
        <div class="info-row">Citations: <strong>{{ hoveredNode.weights?.Citations || 0 }}</strong></div>
        <div class="info-row">Avg. Citations: <strong>{{ hoveredNode.scores?.['Avg. citations']?.toFixed(1) || 'N/A' }}</strong></div>
        <div class="info-row">Avg. Year: <strong>{{ hoveredNode.scores?.['Avg. pub. year']?.toFixed(0) || 'N/A' }}</strong></div>
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
const hoverInfoX = ref(0)
const hoverInfoY = ref(0)

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

const darkenColor = (hex, factor = 0.3) => {
  // 将颜色变暗 - 类似VOSviewer的_calcDarkColor
  const r = parseInt(hex.slice(1, 3), 16)
  const g = parseInt(hex.slice(3, 5), 16)
  const b = parseInt(hex.slice(5, 7), 16)
  
  const newR = Math.floor(r * (1 - factor))
  const newG = Math.floor(g * (1 - factor))
  const newB = Math.floor(b * (1 - factor))
  
  return `rgb(${newR}, ${newG}, ${newB})`
}

// ====== 对齐 VOSviewer 的标签绘制逻辑 ======
const labelColorsCfg = {
  LIGHT_BACKGROUND: 'black',
  ALPHA_DEFAULT: 0.8,
  ALPHA_HIGHLIGHTED: 0.9,
  ALPHA_DIMMED: 0.3
}

const ItemStatus = {
  HOVERED: 'hovered',
  SELECTED: 'selected',
  HIGHLIGHTED: 'highlighted',
  DEFAULT: 'default'
}

const fontFamily = 'Roboto, Arial, sans-serif'

// 基于节点权重计算字体大小、文本宽度与圆半径
const computeNodeMetrics = () => {
  if (!ctx.value) return
  const weights = nodes.value.map(n => (n.weights?.Citations || 0) + (n.weights?.Documents || 0))
  const meanWeight = weights.length ? (weights.reduce((a, b) => a + b, 0) / weights.length) : 1

  nodes.value.forEach(node => {
    const citations = node.weights?.Citations || 0
    const documents = node.weights?.Documents || 0
    const w = citations + documents
    const normalized = meanWeight > 0 ? w / meanWeight : 1
    node._normalizedWeight = normalized

    // 半径与现有实现保持一致，确保视觉一致性
    const radius = Math.sqrt(citations + (documents || 1) * 10) * 0.8 + 3
    node._circleRadius = radius

    // 字号与 VOSviewer 参数类似（9px 基础 + 依据权重的放大）
    node._fontSize = 8 + 3 * Math.pow(normalized, 0.5)
    ctx.value.font = `${Math.round(node._fontSize)}px ${fontFamily}`
    node._labelText = node.label || ''
    node._labelTextWidth = ctx.value.measureText(node._labelText).width
  })
}

// 计算标签缩放因子（使用屏幕坐标，阈值比较为 < 1）
const updateLabelScalingFactors = () => {
  const sorted = [...nodes.value].sort((a, b) => b._circleRadius - a._circleRadius)
  sorted.forEach((item1, i) => {
    item1._labelScalingFactor = 0
    for (let j = 0; j < i; j++) {
      const item2 = sorted[j]
      const xDen = Math.abs((item1.screenX) - (item2.screenX)) || 0.1
      const yDen = Math.abs((item1.screenY) - (item2.screenY)) || 0.1
      const xFactor = (0.5 * (item1._labelTextWidth + item2._labelTextWidth + 2)) / xDen
      const yFactor = (0.5 * (item1._fontSize + item2._fontSize + 2)) / yDen
      const labelScalingFactor = Math.min(xFactor, yFactor)
      if (labelScalingFactor > (item1._labelScalingFactor || 0) && labelScalingFactor > (item2._labelScalingFactor || 0)) {
        item1._labelScalingFactor = labelScalingFactor
      }
    }
  })
}

// 更新节点状态（默认/高亮/悬浮/选中）
const updateItemStatuses = () => {
  const hovered = hoveredNode.value
  const clicked = selectedNode.value
  const highlightedSet = new Set()

  if (hovered) {
    const connected = nodeConnections.value.get(hovered.id) || new Set()
    connected.forEach(id => highlightedSet.add(id))
  }
  if (clicked) {
    const connected = nodeConnections.value.get(clicked.id) || new Set()
    connected.forEach(id => highlightedSet.add(id))
  }

  nodes.value.forEach(item => {
    if (clicked && item.id === clicked.id) item._status = ItemStatus.SELECTED
    else if (hovered && item.id === hovered.id) item._status = ItemStatus.HOVERED
    else if (highlightedSet.has(item.id)) item._status = ItemStatus.HIGHLIGHTED
    else item._status = ItemStatus.DEFAULT
  })
}

// 绘制标签（透明度规则与 VOSviewer 对齐）
const drawLabel = (context, node, status, dimmed) => {
  const color = labelColorsCfg.LIGHT_BACKGROUND
  let alpha = labelColorsCfg.ALPHA_DEFAULT
  switch (status) {
    case ItemStatus.DEFAULT:
      alpha = dimmed ? labelColorsCfg.ALPHA_DIMMED : labelColorsCfg.ALPHA_DEFAULT
      break
    case ItemStatus.HIGHLIGHTED:
    case ItemStatus.SELECTED:
    case ItemStatus.HOVERED:
      alpha = labelColorsCfg.ALPHA_HIGHLIGHTED
      break
    default:
      break
  }
  context.font = `${Math.round(node._fontSize)}px ${fontFamily}`
  context.fillStyle = `rgba(0, 0, 0, ${alpha})`
  context.fillText(node._labelText, node.screenX, node.screenY)
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
    
    // 计算合适的缩放比例 - 增加间距
    const padding = 150
    const scaleX = (canvas.value.width - padding * 2) / dataWidth
    const scaleY = (canvas.value.height - padding * 2) / dataHeight
    viewState.value.scale = Math.min(scaleX, scaleY, 600) * 1.2 // 减小初始缩放比例以增加节点间距
    viewState.value.baseScale = viewState.value.scale
    
    // 居中偏移
    viewState.value.offsetX = canvas.value.width / 2
    viewState.value.offsetY = canvas.value.height / 2
  }
  // 初始化字体度量
  computeNodeMetrics()

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

  // 更新标签缩放因子与状态
  updateLabelScalingFactors()
  updateItemStatuses()
  const zK = Math.min(200, Math.max(0.5, viewState.value.baseScale ? (viewState.value.scale / viewState.value.baseScale) : 1))
  const dimmed = !!(hoveredNode.value || selectedNode.value)
  
  // 绘制链接（曲线）
  if (links.value.length > 0) {
    links.value.forEach(link => {
      const source = nodes.value.find(n => n.id === link.source_id)
      const target = nodes.value.find(n => n.id === link.target_id)
      if (source && target) {
        // 判断是否应该高亮这条连接
        const isHighlighted = hoveredNode.value && 
          (source.id === hoveredNode.value.id || target.id === hoveredNode.value.id)
        
        // 根据连接强度设置透明度 - 使用VOSviewer的透明度策略
        const strength = link.strength || 1
        const baseOpacity = isHighlighted ? 0.8 : 0.4 // VOSviewer: ALPHA_HIGHLIGHTED: 0.8, ALPHA_DEFAULT: 0.4
        const opacity = Math.min(baseOpacity * strength, 0.9)
        
        // 使用更柔和的灰色
        context.strokeStyle = isHighlighted 
          ? `rgba(120, 120, 120, ${opacity})`
          : `rgba(200, 200, 200, ${opacity})`
        context.lineWidth = isHighlighted ? 1.2 : 1
        
        // 绘制贝塞尔曲线
        const dx = target.screenX - source.screenX
        const dy = target.screenY - source.screenY
        const distance = Math.sqrt(dx * dx + dy * dy)
        
        // 控制点偏移 - 使用VOSviewer的曲线算法
        const alpha = 0.3 // VOSviewer的曲率参数
        const sign = -1
        const xm = (source.screenX + target.screenX) / 2
        const ym = (source.screenY + target.screenY) / 2
        
        const cpX = xm + sign * alpha * (target.screenY - source.screenY)
        const cpY = ym - sign * alpha * (target.screenX - source.screenX)
        
        context.beginPath()
        context.moveTo(source.screenX, source.screenY)
        context.quadraticCurveTo(cpX, cpY, target.screenX, target.screenY)
        context.stroke()
      }
    })
  }
  
  // 绘制节点
  nodes.value.forEach(node => {
    // 根据引用数和文档数计算节点大小 - 减小节点尺寸
    const citations = node.weights?.Citations || 0
    const documents = node.weights?.Documents || 1
    const size = Math.sqrt(citations + documents * 10) * 0.8 + 3
    
    const color = getClusterColor(node.cluster)
    
    // 判断节点是否应该高亮或变暗 - 使用VOSviewer的透明度策略
    let opacity = 0.7 // 默认透明度 (VOSviewer: ALPHA_DEFAULT)
    const status = node._status || ItemStatus.DEFAULT
    const isHighlighted = status === ItemStatus.HOVERED || status === ItemStatus.SELECTED || status === ItemStatus.HIGHLIGHTED
    if (isHighlighted) opacity = 1.0
    else if (dimmed) opacity = 0.2
    
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
    
    // 节点边框 - 使用VOSviewer的边框策略（高亮时更明显）
    if (isHighlighted) {
      // 使用更深的颜色作为边框
      const borderColor = darkenColor(color, 0.3)
      context.strokeStyle = borderColor
      context.lineWidth = 1.5
      context.beginPath()
      context.arc(node.screenX, node.screenY, size, 0, Math.PI * 2)
      context.stroke()
    }
    
    // 高亮选中节点 - 使用VOSviewer的双重边框效果
    if (status === ItemStatus.SELECTED) {
      // 内层边框
      const borderColor = darkenColor(color, 0.3)
      context.strokeStyle = borderColor
      context.lineWidth = 1.5
      context.beginPath()
      context.arc(node.screenX, node.screenY, size, 0, Math.PI * 2)
      context.stroke()
      
      // 外层边框（VOSviewer的双重边框效果）
      context.strokeStyle = borderColor
      context.lineWidth = 2
      context.beginPath()
      context.arc(node.screenX, node.screenY, size + 6, 0, Math.PI * 2)
      context.stroke()
    }
  })

  // 分层绘制标签（中心对齐）
  context.textAlign = 'center'
  context.textBaseline = 'middle'
  // 默认项
  for (let i = nodes.value.length - 1; i >= 0; i--) {
    const n = nodes.value[i]
    if ((n._labelScalingFactor || 0) < zK && (n._status === ItemStatus.DEFAULT || !n._status)) {
      drawLabel(context, n, ItemStatus.DEFAULT, dimmed)
    }
  }
  // 高亮项（相邻/联通）
  for (let i = nodes.value.length - 1; i >= 0; i--) {
    const n = nodes.value[i]
    if ((n._labelScalingFactor || 0) < zK && n._status === ItemStatus.HIGHLIGHTED) {
      drawLabel(context, n, ItemStatus.HIGHLIGHTED, dimmed)
    }
  }
  // 选中项
  if (selectedNode.value) {
    const n = nodes.value.find(x => x.id === selectedNode.value.id)
    if (n) drawLabel(context, n, ItemStatus.SELECTED, dimmed)
  }
  // 悬浮项
  if (hoveredNode.value) {
    const n = nodes.value.find(x => x.id === hoveredNode.value.id)
    if (n) drawLabel(context, n, ItemStatus.HOVERED, dimmed)
  }
}

const getNodeAtPosition = (x, y) => {
  // 从后向前遍历（后绘制的在上层）
  for (let i = nodes.value.length - 1; i >= 0; i--) {
    const node = nodes.value[i]
    const citations = node.weights?.Citations || 0
    const documents = node.weights?.Documents || 1
    const size = Math.sqrt(citations + documents * 10) * 0.8 + 3
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
      
      // 更新悬浮信息位置（右下角）
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
    viewState.value.baseScale = viewState.value.scale
    
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
    computeNodeMetrics()
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
.citation-network {
  width: 100%;
  height: 100%;
  background: #fafafa;
  position: relative;
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
  line-height: 1.2;
}

.info-row {
  font-size: 11px;
  color: #666;
  margin: 2px 0;
  line-height: 1.3;
}

.info-row strong {
  color: #333;
  font-weight: 600;
}

.network-canvas-wrapper {
  width: 100%;
  height: 100%;
  position: relative;
  overflow: hidden;
}

.network-canvas-wrapper canvas {
  display: block;
  cursor: move;
  background: linear-gradient(to bottom, #fafafa 0%, #f5f5f5 100%);
}

</style>

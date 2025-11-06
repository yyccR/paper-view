<template>
  <div class="density-visualization">
    <!-- Canvas画布 - WebGL用于密度图 -->
    <div class="canvas-wrapper" ref="canvasWrapper">
      <canvas ref="glCanvas" class="gl-canvas"></canvas>
      <canvas ref="overlayCanvas" class="overlay-canvas" 
        @mousedown="onMouseDown" 
        @mousemove="onMouseMove" 
        @mouseup="onMouseUp" 
        @wheel="onWheel">
      </canvas>
      
      <!-- 悬浮信息 -->
      <div class="hover-info" v-if="hoveredNode" :style="{ left: hoverInfoX + 'px', top: hoverInfoY + 'px' }">
        <div class="info-title">{{ hoveredNode.label }}</div>
        <div class="info-row">{{ $t('densityViz.citations') }}: <strong>{{ hoveredNode.weights?.Citations || 0 }}</strong></div>
        <div class="info-row">{{ $t('densityViz.avgCitations') }}: <strong>{{ hoveredNode.scores?.['Avg. citations']?.toFixed(1) || 'N/A' }}</strong></div>
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

const glCanvas = ref(null)
const overlayCanvas = ref(null)
const canvasWrapper = ref(null)
const gl = ref(null)
const overlayCtx = ref(null)
const hoveredNode = ref(null)
const hoverInfoX = ref(0)
const hoverInfoY = ref(0)

// WebGL程序和资源
const shaderProgram = ref(null)
const positionBuffer = ref(null)
const maxDensity = ref(1.0)

// 控制参数
const kernelSize = ref(50) // 高斯核大小
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

// WebGL着色器代码
const vertexShaderSource = `
  attribute vec2 a_position;
  varying vec2 v_texCoord;
  
  void main() {
    gl_Position = vec4(a_position, 0.0, 1.0);
    v_texCoord = (a_position + 1.0) / 2.0;
  }
`

const fragmentShaderSource = `
  precision highp float;
  
  varying vec2 v_texCoord;
  uniform vec2 u_resolution;
  uniform vec2 u_nodePositions[100];
  uniform float u_nodeWeights[100];
  uniform int u_nodeCount;
  uniform float u_sigma;
  uniform float u_maxDensity;
  
  // VOSviewer颜色映射
  vec3 getDensityColor(float density) {
    if (density < 0.25) {
      float t = density / 0.25;
      return mix(vec3(0.0, 0.0, 1.0), vec3(0.0, 1.0, 1.0), t);
    } else if (density < 0.5) {
      float t = (density - 0.25) / 0.25;
      return mix(vec3(0.0, 1.0, 1.0), vec3(0.0, 1.0, 0.0), t);
    } else if (density < 0.75) {
      float t = (density - 0.5) / 0.25;
      return mix(vec3(0.0, 1.0, 0.0), vec3(1.0, 1.0, 0.0), t);
    } else {
      float t = (density - 0.75) / 0.25;
      return mix(vec3(1.0, 1.0, 0.0), vec3(1.0, 0.0, 0.0), t);
    }
  }
  
  void main() {
    vec2 pixelPos = v_texCoord * u_resolution;
    float density = 0.0;
    
    // 计算所有节点对当前像素的密度贡献
    for (int i = 0; i < 100; i++) {
      if (i >= u_nodeCount) break;
      
      vec2 nodePos = u_nodePositions[i];
      float dist = distance(pixelPos, nodePos);
      float weight = u_nodeWeights[i];
      
      // 高斯核
      density += weight * exp(-(dist * dist) / (2.0 * u_sigma * u_sigma));
    }
    
    // 使用平方根增强对比度，让低密度区域也能显示颜色变化
    float normalizedDensity = sqrt(density / u_maxDensity);
    normalizedDensity = clamp(normalizedDensity, 0.0, 1.0);
    
    vec3 color = getDensityColor(normalizedDensity);
    gl_FragColor = vec4(color, 0.7);
  }
`

// 创建着色器
const createShader = (gl, type, source) => {
  const shader = gl.createShader(type)
  gl.shaderSource(shader, source)
  gl.compileShader(shader)
  
  if (!gl.getShaderParameter(shader, gl.COMPILE_STATUS)) {
    console.error('Shader compilation error:', gl.getShaderInfoLog(shader))
    gl.deleteShader(shader)
    return null
  }
  
  return shader
}

// 创建着色器程序
const createProgram = (gl, vertexShader, fragmentShader) => {
  const program = gl.createProgram()
  gl.attachShader(program, vertexShader)
  gl.attachShader(program, fragmentShader)
  gl.linkProgram(program)
  
  if (!gl.getProgramParameter(program, gl.LINK_STATUS)) {
    console.error('Program linking error:', gl.getProgramInfoLog(program))
    gl.deleteProgram(program)
    return null
  }
  
  return program
}

// 初始化WebGL
const initWebGL = () => {
  if (!glCanvas.value) return false
  
  const glContext = glCanvas.value.getContext('webgl') || glCanvas.value.getContext('experimental-webgl')
  if (!glContext) {
    console.error('WebGL not supported')
    return false
  }
  
  gl.value = glContext
  
  // 创建着色器
  const vertexShader = createShader(glContext, glContext.VERTEX_SHADER, vertexShaderSource)
  const fragmentShader = createShader(glContext, glContext.FRAGMENT_SHADER, fragmentShaderSource)
  
  if (!vertexShader || !fragmentShader) return false
  
  // 创建程序
  const program = createProgram(glContext, vertexShader, fragmentShader)
  if (!program) return false
  
  shaderProgram.value = program
  
  // 创建全屏四边形
  const positions = new Float32Array([
    -1, -1,
     1, -1,
    -1,  1,
     1,  1
  ])
  
  const buffer = glContext.createBuffer()
  glContext.bindBuffer(glContext.ARRAY_BUFFER, buffer)
  glContext.bufferData(glContext.ARRAY_BUFFER, positions, glContext.STATIC_DRAW)
  positionBuffer.value = buffer
  
  // 启用混合
  glContext.enable(glContext.BLEND)
  glContext.blendFunc(glContext.SRC_ALPHA, glContext.ONE_MINUS_SRC_ALPHA)
  
  return true
}

const initCanvas = () => {
  if (!glCanvas.value || !overlayCanvas.value || !canvasWrapper.value) return
  
  const wrapper = canvasWrapper.value
  const width = wrapper.clientWidth
  const height = wrapper.clientHeight
  
  // 初始化WebGL canvas
  glCanvas.value.width = width
  glCanvas.value.height = height
  
  // 初始化overlay canvas
  overlayCanvas.value.width = width
  overlayCanvas.value.height = height
  overlayCtx.value = overlayCanvas.value.getContext('2d')
  
  // 初始化WebGL
  if (!gl.value) {
    if (!initWebGL()) {
      console.error('Failed to initialize WebGL')
      return
    }
  }
  
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
    const scaleX = (width - padding * 2) / dataWidth
    const scaleY = (height - padding * 2) / dataHeight
    viewState.value.scale = Math.min(scaleX, scaleY, 800)
    viewState.value.baseScale = viewState.value.scale
    
    // 居中偏移
    viewState.value.offsetX = width / 2
    viewState.value.offsetY = height / 2
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
  
  // 计算最大密度（用于归一化）
  calculateMaxDensity()
  
  // 渲染
  render()
}

// 计算最大密度值用于归一化
const calculateMaxDensity = () => {
  if (nodes.value.length === 0) {
    maxDensity.value = 1.0
    return
  }
  
  let max = 0
  const sigma = kernelSize.value
  
  // 在关键点采样以估算最大密度
  for (let i = 0; i < nodes.value.length; i++) {
    const node = nodes.value[i]
    let density = 0
    
    for (let j = 0; j < nodes.value.length; j++) {
      const other = nodes.value[j]
      const dx = node.screenX - other.screenX
      const dy = node.screenY - other.screenY
      const dist = Math.sqrt(dx * dx + dy * dy)
      const weight = Math.sqrt((other.weights?.Citations || 0) + (other.weights?.Documents || 1))
      density += weight * Math.exp(-(dist * dist) / (2 * sigma * sigma))
    }
    
    if (density > max) max = density
  }
  
  // 使用更保守的最大值，增强颜色对比度
  maxDensity.value = max > 0 ? max * 0.6 : 1.0
}

// 使用WebGL渲染密度图
const renderDensityMap = () => {
  if (!gl.value || !shaderProgram.value || !glCanvas.value) return
  
  const glContext = gl.value
  const program = shaderProgram.value
  
  glContext.viewport(0, 0, glCanvas.value.width, glCanvas.value.height)
  glContext.clearColor(1, 1, 1, 1)
  glContext.clear(glContext.COLOR_BUFFER_BIT)
  
  glContext.useProgram(program)
  
  // 设置顶点属性
  const positionLocation = glContext.getAttribLocation(program, 'a_position')
  glContext.bindBuffer(glContext.ARRAY_BUFFER, positionBuffer.value)
  glContext.enableVertexAttribArray(positionLocation)
  glContext.vertexAttribPointer(positionLocation, 2, glContext.FLOAT, false, 0, 0)
  
  // 设置uniforms
  const resolutionLocation = glContext.getUniformLocation(program, 'u_resolution')
  glContext.uniform2f(resolutionLocation, glCanvas.value.width, glCanvas.value.height)
  
  const sigmaLocation = glContext.getUniformLocation(program, 'u_sigma')
  glContext.uniform1f(sigmaLocation, kernelSize.value)
  
  const maxDensityLocation = glContext.getUniformLocation(program, 'u_maxDensity')
  glContext.uniform1f(maxDensityLocation, maxDensity.value)
  
  const nodeCountLocation = glContext.getUniformLocation(program, 'u_nodeCount')
  glContext.uniform1i(nodeCountLocation, Math.min(nodes.value.length, 100))
  
  // 传递节点位置和权重
  for (let i = 0; i < Math.min(nodes.value.length, 100); i++) {
    const node = nodes.value[i]
    const posLocation = glContext.getUniformLocation(program, `u_nodePositions[${i}]`)
    glContext.uniform2f(posLocation, node.screenX, glCanvas.value.height - node.screenY)
    
    const weight = Math.sqrt((node.weights?.Citations || 0) + (node.weights?.Documents || 1))
    const weightLocation = glContext.getUniformLocation(program, `u_nodeWeights[${i}]`)
    glContext.uniform1f(weightLocation, weight)
  }
  
  // 绘制
  glContext.drawArrays(glContext.TRIANGLE_STRIP, 0, 4)
}

const render = () => {
  // 渲染WebGL密度图
  renderDensityMap()
  
  // 渲染overlay（节点和标签）
  if (!overlayCtx.value || !overlayCanvas.value) return
  
  const context = overlayCtx.value
  const width = overlayCanvas.value.width
  const height = overlayCanvas.value.height
  
  // 清空overlay
  context.clearRect(0, 0, width, height)
  
  // 确定哪些节点应该显示（基于权重和碰撞检测）
  const nodesToDisplay = new Set()
  
  if (showLabels.value) {
    // 按权重排序节点（权重大的优先显示）
    const sortedNodes = [...nodes.value].sort((a, b) => {
      const weightA = (a.weights?.Citations || 0) + (a.weights?.Documents || 0)
      const weightB = (b.weights?.Citations || 0) + (b.weights?.Documents || 0)
      return weightB - weightA
    })
    
    // 根据缩放级别调整标签密度
    const scale = viewState.value.scale
    const baseScale = viewState.value.baseScale
    const zoomRatio = scale / baseScale
    
    // 缩放越小，显示的标签越少（只显示重要的）
    let maxLabels
    if (zoomRatio < 0.5) {
      maxLabels = Math.ceil(nodes.value.length * 0.1) // 10%
    } else if (zoomRatio < 0.8) {
      maxLabels = Math.ceil(nodes.value.length * 0.3) // 30%
    } else if (zoomRatio < 1.2) {
      maxLabels = Math.ceil(nodes.value.length * 0.6) // 60%
    } else {
      maxLabels = nodes.value.length // 全部显示
    }
    
    // 记录已绘制标签的边界框，用于碰撞检测
    const drawnLabelBoxes = []
    const minLabelSpacing = 15 // 标签最小间距
    
    // 临时设置字体用于测量文本宽度
    context.font = '11px Arial, sans-serif'
    
    let labelCount = 0
    for (const node of sortedNodes) {
      if (labelCount >= maxLabels) break
      
      const label = node.label || ''
      if (!label) continue
      
      // 计算标签边界框
      const labelWidth = context.measureText(label).width
      const labelHeight = 11 // 字体大小
      const labelBox = {
        x: node.screenX - labelWidth / 2,
        y: node.screenY - 8 - labelHeight / 2,
        width: labelWidth,
        height: labelHeight
      }
      
      // 检查是否与已绘制的标签重叠
      let overlaps = false
      for (const existingBox of drawnLabelBoxes) {
        if (
          labelBox.x < existingBox.x + existingBox.width + minLabelSpacing &&
          labelBox.x + labelBox.width + minLabelSpacing > existingBox.x &&
          labelBox.y < existingBox.y + existingBox.height + minLabelSpacing &&
          labelBox.y + labelBox.height + minLabelSpacing > existingBox.y
        ) {
          overlaps = true
          break
        }
      }
      
      // 如果不重叠，标记此节点应该显示
      if (!overlaps) {
        nodesToDisplay.add(node)
        drawnLabelBoxes.push(labelBox)
        labelCount++
      }
    }
  } else {
    // 如果标签不显示，则显示所有节点
    nodes.value.forEach(node => nodesToDisplay.add(node))
  }
  
  // 绘制筛选后的节点（小圆点）
  nodesToDisplay.forEach(node => {
    const size = 3
    context.fillStyle = 'rgba(255, 255, 255, 0.8)'
    context.strokeStyle = 'rgba(50, 50, 50, 0.6)'
    context.lineWidth = 1
    
    context.beginPath()
    context.arc(node.screenX, node.screenY, size, 0, Math.PI * 2)
    context.fill()
    context.stroke()
  })
  
  // 绘制标签（字体大小根据权重调整）
  if (showLabels.value) {
    context.textAlign = 'center'
    context.textBaseline = 'middle'
    context.fillStyle = 'rgba(0, 0, 0, 0.9)'
    
    // 计算权重范围用于归一化字体大小
    let minWeight = Infinity
    let maxWeight = -Infinity
    nodesToDisplay.forEach(node => {
      const weight = (node.weights?.Citations || 0) + (node.weights?.Documents || 0)
      if (weight < minWeight) minWeight = weight
      if (weight > maxWeight) maxWeight = weight
    })
    const weightRange = maxWeight - minWeight || 1
    
    nodesToDisplay.forEach(node => {
      const label = node.label || ''
      if (label) {
        // 根据权重计算字体大小 (9px - 16px)
        const weight = (node.weights?.Citations || 0) + (node.weights?.Documents || 0)
        const normalizedWeight = (weight - minWeight) / weightRange
        const fontSize = Math.round(9 + normalizedWeight * 7) // 9px到16px
        
        context.font = `${fontSize}px Arial, sans-serif`
        context.fillText(label, node.screenX, node.screenY - 8)
      }
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
  const rect = overlayCanvas.value.getBoundingClientRect()
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
  const rect = overlayCanvas.value.getBoundingClientRect()
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
      overlayCanvas.value.style.cursor = node ? 'pointer' : 'move'
      
      if (node) {
        hoverInfoX.value = overlayCanvas.value.width - 220
        hoverInfoY.value = overlayCanvas.value.height - 120
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
  
  const rect = overlayCanvas.value.getBoundingClientRect()
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
  if (nodes.value.length > 0 && glCanvas.value) {
    const xCoords = nodes.value.map(n => n.x)
    const yCoords = nodes.value.map(n => n.y)
    const minX = Math.min(...xCoords)
    const maxX = Math.max(...xCoords)
    const minY = Math.min(...yCoords)
    const maxY = Math.max(...yCoords)
    
    const dataWidth = maxX - minX
    const dataHeight = maxY - minY
    
    const padding = 100
    const scaleX = (glCanvas.value.width - padding * 2) / dataWidth
    const scaleY = (glCanvas.value.height - padding * 2) / dataHeight
    viewState.value.scale = Math.min(scaleX, scaleY, 800)
    viewState.value.baseScale = viewState.value.scale
    
    viewState.value.offsetX = glCanvas.value.width / 2
    viewState.value.offsetY = glCanvas.value.height / 2
  }
  
  updateDensity()
}

const handleResize = () => {
  if (glCanvas.value && overlayCanvas.value && canvasWrapper.value) {
    const width = canvasWrapper.value.clientWidth
    const height = canvasWrapper.value.clientHeight
    
    glCanvas.value.width = width
    glCanvas.value.height = height
    overlayCanvas.value.width = width
    overlayCanvas.value.height = height
    
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


.canvas-wrapper {
  flex: 1;
  position: relative;
  overflow: hidden;
}

.gl-canvas {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: white;
}

.overlay-canvas {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  cursor: move;
  pointer-events: all;
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
</style>

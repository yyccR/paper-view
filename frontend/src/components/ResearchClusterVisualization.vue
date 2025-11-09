<template>
  <div class="cluster-visualization">
    <div class="canvas-wrapper" ref="canvasWrapper">
      <canvas ref="canvas" @mousedown="onMouseDown" @mousemove="onMouseMove" @mouseup="onMouseUp" @wheel="onWheel"></canvas>
      
      <!-- 合并的悬浮信息面板（右下角） -->
      <div class="hover-info-panel" v-if="hoveredNode && hoveredCluster">
        <div class="info-section">
          <div class="info-title">{{ hoveredNode.label }}</div>
          <div class="info-row">Citations: <strong>{{ hoveredNode.weights?.Citations || 0 }}</strong></div>
          <div class="info-row">Documents: <strong>{{ hoveredNode.weights?.Documents || 0 }}</strong></div>
        </div>
        <div class="info-divider"></div>
        <div class="info-section">
          <div class="cluster-title">Cluster #{{ hoveredCluster.id }}</div>
          <div class="info-row">Nodes: <strong>{{ hoveredCluster.nodes.length }}</strong></div>
          <div class="info-row" style="margin-top: 8px;">Top Authors:</div>
          <div class="cluster-authors">
            <div v-for="(node, idx) in hoveredCluster.topNodes.slice(0, 5)" :key="idx" class="author-item">
              {{ node.label }}
            </div>
          </div>
        </div>
      </div>
      
      <!-- 设置控制面板（左上角） -->
      <div class="settings-panel" :class="{ collapsed: panelCollapsed }" ref="settingsPanel">
        <div class="panel-header" @click="panelCollapsed = !panelCollapsed">
          <span class="settings-icon">⚙️</span>
        </div>
        <div class="panel-content" v-if="!panelCollapsed">
          <div class="control-group">
            <label>Cluster Count: <strong>{{ clusterCount }}</strong></label>
            <input type="range" v-model.number="clusterCount" min="3" max="10" step="1" @input="onClusterCountChange">
            <div class="control-hint">3 - 10 clusters</div>
          </div>
          
          <div class="control-group">
            <label>Boundary Padding: <strong>{{ boundaryPadding }}px</strong></label>
            <input type="range" v-model.number="boundaryPadding" min="5" max="25" step="5" @input="onBoundaryChange">
            <div class="control-hint">5px - 25px (tighter boundary)</div>
          </div>
          
          <div class="control-group">
            <label>Smoothness: <strong>{{ smoothness }}</strong></label>
            <input type="range" v-model.number="smoothness" min="1" max="5" step="1" @input="onSmoothnessChange">
            <div class="control-hint">1 (Sharp) - 5 (Smooth)</div>
          </div>
          
          <button class="reset-btn" @click="resetClustering">🔄 Recalculate</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch, nextTick, computed } from 'vue'

const props = defineProps({
  networkData: {
    type: Object,
    required: true
  }
})

const canvas = ref(null)
const canvasWrapper = ref(null)
const ctx = ref(null)
const settingsPanel = ref(null)
const hoveredNode = ref(null)
const hoveredCluster = ref(null)
const hoveredClusterId = ref(null) // 当前悬浮的类ID
const hoverInfoX = ref(0)
const hoverInfoY = ref(0)
const clusterInfoX = ref(20)
const clusterInfoY = ref(20)

// 控制面板参数
const panelCollapsed = ref(true) // 默认折叠
const clusterCount = ref(10) // 默认10个聚类
const boundaryPadding = ref(5) // 默认5px
const smoothness = ref(1) // 最小值
const showLinks = ref(true)
const showInterClusterArrows = ref(true)
const showAllLabels = ref(false)

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

// 节点和聚类数据
const nodes = ref([])
const links = ref([])
const clusters = ref(new Map())

// CiteSpace风格的聚类颜色
const clusterColors = [
  '#E57373', '#F06292', '#BA68C8', '#9575CD', '#7986CB',
  '#64B5F6', '#4FC3F7', '#4DD0E1', '#4DB6AC', '#81C784',
  '#AED581', '#DCE775', '#FFD54F', '#FFB74D', '#FF8A65',
  '#A1887F', '#90A4AE', '#78909C', '#EF5350', '#EC407A',
  '#AB47BC', '#7E57C2', '#5C6BC0', '#42A5F5', '#29B6F6'
]

const getClusterColor = (clusterId) => {
  return clusterColors[clusterId % clusterColors.length]
}

// K-means聚类算法 - 基于空间位置重新聚类
const kMeansClustering = (points, k, maxIterations = 50) => {
  if (points.length === 0 || k <= 0) return []
  
  // 初始化聚类中心 - 使用K-means++算法
  const centroids = []
  centroids.push(points[Math.floor(Math.random() * points.length)])
  
  while (centroids.length < k) {
    const distances = points.map(p => {
      const minDist = Math.min(...centroids.map(c => {
        const dx = p.x - c.x
        const dy = p.y - c.y
        return dx * dx + dy * dy
      }))
      return minDist
    })
    
    const totalDist = distances.reduce((a, b) => a + b, 0)
    let rand = Math.random() * totalDist
    
    for (let i = 0; i < points.length; i++) {
      rand -= distances[i]
      if (rand <= 0) {
        centroids.push(points[i])
        break
      }
    }
  }
  
  // 迭代优化
  let assignments = new Array(points.length).fill(0)
  
  for (let iter = 0; iter < maxIterations; iter++) {
    let changed = false
    
    // 分配点到最近的聚类中心
    points.forEach((p, idx) => {
      let minDist = Infinity
      let bestCluster = 0
      
      centroids.forEach((c, cIdx) => {
        const dx = p.x - c.x
        const dy = p.y - c.y
        const dist = dx * dx + dy * dy
        if (dist < minDist) {
          minDist = dist
          bestCluster = cIdx
        }
      })
      
      if (assignments[idx] !== bestCluster) {
        assignments[idx] = bestCluster
        changed = true
      }
    })
    
    if (!changed) break
    
    // 更新聚类中心
    for (let cIdx = 0; cIdx < k; cIdx++) {
      const clusterPoints = points.filter((_, idx) => assignments[idx] === cIdx)
      if (clusterPoints.length > 0) {
        const sumX = clusterPoints.reduce((sum, p) => sum + p.x, 0)
        const sumY = clusterPoints.reduce((sum, p) => sum + p.y, 0)
        centroids[cIdx] = {
          x: sumX / clusterPoints.length,
          y: sumY / clusterPoints.length
        }
      }
    }
  }
  
  return assignments
}

// 计算凸包 - Graham Scan算法
const computeConvexHull = (points) => {
  if (points.length < 3) return points
  
  // 找到最下方的点（y最小，如果相同则x最小）
  let start = points[0]
  for (let i = 1; i < points.length; i++) {
    if (points[i].screenY > start.screenY || 
        (points[i].screenY === start.screenY && points[i].screenX < start.screenX)) {
      start = points[i]
    }
  }
  
  // 按极角排序
  const sorted = points.filter(p => p !== start).sort((a, b) => {
    const angleA = Math.atan2(a.screenY - start.screenY, a.screenX - start.screenX)
    const angleB = Math.atan2(b.screenY - start.screenY, b.screenX - start.screenX)
    return angleA - angleB
  })
  
  const hull = [start, sorted[0]]
  
  for (let i = 1; i < sorted.length; i++) {
    while (hull.length >= 2) {
      const p1 = hull[hull.length - 2]
      const p2 = hull[hull.length - 1]
      const p3 = sorted[i]
      const cross = (p2.screenX - p1.screenX) * (p3.screenY - p1.screenY) - 
                    (p2.screenY - p1.screenY) * (p3.screenX - p1.screenX)
      if (cross <= 0) {
        hull.pop()
      } else {
        break
      }
    }
    hull.push(sorted[i])
  }
  
  return hull
}

// 扩展凸包边界
const expandHull = (hull, margin) => {
  if (hull.length < 3) return hull
  
  // 计算中心点
  let centerX = 0, centerY = 0
  hull.forEach(p => {
    centerX += p.screenX
    centerY += p.screenY
  })
  centerX /= hull.length
  centerY /= hull.length
  
  // 向外扩展（使用较小的margin避免交叉）
  return hull.map(p => {
    const dx = p.screenX - centerX
    const dy = p.screenY - centerY
    const dist = Math.sqrt(dx * dx + dy * dy)
    const scale = (dist + margin) / (dist || 1)
    return {
      screenX: centerX + dx * scale,
      screenY: centerY + dy * scale
    }
  })
}

// 构建最小生成树（Prim算法）确保所有节点相连
const buildMinimumSpanningTree = (nodes) => {
  if (nodes.length < 2) return []
  
  const edges = []
  const visited = new Set()
  const unvisited = new Set(nodes)
  
  // 从第一个节点开始
  const startNode = nodes[0]
  visited.add(startNode)
  unvisited.delete(startNode)
  
  while (unvisited.size > 0) {
    let minDistance = Infinity
    let closestEdge = null
    
    // 找到已访问集合到未访问集合的最短边
    visited.forEach(visitedNode => {
      unvisited.forEach(unvisitedNode => {
        const dx = visitedNode.screenX - unvisitedNode.screenX
        const dy = visitedNode.screenY - unvisitedNode.screenY
        const distance = Math.sqrt(dx * dx + dy * dy)
        
        if (distance < minDistance) {
          minDistance = distance
          closestEdge = {
            from: visitedNode,
            to: unvisitedNode,
            distance: distance
          }
        }
      })
    })
    
    if (closestEdge) {
      edges.push(closestEdge)
      visited.add(closestEdge.to)
      unvisited.delete(closestEdge.to)
    } else {
      break // 防止无限循环
    }
  }
  
  return edges
}

// Chaikin角点平滑算法 - 多次迭代使边界更圆滑
const smoothCorners = (points, iterations = 2) => {
  if (points.length < 3) return points
  
  let smoothed = [...points]
  
  for (let iter = 0; iter < iterations; iter++) {
    const newPoints = []
    const len = smoothed.length
    
    for (let i = 0; i < len; i++) {
      const p0 = smoothed[i]
      const p1 = smoothed[(i + 1) % len]
      
      // 在每条边上取两个点（1/4 和 3/4 处）
      const q = {
        screenX: 0.75 * p0.screenX + 0.25 * p1.screenX,
        screenY: 0.75 * p0.screenY + 0.25 * p1.screenY
      }
      const r = {
        screenX: 0.25 * p0.screenX + 0.75 * p1.screenX,
        screenY: 0.25 * p0.screenY + 0.75 * p1.screenY
      }
      
      newPoints.push(q, r)
    }
    
    smoothed = newPoints
  }
  
  return smoothed
}

// 使用Catmull-Rom样条曲线绘制平滑边界
const drawSmoothBoundary = (context, points) => {
  if (points.length < 3) return
  
  const tension = 0.5 // 张力参数，0.5 是标准Catmull-Rom
  const numPoints = points.length
  
  context.beginPath()
  
  // 从第一个点开始
  context.moveTo(points[0].screenX, points[0].screenY)
  
  // 为闭合路径，扩展点数组
  const extendedPoints = [points[numPoints - 1], ...points, points[0], points[1]]
  
  // 使用三次贝塞尔曲线绘制Catmull-Rom样条
  for (let i = 0; i < numPoints; i++) {
    const p0 = extendedPoints[i]
    const p1 = extendedPoints[i + 1]
    const p2 = extendedPoints[i + 2]
    const p3 = extendedPoints[i + 3]
    
    // Catmull-Rom转三次贝塞尔的控制点
    const cp1x = p1.screenX + (p2.screenX - p0.screenX) / 6 * tension
    const cp1y = p1.screenY + (p2.screenY - p0.screenY) / 6 * tension
    
    const cp2x = p2.screenX - (p3.screenX - p1.screenX) / 6 * tension
    const cp2y = p2.screenY - (p3.screenY - p1.screenY) / 6 * tension
    
    context.bezierCurveTo(
      cp1x, cp1y,
      cp2x, cp2y,
      p2.screenX, p2.screenY
    )
  }
  
  context.closePath()
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
    
    // 解析连线数据
    if (props.networkData?.network?.links) {
      links.value = props.networkData.network.links.map(link => ({
        ...link
      }))
    }
    
    // 使用K-means基于空间位置重新聚类
    const assignments = kMeansClustering(nodes.value, clusterCount.value)
    
    // 根据新的聚类分配更新节点
    const clusterMap = new Map()
    nodes.value.forEach((node, idx) => {
      const newClusterId = assignments[idx]
      node.cluster = newClusterId // 更新cluster ID
      
      if (!clusterMap.has(newClusterId)) {
        clusterMap.set(newClusterId, {
          id: newClusterId,
          nodes: [],
          topNodes: []
        })
      }
      clusterMap.get(newClusterId).nodes.push(node)
    })
    
    // 过滤掉过小的聚类（少于3个节点），并将其合并到最近的聚类
    const minClusterSize = 3
    const smallClusters = []
    const validClusters = []
    
    clusterMap.forEach((clusterData, clusterId) => {
      if (clusterData.nodes.length < minClusterSize) {
        smallClusters.push([clusterId, clusterData])
      } else {
        validClusters.push([clusterId, clusterData])
      }
    })
    
    // 合并小聚类到最近的有效聚类
    smallClusters.forEach(([smallId, smallData]) => {
      if (validClusters.length === 0) return
      
      // 计算小聚类的中心
      const smallCenterX = smallData.nodes.reduce((sum, n) => sum + n.x, 0) / smallData.nodes.length
      const smallCenterY = smallData.nodes.reduce((sum, n) => sum + n.y, 0) / smallData.nodes.length
      
      let nearestCluster = validClusters[0]
      let minDistance = Infinity
      
      validClusters.forEach(([validId, validData]) => {
        const validCenterX = validData.nodes.reduce((sum, n) => sum + n.x, 0) / validData.nodes.length
        const validCenterY = validData.nodes.reduce((sum, n) => sum + n.y, 0) / validData.nodes.length
        
        const dx = smallCenterX - validCenterX
        const dy = smallCenterY - validCenterY
        const dist = Math.sqrt(dx * dx + dy * dy)
        
        if (dist < minDistance) {
          minDistance = dist
          nearestCluster = [validId, validData]
        }
      })
      
      // 合并节点
      smallData.nodes.forEach(node => {
        node.cluster = nearestCluster[0]
        nearestCluster[1].nodes.push(node)
      })
      clusterMap.delete(smallId)
    })
    
    // 为每个聚类计算top节点
    clusterMap.forEach(clusterData => {
      clusterData.topNodes = [...clusterData.nodes].sort((a, b) => {
        const weightA = (a.weights?.Citations || 0) + (a.weights?.Documents || 0)
        const weightB = (b.weights?.Citations || 0) + (b.weights?.Documents || 0)
        return weightB - weightA
      })
    })
    
    clusters.value = clusterMap
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
    
    const padding = 150
    const scaleX = (canvas.value.width - padding * 2) / dataWidth
    const scaleY = (canvas.value.height - padding * 2) / dataHeight
    viewState.value.scale = Math.min(scaleX, scaleY, 600)
    viewState.value.baseScale = viewState.value.scale
    
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
  
  // 背景
  context.fillStyle = '#fafafa'
  context.fillRect(0, 0, canvas.value.width, canvas.value.height)
  
  // 更新节点屏幕坐标
  nodes.value.forEach(node => {
    const screen = worldToScreen(node.x, node.y)
    node.screenX = screen.x
    node.screenY = screen.y
  })
  
  // 计算聚类中心点（用于聚类间连线）
  const clusterCenters = new Map()
  clusters.value.forEach((clusterData, clusterId) => {
    let sumX = 0, sumY = 0
    clusterData.nodes.forEach(node => {
      sumX += node.screenX
      sumY += node.screenY
    })
    clusterCenters.set(clusterId, {
      x: sumX / clusterData.nodes.length,
      y: sumY / clusterData.nodes.length
    })
  })
  
  // 统计聚类之间的连线（每对聚类之间最多一条）
  const clusterPairLinks = new Map()
  links.value.forEach(link => {
    const sourceNode = nodes.value.find(n => n.id === link.source_id)
    const targetNode = nodes.value.find(n => n.id === link.target_id)
    
    if (sourceNode && targetNode && sourceNode.cluster !== targetNode.cluster) {
      // 创建无向的聚类对key（小ID在前，大ID在后）
      const cluster1 = Math.min(sourceNode.cluster, targetNode.cluster)
      const cluster2 = Math.max(sourceNode.cluster, targetNode.cluster)
      const pairKey = `${cluster1}-${cluster2}`
      
      if (!clusterPairLinks.has(pairKey)) {
        clusterPairLinks.set(pairKey, {
          cluster1,
          cluster2,
          forwardStrength: 0,  // cluster1 -> cluster2
          backwardStrength: 0, // cluster2 -> cluster1
          forwardCount: 0,
          backwardCount: 0
        })
      }
      
      const pairData = clusterPairLinks.get(pairKey)
      // 统计正向和反向的强度
      if (sourceNode.cluster === cluster1) {
        pairData.forwardStrength += (link.strength || 1)
        pairData.forwardCount++
      } else {
        pairData.backwardStrength += (link.strength || 1)
        pairData.backwardCount++
      }
    }
  })
  
  // 将双向连接合并为单向，选择强度更大的方向
  const directedInterClusterLinks = []
  clusterPairLinks.forEach(pairData => {
    const totalStrength = pairData.forwardStrength + pairData.backwardStrength
    
    // 选择主导方向（强度更大的）
    let fromCluster, toCluster, strength
    if (pairData.forwardStrength >= pairData.backwardStrength) {
      fromCluster = pairData.cluster1
      toCluster = pairData.cluster2
      strength = totalStrength // 使用总强度
    } else {
      fromCluster = pairData.cluster2
      toCluster = pairData.cluster1
      strength = totalStrength
    }
    
    directedInterClusterLinks.push({
      fromCluster,
      toCluster,
      strength,
      count: pairData.forwardCount + pairData.backwardCount
    })
  })
  
  // 只选择最重要的几条跨聚类连接（按强度排序）
  const topInterClusterLinks = directedInterClusterLinks
    .sort((a, b) => b.strength - a.strength)
    .slice(0, 8) // 只显示最重要的8条
  
  // 暂存类簇箭头数据，稍后绘制（避免被标签遮挡）
  const interClusterArrows = []
  if (showInterClusterArrows.value && topInterClusterLinks.length > 0) {
    topInterClusterLinks.forEach(linkData => {
      const fromCenter = clusterCenters.get(linkData.fromCluster)
      const toCenter = clusterCenters.get(linkData.toCluster)
      
      if (!fromCenter || !toCenter) return
      
      // 计算连线强度（用于调整线宽和透明度）
      const maxStrength = Math.max(...topInterClusterLinks.map(l => l.strength))
      const normalizedStrength = linkData.strength / maxStrength
      
      // 计算控制点，创建弯曲效果
      const dx = toCenter.x - fromCenter.x
      const dy = toCenter.y - fromCenter.y
      const distance = Math.sqrt(dx * dx + dy * dy)
      
      // 垂直于连线方向的偏移，创建曲线效果
      const curvature = 0.3 // 曲率系数
      const offset = distance * curvature
      
      // 中点位置
      const midX = (fromCenter.x + toCenter.x) / 2
      const midY = (fromCenter.y + toCenter.y) / 2
      
      // 垂直方向的单位向量
      const perpX = -dy / distance
      const perpY = dx / distance
      
      // 控制点（在中点旁边产生弯曲）
      const controlX = midX + perpX * offset
      const controlY = midY + perpY * offset
      
      // 获取源聚类和目标聚类颜色
      const fromColor = getClusterColor(linkData.fromCluster)
      const toColor = getClusterColor(linkData.toCluster)
      
      // 存储箭头数据，稍后绘制
      interClusterArrows.push({
        fromCenter,
        toCenter,
        controlX,
        controlY,
        fromColor,
        toColor,
        normalizedStrength,
        fromCluster: linkData.fromCluster,
        toCluster: linkData.toCluster
      })
    })
  }
  
  // 绘制聚类内部连线（使用最小生成树确保所有点相连，带暗化效果）
  if (showLinks.value) {
    clusters.value.forEach((clusterData, clusterId) => {
      const clusterNodes = clusterData.nodes
      if (clusterNodes.length < 2) return
      
      // 使用Prim算法构建最小生成树，确保所有节点相连
      const mstEdges = buildMinimumSpanningTree(clusterNodes)
      
      const color = getClusterColor(clusterId)
      const r = parseInt(color.slice(1, 3), 16)
      const g = parseInt(color.slice(3, 5), 16)
      const b = parseInt(color.slice(5, 7), 16)
      
      const isDimmed = hoveredClusterId.value !== null && hoveredClusterId.value !== clusterId
      
      // 绘制MST边
      mstEdges.forEach(edge => {
        const sourceNode = edge.from
        const targetNode = edge.to
        
        // 根据节点权重决定线条样式
        const sourceWeight = (sourceNode.weights?.Citations || 0) + (sourceNode.weights?.Documents || 0)
        const targetWeight = (targetNode.weights?.Citations || 0) + (targetNode.weights?.Documents || 0)
        const avgWeight = (sourceWeight + targetWeight) / 2
        const normalizedWeight = Math.min(avgWeight / 100, 1)
        
        const lineWidth = 0.5 + normalizedWeight * 0.8 // 0.5px - 1.3px
        let opacity = 0.35 + normalizedWeight * 0.35 // 0.35 - 0.7 (颜色更深)
        
        // 暗化效果
        if (isDimmed) {
          opacity *= 0.3 // 暗化时透明度更低
        }
        
        context.strokeStyle = `rgba(${r}, ${g}, ${b}, ${opacity})`
        context.lineWidth = lineWidth
        context.lineCap = 'round'
        context.beginPath()
        context.moveTo(sourceNode.screenX, sourceNode.screenY)
        context.lineTo(targetNode.screenX, targetNode.screenY)
        context.stroke()
      })
    })
  }
  
  // 绘制聚类区域（云朵形状，带高亮效果）
  clusters.value.forEach((clusterData, clusterId) => {
    if (clusterData.nodes.length < 3) return // 节点太少无法形成凸包
    
    const hull = computeConvexHull([...clusterData.nodes])
    // 使用更大的padding让形状更像云朵
    const cloudPadding = boundaryPadding.value + 15
    const expandedHull = expandHull(hull, cloudPadding)
    // 更多的平滑迭代使边界更圆滑
    const smoothedHull = smoothCorners(expandedHull, smoothness.value + 2)
    
    if (smoothedHull.length >= 3) {
      const color = getClusterColor(clusterId)
      const isHovered = hoveredClusterId.value === clusterId
      const isDimmed = hoveredClusterId.value !== null && !isHovered
      
      // 绘制平滑边界
      drawSmoothBoundary(context, smoothedHull)
      
      // 填充区域（悬浮时高亮，其他暗化）
      if (isDimmed) {
        context.fillStyle = `${color}08` // 暗化
      } else if (isHovered) {
        context.fillStyle = `${color}30` // 高亮
      } else {
        context.fillStyle = `${color}18` // 正常
      }
      context.fill()
      
      // 边界线（悬浮时更明显）
      if (isDimmed) {
        context.strokeStyle = `${color}30` // 暗化
        context.lineWidth = 0.5
      } else if (isHovered) {
        context.strokeStyle = `${color}90` // 高亮
        context.lineWidth = 1.5
      } else {
        context.strokeStyle = `${color}60` // 正常
        context.lineWidth = 0.5
      }
      context.stroke()
      
      // 在类中心绘制标签 "#x 核心概念"
      const center = clusterCenters.get(clusterId)
      if (center) {
        // 获取聚类的核心节点（权重最高）
        const topNode = clusterData.topNodes[0]
        const coreLabel = topNode ? topNode.label.split(' ').slice(0, 3).join(' ') : 'Core'
        
        const labelText = `#${clusterId} ${coreLabel}`
        
        // 绘制背景
        context.font = 'bold 13px Arial, sans-serif'
        const metrics = context.measureText(labelText)
        const padding = 8
        const bgWidth = metrics.width + padding * 2
        const bgHeight = 22
        
        context.fillStyle = 'rgba(255, 255, 255, 0.95)'
        context.beginPath()
        // 使用圆角矩形（兼容性更好）
        const x = center.x - bgWidth/2
        const y = center.y - bgHeight/2
        const radius = 4
        context.moveTo(x + radius, y)
        context.lineTo(x + bgWidth - radius, y)
        context.quadraticCurveTo(x + bgWidth, y, x + bgWidth, y + radius)
        context.lineTo(x + bgWidth, y + bgHeight - radius)
        context.quadraticCurveTo(x + bgWidth, y + bgHeight, x + bgWidth - radius, y + bgHeight)
        context.lineTo(x + radius, y + bgHeight)
        context.quadraticCurveTo(x, y + bgHeight, x, y + bgHeight - radius)
        context.lineTo(x, y + radius)
        context.quadraticCurveTo(x, y, x + radius, y)
        context.closePath()
        context.fill()
        
        // 边框
        context.strokeStyle = color
        context.lineWidth = 2
        context.stroke()
        
        // 绘制文本
        context.fillStyle = color
        context.textAlign = 'center'
        context.textBaseline = 'middle'
        context.fillText(labelText, center.x, center.y)
      }
    }
  })
  
  // 绘制节点（带暗化效果）
  nodes.value.forEach(node => {
    const citations = node.weights?.Citations || 0
    const documents = node.weights?.Documents || 1
    const size = Math.sqrt(citations + documents * 5) * 0.6 + 2
    
    const color = getClusterColor(node.cluster)
    const isHighlighted = hoveredNode.value?.id === node.id
    const isDimmed = hoveredClusterId.value !== null && hoveredClusterId.value !== node.cluster
    
    // 节点圆圈（根据悬浮状态调整透明度）
    if (isDimmed) {
      context.fillStyle = `${color}30` // 暗化
    } else if (isHighlighted) {
      context.fillStyle = color // 高亮
    } else {
      context.fillStyle = `${color}CC` // 正常
    }
    context.beginPath()
    context.arc(node.screenX, node.screenY, size, 0, Math.PI * 2)
    context.fill()
    
    // 节点边框
    if (isHighlighted) {
      context.strokeStyle = '#fff'
      context.lineWidth = 2
      context.stroke()
    }
  })
  
  // 绘制标签（使用智能碰撞检测和权重优化）
  context.textAlign = 'center'
  context.textBaseline = 'middle'
  
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
  
  let maxLabels
  if (showAllLabels.value) {
    maxLabels = nodes.value.length // 显示所有
  } else {
    // 缩放越小，显示的标签越少（只显示重要的）
    if (zoomRatio < 0.5) {
      maxLabels = Math.ceil(nodes.value.length * 0.15) // 15%
    } else if (zoomRatio < 0.8) {
      maxLabels = Math.ceil(nodes.value.length * 0.3) // 30%
    } else if (zoomRatio < 1.2) {
      maxLabels = Math.ceil(nodes.value.length * 0.5) // 50%
    } else {
      maxLabels = Math.ceil(nodes.value.length * 0.7) // 70%
    }
  }
  
  // 记录已绘制标签的边界框，用于碰撞检测
  const drawnLabelBoxes = []
  const minLabelSpacing = 12 // 标签最小间距
  const nodesToDisplay = []
  
  // 临时设置字体用于测量文本宽度
  context.font = '11px Arial, sans-serif'
  
  let labelCount = 0
  for (const node of sortedNodes) {
    if (labelCount >= maxLabels) break
    
    const label = node.label || ''
    if (!label) continue
    
    // 根据权重计算字体大小
    const weight = (node.weights?.Citations || 0) + (node.weights?.Documents || 0)
    const fontSize = Math.round(9 + Math.min(weight / 50, 1) * 5) // 9px到14px
    context.font = `${fontSize}px Arial, sans-serif`
    
    // 计算标签边界框
    const labelWidth = context.measureText(label).width
    const labelHeight = fontSize
    const labelBox = {
      x: node.screenX - labelWidth / 2,
      y: node.screenY - 10 - labelHeight / 2,
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
      nodesToDisplay.push({ node, fontSize })
      drawnLabelBoxes.push(labelBox)
      labelCount++
    }
  }
  
  // 绘制筛选后的标签（带暗化效果）
  nodesToDisplay.forEach(({ node, fontSize }) => {
    const isDimmed = hoveredClusterId.value !== null && hoveredClusterId.value !== node.cluster
    
    // 根据悬浮状态调整标签透明度
    if (isDimmed) {
      context.fillStyle = 'rgba(0, 0, 0, 0.3)' // 暗化
    } else {
      context.fillStyle = 'rgba(0, 0, 0, 0.9)' // 正常
    }
    
    context.font = `${fontSize}px Arial, sans-serif`
    context.fillText(node.label || '', node.screenX, node.screenY - 10)
  })
  
  // 高亮悬浮节点
  if (hoveredNode.value) {
    const node = hoveredNode.value
    const citations = node.weights?.Citations || 0
    const documents = node.weights?.Documents || 1
    const size = Math.sqrt(citations + documents * 5) * 0.6 + 2
    
    context.strokeStyle = '#FFD700'
    context.lineWidth = 3
    context.beginPath()
    context.arc(node.screenX, node.screenY, size + 2, 0, Math.PI * 2)
    context.stroke()
  }
  
  // 最后绘制类簇之间的弯曲箭头（避免被其他元素遮挡）
  interClusterArrows.forEach(arrowData => {
    const { fromCenter, toCenter, controlX, controlY, fromColor, toColor, normalizedStrength, fromCluster, toCluster } = arrowData
    
    // 判断是否需要高亮或暗化
    const isRelated = hoveredClusterId.value !== null && 
                      (hoveredClusterId.value === fromCluster || hoveredClusterId.value === toCluster)
    const isDimmed = hoveredClusterId.value !== null && !isRelated
    
    // 获取颜色的RGB值
    const fromR = parseInt(fromColor.slice(1, 3), 16)
    const fromG = parseInt(fromColor.slice(3, 5), 16)
    const fromB = parseInt(fromColor.slice(5, 7), 16)
    const toR = parseInt(toColor.slice(1, 3), 16)
    const toG = parseInt(toColor.slice(3, 5), 16)
    const toB = parseInt(toColor.slice(5, 7), 16)
    
    // 根据强度调整线宽和透明度（线条更粗）
    let lineWidth = 3 + normalizedStrength * 5 // 3px - 8px
    let opacity = 0.35 + normalizedStrength * 0.3 // 0.35 - 0.65（保持半透明）
    
    // 应用高亮或暗化效果
    if (isDimmed) {
      opacity *= 0.25 // 暗化：透明度降低到25%
      lineWidth *= 0.7 // 线条变细
    } else if (isRelated) {
      opacity = Math.min(opacity * 1.4, 0.8) // 高亮：透明度增加但不超过0.8（保持半透明）
      lineWidth *= 1.2 // 线条变粗
    }
    
    // 创建渐变（从源聚类到目标聚类）
    const gradient = context.createLinearGradient(
      fromCenter.x, fromCenter.y,
      toCenter.x, toCenter.y
    )
    gradient.addColorStop(0, `rgba(${fromR}, ${fromG}, ${fromB}, ${opacity})`)
    gradient.addColorStop(0.5, `rgba(${Math.floor((fromR + toR) / 2)}, ${Math.floor((fromG + toG) / 2)}, ${Math.floor((fromB + toB) / 2)}, ${opacity})`)
    gradient.addColorStop(1, `rgba(${toR}, ${toG}, ${toB}, ${opacity})`)
    
    // 绘制带渐变的贝塞尔曲线
    context.strokeStyle = gradient
    context.lineWidth = lineWidth
    context.lineCap = 'round'
    context.lineJoin = 'round'
    context.beginPath()
    context.moveTo(fromCenter.x, fromCenter.y)
    context.quadraticCurveTo(controlX, controlY, toCenter.x, toCenter.y)
    context.stroke()
    
    // 绘制箭头（在目标聚类端，更大更明显）
    const arrowDx = toCenter.x - controlX
    const arrowDy = toCenter.y - controlY
    const arrowDist = Math.sqrt(arrowDx * arrowDx + arrowDy * arrowDy)
    
    if (arrowDist > 0) {
      // 箭头大小根据强度调整（更大）
      const arrowSize = 14 + normalizedStrength * 10 // 14px - 24px
      const arrowAngle = Math.PI / 5 // 36度（更宽的箭头）
      
      // 箭头方向的单位向量
      const dirX = arrowDx / arrowDist
      const dirY = arrowDy / arrowDist
      
      // 箭头的两个翼端点
      const angle1 = Math.atan2(dirY, dirX) + Math.PI - arrowAngle
      const angle2 = Math.atan2(dirY, dirX) + Math.PI + arrowAngle
      
      const arrowX1 = toCenter.x + Math.cos(angle1) * arrowSize
      const arrowY1 = toCenter.y + Math.sin(angle1) * arrowSize
      const arrowX2 = toCenter.x + Math.cos(angle2) * arrowSize
      const arrowY2 = toCenter.y + Math.sin(angle2) * arrowSize
      
      // 计算箭头透明度（根据高亮/暗化状态调整，保持半透明）
      let arrowOpacity = Math.min(opacity + 0.2, 0.75) // 箭头最高透明度0.75
      let arrowBorderOpacity = Math.min(opacity + 0.25, 0.8) // 边框最高透明度0.8
      
      if (isDimmed) {
        arrowOpacity *= 0.3 // 暗化箭头
        arrowBorderOpacity *= 0.3
      } else if (isRelated) {
        arrowOpacity = Math.min(arrowOpacity * 1.15, 0.75) // 高亮箭头，保持半透明
        arrowBorderOpacity = Math.min(arrowBorderOpacity * 1.15, 0.8)
      }
      
      // 绘制实心箭头（更高的透明度）
      context.fillStyle = `rgba(${toR}, ${toG}, ${toB}, ${arrowOpacity})`
      context.beginPath()
      context.moveTo(toCenter.x, toCenter.y)
      context.lineTo(arrowX1, arrowY1)
      context.lineTo(arrowX2, arrowY2)
      context.closePath()
      context.fill()
      
      // 添加箭头边框使其更明显
      context.strokeStyle = `rgba(${toR}, ${toG}, ${toB}, ${arrowBorderOpacity})`
      context.lineWidth = isRelated ? 2 : 1.5 // 高亮时边框更粗
      context.stroke()
    }
  })
}

const getNodeAtPosition = (x, y) => {
  for (let i = nodes.value.length - 1; i >= 0; i--) {
    const node = nodes.value[i]
    const citations = node.weights?.Citations || 0
    const documents = node.weights?.Documents || 1
    const size = Math.sqrt(citations + documents * 5) * 0.6 + 2
    const dx = x - node.screenX
    const dy = y - node.screenY
    const distance = Math.sqrt(dx * dx + dy * dy)
    if (distance <= size + 3) {
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
  
  viewState.value.isDragging = true
  viewState.value.dragStartX = e.clientX
  viewState.value.dragStartY = e.clientY
  viewState.value.dragStartOffsetX = viewState.value.offsetX
  viewState.value.dragStartOffsetY = viewState.value.offsetY
}

// 检测鼠标是否在某个聚类内（用于高亮效果）
const getClusterAtPosition = (x, y) => {
  // 检查鼠标位置是否在任何节点附近
  const node = getNodeAtPosition(x, y)
  if (node) {
    return node.cluster
  }
  
  // 如果不在节点上，检查是否在聚类区域内
  for (const [clusterId, clusterData] of clusters.value) {
    const nodes = clusterData.nodes
    if (nodes.length < 3) continue
    
    // 简单的边界框检查
    let minX = Infinity, maxX = -Infinity, minY = Infinity, maxY = -Infinity
    nodes.forEach(node => {
      if (node.screenX < minX) minX = node.screenX
      if (node.screenX > maxX) maxX = node.screenX
      if (node.screenY < minY) minY = node.screenY
      if (node.screenY > maxY) maxY = node.screenY
    })
    
    // 扩展边界框
    const margin = boundaryPadding.value + 15
    if (x >= minX - margin && x <= maxX + margin && y >= minY - margin && y <= maxY + margin) {
      return clusterId
    }
  }
  
  return null
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
    // 检测悬浮的节点
    const node = getNodeAtPosition(x, y)
    // 检测悬浮的聚类
    const clusterId = getClusterAtPosition(x, y)
    
    let needsRender = false
    
    if (node !== hoveredNode.value) {
      hoveredNode.value = node
      canvas.value.style.cursor = node ? 'pointer' : 'move'
      
      if (node) {
        hoverInfoX.value = canvas.value.width - 220
        hoverInfoY.value = canvas.value.height - 140
        
        hoveredCluster.value = {
          id: node.cluster,
          nodes: clusters.value.get(node.cluster)?.nodes || [],
          topNodes: clusters.value.get(node.cluster)?.topNodes || []
        }
        clusterInfoX.value = 20
        clusterInfoY.value = 20
      } else {
        hoveredCluster.value = null
      }
      
      needsRender = true
    }
    
    // 更新悬浮的聚类ID（用于高亮效果）
    if (clusterId !== hoveredClusterId.value) {
      hoveredClusterId.value = clusterId
      needsRender = true
    }
    
    if (needsRender) {
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
  
  render()
}

// 参数变化时重新计算聚类
const onClusterCountChange = () => {
  initCanvas()
}

const onBoundaryChange = () => {
  render()
}

const onSmoothnessChange = () => {
  render()
}

const resetClustering = () => {
  initCanvas()
}

const handleResize = () => {
  if (canvas.value && canvasWrapper.value) {
    canvas.value.width = canvasWrapper.value.clientWidth
    canvas.value.height = canvasWrapper.value.clientHeight
    render()
  }
}

// 点击外部区域自动折叠面板
const handleClickOutside = (event) => {
  if (!panelCollapsed.value && settingsPanel.value && !settingsPanel.value.contains(event.target)) {
    panelCollapsed.value = true
  }
}

onMounted(() => {
  nextTick(() => {
    initCanvas()
    window.addEventListener('resize', handleResize)
    document.addEventListener('click', handleClickOutside)
  })
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  document.removeEventListener('click', handleClickOutside)
})

watch(() => props.networkData, () => {
  nextTick(() => {
    initCanvas()
  })
}, { deep: true })
</script>

<style scoped>
.cluster-visualization {
  width: 100%;
  height: 100%;
  background: #fafafa;
  position: relative;
}

.canvas-wrapper {
  width: 100%;
  height: 100%;
  position: relative;
  overflow: hidden;
}

.canvas-wrapper canvas {
  display: block;
  cursor: move;
  background: linear-gradient(to bottom, #fafafa 0%, #f5f5f5 100%);
}

/* 合并的悬浮信息面板（右下角） */
.hover-info-panel {
  position: absolute;
  bottom: 20px;
  right: 20px;
  background: rgba(255, 255, 255, 0.95);
  border: 1px solid #ddd;
  border-radius: 8px;
  padding: 14px 16px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.15);
  pointer-events: none;
  z-index: 1000;
  min-width: 240px;
  max-width: 280px;
  backdrop-filter: blur(10px);
}

.info-section {
  margin-bottom: 10px;
}

.info-section:last-child {
  margin-bottom: 0;
}

.info-divider {
  height: 1px;
  background: #e0e0e0;
  margin: 10px 0;
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
  margin: 3px 0;
}

.info-row strong {
  color: #333;
  font-weight: 600;
}

.cluster-title {
  font-size: 13px;
  font-weight: 600;
  color: #333;
  margin-bottom: 6px;
}

.cluster-authors {
  margin-top: 4px;
  max-height: 100px;
  overflow-y: auto;
}

.author-item {
  font-size: 10px;
  color: #555;
  padding: 2px 0;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* 设置控制面板（左上角，蓝色主题） */
.settings-panel {
  position: absolute;
  top: 20px;
  left: 20px;
  background: rgba(255, 255, 255, 0.95);
  border: 1px solid #e3f2fd;
  border-radius: 8px;
  box-shadow: 0 2px 12px rgba(33, 150, 243, 0.15);
  backdrop-filter: blur(10px);
  z-index: 1001;
}

.settings-panel.collapsed {
  min-width: auto;
}

.panel-header {
  padding: 10px;
  background: white;
  color: #2196F3;
  border-radius: 8px;
  cursor: pointer;
  display: flex;
  justify-content: center;
  align-items: center;
  user-select: none;
  width: 40px;
  height: 40px;
  box-shadow: 0 2px 8px rgba(33, 150, 243, 0.15);
}

.panel-header:hover {
  background: #f5f9ff;
  box-shadow: 0 2px 12px rgba(33, 150, 243, 0.25);
}

.settings-panel.collapsed .panel-header {
  border-radius: 8px;
}

.settings-panel:not(.collapsed) .panel-header {
  border-radius: 8px 8px 0 0;
  width: 100%;
  justify-content: flex-start;
  padding: 12px 16px;
  border-bottom: 1px solid #e3f2fd;
}

.settings-icon {
  font-size: 18px;
  line-height: 1;
}

.panel-content {
  padding: 16px;
  max-height: 500px;
  overflow-y: auto;
  min-width: 260px;
  background: white;
  border-radius: 0 0 8px 8px;
}

.control-group {
  margin-bottom: 18px;
}

.control-group:last-of-type {
  margin-bottom: 0;
}

.control-group label {
  display: block;
  font-size: 13px;
  color: #333;
  margin-bottom: 8px;
  font-weight: 500;
}

.control-group label strong {
  color: #667eea;
  float: right;
}

.control-group input[type="range"] {
  width: 100%;
  height: 6px;
  border-radius: 3px;
  background: #e0e0e0;
  outline: none;
  appearance: none;
  -webkit-appearance: none;
  margin: 4px 0;
}

.control-group input[type="range"]::-webkit-slider-thumb {
  -webkit-appearance: none;
  appearance: none;
  width: 16px;
  height: 16px;
  border-radius: 50%;
  background: linear-gradient(135deg, #2196F3 0%, #1976D2 100%);
  cursor: pointer;
  box-shadow: 0 2px 4px rgba(33, 150, 243, 0.3);
  transition: transform 0.2s;
}

.control-group input[type="range"]::-webkit-slider-thumb:hover {
  transform: scale(1.2);
}

.control-group input[type="range"]::-moz-range-thumb {
  width: 16px;
  height: 16px;
  border-radius: 50%;
  background: linear-gradient(135deg, #2196F3 0%, #1976D2 100%);
  cursor: pointer;
  border: none;
  box-shadow: 0 2px 4px rgba(33, 150, 243, 0.3);
}

.control-hint {
  font-size: 11px;
  color: #999;
  margin-top: 4px;
}

.checkbox-label {
  display: flex;
  align-items: center;
  cursor: pointer;
  font-size: 13px;
  font-weight: normal !important;
}

.checkbox-label input[type="checkbox"] {
  margin-right: 8px;
  cursor: pointer;
  width: 16px;
  height: 16px;
}

.reset-btn {
  width: 100%;
  padding: 10px;
  background: linear-gradient(135deg, #2196F3 0%, #1976D2 100%);
  color: white;
  border: none;
  border-radius: 6px;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
  margin-top: 12px;
}

.reset-btn:hover {
  background: linear-gradient(135deg, #1E88E5 0%, #1565C0 100%);
  transform: translateY(-1px);
  box-shadow: 0 4px 8px rgba(33, 150, 243, 0.3);
}

.reset-btn:active {
  transform: translateY(0);
}
</style>

<template>
  <div class="connected-papers-container">
    <!-- 左侧论文列表 -->
    <aside class="papers-list-panel" v-show="showPapersList">
      <div class="list-header">
        <div class="list-title-group">
          <h3>{{ $t('paperGraph.paperList.title') }}</h3>
          <span class="paper-count">{{ $t('paperGraph.paperList.total', { count: papers.length }) }}</span>
        </div>
        <button class="close-list-btn" @click="showPapersList = false" :title="$t('common.close')">&times;</button>
      </div>
      <div class="papers-list">
        <div 
          v-for="paper in sortedPapers" 
          :key="paper.id" 
          :data-paper-id="paper.id"
          class="paper-item"
          :class="{ 'is-main': paper.isMainPaper, 'is-selected': selectedPaper && selectedPaper.id === paper.id }"
          @click="handlePaperClick(paper)"
        >
          <div class="paper-badge" v-if="paper.isMainPaper">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none">
              <path d="M12 2L15.09 8.26L22 9.27L17 14.14L18.18 21.02L12 17.77L5.82 21.02L7 14.14L2 9.27L8.91 8.26L12 2Z" fill="currentColor"/>
            </svg>
          </div>
          <div class="paper-info">
            <h4 class="paper-title">{{ paper.title }}</h4>
            <p class="paper-authors">{{ paper.authors.slice(0, 2).join(', ') }}{{ paper.authors.length > 2 ? ` ${$t('paperGraph.paperDetail.andOthers')}` : '' }}</p>
            <div class="paper-meta">
              <span class="meta-badge year">{{ paper.year }}</span>
              <span class="meta-badge citations">
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none">
                  <path d="M16 6L18.29 8.29L13.41 13.17L9.41 9.17L2 16.59L3.41 18L9.41 12L13.41 16L19.71 9.71L22 12V6H16Z" fill="currentColor"/>
                </svg>
                {{ paper.citationCount }}
              </span>
            </div>
          </div>
        </div>
      </div>
    </aside>
    
    <!-- 右侧可视化区域 -->
    <div class="graph-wrapper">
      <div ref="graphContainer" class="graph-canvas">
        <div v-if="!isRendered" class="loading-indicator">
          <div class="spinner"></div>
          <p>{{ $t('paperGraph.loading.generating') }}</p>
        </div>
      </div>
      
      <!-- 右侧论文详情面板 -->
      <transition name="slide-left">
        <aside v-if="selectedPaper" class="paper-detail-panel">
          <div class="detail-header">
            <h3>{{ $t('paperGraph.paperDetail.title') }}</h3>
            <button class="close-detail-btn" @click="selectedPaper = null" :title="$t('common.close')">&times;</button>
          </div>
          <div class="detail-content">
            <div class="detail-section">
              <h4 class="section-label">{{ $t('paperGraph.paperDetail.titleLabel') }}</h4>
              <p class="paper-full-title">{{ selectedPaper.title }}</p>
            </div>
            
            <div class="detail-section">
              <h4 class="section-label">{{ $t('paperGraph.paperDetail.authorsLabel') }}</h4>
              <p class="paper-authors-full">{{ selectedPaper.authors.join(', ') }}</p>
            </div>
            
            <div class="detail-section" v-if="selectedPaper.year">
              <h4 class="section-label">{{ $t('paperGraph.paperDetail.yearLabel') }}</h4>
              <p class="paper-year">{{ selectedPaper.year }}</p>
            </div>
            
            <div class="detail-section" v-if="selectedPaper.citationCount !== undefined">
              <h4 class="section-label">{{ $t('paperGraph.paperDetail.citationsLabel') }}</h4>
              <p class="paper-citations">{{ selectedPaper.citationCount }}</p>
            </div>
            
            <div class="detail-section" v-if="selectedPaper.abstract">
              <h4 class="section-label">{{ $t('paperGraph.paperDetail.abstractLabel') }}</h4>
              <p class="paper-abstract-full">{{ selectedPaper.abstract }}</p>
            </div>
            
            <div class="detail-actions" v-if="selectedPaper.url">
              <a :href="selectedPaper.url" target="_blank" class="detail-btn primary">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
                  <path d="M19 19H5V5H12V3H5C3.89 3 3 3.9 3 5V19C3 20.1 3.89 21 5 21H19C20.1 21 21 20.1 21 19V12H19V19ZM14 3V5H17.59L7.76 14.83L9.17 16.24L19 6.41V10H21V3H14Z" fill="currentColor"/>
                </svg>
                {{ $t('paperGraph.paperDetail.viewFullPaper') }}
              </a>
            </div>
          </div>
        </aside>
      </transition>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, nextTick, onMounted, onUnmounted, watch } from 'vue'
import * as d3 from 'd3'

const props = defineProps({
  papers: {
    type: Array,
    required: true
  },
  edges: {
    type: Array,
    required: true
  },
  mainPaper: {
    type: Object,
    default: null
  }
})

const graphContainer = ref(null)
const isRendered = ref(false)
const selectedPaper = ref(null)
const showPapersList = ref(true)
let simulation = null
let svg = null
let nodesCopyRef = [] // 保存节点数据引用，用于获取实时坐标
let zoomBehavior = null // 保存 zoom 行为

// 排序论文：主论文在最前面，其他按引用数排序
const sortedPapers = computed(() => {
  return [...props.papers].sort((a, b) => {
    if (a.isMainPaper) return -1
    if (b.isMainPaper) return 1
    return b.citationCount - a.citationCount
  })
})

// 滚动到指定的论文列表项
const scrollToListItem = (paperId) => {
  if (!showPapersList.value) return
  
  // 使用 nextTick 确保 DOM 已更新
  nextTick(() => {
    const paperItem = document.querySelector(`[data-paper-id="${paperId}"]`)
    if (paperItem) {
      paperItem.scrollIntoView({
        behavior: 'smooth',
        block: 'center'
      })
      console.log('Scrolled to paper item:', paperId)
    }
  })
}

// 处理论文列表项点击
const handlePaperClick = (paper) => {
  selectedPaper.value = paper
  
  if (!svg || !graphContainer.value || !zoomBehavior) {
    console.log('SVG or container not ready')
    return
  }
  
  // 从保存的节点引用中找到对应的节点数据（包含实时坐标）
  const nodeData = nodesCopyRef.find(p => p.id === paper.id)
  if (!nodeData || nodeData.x === undefined || nodeData.y === undefined) {
    console.log('Node data not found or coordinates not ready:', nodeData)
    return
  }
  
  console.log('Moving to node:', nodeData.title, 'at', nodeData.x, nodeData.y)
  
  // 获取容器尺寸
  const width = graphContainer.value.clientWidth || 800
  const height = graphContainer.value.clientHeight || 600
  
  // 获取当前的缩放变换
  const currentTransform = d3.zoomTransform(svg.node())
  const scale = currentTransform.k
  
  // 考虑左右面板宽度，计算实际可视区域中心
  // 左侧论文列表: 350px (打开时)
  // 右侧详情面板: 450px (点击后必定打开)
  const leftPanelWidth = showPapersList.value ? 350 : 0
  const rightPanelWidth = 450 // 点击后必定会显示详情面板
  
  // 可视区域的实际中心点（相对于整个画布）
  // 可视区域左边界：leftPanelWidth
  // 可视区域右边界：width - rightPanelWidth
  // 可视区域中心：leftPanelWidth + (width - leftPanelWidth - rightPanelWidth) / 2
  const visualCenter = leftPanelWidth + (width - leftPanelWidth - rightPanelWidth) / 2
  
  // 计算需要的偏移量，将节点移到实际可视区域中心
  const targetX = visualCenter - nodeData.x * scale
  const targetY = height / 2 - nodeData.y * scale
  
  console.log('Left panel:', leftPanelWidth, 'Right panel:', rightPanelWidth, 'Visual center:', visualCenter)
  
  // 平滑过渡到目标位置
  svg.transition()
    .duration(750)
    .call(
      zoomBehavior.transform,
      d3.zoomIdentity.translate(targetX, targetY).scale(scale)
    )
  
  // 高亮对应的节点 - 只更新需要改变的节点，避免闪烁
  svg.selectAll('.node circle')
    .each(function(d) {
      const circle = d3.select(this)
      if (d.id === paper.id) {
        // 高亮当前节点
        circle.transition()
          .duration(300)
          .attr('stroke-width', 8)
          .attr('stroke', '#FFD700')
          .style('filter', 'drop-shadow(0 0 12px rgba(255, 215, 0, 0.8)) drop-shadow(0 2px 4px rgba(0,0,0,0.2))')
      } else {
        // 只对已高亮的节点恢复默认状态
        const currentStroke = circle.attr('stroke')
        if (currentStroke !== '#fff') {
          circle.transition()
            .duration(300)
            .attr('stroke-width', 4)
            .attr('stroke', '#fff')
            .style('filter', 'drop-shadow(0 2px 4px rgba(0,0,0,0.2))')
        }
      }
    })
}

const renderGraph = () => {
  if (!graphContainer.value || props.papers.length === 0) return

  const container = graphContainer.value
  const width = container.clientWidth || 800
  const height = container.clientHeight || 600
  
  console.log('Canvas dimensions:', width, height)
  
  if (width < 100 || height < 100) {
    console.warn('Container too small, retrying...', {width, height})
    setTimeout(renderGraph, 100)
    return
  }
  
  isRendered.value = false
  
  // 清空之前的SVG内容
  d3.select(graphContainer.value).selectAll('svg').remove()

  // 创建 SVG
  svg = d3.select(container)
    .append('svg')
    .attr('width', width)
    .attr('height', height)
    .style('background', '#f5f5f5')
  
  console.log('SVG created:', svg.node())
  
  // 添加缩放和平移功能
  const g = svg.append('g')
  
  zoomBehavior = d3.zoom()
    .scaleExtent([0.1, 4])
    .on('zoom', (event) => {
      g.attr('transform', event.transform)
    })
  
  // 设置初始缩放比例，让视图更小一些
  const initialScale = 0.6
  const initialTransform = d3.zoomIdentity
    .translate(width / 2, height / 2)
    .scale(initialScale)
    .translate(-width / 2, -height / 2)
  
  svg.call(zoomBehavior)
    .call(zoomBehavior.transform, initialTransform)

  // 创建箭头标记
  svg.append('defs').selectAll('marker')
    .data(['arrow'])
    .join('marker')
    .attr('id', 'arrow')
    .attr('viewBox', '0 -5 10 10')
    .attr('refX', 20)
    .attr('refY', 0)
    .attr('markerWidth', 6)
    .attr('markerHeight', 6)
    .attr('orient', 'auto')
    .append('path')
    .attr('d', 'M0,-5L10,0L0,5')
    .attr('fill', '#95a5a6')

  // 复制数据以避免修改原始对象，并给初始位置
  const nodesCopy = props.papers.map((d, i) => {
    // 计算节点大小（基于引用数）- 增大节点，增强对比
    const radius = d.isMainPaper ? 55 : Math.max(30, Math.min(70, 30 + d.citationCount / 3))
    return {
      ...d,
      x: width / 2 + (Math.random() - 0.5) * 300,
      y: height / 2 + (Math.random() - 0.5) * 300,
      radius
    }
  })
  
  // 保存节点数据引用，用于后续获取实时坐标
  nodesCopyRef = nodesCopy
  const edgesCopy = props.edges.map(d => ({...d}))
  
  console.log('节点示例:', nodesCopy[0])
  console.log('边示例:', edgesCopy[0])
  
  // 创建力导向图
  simulation = d3.forceSimulation(nodesCopy)
    .force('link', d3.forceLink(edgesCopy)
      .id(d => d.id)
      .distance(d => {
        const sourceRadius = d.source.radius || 35
        const targetRadius = d.target.radius || 35
        return sourceRadius + targetRadius + 10  // 更紧密
      }))
    .force('charge', d3.forceManyBody().strength(-1400))
    .force('center', d3.forceCenter(width / 2, height / 2))
    .force('collision', d3.forceCollide().radius(d => d.radius + 8))
    .alpha(1)
    .alphaDecay(0.015)

  // 绘制连线 - 根据连接的节点重要性设置样式
  const link = g.append('g')
    .attr('class', 'links')
    .selectAll('line')
    .data(edgesCopy)
    .join('line')
    .attr('stroke', d => {
      // 如果连接到主节点，颜色更深
      const sourceNode = nodesCopy.find(n => n.id === d.source.id)
      const targetNode = nodesCopy.find(n => n.id === d.target.id)
      if (sourceNode?.isMainPaper || targetNode?.isMainPaper) {
        return '#666666'
      }
      // 根据节点大小决定颜色深浅
      const avgRadius = ((d.source.radius || 30) + (d.target.radius || 30)) / 2
      if (avgRadius > 50) return '#777777'
      if (avgRadius > 40) return '#999999'
      return '#bbbbbb'
    })
    .attr('stroke-width', d => {
      // 如果连接到主节点，线更粗
      const sourceNode = nodesCopy.find(n => n.id === d.source.id)
      const targetNode = nodesCopy.find(n => n.id === d.target.id)
      if (sourceNode?.isMainPaper || targetNode?.isMainPaper) {
        return 3
      }
      // 根据节点大小决定线的粗细
      const avgRadius = ((d.source.radius || 30) + (d.target.radius || 30)) / 2
      if (avgRadius > 50) return 2.5
      if (avgRadius > 40) return 2
      return 1.5
    })
    .attr('opacity', d => {
      // 主节点连线更明显
      const sourceNode = nodesCopy.find(n => n.id === d.source.id)
      const targetNode = nodesCopy.find(n => n.id === d.target.id)
      if (sourceNode?.isMainPaper || targetNode?.isMainPaper) {
        return 0.85
      }
      return 0.6
    })

  // 创建节点组
  const node = g.append('g')
    .attr('class', 'nodes')
    .selectAll('g')
    .data(nodesCopy)
    .join('g')
    .attr('class', 'node')
    .call(drag(simulation))
  
  console.log('创建了', node.size(), '个节点组')
  
  // 主节点添加光晕 - 增强光晕效果
  node.filter(d => d.isMainPaper)
    .append('circle')
    .attr('r', d => d.radius + 25)
    .attr('fill', '#ff69b4')
    .attr('opacity', 0.2)
  
  node.filter(d => d.isMainPaper)
    .append('circle')
    .attr('r', d => d.radius + 15)
    .attr('fill', '#ff1493')
    .attr('opacity', 0.3)
  
  node.filter(d => d.isMainPaper)
    .append('circle')
    .attr('r', d => d.radius + 8)
    .attr('fill', '#ff1493')
    .attr('opacity', 0.4)

  // 绘制节点圆圈 - 增强颜色对比
  node.append('circle')
    .attr('r', d => d.radius)
    .attr('fill', d => {
      if (d.isMainPaper) return '#d02090'  // 更亮的主节点
      const year = parseInt(d.year)
      if (year >= 2025) return '#4a6d6c'  // 更深的2025
      if (year >= 2024) return '#6f9993'  // 中等深度2024
      if (year >= 2023) return '#90b4b0'  // 浅色2023
      return '#a8c8c5'  // 更浅的旧论文
    })
    .attr('stroke', '#fff')
    .attr('stroke-width', 4)
    .style('cursor', 'pointer')
    .style('opacity', 1)
    .style('filter', 'drop-shadow(0 2px 4px rgba(0,0,0,0.2))')
    .on('click', function(event, d) {
      event.stopPropagation()
      selectedPaper.value = d
      console.log('点击节点:', d)
      
      // 联动左侧论文列表滚动到对应项
      scrollToListItem(d.id)
      
      // 点击视觉效果：只对需要改变的节点应用过渡，避免闪烁
      const clickedCircle = d3.select(this)
      const clickedNode = clickedCircle.node()
      
      svg.selectAll('.node circle')
        .each(function() {
          if (this === clickedNode) return
          
          const circle = d3.select(this)
          const currentStroke = circle.attr('stroke')
          
          // 只对已高亮的节点恢复默认状态
          if (currentStroke !== '#fff') {
            circle.transition()
              .duration(300)
              .attr('stroke-width', 4)
              .attr('stroke', '#fff')
              .style('filter', 'drop-shadow(0 2px 4px rgba(0,0,0,0.2))')
          }
        })
      
      // 当前节点高亮 - 金黄色边框 + 外发光
      clickedCircle
        .transition()
        .duration(300)
        .attr('stroke-width', 8)
        .attr('stroke', '#FFD700')
        .style('filter', 'drop-shadow(0 0 12px rgba(255, 215, 0, 0.8)) drop-shadow(0 2px 4px rgba(0,0,0,0.2))')
    })

  // 添加节点标签（显示作者姓氏 + 年份）- 增强文字对比
  node.append('text')
    .text(d => {
      // 提取第一作者的姓氏
      const firstAuthor = d.authors && d.authors.length > 0 ? d.authors[0].split(' ').pop() : 'Unknown'
      return `${firstAuthor}, ${d.year}`
    })
    .attr('x', 0)
    .attr('y', 6)
    .attr('text-anchor', 'middle')
    .attr('font-size', d => d.isMainPaper ? '15px' : '13px')
    .attr('fill', '#ffffff')
    .attr('font-weight', d => d.isMainPaper ? 'bold' : '700')
    .style('pointer-events', 'none')
    .style('text-shadow', '0 2px 4px rgba(0,0,0,0.7), 0 0 8px rgba(0,0,0,0.3)')

  // 添加悬停提示
  node.append('title')
    .text(d => `${d.title}\n\n作者: ${d.authors.slice(0, 3).join(', ')}${d.authors.length > 3 ? ' ...' : ''}\n年份: ${d.year}\n引用数: ${d.citationCount}`)

  // 更新节点和连线位置
  let tickCount = 0
  simulation.on('tick', () => {
    tickCount++
    
    link
      .attr('x1', d => d.source.x)
      .attr('y1', d => d.source.y)
      .attr('x2', d => d.target.x)
      .attr('y2', d => d.target.y)

    node.attr('transform', d => `translate(${d.x},${d.y})`)
  })
  
  // 渲染完成后标记
  simulation.on('end', () => {
    console.log('力模拟完成，总tick:', tickCount)
    isRendered.value = true
  })
  
  // 初始渲染后立即标记为完成（显示初始状态）
  setTimeout(() => {
    console.log('初始渲染完成，隐藏loading')
    isRendered.value = true
  }, 300)
}

// 拖拽功能
const drag = (simulation) => {
  function dragstarted(event) {
    if (!event.active) simulation.alphaTarget(0.3).restart()
    event.subject.fx = event.subject.x
    event.subject.fy = event.subject.y
  }
  
  function dragged(event) {
    event.subject.fx = event.x
    event.subject.fy = event.y
  }
  
  function dragended(event) {
    if (!event.active) simulation.alphaTarget(0)
    event.subject.fx = null
    event.subject.fy = null
  }
  
  return d3.drag()
    .on('start', dragstarted)
    .on('drag', dragged)
    .on('end', dragended)
}

onMounted(() => {
  // 延迟渲染确保容器已经有尺寸
  setTimeout(() => {
    renderGraph()
  }, 100)
  window.addEventListener('resize', renderGraph)
})

onUnmounted(() => {
  if (simulation) {
    simulation.stop()
  }
  window.removeEventListener('resize', renderGraph)
})

watch(() => [props.papers, props.edges], () => {
  renderGraph()
}, { deep: true })
</script>

<style scoped>
.connected-papers-container {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: row;
  background: #f8f9fa;
  position: relative;
  gap: 0;
}

/* 左侧论文列表面板 - fixed定位，从屏幕最左开始，右边界与模板列表对齐 */
.papers-list-panel {
  position: fixed;
  left: 0;
  top: 0;
  width: 350px;
  height: 100vh;
  background: #ffffff;
  border-right: 1px solid #e1e4e8;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  z-index: 200;
  box-shadow: 2px 0 20px rgba(0, 0, 0, 0.15);
}

.list-header {
  padding: 20px 24px;
  background: #f8f9fa;
  border-bottom: 1px solid #e1e4e8;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.list-title-group {
  display: flex;
  align-items: center;
  gap: 12px;
}

.list-header h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: #2c3e50;
}

.paper-count {
  font-size: 13px;
  color: #7f8c8d;
  background: #ecf0f1;
  padding: 4px 10px;
  border-radius: 12px;
}

.close-list-btn {
  width: 32px;
  height: 32px;
  border: none;
  background: transparent;
  color: #7f8c8d;
  font-size: 28px;
  line-height: 1;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s ease;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0;
}

.close-list-btn:hover {
  background: #e74c3c;
  color: white;
}

.papers-list {
  flex: 1;
  overflow-y: auto;
  padding: 12px;
}

/* 论文列表项 */
.paper-item {
  position: relative;
  padding: 16px;
  margin-bottom: 8px;
  background: #f8f9fa;
  border: 2px solid transparent;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.paper-item:hover:not(.is-selected) {
  background: #e8f4f8;
  border-color: #3498db;
  transform: translateX(4px);
}

.paper-item.is-main {
  background: linear-gradient(135deg, #ffeef8 0%, #ffe8f5 100%);
  border-color: #ff69b4;
}

.paper-item.is-main:hover:not(.is-selected) {
  background: linear-gradient(135deg, #ffe0f0 0%, #ffd5ed 100%);
  border-color: #ff1493;
}

.paper-item.is-selected {
  background: #fffbea;
  border-color: #FFD700;
  box-shadow: 0 4px 16px rgba(255, 215, 0, 0.4), 0 0 0 3px rgba(255, 215, 0, 0.1);
}

.paper-badge {
  position: absolute;
  top: 12px;
  right: 12px;
  width: 24px;
  height: 24px;
  background: #ff1493;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
}

.paper-info {
  padding-right: 30px;
}

.paper-title {
  margin: 0 0 8px 0;
  font-size: 14px;
  font-weight: 600;
  color: #2c3e50;
  line-height: 1.4;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.paper-authors {
  margin: 0 0 8px 0;
  font-size: 12px;
  color: #7f8c8d;
  display: -webkit-box;
  -webkit-line-clamp: 1;
  line-clamp: 1;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.paper-meta {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.meta-badge {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 2px 8px;
  font-size: 11px;
  font-weight: 500;
  border-radius: 4px;
}

.meta-badge.year {
  background: #e3f2fd;
  color: #1976d2;
}

.meta-badge.citations {
  background: #f3e5f5;
  color: #7b1fa2;
}

.meta-badge svg {
  width: 12px;
  height: 12px;
}

/* 右侧图表区域 */
.graph-wrapper {
  flex: 1;
  height: 100%;
  display: flex;
  flex-direction: column;
  position: relative;
  overflow: hidden;
}

/* 右侧论文详情面板 - 对齐到屏幕右边缘 */
.paper-detail-panel {
  position: fixed;
  right: 0;
  top: 0;
  width: 450px;
  max-width: 450px;
  height: 100vh;
  background: #ffffff;
  border-left: 1px solid #e1e4e8;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  z-index: 150;
  box-shadow: -2px 0 20px rgba(0, 0, 0, 0.15);
}

.detail-header {
  padding: 20px 24px;
  background: #f8f9fa;
  border-bottom: 1px solid #e1e4e8;
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-shrink: 0;
}

.detail-header h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: #2c3e50;
}

.close-detail-btn {
  width: 32px;
  height: 32px;
  border: none;
  background: transparent;
  color: #7f8c8d;
  font-size: 28px;
  line-height: 1;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s ease;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0;
}

.close-detail-btn:hover {
  background: #e74c3c;
  color: white;
}

.detail-content {
  flex: 1;
  overflow-y: auto;
  padding: 24px;
}

.detail-section {
  margin-bottom: 24px;
}

.section-label {
  font-size: 12px;
  font-weight: 600;
  color: #7f8c8d;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin: 0 0 8px 0;
}

.paper-full-title {
  font-size: 16px;
  font-weight: 600;
  color: #2c3e50;
  line-height: 1.5;
  margin: 0;
}

.paper-authors-full {
  font-size: 14px;
  color: #2c3e50;
  line-height: 1.6;
  margin: 0;
}

.paper-year,
.paper-citations {
  font-size: 14px;
  color: #2c3e50;
  margin: 0;
}

.paper-abstract-full {
  font-size: 14px;
  color: #2c3e50;
  line-height: 1.7;
  margin: 0;
  white-space: pre-wrap;
  word-wrap: break-word;
}

.detail-actions {
  margin-top: 24px;
  padding-top: 24px;
  border-top: 1px solid #ecf0f1;
}

.detail-btn {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 12px 20px;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  text-decoration: none;
  transition: all 0.2s ease;
}

.detail-btn.primary {
  background: #3498db;
  color: white;
}

.detail-btn.primary:hover {
  background: #2980b9;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(52, 152, 219, 0.3);
}

/* 滑入动画 */
.slide-left-enter-active,
.slide-left-leave-active {
  transition: all 0.3s ease;
}

.slide-left-enter-from {
  transform: translateX(100%);
  opacity: 0;
}

.slide-left-leave-to {
  transform: translateX(100%);
  opacity: 0;
}

.graph-canvas {
  width: 100%;
  height: 100%;
  background: #f5f5f5;
  position: relative;
  overflow: hidden;
}

.graph-canvas svg {
  display: block;
}

.loading-indicator {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: #7f8c8d;
}

.spinner {
  width: 40px;
  height: 40px;
  border: 4px solid #ecf0f1;
  border-top-color: #3498db;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: 16px;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* 论文详情卡片 */
.paper-card {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  background: white;
  border-top: 3px solid #3498db;
  box-shadow: 0 -4px 20px rgba(0, 0, 0, 0.15);
  max-height: 60%;
  overflow-y: auto;
  z-index: 1000;
}

.card-close-btn {
  position: absolute;
  top: 16px;
  right: 16px;
  width: 32px;
  height: 32px;
  border: none;
  background: #ecf0f1;
  color: #7f8c8d;
  font-size: 24px;
  line-height: 1;
  border-radius: 50%;
  cursor: pointer;
  transition: all 0.2s ease;
  display: flex;
  align-items: center;
  justify-content: center;
}

.card-close-btn:hover {
  background: #e74c3c;
  color: white;
  transform: rotate(90deg);
}

.card-content {
  padding: 24px 60px 24px 24px;
}

.card-title {
  font-size: 20px;
  color: #2c3e50;
  margin: 0 0 16px 0;
  font-weight: 600;
  line-height: 1.4;
}

.card-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 20px;
  margin-bottom: 20px;
  padding: 12px 0;
  border-bottom: 1px solid #ecf0f1;
}

.meta-item {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 14px;
  color: #7f8c8d;
}

.meta-item svg {
  color: #3498db;
  flex-shrink: 0;
}

.card-abstract {
  margin-bottom: 20px;
}

.card-abstract h4 {
  font-size: 14px;
  color: #7f8c8d;
  margin: 0 0 8px 0;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.card-abstract p {
  font-size: 14px;
  color: #2c3e50;
  line-height: 1.6;
  margin: 0;
  max-height: 150px;
  overflow-y: auto;
}

.card-actions {
  display: flex;
  gap: 12px;
}

.card-btn {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 10px 20px;
  border: none;
  border-radius: 6px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  text-decoration: none;
  transition: all 0.2s ease;
}

.card-btn.primary {
  background: #3498db;
  color: white;
}

.card-btn.primary:hover {
  background: #2980b9;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(52, 152, 219, 0.3);
}

/* 滑入动画 */
.slide-up-enter-active,
.slide-up-leave-active {
  transition: all 0.3s ease;
}

.slide-up-enter-from {
  transform: translateY(100%);
  opacity: 0;
}

.slide-up-leave-to {
  transform: translateY(100%);
  opacity: 0;
}

/* 滚动条样式 */
.papers-list::-webkit-scrollbar,
.detail-content::-webkit-scrollbar,
.paper-card::-webkit-scrollbar,
.card-abstract p::-webkit-scrollbar {
  width: 6px;
}

.papers-list::-webkit-scrollbar-track,
.detail-content::-webkit-scrollbar-track,
.paper-card::-webkit-scrollbar-track,
.card-abstract p::-webkit-scrollbar-track {
  background: #f8f9fa;
}

.papers-list::-webkit-scrollbar-thumb,
.detail-content::-webkit-scrollbar-thumb,
.paper-card::-webkit-scrollbar-thumb,
.card-abstract p::-webkit-scrollbar-thumb {
  background: #cbd5e0;
  border-radius: 3px;
}

.papers-list::-webkit-scrollbar-thumb:hover,
.detail-content::-webkit-scrollbar-thumb:hover,
.paper-card::-webkit-scrollbar-thumb:hover,
.card-abstract p::-webkit-scrollbar-thumb:hover {
  background: #a0aec0;
}
</style>

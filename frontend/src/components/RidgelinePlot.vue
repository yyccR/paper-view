<template>
  <div class="ridgeline-plot">
    <div class="canvas-container" ref="containerRef">
      <svg ref="svgRef" class="ridgeline-svg"></svg>
      <!-- 重置按钮浮动在右上角 -->
      <button class="reset-btn" @click="resetView" :title="$t('workspace.visualization.resetView', '重置视图')">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
          <path d="M3 12C3 7.02944 7.02944 3 12 3C16.9706 3 21 7.02944 21 12C21 16.9706 16.9706 21 12 21C9.5 21 7.5 20 6 18.5" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
          <path d="M3 16V12H7" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
      </button>
      <!-- 悬浮信息提示 -->
      <div v-if="hoveredArea" class="tooltip" :style="tooltipStyle">
        <div class="tooltip-title">{{ hoveredArea.field }}</div>
        <div class="tooltip-content">
          <div class="tooltip-row">
            <span class="tooltip-label">{{ $t('workspace.visualization.year', '年份') }}:</span>
            <span class="tooltip-value">{{ hoveredArea.year }}</span>
          </div>
          <div class="tooltip-row">
            <span class="tooltip-label">{{ $t('workspace.visualization.density', '热度') }}:</span>
            <span class="tooltip-value">{{ hoveredArea.density.toFixed(1) }}</span>
          </div>
          <div class="tooltip-row">
            <span class="tooltip-label">{{ $t('workspace.visualization.papers', '论文数') }}:</span>
            <span class="tooltip-value">{{ hoveredArea.papers }}</span>
          </div>
          <div class="tooltip-row" v-if="hoveredArea.citations">
            <span class="tooltip-label">{{ $t('densityViz.citations', '引用数') }}:</span>
            <span class="tooltip-value">{{ hoveredArea.citations }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch, nextTick } from 'vue'
import { useI18n } from 'vue-i18n'
import * as d3 from 'd3'

const { t } = useI18n()

const props = defineProps({
  ridgelineData: {
    type: Object,
    required: true
  }
})

const containerRef = ref(null)
const svgRef = ref(null)
const hoveredArea = ref(null)
const tooltipStyle = ref({})

let svg = null
let g = null
let zoom = null
let xScale = null
let yScale = null

// 从网络数据生成时间线热度数据
const generateRidgelineData = (networkData) => {
  if (!networkData || !networkData.network || !networkData.network.items) {
    return { fields: [], yearRange: [], data: [] }
  }

  const items = networkData.network.items
  
  // 提取年份信息（从节点的属性中）
  const yearData = []
  items.forEach(item => {
    // 尝试从不同字段提取年份
    let year = null
    if (item.attributes) {
      year = item.attributes.year || item.attributes.Year || item.attributes.publication_year
    }
    if (!year && item.description) {
      // 尝试从描述中提取年份
      const yearMatch = item.description.match(/\b(19|20)\d{2}\b/)
      year = yearMatch ? parseInt(yearMatch[0]) : null
    }
    
    // 获取聚类信息作为领域
    const cluster = item.cluster || 0
    const citations = item.weights?.Citations || 0
    
    if (year && year >= 1990 && year <= 2025) {
      yearData.push({
        year: year,
        cluster: cluster,
        label: item.label || '',
        citations: citations
      })
    }
  })

  if (yearData.length === 0) {
    // 如果没有年份信息，生成示例数据
    return generateSampleData()
  }

  // 统计年份范围
  const years = [...new Set(yearData.map(d => d.year))].sort((a, b) => a - b)
  const minYear = Math.min(...years)
  const maxYear = Math.max(...years)
  const yearRange = []
  for (let y = minYear; y <= maxYear; y++) {
    yearRange.push(y)
  }

  // 统计聚类（领域）
  const clusters = [...new Set(yearData.map(d => d.cluster))].sort((a, b) => a - b)
  
  // 为每个聚类生成领域名称
  const fields = clusters.map((c, i) => {
    const clusterItems = items.filter(item => item.cluster === c)
    // 使用该聚类中最常见的词作为领域名
    if (clusterItems.length > 0) {
      return clusterItems[0].label || `${t('workspace.visualization.field', '领域')} ${i + 1}`
    }
    return `${t('workspace.visualization.field', '领域')} ${i + 1}`
  })

  // 为每个领域和年份计算密度
  const data = []
  clusters.forEach((cluster, fieldIndex) => {
    const clusterData = yearData.filter(d => d.cluster === cluster)
    const fieldData = {
      field: fields[fieldIndex],
      cluster: cluster,
      values: []
    }
    
    yearRange.forEach(year => {
      const yearPapers = clusterData.filter(d => d.year === year)
      const count = yearPapers.length
      const totalCitations = yearPapers.reduce((sum, d) => sum + d.citations, 0)
      
      // 使用高斯核密度估计来平滑密度曲线
      let density = 0
      const bandwidth = 1.5 // 带宽参数
      clusterData.forEach(d => {
        const diff = (year - d.year) / bandwidth
        density += Math.exp(-0.5 * diff * diff) * (1 + d.citations / 10)
      })
      
      fieldData.values.push({
        year: year,
        density: density,
        papers: count,
        citations: totalCitations
      })
    })
    
    data.push(fieldData)
  })

  return { fields, yearRange, data }
}

// 生成示例数据
const generateSampleData = () => {
  const fields = [
    t('workspace.visualization.artificialIntelligence', '人工智能'),
    t('workspace.visualization.machineLearning', '机器学习'),
    t('workspace.visualization.deepLearning', '深度学习'),
    t('workspace.visualization.neuralNetworks', '神经网络'),
    t('workspace.visualization.naturalLanguageProcessing', '自然语言处理'),
    t('workspace.visualization.computerVision', '计算机视觉'),
    t('workspace.visualization.reinforcementLearning', '强化学习'),
    t('workspace.visualization.knowledgeGraph', '知识图谱'),
    t('workspace.visualization.dataMining', '数据挖掘'),
    t('workspace.visualization.cloudComputing', '云计算'),
    t('workspace.visualization.blockChain', '区块链'),
    t('workspace.visualization.quantumComputing', '量子计算')
  ]
  
  // 扩展时间跨度：2000-2024
  const yearRange = []
  for (let y = 2000; y <= 2024; y++) {
    yearRange.push(y)
  }

  const data = fields.map((field, fieldIndex) => {
    // 为每个领域创建不同的增长趋势和峰值年份
    const peakYear = 2008 + fieldIndex * 1.5
    const values = yearRange.map(year => {
      // 使用高斯分布生成密度值
      const distance = (year - peakYear) / 4
      const baseDensity = Math.exp(-0.5 * distance * distance) * (40 + Math.random() * 25)
      // 添加整体增长趋势
      const growthFactor = 1 + (year - yearRange[0]) * 0.08
      // 添加一些随机波动
      const fluctuation = 1 + (Math.sin(year * 0.5 + fieldIndex) * 0.15)
      const density = baseDensity * growthFactor * fluctuation
      
      return {
        year: year,
        density: Math.max(0, density),
        papers: Math.floor(density * 0.6 + Math.random() * 15),
        citations: Math.floor(density * 2.5 + Math.random() * 60)
      }
    })
    
    return { field, values }
  })

  return { fields, yearRange, data }
}

const initVisualization = () => {
  if (!containerRef.value || !svgRef.value) return

  const container = containerRef.value
  const width = container.clientWidth
  const height = container.clientHeight

  // 清除旧的SVG内容
  d3.select(svgRef.value).selectAll('*').remove()

  // 创建SVG
  svg = d3.select(svgRef.value)
    .attr('width', width)
    .attr('height', height)

  // 创建 defs 用于渐变定义
  const defs = svg.append('defs')

  // 创建主绘图区域
  g = svg.append('g')

  // 生成数据
  const { fields, yearRange, data } = generateRidgelineData(props.ridgelineData)

  if (data.length === 0) {
    return
  }

  // 设置边距 - 减小宽度让曲线更窄，波峰起伏更明显，调整左右边距让图形居中
  const margin = { top: 40, right: 150, bottom: 60, left: 150 }
  const plotWidth = width - margin.left - margin.right
  const plotHeight = height - margin.top - margin.bottom

  // 创建比例尺
  xScale = d3.scaleLinear()
    .domain([yearRange[0], yearRange[yearRange.length - 1]])
    .range([0, plotWidth])

  const ridgeHeight = plotHeight / data.length
  yScale = d3.scaleLinear()
    .range([0, data.length])

  // 为每个领域创建垂直比例尺 - 增大缩放比例让波峰起伏更明显
  const maxDensity = d3.max(data, d => d3.max(d.values, v => v.density)) || 1
  const yDensityScale = d3.scaleLinear()
    .domain([0, maxDensity])
    .range([0, ridgeHeight * 2.2])  // 从 1.5 增加到 2.2，让波峰低谷对比更加明显

  // 为每个领域分配不同的基色 - 使用更鲜艳、对比度更高的颜色
  const fieldColors = [
    '#E74C3C', // 鲜红色
    '#1ABC9C', // 绿松石色
    '#3498DB', // 明亮蓝色
    '#F39C12', // 橙色
    '#2ECC71', // 翡翠绿
    '#9B59B6', // 紫罗兰色
    '#E67E22', // 胡萝卜橙
    '#16A085', // 深绿松石
    '#C0392B', // 深红色
    '#8E44AD', // 深紫色
    '#27AE60', // 深绿色
    '#D35400'  // 南瓜橙
  ]

  // 创建区域生成器
  const area = d3.area()
    .x(d => xScale(d.year))
    .y0(0)
    .y1(d => -yDensityScale(d.density))
    .curve(d3.curveBasis)

  // 创建线条生成器（用于绘制顶部边界）
  const line = d3.line()
    .x(d => xScale(d.year))
    .y(d => -yDensityScale(d.density))
    .curve(d3.curveBasis)

  // 绘制每个领域的密度图
  const ridgeGroup = g.append('g')
    .attr('transform', `translate(${margin.left}, ${margin.top})`)

  data.forEach((fieldData, i) => {
    const fieldGroup = ridgeGroup.append('g')
      .attr('transform', `translate(0, ${i * ridgeHeight + ridgeHeight})`)

    const baseColor = d3.color(fieldColors[i % fieldColors.length])
    
    // 绘制密度曲线区域（使用统一的半透明填充）
    const path = fieldGroup.append('path')
      .datum(fieldData.values)
      .attr('class', 'ridge-area')
      .attr('d', area)
      .attr('fill', baseColor)
      .attr('fill-opacity', 0.55)  // 统一的半透明度
      .attr('stroke', baseColor.darker(0.8))  // 更深的边框颜色
      .attr('stroke-width', 2.5)

    // 添加交互
    fieldData.values.forEach((value, valueIndex) => {
      if (valueIndex === fieldData.values.length - 1) return
      
      const nextValue = fieldData.values[valueIndex + 1]
      const x1 = xScale(value.year)
      const x2 = xScale(nextValue.year)
      const y1 = -yDensityScale(value.density)
      const y2 = -yDensityScale(nextValue.density)
      
      // 创建不可见的交互区域 - 修复边缘平滑问题：不高亮交互区域本身
      fieldGroup.append('path')
        .attr('d', `M${x1},0 L${x1},${y1} L${x2},${y2} L${x2},0 Z`)
        .attr('fill', 'transparent')
        .attr('cursor', 'pointer')
        .on('mouseenter', (event) => {
          hoveredArea.value = {
            field: fieldData.field,
            year: value.year,
            density: value.density,
            papers: value.papers,
            citations: value.citations
          }
          updateTooltipPosition(event)
          
          // 只增强整条曲线的显示，不高亮交互区域本身
          path.transition()
            .duration(200)
            .attr('stroke-width', 3.5)
            .attr('fill-opacity', 0.75)
        })
        .on('mousemove', (event) => {
          updateTooltipPosition(event)
        })
        .on('mouseleave', (event) => {
          hoveredArea.value = null
          
          // 恢复曲线的原始样式
          path.transition()
            .duration(200)
            .attr('stroke-width', 2.5)
            .attr('fill-opacity', 0.55)
        })
    })

    // 绘制领域标签 - 增大字体
    fieldGroup.append('text')
      .attr('x', -15)
      .attr('y', -ridgeHeight / 2)
      .attr('text-anchor', 'end')
      .attr('dominant-baseline', 'middle')
      .attr('font-size', '15px')
      .attr('font-weight', '600')
      .attr('fill', '#2c3e50')
      .text(fieldData.field)

    // 绘制基线
    fieldGroup.append('line')
      .attr('x1', 0)
      .attr('x2', plotWidth)
      .attr('y1', 0)
      .attr('y2', 0)
      .attr('stroke', '#ddd')
      .attr('stroke-width', 1)
  })

  // 添加X轴
  const xAxis = d3.axisBottom(xScale)
    .tickFormat(d3.format('d'))
    .ticks(Math.min(yearRange.length, 15))

  g.append('g')
    .attr('class', 'x-axis')
    .attr('transform', `translate(${margin.left}, ${height - margin.bottom})`)
    .call(xAxis)
    .selectAll('text')
    .attr('font-size', '11px')

  // 添加X轴标签
  g.append('text')
    .attr('class', 'axis-label')
    .attr('x', margin.left + plotWidth / 2)
    .attr('y', height - 20)
    .attr('text-anchor', 'middle')
    .attr('font-size', '13px')
    .attr('font-weight', '600')
    .attr('fill', '#333')
    .text(t('workspace.visualization.yearAxis', '年份'))

  // 添加缩放功能
  zoom = d3.zoom()
    .scaleExtent([0.5, 5])
    .on('zoom', (event) => {
      g.attr('transform', event.transform)
    })

  svg.call(zoom)
}

const updateTooltipPosition = (event) => {
  const rect = containerRef.value.getBoundingClientRect()
  const mouseX = event.clientX - rect.left
  const mouseY = event.clientY - rect.top
  
  // 预估 tooltip 宽度和高度
  const tooltipWidth = 220
  const tooltipHeight = 130
  const verticalOffset = 20 // 垂直方向的偏移量（远离鼠标水平线）
  const horizontalOffset = 80 // 水平方向的偏移量（避开鼠标点）
  
  let left, top
  
  // 计算鼠标在容器中的相对位置（0-1）
  const relativeX = mouseX / rect.width
  const relativeY = mouseY / rect.height
  
  // Ridgeline Plot 的关键是不要遮挡横向的曲线
  // 策略：浮窗始终显示在鼠标的上方或下方，同时水平方向偏移避开鼠标点
  
  // 垂直方向：根据鼠标位置决定上下
  if (relativeY > 0.5) {
    // 鼠标在下半部分 -> 浮窗显示在上方（远离鼠标水平线）
    top = `${mouseY - tooltipHeight - verticalOffset}px`
  } else {
    // 鼠标在上半部分 -> 浮窗显示在下方（远离鼠标水平线）
    top = `${mouseY + verticalOffset}px`
  }
  
  // 水平方向：向左或向右偏移，避开鼠标点
  if (relativeX > 0.5) {
    // 鼠标在右侧 -> 浮窗向左偏移
    left = `${mouseX - tooltipWidth - horizontalOffset}px`
  } else {
    // 鼠标在左侧 -> 浮窗向右偏移
    left = `${mouseX + horizontalOffset}px`
  }
  
  // 边界检查，确保浮窗不超出容器范围
  let leftNum = parseFloat(left)
  let topNum = parseFloat(top)
  
  // 水平边界检查
  if (leftNum < 10) {
    leftNum = 10
  } else if (leftNum + tooltipWidth > rect.width - 10) {
    leftNum = rect.width - tooltipWidth - 10
  }
  
  // 垂直边界检查
  if (topNum < 10) {
    topNum = 10
  } else if (topNum + tooltipHeight > rect.height - 10) {
    topNum = rect.height - tooltipHeight - 10
  }
  
  tooltipStyle.value = { 
    left: `${leftNum}px`, 
    top: `${topNum}px` 
  }
}

const resetView = () => {
  if (svg && zoom) {
    svg.transition()
      .duration(750)
      .call(zoom.transform, d3.zoomIdentity)
  }
}

const handleResize = () => {
  initVisualization()
}

onMounted(() => {
  nextTick(() => {
    initVisualization()
    window.addEventListener('resize', handleResize)
  })
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
})

watch(() => props.ridgelineData, () => {
  nextTick(() => {
    initVisualization()
  })
}, { deep: true })
</script>

<style scoped>
.ridgeline-plot {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  background: #fafafa;
  position: relative;
}

.canvas-container {
  flex: 1;
  position: relative;
  overflow: hidden;
  background: white;
}

.reset-btn {
  position: absolute;
  top: 20px;
  right: 20px;
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(255, 255, 255, 0.95);
  border: 1px solid #ddd;
  border-radius: 50%;
  cursor: pointer;
  transition: all 0.3s ease;
  color: #666;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  z-index: 10;
}

.reset-btn:hover {
  background: white;
  border-color: #3498db;
  color: #3498db;
  box-shadow: 0 4px 12px rgba(52, 152, 219, 0.3);
  transform: scale(1.1);
}

.ridgeline-svg {
  width: 100%;
  height: 100%;
}

.tooltip {
  position: absolute;
  background: rgba(255, 255, 255, 0.98);
  border: 2px solid #3498db;
  border-radius: 8px;
  padding: 12px 14px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.2);
  pointer-events: none;
  z-index: 1000;
  min-width: 200px;
  backdrop-filter: blur(10px);
  animation: tooltipFadeIn 0.2s ease;
}

@keyframes tooltipFadeIn {
  from {
    opacity: 0;
    transform: translateY(-5px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.tooltip-title {
  font-size: 14px;
  font-weight: 700;
  color: #2c3e50;
  margin-bottom: 10px;
  padding-bottom: 8px;
  border-bottom: 2px solid #3498db;
}

.tooltip-content {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.tooltip-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 12px;
  gap: 16px;
}

.tooltip-label {
  color: #7f8c8d;
  font-weight: 500;
}

.tooltip-value {
  color: #2c3e50;
  font-weight: 700;
  background: rgba(52, 152, 219, 0.1);
  padding: 2px 8px;
  border-radius: 4px;
}

:deep(.x-axis path),
:deep(.x-axis line) {
  stroke: #999;
}

:deep(.x-axis text) {
  fill: #666;
}

:deep(.axis-label) {
  fill: #333;
}

:deep(.ridge-area) {
  transition: opacity 0.2s ease;
}

:deep(.ridge-area:hover) {
  opacity: 1 !important;
}
</style>

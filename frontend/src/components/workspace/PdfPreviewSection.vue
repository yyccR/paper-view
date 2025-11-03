<template>
  <div class="pdf-preview-section" v-if="visible" :class="{ 'pdf-collapsed': showVisualization && !pdfExpanded }">
    <div class="preview-content" :class="{ 'pdf-expanded': pdfExpanded }" ref="localPreviewContent">
      <!-- 圆形进度加载 -->
      <div v-if="isDownloading" class="pdf-loading">
        <div class="circle-wrapper">
          <svg class="progress-ring" width="120" height="120">
            <circle class="progress-ring__background" stroke="#ecf0f1" stroke-width="10" fill="transparent" r="52" cx="60" cy="60" />
            <circle class="progress-ring__progress" :stroke="progressColor" stroke-width="10" fill="transparent" r="52" cx="60" cy="60"
                    :style="{ strokeDasharray: circumference, strokeDashoffset: dashOffset }" stroke-linecap="round" />
          </svg>
          <div class="progress-text">{{ downloadProgress }}%</div>
        </div>
      </div>

      <!-- PDF 预览 -->
      <div v-if="!showVisualization && currentFileType === 'pdf'" class="pdf-viewer" style="width:100%; height:100%; overflow: auto;">
        <!-- 下载错误提示 -->
        <div v-if="downloadError" class="download-error">
          <svg width="80" height="80" viewBox="0 0 24 24" fill="none">
            <circle cx="12" cy="12" r="10" stroke="#e74c3c" stroke-width="2"/>
            <path d="M12 8V12M12 16H12.01" stroke="#e74c3c" stroke-width="2" stroke-linecap="round"/>
          </svg>
          <h3>{{ downloadError }}</h3>
          <p>请检查网络连接或稍后重试</p>
        </div>
        <!-- PDF 正常预览 -->
        <template v-else>
          <template v-if="!useIframeFallback">
            <div ref="localPdfContainer" class="pdf-canvas-container"></div>
            <p v-if="!isDownloading && !pdfBlobUrl" style="color:#95a5a6;">准备预览PDF...</p>
          </template>
          <template v-else>
            <iframe v-if="viewerSrc" ref="localViewerFrame" :src="viewerSrc" @load="emitViewerLoaded" style="border:none; width:100%; height:100%;"></iframe>
            <p v-else style="color:#95a5a6;">准备预览PDF...</p>
          </template>
        </template>
      </div>
      
      <!-- Word 预览 -->
      <div v-if="!showVisualization && currentFileType === 'word'" class="word-preview" style="width:100%; height:100%; display: flex; flex-direction: column; overflow-y: auto;">
        <div class="file-toolbar">
          <div class="toolbar-left">
            <button class="toolbar-btn" @click="$emit('close-preview')" title="返回列表">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
                <path d="M19 12H5M5 12L12 19M5 12L12 5" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
              返回
            </button>
            <div class="toolbar-sep"></div>
            <span class="file-title">{{ selectedPaperTitle }}</span>
          </div>
        </div>
        <div class="word-viewer" style="flex: 1; background: #f8f9fa;">
          <div class="word-container">
            <div v-if="filePreviewContent" v-html="filePreviewContent" class="word-content"></div>
            <p v-else class="loading-text">加载中...</p>
          </div>
        </div>
      </div>
      
      <!-- Excel 预览 -->
      <div v-if="!showVisualization && currentFileType === 'excel'" class="excel-preview" style="width:100%; height:100%; display: flex; flex-direction: column; overflow-y: auto;">
        <div class="file-toolbar">
          <div class="toolbar-left">
            <button class="toolbar-btn" @click="$emit('close-preview')" title="返回列表">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
                <path d="M19 12H5M5 12L12 19M5 12L12 5" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
              返回
            </button>
            <div class="toolbar-sep"></div>
            <span class="file-title">{{ selectedPaperTitle }}</span>
          </div>
        </div>
        <div class="excel-tabs" v-if="excelData && excelData.sheets" style="display: flex; gap: 4px; padding: 12px 16px 0; background: white; border-bottom: 1px solid #e0e0e0;">
          <button 
            v-for="(sheet, index) in excelData.sheets" 
            :key="sheet"
            :class="['excel-tab', { active: currentExcelSheet === index }]"
            @click="$emit('set-excel-sheet', index)"
            style="padding: 8px 16px; background: transparent; border: none; border-bottom: 2px solid transparent; cursor: pointer; font-size: 13px; color: #7f8c8d; transition: all 0.2s;"
          >
            {{ sheet }}
          </button>
        </div>
        <div class="excel-content" v-if="currentSheetData" style="flex: 1; padding: 24px;">
          <div class="excel-content-wrapper">
            <div class="table-wrapper" style="overflow-x: auto;">
              <table class="excel-table" style="width: 100%; border-collapse: collapse; font-size: 13px; background: white; box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);">
              <thead style="background: #f8f9fa;">
                <tr>
                  <th v-for="(col, idx) in currentSheetData.columns" :key="idx" style="padding: 12px; text-align: left; font-weight: 600; color: #2c3e50; border: 1px solid #e0e0e0; white-space: nowrap;">
                    {{ col }}
                  </th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="(row, rowIdx) in currentSheetData.data" :key="rowIdx" style="transition: background 0.2s;">
                  <td v-for="(cell, cellIdx) in row" :key="cellIdx" style="padding: 10px 12px; border: 1px solid #e0e0e0; color: #34495e;">
                    {{ cell !== null ? cell : '' }}
                  </td>
                </tr>
                </tbody>
              </table>
            </div>
            <div class="excel-info" style="margin-top: 12px; padding: 8px 12px; background: white; border-radius: 6px; font-size: 12px; color: #7f8c8d; text-align: center; box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);">
              {{ currentSheetData.rows }} 行 × {{ currentSheetData.cols }} 列
            </div>
          </div>
        </div>
      </div>
      
      <!-- TXT 预览 -->
      <div v-if="!showVisualization && currentFileType === 'text'" class="text-preview" style="width:100%; height:100%; display: flex; flex-direction: column; overflow-y: auto;">
        <div class="file-toolbar">
          <div class="toolbar-left">
            <button class="toolbar-btn" @click="$emit('close-preview')" title="返回列表">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
                <path d="M19 12H5M5 12L12 19M5 12L12 5" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
              返回
            </button>
            <div class="toolbar-sep"></div>
            <span class="file-title">{{ selectedPaperTitle }}</span>
          </div>
        </div>
        <div class="text-viewer" style="flex: 1; background: #f8f9fa;">
          <div class="text-container">
            <pre v-if="filePreviewContent" class="text-content">{{ filePreviewContent }}</pre>
            <p v-else class="loading-text">加载中...</p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, ref, toRefs, watchEffect } from 'vue'

const props = defineProps({
  visible: { type: Boolean, default: false },
  showVisualization: { type: Boolean, default: false },
  pdfExpanded: { type: Boolean, default: false },
  isDownloading: { type: Boolean, default: false },
  downloadProgress: { type: Number, default: 0 },
  downloadError: { type: String, default: '' },
  currentFileType: { type: String, default: 'pdf' },
  useIframeFallback: { type: Boolean, default: true },
  viewerSrc: { type: String, default: '' },
  pdfBlobUrl: { type: String, default: '' },
  selectedPaperTitle: { type: String, default: '' },
  filePreviewContent: { type: String, default: '' },
  excelData: { type: Object, default: null },
  currentExcelSheet: { type: Number, default: 0 }
})
const emit = defineEmits(['close-preview','viewer-loaded','register-pdf-container','register-preview-content','set-excel-sheet'])

const localViewerFrame = ref(null)
const localPdfContainer = ref(null)
const localPreviewContent = ref(null)

const radius = 52
const circumferenceVal = 2 * Math.PI * radius
const circumference = `${circumferenceVal}px`
const progressColor = '#3498db'
const dashOffset = computed(() => {
  const pct = Math.max(0, Math.min(100, props.downloadProgress))
  const val = circumferenceVal - (pct / 100) * circumferenceVal
  return `${val}px`
})

const currentSheetData = computed(() => {
  if (!props.excelData || !props.excelData.data) return null
  const sheetName = props.excelData.sheets[props.currentExcelSheet]
  return props.excelData.data[sheetName]
})

const emitViewerLoaded = () => {
  if (localViewerFrame.value) emit('viewer-loaded', localViewerFrame.value)
}

watchEffect(() => {
  if (localPdfContainer.value) emit('register-pdf-container', localPdfContainer.value)
  if (localPreviewContent.value) emit('register-preview-content', localPreviewContent.value)
})
</script>

<style scoped>
/* 预览容器内的加载样式 */
.pdf-loading { width: 100%; height: 100%; display: flex; align-items: center; justify-content: center; }
.circle-wrapper { position: relative; width: 140px; height: 140px; display: flex; flex-direction: column; align-items: center; justify-content: center; }
.progress-ring { transform: rotate(-90deg); }
.progress-ring__background, .progress-ring__progress { transition: stroke-dashoffset 0.2s ease; }
.progress-text { position: absolute; top: 50%; left: 50%; transform: translate(-50%, -60%); font-size: 20px; font-weight: 600; color: #2c3e50; }

.pdf-canvas-container { max-width: 1100px; margin: 0 auto; padding: 16px 0 24px; }

/* Excel 预览样式 */
.excel-content-wrapper { max-width: 1200px; margin: 0 auto; }
.excel-tab:hover { color: #2c3e50; }
.excel-tab.active { color: #3498db !important; border-bottom-color: #3498db !important; font-weight: 600; }
.excel-table tbody tr:hover { background: #f8f9fa; }

/* Word 预览样式 */
.word-container { max-width: 900px; margin: 0 auto; padding: 40px 60px; background: white; min-height: 100%; box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08); }
.word-content { color: #2c3e50; font-size: 15px; line-height: 1.8; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; }
.word-content :deep(p) { margin: 0 0 16px 0; text-align: justify; }
.word-content :deep(h1), .word-content :deep(h2), .word-content :deep(h3) { margin: 24px 0 16px 0; color: #1a1a1a; font-weight: 600; }
.word-content :deep(h1) { font-size: 28px; border-bottom: 2px solid #e0e0e0; padding-bottom: 8px; }
.word-content :deep(h2) { font-size: 22px; }
.word-content :deep(h3) { font-size: 18px; }
.word-content :deep(ul), .word-content :deep(ol) { margin: 12px 0; padding-left: 30px; }
.word-content :deep(li) { margin: 6px 0; }
.word-content :deep(table) { width: 100%; margin: 20px 0; border-collapse: collapse; box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1); }
.word-content :deep(th) { background: #f8f9fa; color: #2c3e50; font-weight: 600; padding: 12px; border: 1px solid #dee2e6; text-align: left; }
.word-content :deep(td) { padding: 10px 12px; border: 1px solid #dee2e6; color: #34495e; }
.word-content :deep(tr:hover) { background: #f8f9fa; }
.word-content :deep(strong), .word-content :deep(b) { font-weight: 600; color: #1a1a1a; }
.word-content :deep(em), .word-content :deep(i) { font-style: italic; }
.word-content :deep(blockquote) { margin: 16px 0; padding: 12px 20px; background: #f8f9fa; border-left: 4px solid #3498db; color: #555; }

/* TXT 预览样式 */
.text-container { max-width: 1000px; margin: 0 auto; padding: 32px 48px; background: white; min-height: 100%; box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08); }
.text-content { margin: 0; font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', 'Consolas', 'Courier New', monospace; font-size: 14px; line-height: 1.7; white-space: pre-wrap; word-wrap: break-word; color: #2c3e50; background: #fafbfc; padding: 24px; border-radius: 6px; border: 1px solid #e1e4e8; }

/* 加载文本样式 */
.loading-text { color: #95a5a6; text-align: center; padding: 40px; font-size: 14px; }

/* PDF下载错误样式 */
.download-error { display: flex; flex-direction: column; align-items: center; justify-content: center; height: 100%; padding: 40px; text-align: center; }
.download-error svg { margin-bottom: 24px; }
.download-error h3 { font-size: 18px; font-weight: 600; color: #e74c3c; margin: 0 0 12px 0; }
.download-error p { font-size: 14px; color: #7f8c8d; margin: 0; }

/* 文件预览工具栏样式 - 与PDF预览toolbar保持一致 */
.file-toolbar { height: 60px; display: flex; align-items: center; justify-content: space-between; padding: 0 12px; border-bottom: 1px solid #eee; background: #fff; position: sticky; top: 0; z-index: 10; gap: 12px; box-shadow: 0 1px 3px rgba(0, 0, 0, 0.06); }
.toolbar-left { display: flex; align-items: center; gap: 8px; flex: 1; min-width: 0; }
.toolbar-btn { height: 30px; padding: 0 10px; border: 1px solid #e3e6eb; background: #fff; border-radius: 6px; cursor: pointer; white-space: nowrap; font-size: 14px; display: flex; align-items: center; gap: 6px; color: #4b5563; transition: all 0.2s; }
.toolbar-btn:hover { background: #f8f9fa; border-color: #d0d5dd; }
.toolbar-btn svg { flex-shrink: 0; }
.toolbar-sep { width: 1px; height: 45px; background: #eee; margin: 0 6px; }
.file-title { color: #4b5563; font-size: 14px; font-weight: 500; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
</style>

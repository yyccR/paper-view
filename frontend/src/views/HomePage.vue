<template>
  <div class="home-page">
    <Header />
    <div class="main-background-container">
      <div class="background-images-wrapper">
        <div class="hero-background" ref="heroBackground">
          <img 
            v-for="(image, index) in displayImages" 
            :key="index"
            :src="`/assets/index_images/${image}`"
            :class="`bg-image bg-${index + 1}`"
            alt="Background"
            loading="lazy"
            decoding="async"
          >
        </div>
      </div>
      <HeroSection 
        @search="handleSearch" 
        @upload="handleUpload"
        :display-images="displayImages"
      />
      <FeaturesSection />
    </div>
    
    <Footer />
    
    <!-- 隐藏的文件上传输入 -->
    <input 
      type="file" 
      ref="fileInput"
      accept=".pdf,.doc,.docx,.xls,.xlsx,.csv,.txt" 
      style="display: none;"
      @change="handleFileChange"
    >
    
    <!-- 文件上传Loading弹窗 -->
    <Teleport to="body">
      <div v-if="showUploadModal" class="upload-modal-overlay">
        <div class="upload-modal">
          <div class="upload-modal-content">
            <div class="circle-wrapper">
              <svg class="progress-ring" width="120" height="120">
                <circle class="progress-ring__background" stroke="#ecf0f1" stroke-width="10" fill="transparent" r="52" cx="60" cy="60" />
                <circle class="progress-ring__progress" stroke="#3498db" stroke-width="10" fill="transparent" r="52" cx="60" cy="60"
                        :style="{ strokeDasharray: circumference, strokeDashoffset: dashOffset }" stroke-linecap="round" />
              </svg>
              <div class="progress-text">{{ uploadProgress }}%</div>
            </div>
            <p class="upload-modal-text">正在上传文件...</p>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { apiService } from '@/api'

import Header from '@/components/Header.vue'
import HeroSection from '@/components/HeroSection.vue'
import FeaturesSection from '@/components/FeaturesSection.vue'
import Footer from '@/components/Footer.vue'

const router = useRouter()

const showUploadModal = ref(false)
const uploadProgress = ref(0)
const fileInput = ref(null)
const displayImages = ref([])
const heroBackground = ref(null)

// 进度环参数
const radius = 52
const circumferenceVal = 2 * Math.PI * radius
const circumference = `${circumferenceVal}px`
const dashOffset = computed(() => {
  const pct = Math.max(0, Math.min(100, uploadProgress.value))
  const val = circumferenceVal - (pct / 100) * circumferenceVal
  return `${val}px`
})

const handleSearch = (query) => {
  router.push(`/workspace?q=${encodeURIComponent(query)}`)
}

const handleUpload = () => {
  fileInput.value.click()
}

const handleFileChange = async (event) => {
  const file = event.target.files[0]
  if (!file) return
  
  // 验证文件类型
  const allowedExtensions = ['.pdf', '.doc', '.docx', '.xls', '.xlsx', '.csv', '.txt']
  const fileExtension = '.' + file.name.split('.').pop().toLowerCase()
  
  if (!allowedExtensions.includes(fileExtension)) {
    alert('不支持的文件类型。支持的格式：PDF, Word, Excel, CSV, TXT')
    return
  }
  
  // 显示上传弹窗
  showUploadModal.value = true
  uploadProgress.value = 0
  
  try {
    // 上传文件
    const response = await apiService.uploadFile(file, (progressEvent) => {
      if (progressEvent.total) {
        uploadProgress.value = Math.round((progressEvent.loaded * 100) / progressEvent.total)
      }
    })
    
    if (response.success) {
      // 上传成功，存储文件信息并跳转到 WorkspacePage
      sessionStorage.setItem('uploadedFileInfo', JSON.stringify(response))
      router.push('/workspace')
    } else {
      showUploadModal.value = false
      alert('上传失败：' + (response.error || '未知错误'))
    }
  } catch (error) {
    console.error('Upload error:', error)
    showUploadModal.value = false
    alert('上传失败，请重试')
  }
  
  // 清空 input
  event.target.value = ''
}

const loadBackgroundImages = async () => {
  try {
    const data = await apiService.getIndexImages()
    if (data.images && data.images.length > 0) {
      const images = data.images
      const screenWidth = window.innerWidth
      const imageWidth = 350 + 10
      const imagesPerRow = Math.floor((screenWidth - 120) / imageWidth)
      const targetCount = Math.max(imagesPerRow * 3, 18) // Increased to cover more area
      
      if (images.length < targetCount) {
        for (let i = 0; i < targetCount; i++) {
          const randomIndex = Math.floor(Math.random() * images.length)
          displayImages.value.push(images[randomIndex])
        }
      } else {
        displayImages.value = [...images]
      }
    }
  } catch (error) {
    console.error('加载背景图片失败:', error)
  }
}

onMounted(() => {
  loadBackgroundImages()
})
</script>

<style scoped>
/* 样式已在main.js中全局导入 */
.home-page {
  width: 100%;
  min-height: 100vh;
}

.main-background-container {
  position: relative;
  min-height: 100vh;
}

.background-images-wrapper {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 0;
  overflow: hidden;
}

.hero-background {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 0;
  opacity: 0.3;
  padding: 40px 60px;
  overflow: hidden;
  column-count: 5;
  column-gap: 10px;
}

.bg-image {
  width: 100%;
  height: auto;
  border-radius: 20px;
  border: 1px solid rgba(255, 255, 255, 0.24);
  backdrop-filter: blur(20px);
  object-fit: cover;
  -webkit-mask-image: linear-gradient(to bottom, rgba(0, 0, 0, 0.8) 0%, rgba(0, 0, 0, 0.5) 100%);
  mask-image: linear-gradient(to bottom, rgba(0, 0, 0, 0.8) 0%, rgba(0, 0, 0, 0.5) 100%);
  margin-bottom: 10px;
  display: block;
  break-inside: avoid;
  page-break-inside: avoid;
}

/* 上传弹窗样式 */
.upload-modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 10000;
  backdrop-filter: blur(4px);
}

.upload-modal {
  background: white;
  border-radius: 12px;
  padding: 40px;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.2);
  animation: modalFadeIn 0.3s ease;
}

@keyframes modalFadeIn {
  from {
    opacity: 0;
    transform: scale(0.9);
  }
  to {
    opacity: 1;
    transform: scale(1);
  }
}

.upload-modal-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 20px;
}

.circle-wrapper {
  position: relative;
  width: 140px;
  height: 140px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}

.progress-ring {
  transform: rotate(-90deg);
}

.progress-ring__background,
.progress-ring__progress {
  transition: stroke-dashoffset 0.2s ease;
}

.progress-text {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  font-size: 20px;
  font-weight: 600;
  color: #2c3e50;
}

.upload-modal-text {
  font-size: 16px;
  color: #2c3e50;
  margin: 0;
  font-weight: 500;
}

@media (max-width: 1200px) {
  .hero-background {
    column-count: 4;
  }
}

@media (max-width: 768px) {
  .hero-background {
    column-count: 2;
  }
}
</style>

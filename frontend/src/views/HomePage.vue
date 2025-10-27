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
        :show-progress="showProgress"
        :progress="uploadProgress"
        :progress-text="progressText"
        :display-images="displayImages"
      />
      <FeaturesSection />
    </div>
    
    <Footer />
    
    <!-- 隐藏的文件上传输入 -->
    <input 
      type="file" 
      ref="fileInput"
      accept=".pdf" 
      style="display: none;"
      @change="handleFileChange"
    >
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { apiService } from '@/api'

import Header from '@/components/Header.vue'
import HeroSection from '@/components/HeroSection.vue'
import FeaturesSection from '@/components/FeaturesSection.vue'
import Footer from '@/components/Footer.vue'

const router = useRouter()

const showProgress = ref(false)
const uploadProgress = ref(0)
const progressText = ref('处理中...')
const fileInput = ref(null)
const displayImages = ref([])
const heroBackground = ref(null)

const handleSearch = (query) => {
  router.push(`/workspace?q=${encodeURIComponent(query)}`)
}

const handleUpload = () => {
  fileInput.value.click()
}

const handleFileChange = (event) => {
  const file = event.target.files[0]
  if (file && file.type === 'application/pdf') {
    sessionStorage.setItem('pendingUpload', 'true')
    sessionStorage.setItem('uploadFileName', file.name)
    router.push('/workspace')
  } else {
    alert('请上传PDF文件')
  }
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
  -webkit-column-break-inside: avoid;
  will-change: transform;
  content-visibility: auto;
}

@media (min-width: 1600px) {
  .hero-background {
    column-count: 6;
  }
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

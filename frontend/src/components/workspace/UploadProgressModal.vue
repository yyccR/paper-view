<template>
  <Teleport to="body">
    <div v-if="visible" class="upload-modal-overlay" @click.self="">
      <div class="upload-modal">
        <div class="upload-modal-content">
          <div class="circle-wrapper">
            <svg class="progress-ring" width="120" height="120">
              <circle class="progress-ring__background" stroke="#ecf0f1" stroke-width="10" fill="transparent" r="52" cx="60" cy="60" />
              <circle class="progress-ring__progress" :stroke="progressColor" stroke-width="10" fill="transparent" r="52" cx="60" cy="60"
                      :style="{ strokeDasharray: circumference, strokeDashoffset: dashOffset }" stroke-linecap="round" />
            </svg>
            <div class="progress-text">{{ progress }}%</div>
          </div>
          <p class="upload-modal-text">正在上传文件...</p>
        </div>
      </div>
    </div>
  </Teleport>
</template>
<script setup>
import { computed } from 'vue'

const props = defineProps({
  visible: { type: Boolean, default: false },
  progress: { type: Number, default: 0 }
})
const radius = 52
const circumferenceVal = 2 * Math.PI * radius
const circumference = `${circumferenceVal}px`
const progressColor = '#3498db'
const dashOffset = computed(() => {
  const pct = Math.max(0, Math.min(100, props.progress))
  const val = circumferenceVal - (pct / 100) * circumferenceVal
  return `${val}px`
})
</script>

<style scoped>
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
  from { opacity: 0; transform: scale(0.9); }
  to { opacity: 1; transform: scale(1); }
}

.upload-modal-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 20px;
}

.upload-modal-text {
  font-size: 16px;
  color: #2c3e50;
  margin: 0;
  font-weight: 500;
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
.progress-ring { transform: rotate(-90deg); }
.progress-ring__background,
.progress-ring__progress { transition: stroke-dashoffset 0.2s ease; }
.progress-text {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -60%);
  font-size: 20px;
  font-weight: 600;
  color: #2c3e50;
}
</style>

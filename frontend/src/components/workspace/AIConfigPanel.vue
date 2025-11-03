<template>
  <div class="ai-config-panel" :class="{ active: active }">
    <div class="ai-config-header">
      <h3>{{ $t('aiConfig.title') }}</h3>
      <button class="close-btn" @click="$emit('close')">&times;</button>
    </div>
    <div class="ai-config-content">
      <div v-if="currentAIConfig" class="current-model-info">
        <div class="info-row">
          <div class="info-label">{{ $t('aiConfig.currentModel') }}</div>
          <div class="current-badge">Active</div>
        </div>
        <div class="info-value">
          <span class="provider-tag">{{ getProviderDisplayName(currentAIConfig.provider) }}</span>
          <span class="model-tag">{{ currentAIConfig.model_name }}</span>
        </div>
      </div>

      <div class="ai-providers-grid">
        <div 
          v-for="(provider, key) in aiProviders" 
          :key="key"
          class="provider-card"
          :class="{ expanded: expandedProviders.has(key), 'has-selected': hasSelectedModel(key) }"
        >
          <div class="provider-header" @click="$emit('toggle-provider', key)">
            <div class="provider-info">
              <div class="provider-logo">
                <img :src="`/assets/logos/${provider.logo}.png`" :alt="provider.name" @error="handleLogoError">
              </div>
              <div class="provider-details">
                <span class="provider-name">{{ provider.name }}</span>
                <span class="model-count">{{ provider.models.length }} {{ $t('aiConfig.models') }}</span>
              </div>
            </div>
            <div class="provider-actions">
              <span v-if="hasSelectedModel(key)" class="active-indicator">●</span>
              <svg class="expand-icon" :class="{ rotated: expandedProviders.has(key) }" width="20" height="20" viewBox="0 0 24 24" fill="none">
                <path d="M6 9L12 15L18 9" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
            </div>
          </div>
          <transition name="expand-down">
            <div v-show="expandedProviders.has(key)" class="models-list">
              <div 
                v-for="model in provider.models" 
                :key="model.id"
                class="model-item"
                @click="$emit('select-model', { provider: key, model })"
                :class="{ selected: isModelSelected(key, model.id) }"
              >
                <div class="model-info">
                  <div class="model-name">{{ model.name }}</div>
                  <div class="model-description">{{ model.description }}</div>
                </div>
                <div v-if="isModelSelected(key, model.id)" class="selected-badge">✓</div>
              </div>
            </div>
          </transition>
        </div>

        <div class="provider-card custom-model-card" :class="{ expanded: showCustomModelForm }">
          <div class="provider-header" @click="$emit('toggle-custom-form')">
            <div class="provider-info">
              <div class="provider-logo custom-logo">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
                  <path d="M12 5V19M5 12H19" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
                </svg>
              </div>
              <div class="provider-details">
                <span class="provider-name">{{ $t('aiConfig.customModel.title') }}</span>
                <span class="model-count">{{ $t('aiConfig.customModel.subtitle') }}</span>
              </div>
            </div>
            <div class="provider-actions">
              <svg class="expand-icon" :class="{ rotated: showCustomModelForm }" width="20" height="20" viewBox="0 0 24 24" fill="none">
                <path d="M6 9L12 15L18 9" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
            </div>
          </div>

          <div v-if="showCustomModelForm" class="custom-model-form">
            <div class="form-group">
              <label>{{ $t('aiConfig.customModel.providerName') }}</label>
              <input v-model="customModel.provider" type="text" :placeholder="$t('aiConfig.customModel.providerPlaceholder')" class="form-input" />
            </div>
            <div class="form-group">
              <label>{{ $t('aiConfig.customModel.modelName') }}</label>
              <input v-model="customModel.modelName" type="text" :placeholder="$t('aiConfig.customModel.modelPlaceholder')" class="form-input" />
            </div>
            <div class="form-group">
              <label>{{ $t('aiConfig.customModel.apiBase') }}</label>
              <input v-model="customModel.apiBase" type="text" :placeholder="$t('aiConfig.customModel.apiBasePlaceholder')" class="form-input" />
            </div>
            <div class="form-group">
              <label>{{ $t('aiConfig.customModel.apiKey') }}</label>
              <input v-model="customModel.apiKey" type="password" :placeholder="$t('aiConfig.customModel.apiKeyPlaceholder')" class="form-input" />
            </div>
            <div class="form-group">
              <label>{{ $t('aiConfig.customModel.description') }}</label>
              <textarea v-model="customModel.description" :placeholder="$t('aiConfig.customModel.descriptionPlaceholder')" class="form-textarea" rows="2"></textarea>
            </div>
            <div class="form-actions">
              <button @click="$emit('save-custom-model')" class="btn-primary" :disabled="!isCustomModelValid">
                {{ $t('aiConfig.customModel.save') }}
              </button>
              <button @click="$emit('reset-custom-model')" class="btn-secondary">
                {{ $t('aiConfig.customModel.reset') }}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, toRefs } from 'vue'

const props = defineProps({
  active: { type: Boolean, default: false },
  aiProviders: { type: Object, default: () => ({}) },
  expandedProviders: { type: Object, required: true }, // Set
  currentAIConfig: { type: Object, default: null },
  showCustomModelForm: { type: Boolean, default: false },
  customModel: { type: Object, required: true },
  isCustomModelValid: { type: Boolean, default: false }
})
const emit = defineEmits(['close','toggle-provider','select-model','toggle-custom-form','save-custom-model','reset-custom-model'])

const { active, aiProviders, expandedProviders, currentAIConfig, showCustomModelForm, customModel, isCustomModelValid } = toRefs(props)

const getProviderDisplayName = (provider) => {
  const names = { gpt: 'GPT', claude: 'Claude', qwen: '通义千问', doubao: '豆包', gemini: 'Gemini' }
  return names[provider] || provider
}

const isModelSelected = (provider, modelId) => {
  return currentAIConfig.value && currentAIConfig.value.provider === provider && currentAIConfig.value.model_name === modelId
}

const hasSelectedModel = (provider) => {
  return currentAIConfig.value && currentAIConfig.value.provider === provider
}

const handleLogoError = (e) => {
  e.target.style.display = 'none'
}
</script>

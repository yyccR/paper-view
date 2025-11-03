<template>
  <div 
    v-if="visible && selectionText"
    class="selection-actions"
    :style="{ top: position.top + 'px', left: position.left + 'px' }"
    @mousedown.stop="$emit('mousedown')"
  >
    <button class="sel-btn" @click="$emit('translate')" :title="$t('selection.translate')">
      {{ $t('selection.translate') }}
    </button>
    <div class="lang-selector" @click.stop>
      <button class="lang-btn" @click="$emit('toggle-lang-menu')" :title="$t('selection.language')">
        {{ $t(`selection.lang.${selectedLang}`) }}
        <svg class="chevron" width="12" height="12" viewBox="0 0 24 24"><path d="M6 9l6 6 6-6" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>
      </button>
      <ul v-if="showLangMenu" class="lang-menu">
        <li 
          v-for="code in langCodes" 
          :key="code" 
          :class="{ active: code === selectedLang }"
          @click="$emit('select-lang', code)"
        >{{ $t(`selection.lang.${code}`) }}</li>
      </ul>
    </div>
    <button class="sel-btn" @click="$emit('ask')" :title="$t('selection.ask')">
      {{ $t('selection.ask') }}
    </button>
    <button class="sel-btn" @click="$emit('copy')" :title="$t('selection.copy')">
      {{ $t('selection.copy') }}
    </button>
  </div>
</template>
<script setup>
const props = defineProps({
  visible: { type: Boolean, default: false },
  position: { type: Object, required: true },
  selectionText: { type: String, default: '' },
  selectedLang: { type: String, default: 'zh' },
  langCodes: { type: Array, default: () => ['zh','en','ja','ko','es'] },
  showLangMenu: { type: Boolean, default: false }
})
const emit = defineEmits(['translate','ask','copy','toggle-lang-menu','select-lang','mousedown'])
</script>

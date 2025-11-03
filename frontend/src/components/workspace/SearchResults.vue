<template>
  <div class="search-results">
    <h3 class="results-title">{{ $t('workspace.searchResults.title') }}</h3>
    <div class="results-list">
      <div 
        v-for="result in results" 
        :key="result.title" 
        class="result-item"
        @click="$emit('select-paper', result)"
      >
        <h3 class="result-title">{{ result.title }}</h3>
        <p class="result-authors">{{ result.authors }}</p>
        <p class="result-abstract">{{ result.abstract }}</p>
        <div class="result-meta">
          <span>{{ $t('workspace.searchResults.year', { year: result.year }) }}</span>
          <span>{{ $t('workspace.searchResults.citations', { count: result.citations }) }}</span>
        </div>
      </div>
    </div>
    <div class="pagination" v-if="totalPages > 1">
      <span class="pagination-info">{{ $t('workspace.pagination.showing') }} {{ startItem }}-{{ endItem }} {{ $t('workspace.pagination.of') }} {{ $t('workspace.pagination.total', { total: total }) }}</span>
      <button class="pagination-btn" @click="$emit('goto-page', 1)" :disabled="currentPage === 1">{{ $t('workspace.pagination.first') }}</button>
      <button class="pagination-btn" @click="$emit('goto-page', currentPage - 1)" :disabled="currentPage === 1">{{ $t('workspace.pagination.previous') }}</button>
      <div class="pagination-pages">
        <button 
          v-for="page in pageButtons" 
          :key="page"
          class="pagination-btn" 
          :class="{ active: page === currentPage }"
          @click="$emit('goto-page', page)"
        >
          {{ page }}
        </button>
      </div>
      <button class="pagination-btn" @click="$emit('goto-page', currentPage + 1)" :disabled="currentPage === totalPages">{{ $t('workspace.pagination.next') }}</button>
      <button class="pagination-btn" @click="$emit('goto-page', totalPages)" :disabled="currentPage === totalPages">{{ $t('workspace.pagination.last') }}</button>
    </div>
  </div>
</template>
<script setup>
const props = defineProps({
  results: { type: Array, default: () => [] },
  total: { type: Number, default: 0 },
  currentPage: { type: Number, default: 1 },
  totalPages: { type: Number, default: 1 },
  pageButtons: { type: Array, default: () => [] },
  startItem: { type: Number, default: 0 },
  endItem: { type: Number, default: 0 }
})
const emit = defineEmits(['select-paper','goto-page'])
</script>

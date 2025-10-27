<template>
  <section class="features" id="features">
    <div class="container">
      <h2 class="section-title">{{ $t('features.sectionTitle') }}</h2>
      <div class="feature-grid">
        <div class="feature-card">
          <div class="feature-icon">
            <svg width="48" height="48" viewBox="0 0 24 24" fill="none">
              <path d="M9 12H15M9 16H15M17 21H7C5.89543 21 5 20.1046 5 19V5C5 3.89543 5.89543 3 7 3H12.5858C12.851 3 13.1054 3.10536 13.2929 3.29289L18.7071 8.70711C18.8946 8.89464 19 9.149 19 9.41421V19C19 20.1046 18.1046 21 17 21Z" stroke="currentColor" stroke-width="2"/>
            </svg>
          </div>
          <h3>{{ $t('features.arxiv.title') }}</h3>
          <p style="white-space: pre-line;">{{ $t('features.arxiv.description') }}</p>
        </div>
        
        <div class="feature-card">
          <div class="feature-icon">
            <svg width="48" height="48" viewBox="0 0 24 24" fill="none">
              <path d="M9.5 2C13.0899 2 16 4.91015 16 8.5C16 10.0968 15.4217 11.5596 14.4595 12.6833L21.5 19.7238L19.7238 21.5L12.6833 14.4595C11.5596 15.4217 10.0968 16 8.5 16C4.91015 16 2 13.0899 2 9.5C2 5.91015 4.91015 3 8.5 3Z" stroke="currentColor" stroke-width="2"/>
            </svg>
          </div>
          <h3>{{ $t('features.visualization.title') }}</h3>
          <p style="white-space: pre-line;">{{ $t('features.visualization.description') }}</p>
        </div>
        
        <div class="feature-card">
          <div class="feature-icon">
            <svg width="48" height="48" viewBox="0 0 24 24" fill="none">
              <path d="M13 2L3 14H12L11 22L21 10H12L13 2Z" stroke="currentColor" stroke-width="2" stroke-linejoin="round"/>
            </svg>
          </div>
          <h3>{{ $t('features.realtime.title') }}</h3>
          <p style="white-space: pre-line;">{{ $t('features.realtime.description') }}</p>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup>
</script>

<style scoped>
/* Features样式已在全局CSS中定义 */
</style>

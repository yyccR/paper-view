<template>
  <footer class="footer" id="about">
    <div class="container">
      <div class="footer-content">
        <div class="footer-section">
          <h4>Paper View</h4>
          <p style="white-space: pre-line;">{{ $t('footer.description') }}</p>
        </div>
        <div class="footer-section">
          <h4>{{ $t('footer.functionsTitle') }}</h4>
          <a href="#features">{{ $t('footer.arxivSupport') }}</a>
          <a href="#features">{{ $t('footer.paperVisualization') }}</a>
          <a href="#features">{{ $t('footer.realtimeUpdate') }}</a>
        </div>
        <div class="footer-section">
          <h4>{{ $t('footer.supportTitle') }}</h4>
          <a href="#">{{ $t('footer.helpCenter') }}</a>
          <a href="#">{{ $t('footer.apiDocs') }}</a>
          <a href="#">{{ $t('footer.contactUs') }}</a>
        </div>
      </div>
      <div class="footer-bottom">
        <p>{{ $t('footer.copyright') }}</p>
      </div>
    </div>
  </footer>
</template>

<script setup>
</script>

<style scoped>
/* Footer样式已在全局CSS中定义 */
</style>

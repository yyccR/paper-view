<template>
  <div class="user-panel" :class="{ active: active }">
    <div class="user-info">
      <img src="/default-avatar.svg" alt="用户头像" class="user-avatar">
      <div class="user-details">
        <h4>{{ $t('workspace.user.guestUser') }}</h4>
        <p>{{ $t('workspace.user.notLoggedIn') }}</p>
      </div>
    </div>
    <div class="user-menu">
      <a href="#profile" class="menu-item">{{ $t('workspace.user.profile') }}</a>
      <a href="#settings" class="menu-item">{{ $t('workspace.user.settings') }}</a>
      <div class="menu-divider"></div>
      <a href="#login" class="menu-item">{{ $t('workspace.user.login') }}</a>
    </div>
  </div>
</template>
<script setup>
const props = defineProps({ active: { type: Boolean, default: false } })
</script>

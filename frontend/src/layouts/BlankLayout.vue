<template>
  <div class="blank-layout">
    <router-view />
  </div>
</template>

<script setup lang="ts">
</script>

<style scoped>
/* 纯全屏容器：登录页 / 沉浸式复习页自行决定内部布局 */
.blank-layout {
  min-height: 100vh;
}
</style>

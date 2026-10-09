<template>
  <div class="card placeholder">
    <svg class="icon ph-icon" aria-hidden="true"><use href="#i-library" /></svg>
    <h2>{{ title }}</h2>
    <p>这个模块正在建设中，里程碑 M2 起陆续落地。</p>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()
const title = computed(() => (route.meta.title as string) || '模块')
</script>

<style scoped>
.placeholder {
  padding: 48px;
  text-align: center;
  max-width: 560px;
  margin: 40px auto;
}
.ph-icon {
  width: 44px;
  height: 44px;
  margin: 0 auto;
  color: var(--ink3);
}
h2 {
  font-size: 22px;
  margin-top: 12px;
  letter-spacing: -0.5px;
}
p {
  color: var(--ink2);
  margin-top: 8px;
  font-size: 14px;
}
</style>

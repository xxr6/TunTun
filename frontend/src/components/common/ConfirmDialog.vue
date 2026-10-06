<template>
  <Transition name="confirm">
    <div v-if="visible" class="cd-mask" @click.self="onCancel">
      <div class="card cd-card" role="dialog" aria-modal="true" :aria-label="title">
        <div class="cd-ic" :class="{ danger }" aria-hidden="true">
          <svg class="icon"><use :href="danger ? '#i-close' : '#i-check'" /></svg>
        </div>
        <h3 class="cd-title">{{ title }}</h3>
        <p class="cd-msg">{{ message }}</p>
        <div class="cd-actions">
          <button class="btn" @click="onCancel">{{ cancelText }}</button>
          <button class="btn" :class="danger ? 'cd-danger' : 'btn-primary'" @click="onConfirm">{{ confirmText }}</button>
        </div>
      </div>
    </div>
  </Transition>
</template>

<script setup lang="ts">
/** 贴纸风二次确认弹窗：替代浏览器 confirm()，全站复用。 */
withDefaults(defineProps<{
  visible: boolean
  title: string
  message: string
  confirmText?: string
  cancelText?: string
  danger?: boolean
}>(), {
  confirmText: '确认',
  cancelText: '取消',
  danger: false,
})

const emit = defineEmits<{ confirm: []; cancel: [] }>()

function onConfirm() {
  emit('confirm')
}
function onCancel() {
  emit('cancel')
}
</script>

<style scoped>
.cd-mask {
  position: fixed; inset: 0; z-index: 120;
  background: rgba(10, 7, 4, 0.48);
  display: flex; align-items: center; justify-content: center; padding: 20px;
}
.cd-card {
  width: min(360px, 100%);
  padding: 26px 24px 22px;
  text-align: center;
  box-shadow: var(--pop-lg);
}
.cd-ic {
  width: 52px; height: 52px; margin: 0 auto 12px; border-radius: 16px;
  display: flex; align-items: center; justify-content: center;
  background: var(--mint-l); color: var(--mint-d); border: 2.5px solid var(--line);
}
.cd-ic .icon { width: 24px; height: 24px; }
.cd-ic.danger { background: var(--berry-l); color: var(--berry); }
.cd-title { font-size: 17px; font-weight: 800; letter-spacing: -0.3px; }
.cd-msg { color: var(--ink2); font-size: 13.5px; margin-top: 6px; line-height: 1.6; }
.cd-actions { display: flex; gap: 10px; justify-content: center; margin-top: 18px; }
.cd-danger { background: var(--berry); color: var(--onfill); border-color: var(--line); }

/* 进出场 */
.confirm-enter-active { transition: opacity 0.22s var(--ease-out); }
.confirm-enter-active .cd-card { animation: cdIn 0.3s var(--ease-out-quart) both; }
.confirm-leave-active { transition: opacity 0.16s ease; }
.confirm-enter-from, .confirm-leave-to { opacity: 0; }
@keyframes cdIn {
  from { opacity: 0; transform: translateY(14px) scale(0.95); }
  to { opacity: 1; transform: none; }
}
</style>

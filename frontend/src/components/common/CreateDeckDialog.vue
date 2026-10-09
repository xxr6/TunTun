<template>
  <div class="deck-mask" @click.self="$emit('close')">
    <form class="deck-dialog card" @submit.prevent="create">
      <h3>新建卡组</h3>
      <p>创建后即可将卡片存入这个卡组。</p>
      <label>卡组名称<input v-model="name" maxlength="100" autofocus placeholder="例如：英语词根" /></label>
      <label>说明（可选）<input v-model="description" maxlength="255" placeholder="这个卡组用来学什么" /></label>
      <p v-if="error" class="deck-error">{{ error }}</p>
      <div class="deck-actions">
        <button type="button" class="btn" @click="$emit('close')">取消</button>
        <button type="submit" class="btn btn-primary" :disabled="saving || !name.trim()">{{ saving ? '创建中…' : '创建并选用' }}</button>
      </div>
    </form>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { decksApi } from '@/api/decks'
import type { Deck } from '@/types/api'

const emit = defineEmits<{ close: []; created: [deck: Deck] }>()
const name = ref('')
const description = ref('')
const saving = ref(false)
const error = ref('')

async function create() {
  const trimmed = name.value.trim()
  if (!trimmed || saving.value) return
  saving.value = true
  error.value = ''
  try {
    const res = await decksApi.create({ name: trimmed, description: description.value.trim() })
    emit('created', res.data)
  } catch (e: any) {
    error.value = e?.response?.data?.message || '创建失败，请重试'
  } finally {
    saving.value = false
  }
}
</script>

<style scoped>
.deck-mask { position: fixed; inset: 0; z-index: 110; display: flex; align-items: center; justify-content: center; padding: 20px; background: rgba(10, 7, 4, .5); }
.deck-dialog { width: min(420px, 100%); padding: 26px; background: var(--paper); }
h3 { font-size: 19px; margin: 0 0 5px; }
p { color: var(--ink2); font-size: 13px; margin: 0 0 18px; }
label { display: block; margin: 0 0 14px; color: var(--ink2); font-size: 12.5px; font-weight: 750; }
input { display: block; width: 100%; padding: 10px 12px; margin-top: 6px; border: 2.5px solid var(--line); border-radius: 12px; outline: none; background: var(--cream); color: var(--ink); font: inherit; font-size: 14px; }
input:focus { border-color: var(--orange); }
.deck-error { color: var(--berry); margin-bottom: 10px; }
.deck-actions { display: flex; justify-content: flex-end; gap: 10px; }
</style>

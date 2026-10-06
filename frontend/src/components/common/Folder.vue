<template>
  <div class="fd-scale" :style="{ transform: `scale(${size})` }">
    <div class="fd" :class="{ open }" @click="toggle">
      <div class="fd-back">
        <span class="fd-tab"></span>
        <div v-for="(item, i) in papers" :key="i" class="fd-paper" :class="`fd-paper-${i + 1}`" :style="paperStyle(i)">
          <span v-if="item" class="fd-paper-text">{{ item }}</span>
        </div>
        <div class="fd-flap fd-flap-front"></div>
        <div class="fd-flap fd-flap-right"></div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
/** 贴纸风文件夹：结构移植自 vue-bits Folder（背板 + 三张纸 + 双 skew 前盖开合），
    视觉按三主题贴纸系统重写——焦糖黄文件夹 + 描边 + 硬投影。
    有内容的便签纸叠在前盖之上（合上也能读到预览文字），打开时飞出。 */
import { computed, ref, watch } from 'vue'

interface Props {
  /** 文件夹颜色，走 CSS 变量如 'var(--ham)' */
  color?: string
  size?: number
  /** 纸张内容（最多 3 张），字符串会渲染为预览文字 */
  items?: (string | null)[]
  disabled?: boolean
  /** 受控开关：传入时由父级控制开合（弹窗开→文件夹开，弹窗关→文件夹合） */
  open?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  color: 'var(--ham)',
  size: 1,
  items: () => [],
  disabled: false,
  open: undefined,
})
const emit = defineEmits<{ select: [] }>()

const innerOpen = ref(false)
const open = computed(() => (props.open !== undefined ? props.open : innerOpen.value))
const maxItems = 3

watch(
  () => props.open,
  (v) => {
    if (v !== undefined) innerOpen.value = v
  },
)

const papers = computed(() => {
  const result = props.items.slice(0, maxItems)
  while (result.length < maxItems) result.push(null)
  return result
})

const toggle = () => {
  if (props.disabled) return
  if (props.open === undefined) innerOpen.value = !innerOpen.value
  emit('select')
}

const paperStyle = (i: number) => {
  const mix = ['94%', '96%', '100%'][i]
  const base = {
    backgroundColor: i === 2 ? 'var(--paper)' : `color-mix(in srgb, var(--paper) ${mix}, var(--ink))`,
  }
  if (!open.value) return base
  const transforms = [
    'translate(-78%, -108%) rotate(-12deg)',
    'translate(14%, -108%) rotate(12deg)',
    'translate(-50%, -150%) rotate(4deg)',
  ]
  return { ...base, transform: transforms[i] }
}
</script>

<style scoped>
.fd-scale { width: 100px; height: 84px; display: inline-block; }

.fd {
  position: relative;
  display: inline-block;
  cursor: pointer;
  filter: drop-shadow(3px 3px 0 var(--line));
  transition: transform 0.24s var(--ease-out-quart);
}
.fd:not(.open):hover { transform: translateY(-4px); }
.fd.open { transform: translateY(-6px); }

/* 背板 + 左上标签耳 */
.fd-back {
  position: relative;
  width: 100px;
  height: 80px;
  border-radius: 0 10px 10px 10px;
  background: color-mix(in srgb, var(--fd-color, var(--ham)) 88%, var(--ink));
  border: 2.5px solid var(--line);
}
.fd-tab {
  position: absolute;
  z-index: 0;
  bottom: 98%;
  left: -2.5px;
  width: 30px;
  height: 12px;
  border-radius: 5px 5px 0 0;
  background: color-mix(in srgb, var(--fd-color, var(--ham)) 88%, var(--ink));
  border: 2.5px solid var(--line);
  border-bottom: none;
}
.fd-back { --fd-color: var(--ham); }

/* 三张纸：第一张是「便签」——叠在前盖之上，合着也能读到预览文字；打开时飞出 */
.fd-paper {
  position: absolute;
  z-index: 20;
  bottom: 10%;
  left: 50%;
  border-radius: 8px;
  border: 2px solid var(--line);
  overflow: hidden;
  transform: translateX(-50%) translateY(10%);
  transition: all 0.3s var(--ease-out-quart);
}
.fd-paper:nth-child(2) { width: 76%; height: 58%; bottom: 8%; z-index: 40; }
.fd-paper:nth-child(3) { width: 80%; height: 70%; z-index: 18; bottom: 12%; }
.fd-paper:nth-child(4) { width: 90%; height: 60%; z-index: 19; bottom: 14%; }
.fd-paper:nth-child(2) { transform: translateX(-50%) translateY(0); }

.fd-paper-text {
  position: absolute;
  inset: 0;
  display: -webkit-box;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 3;
  overflow: hidden;
  padding: 5px 7px;
  font-size: 10px;
  line-height: 1.35;
  color: var(--ink2);
  font-weight: 650;
  word-break: break-all;
}

/* 双片前盖：开合时向两侧 skew 倒下 */
.fd-flap {
  position: absolute;
  z-index: 30;
  width: 100%;
  height: 100%;
  transform-origin: bottom;
  background: var(--fd-color, var(--ham));
  border: 2.5px solid var(--line);
  border-radius: 5px 10px 10px 10px;
  transition: all 0.3s var(--ease-out-quart);
}
.fd-flap-front { transform: skew(0) scaleY(1); }
.fd-flap-right { transform: skew(0) scaleY(1); }
.fd.open .fd-flap-front { transform: skew(15deg) scaleY(0.6); }
.fd.open .fd-flap-right { transform: skew(-15deg) scaleY(0.6); }
.fd:not(.open):hover .fd-flap-front { transform: skew(15deg) scaleY(0.6); }
.fd:not(.open):hover .fd-flap-right { transform: skew(-15deg) scaleY(0.6); }

@media (prefers-reduced-motion: reduce) {
  .fd, .fd-paper, .fd-flap { transition: none !important; }
  .fd:not(.open):hover { transform: none; }
}
</style>

import { onBeforeUnmount, ref } from 'vue'

/**
 * 弹簧物理翻卡（迁移自 demo 的 rySpring）。
 * 用 rAF + 半隐式欧拉积分驱动 rotateY，替代 CSS transition——
 * 因为 transition 无法从「当前任意角度」起步并携带释放速度。
 *
 * 关键（demo 血泪教训）：
 * - 首帧只做时间轴对齐，不积分（last=0 是「下次回调对齐时间」的信号），否则起步顿挫。
 * - dt 上限收 0.022s，掉帧只当慢了一帧。
 * - 刚度 170 / 阻尼 23（ζ≈0.89 近临界阻尼），起步加速度峰值压在稳定段 1.3 倍内。
 */
export function useSpringFlip() {
  const ry = ref(0)
  let vel = 0
  let tgt = 0
  let raf = 0
  let last = 0

  const STIFF = 170
  const DAMP = 23

  function tick(ts: number) {
    if (!last) {
      last = ts
      raf = requestAnimationFrame(tick)
      return
    }
    let dt = (ts - last) / 1000
    if (!(dt > 0)) dt = 1 / 60
    if (dt > 0.022) dt = 0.022
    last = ts

    const acc = (tgt - ry.value) * STIFF - vel * DAMP
    vel += acc * dt
    ry.value += vel * dt

    if (Math.abs(tgt - ry.value) < 0.06 && Math.abs(vel) < 0.6) {
      ry.value = tgt
      vel = 0
      raf = 0
      last = 0
      return
    }
    raf = requestAnimationFrame(tick)
  }

  function start(target: number) {
    tgt = target
    last = 0
    if (!raf) raf = requestAnimationFrame(tick)
  }

  /** 当前是否朝「背面」方向（用于判断翻面） */
  function isBack() {
    return Math.abs(ry.value - 180) < Math.abs(ry.value)
  }

  function toggle() {
    start(isBack() ? 0 : 180)
  }

  function reset() {
    ry.value = 0
    vel = 0
    tgt = 0
    last = 0
    if (raf) {
      cancelAnimationFrame(raf)
      raf = 0
    }
  }

  onBeforeUnmount(() => {
    if (raf) cancelAnimationFrame(raf)
  })

  return { ry, toggle, isBack, reset }
}

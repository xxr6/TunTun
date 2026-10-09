const clozePattern = /\{\{c\d+::[^{}]+\}\}/
const tableRule = /^\s*\|?\s*:?-{3,}:?\s*\|/m

export function cardQualityError(type: string, front: string, back: string): string | null {
  if (!front.trim()) return '请填写卡片正面'
  if (type === 'cloze') {
    if (!clozePattern.test(front)) return '挖空卡请在正面使用 {{c1::答案}} 格式'
  } else if (!back.trim()) {
    return '请填写背面答案，不能把题目当作答案'
  }
  if (type === 'basic' && tableRule.test(front)) return '请把表格拆成单个问题，再保存卡片'
  return null
}

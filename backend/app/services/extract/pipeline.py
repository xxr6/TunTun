"""AI 提炼管线：文件正文 → Markdown 笔记 + 考点候选。

技术文档 12 章的五阶段（读取/切段/提炼/归并/渲染）在这里做工程简化：
- 读取：复用 M3 的 documents.text（已解析正文）
- 切段：按 ~3000 字符切（中文约 1500 token，远低于 32K 上下文）
- 提炼：每段独立调 LLM，输出要点 / 易错点 / 考点候选
- 归并：拼接各段结果，去重
- 渲染：固定模板生成 Markdown

无 LLM key 时抛 LLMNotConfigured，由 API 层转成明确提示（不降级——提炼必须依赖 LLM）。
"""
import re

from app.services.llm.provider import OpenAICompatProvider

# 每段约 3000 字符
SEGMENT_SIZE = 3000

_SYSTEM = (
    "你是学习笔记提炼助手。阅读给定文本，提炼出：\n"
    "1. points：核心知识点（3~8 条，简洁准确，忠于原文，不要编造）\n"
    "2. pitfalls：易错点 / 易混淆点（0~3 条）\n"
    "3. candidates：适合做成间隔重复复习卡片的考点（1~5 条），每条含 card_type（basic 问答 或 cloze 挖空）、front、back\n"
    "只返回 JSON，格式：\n"
    '{"points":["..."],"pitfalls":["..."],"candidates":[{"card_type":"basic","front":"...","back":"..."}]}'
)


def _split(text: str, size: int = SEGMENT_SIZE) -> list[str]:
    """按段落尽量完整地切段，超长段再硬切。"""
    text = text.strip()
    if len(text) <= size:
        return [text] if text else []

    # 先按空行/段落切
    paras = re.split(r"\n\s*\n", text)
    segments: list[str] = []
    buf = ""
    for p in paras:
        if len(buf) + len(p) + 1 <= size:
            buf = (buf + "\n\n" + p).strip()
        else:
            if buf:
                segments.append(buf)
            # 单段超长：硬切
            if len(p) > size:
                for i in range(0, len(p), size):
                    segments.append(p[i : i + size])
            else:
                buf = p
    if buf:
        segments.append(buf)
    return segments


def _render_md(title: str, points: list[str], pitfalls: list[str]) -> str:
    lines = [f"# {title}", ""]
    lines.append("## 知识点清单")
    for p in points:
        lines.append(f"- {p}")
    lines.append("")
    if pitfalls:
        lines.append("## 易错点")
        for p in pitfalls:
            lines.append(f"- {p}")
        lines.append("")
    return "\n".join(lines)


async def distill_document(text: str, title: str, llm: OpenAICompatProvider) -> tuple[str, list[dict]]:
    """提炼正文 → (content_md, candidates)。"""
    segments = _split(text)
    if not segments:
        return _render_md(title, [], []), []

    all_points: list[str] = []
    all_pitfalls: list[str] = []
    all_candidates: list[dict] = []

    for i, seg in enumerate(segments):
        messages = [
            {"role": "system", "content": _SYSTEM},
            {"role": "user", "content": f"文本（第 {i + 1}/{len(segments)} 段）：\n{seg}"},
        ]
        data = await llm.chat_json(messages)
        all_points.extend(str(p) for p in data.get("points", []) if p)
        all_pitfalls.extend(str(p) for p in data.get("pitfalls", []) if p)
        for c in data.get("candidates", []):
            if isinstance(c, dict) and c.get("front"):
                all_candidates.append(c)

    # 去重（保序）
    seen: set[str] = set()
    points, pitfalls = [], []
    for p in all_points:
        if p not in seen:
            seen.add(p)
            points.append(p)
    for p in all_pitfalls:
        if p not in seen:
            seen.add(p)
            pitfalls.append(p)

    content_md = _render_md(title, points, pitfalls)
    return content_md, all_candidates

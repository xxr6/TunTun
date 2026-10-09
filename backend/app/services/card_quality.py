"""入库与复习共用的卡片质量检查。"""
import re

_CLOZE = re.compile(r"\{\{c\d+::([^{}]+)\}\}")
_TABLE_RULE = re.compile(r"^\s*\|?\s*:?-{3,}:?\s*\|", re.MULTILINE)


def card_quality_error(card_type: str, front: str, back: str) -> str | None:
    prompt = front.strip()
    answer = back.strip()
    if not prompt:
        return "请填写卡片正面"
    if card_type == "cloze":
        if not _CLOZE.search(prompt):
            return "挖空卡请在正面使用 {{c1::答案}} 格式"
    elif not answer:
        return "请填写卡片背面答案，避免翻面后重复显示题目"
    if card_type == "basic" and _TABLE_RULE.search(prompt):
        return "整张表格不适合直接做问答卡，请拆成单个知识点"
    return None


def reviewable(card_type: str, front: str, back: str) -> bool:
    return card_quality_error(card_type, front, back) is None


def generated_candidate_ready(card_type: str, front: str, back: str) -> bool:
    """AI 候选保持短小；手动卡片仍允许较长的题面。"""
    if card_quality_error(card_type, front, back) is not None:
        return False
    if card_type == "basic":
        return len(front.strip()) <= 180 and ("？" in front or "?" in front)
    return len(front.strip()) <= 240

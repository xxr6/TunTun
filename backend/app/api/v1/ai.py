"""AI 生成接口：划词成卡（M4 核心）。"""
from fastapi import APIRouter, Depends

from app.core.deps import get_current_user, get_db
from app.models.ai_usage import AiUsage
from app.models.user import User
from app.schemas.ai import CardSelectionIn, CardSelectionOut, GeneratedCard
from app.services.card_quality import generated_candidate_ready
from app.services.llm.provider import LLMError, LLMNotConfigured, get_llm

router = APIRouter(prefix="/ai", tags=["ai"])

_SYSTEM = (
    "你是知识卡片生成助手。根据用户选中的文本，生成适合间隔重复复习的卡片。\n"
    "规则：\n"
    "1. 类型：basic（问答，正面问题背面答案）或 cloze（挖空，把关键词用 {{c1::答案}} 挖空）。"
    "概念/定义用 basic，关键句用 cloze。\n"
    "2. 忠于原文，不要编造原文没有的内容。\n"
    "3. 一般 1~3 张，只有确实包含多个独立知识点时才多张；每张只问一个问题，正面不超过 180 字。\n"
    "4. 不要把整段文字、列表或表格直接放在正面。basic 正面必须是具体问题，背面必须有答案。\n"
    "5. 只返回 JSON，格式：{\"cards\":[{\"card_type\":\"basic\",\"front\":\"...\",\"back\":\"...\"}]}"
)


@router.post("/cards/from-selection", response_model=CardSelectionOut)
async def cards_from_selection(
    body: CardSelectionIn,
    user: User = Depends(get_current_user),
    db=Depends(get_db),
):
    llm = get_llm()
    if llm is None:
        # 降级：未配置 LLM，选中文本直接成一张 basic 卡，前端提示补背面
        return CardSelectionOut(
            cards=[GeneratedCard(card_type="basic", front=body.selection, back="")],
            fallback=True,
        )

    mode_hint = "" if body.mode == "auto" else f"（用户偏好类型：{body.mode}）"
    messages = [
        {"role": "system", "content": _SYSTEM},
        {"role": "user", "content": f"选中文本：\n{body.selection}\n{mode_hint}\n最多 {body.max_cards} 张。"},
    ]
    try:
        data = await llm.chat_json(messages)
        cards = [
            GeneratedCard(
                card_type=c.get("card_type", "basic"),
                front=str(c.get("front", "")),
                back=str(c.get("back", "")),
                hint=c.get("hint"),
                confidence=float(c.get("confidence", 0.8)),
            )
            for c in data.get("cards", [])
            if generated_candidate_ready(str(c.get("card_type", "basic")), str(c.get("front", "")), str(c.get("back", "")))
        ]
        if not cards:
            raise LLMError("LLM 未返回卡片")
    except (LLMError, LLMNotConfigured):
        # LLM 失败也降级，保证划词成卡闭环可用
        return CardSelectionOut(
            cards=[GeneratedCard(card_type="basic", front=body.selection, back="")],
            fallback=True,
        )

    # 用量记录（统计页「AI 用量」）
    db.add(AiUsage(user_id=user.id, kind="selection"))
    await db.commit()

    return CardSelectionOut(cards=cards[: body.max_cards], fallback=False)

"""LLM 抽象层：OpenAI 兼容协议直调（deepseek / ollama / 通义等）。

技术文档选 LiteLLM 统一 100+ 家供应商；这里为控制依赖体积、且 M4 阶段
目标是「OpenAI 兼容协议」，直接 httpx 调用足够。后续接更多非 OpenAI 协议
供应商时再引入 LiteLLM，provider 接口不变。

无 API key 时 `get_llm()` 返回 None，调用方走降级路径（划词成卡 → 模板化兜底）。
"""
import json
import re
from typing import Any

import httpx

from app.core.config import settings


class LLMError(Exception):
    """LLM 调用失败（网络 / 供应商错误等）。"""


class LLMNotConfigured(LLMError):
    """未配置 API key。"""


class OpenAICompatProvider:
    def __init__(self, base_url: str, api_key: str, model: str):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.model = model

    async def chat(self, messages: list[dict[str, str]], *, temperature: float = 0.3,
                   max_tokens: int = 2000) -> str:
        async with httpx.AsyncClient(timeout=90) as client:
            try:
                r = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    json={
                        "model": self.model,
                        "messages": messages,
                        "temperature": temperature,
                        "max_tokens": max_tokens,
                    },
                )
                r.raise_for_status()
            except httpx.HTTPError as e:
                raise LLMError(f"LLM 请求失败：{e}") from e
        data = r.json()
        return data["choices"][0]["message"]["content"]

    async def chat_json(self, messages: list[dict[str, str]], *, retries: int = 2) -> dict[str, Any]:
        """要求模型返回 JSON，解析失败自动重试一次。"""
        last: str = ""
        for _ in range(retries + 1):
            last = await self.chat(messages, temperature=0.2)
            parsed = _extract_json(last)
            if parsed is not None:
                return parsed
        raise LLMError(f"LLM 未返回合法 JSON：{last[:200]}")


def _extract_json(text: str) -> dict[str, Any] | None:
    """从模型输出里抠出 JSON（容忍 ```json 围栏与前后杂文本）。"""
    if not text:
        return None
    # 去掉 markdown 代码围栏
    m = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
    if m:
        text = m.group(1)
    # 找首个 { 到最后一个 }
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end <= start:
        return None
    try:
        return json.loads(text[start : end + 1])
    except json.JSONDecodeError:
        return None


def get_llm() -> OpenAICompatProvider | None:
    if not settings.LLM_API_KEY:
        return None
    return OpenAICompatProvider(settings.LLM_BASE_URL, settings.LLM_API_KEY, settings.LLM_MODEL)

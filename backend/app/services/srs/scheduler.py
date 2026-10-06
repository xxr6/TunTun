"""FSRS 调度封装。

直接依赖 py-fsrs（`fsrs` 包，v6.x），不在外层重写算法——FSRS 边界条件极多，
自己实现必然与参考实现产生偏差。这里只做「DB 状态 ↔ fsrs.Card」的翻译与结果回写。

fsrs 6.x 要点（已读源码确认）：
- 主类 `Scheduler`，`review_card(card, rating, review_datetime) -> (new_card, log)`。
- rating 1=Again 2=Hard 3=Good 4=Easy；state Learning/Review/Relearning（无 New）。
- 新卡 = Learning 且 stability/difficulty 为 None。
- 学习步骤推进依赖 `card.step`，必须持久化（否则新卡永远停在第一步）。
- `review_datetime` 必须 timezone-aware 且为 UTC，否则抛 ValueError。
- elapsed 用 `last_review` 算（`.days`），不是 due。
"""
from datetime import datetime, timezone

from fsrs import Card as FsrsCard
from fsrs import Rating as FsrsRating
from fsrs import Scheduler as FsrsScheduler
from fsrs import State as FsrsState

# DB 业务状态 → fsrs 状态
_DB_TO_FSRS = {
    "new": FsrsState.Learning,
    "learning": FsrsState.Learning,
    "review": FsrsState.Review,
    "relearning": FsrsState.Relearning,
}
# fsrs 状态 → DB 业务状态
_FSRS_TO_DB = {
    FsrsState.Learning: "learning",
    FsrsState.Review: "review",
    FsrsState.Relearning: "relearning",
}

# 评分 1-4 → fsrs Rating（对外接口用 1-4，与前端键盘一致）
RATING_MIN, RATING_MAX = 1, 4


class ReviewScheduler:
    """无状态封装：默认用社区通用参数，个性化参数在 M7 用自有 review_logs 拟合后注入。"""

    def __init__(self, params: list[float] | None = None, desired_retention: float = 0.9):
        kwargs: dict = {"desired_retention": desired_retention}
        if params is not None:
            kwargs["parameters"] = list(params)
        self._sched = FsrsScheduler(**kwargs)

    def review(
        self,
        *,
        state: str,
        step: int | None,
        stability: float | None,
        difficulty: float | None,
        last_review: datetime | None,
        rating: int,
        now: datetime | None = None,
    ) -> dict:
        """评分一次，返回更新后的调度状态（不落库，由调用方写回）。"""
        if not (RATING_MIN <= rating <= RATING_MAX):
            raise ValueError(f"rating 必须在 {RATING_MIN}~{RATING_MAX}，得到 {rating}")

        now = now or datetime.now(timezone.utc)
        if now.tzinfo is None:
            now = now.replace(tzinfo=timezone.utc)
        if last_review is not None and last_review.tzinfo is None:
            last_review = last_review.replace(tzinfo=timezone.utc)

        is_new = state == "new" or stability is None
        card = FsrsCard(
            state=_DB_TO_FSRS.get(state, FsrsState.Learning),
            step=0 if (step is None and is_new) else step,
            stability=None if is_new else stability,
            difficulty=None if is_new else difficulty,
            due=now,
            last_review=last_review,
        )

        new_card, _log = self._sched.review_card(card, FsrsRating(rating), review_datetime=now)

        elapsed_days = 0.0
        if last_review is not None:
            elapsed_days = (now - last_review).total_seconds() / 86400.0
        scheduled_days = (new_card.due - now).total_seconds() / 86400.0

        return {
            "state": _FSRS_TO_DB.get(new_card.state, "review"),
            "step": new_card.step,
            "stability": new_card.stability,
            "difficulty": new_card.difficulty,
            "due": new_card.due,
            "elapsed_days": round(elapsed_days, 6),
            "scheduled_days": round(scheduled_days, 6),
        }

"""Run with: python tests/test_focus_interrupt.py (isolated temporary database)."""
import asyncio
import os
import sys
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

import httpx


async def main() -> None:
    backend_root = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(backend_root))
    db_path = backend_root / "tests" / f"focus_interrupt_{uuid.uuid4().hex}.db"
    os.environ["DB_DSN"] = f"sqlite+aiosqlite:///{db_path.as_posix()}"
    try:
        from app.db.init_db import init_db
        from app.db.session import engine
        from app.main import app

        await init_db()
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            auth = await client.post("/api/v1/auth/register", json={
                "email": "focus@example.com", "username": "focus-test", "password": "testpass123"
            })
            assert auth.status_code == 201, auth.text
            client.headers["Authorization"] = f"Bearer {auth.json()['access_token']}"

            saved = await client.post("/api/v1/auth/me/focus-topics", json={"label": "  准备面试  "})
            assert saved.status_code == 200, saved.text
            assert saved.json() == ["准备面试"]
            assert (await client.get("/api/v1/auth/me/focus-topics")).json() == ["准备面试"]
            assert (await client.post("/api/v1/auth/me/focus-topics", json={"label": "准备面试"})).json() == ["准备面试"]
            assert (await client.post("/api/v1/auth/me/focus-topics", json={"label": " "})).status_code == 422
            removed = await client.request("DELETE", "/api/v1/auth/me/focus-topics", json={"label": "准备面试"})
            assert removed.status_code == 200 and removed.json() == [], removed.text
            assert (await client.post("/api/v1/stats/achievements/claim")).json() == []

            now = datetime.now(timezone.utc)
            async def record(seconds: int, completed: bool, interrupted: bool, mode: str = "pomodoro", name: str = ""):
                response = await client.post("/api/v1/focus/sessions", json={
                    "mode": mode,
                    "started_at": (now - timedelta(seconds=seconds)).isoformat(),
                    "ended_at": now.isoformat(),
                    "duration_seconds": seconds,
                    "completed": completed,
                    "interrupted": interrupted,
                    "deck_name": name,
                })
                assert response.status_code == 201, response.text
                assert response.json()["interrupted"] is interrupted

            await record(120, True, False, name="AI 卡组")
            await record(90, False, True, name="准备面试")
            await record(15, True, False)  # unnamed focus remains visible as its own category
            await record(60, False, False, name="不应计入")  # reset: keep history, exclude from totals
            await record(30, False, True, "nap", "不应计入")  # rest mode: exclude from focus

            summary = (await client.get("/api/v1/focus/summary")).json()
            assert summary["today_seconds"] == 225, summary
            assert summary["week_seconds"] == 225, summary
            assert summary["month_seconds"] == 225, summary
            assert summary["today_count"] == 2, summary

            dash_response = await client.get("/api/v1/stats/dashboard")
            assert dash_response.status_code == 200, dash_response.text
            dash = dash_response.json()["focus"]
            for period in ("today", "week", "month"):
                assert dash[period]["sec"] == 225, dash
                assert dash["topics"][period] == [
                    {"name": "AI 卡组", "sec": 120},
                    {"name": "准备面试", "sec": 90},
                    {"name": "未指定", "sec": 15},
                ], dash
            badges = {badge["name"]: badge for badge in dash_response.json()["achievements"]}
            assert len(badges) == 26, badges
            assert badges["番茄初心"]["unlocked"] is True, badges
            assert badges["番茄初心"]["progress"] == 1, badges
            assert badges["番茄大师"]["unlocked"] is False, badges
            assert badges["博览群书"]["progress"] == 0, badges
            newly_earned = (await client.post("/api/v1/stats/achievements/claim")).json()
            assert [badge["name"] for badge in newly_earned] == ["番茄初心"], newly_earned
            assert (await client.post("/api/v1/stats/achievements/claim")).json() == []
            overview = (await client.get("/api/v1/stats/overview")).json()
            assert overview["focus_seconds"] == 225, overview
            await record(30, True, False, "deep", "深度学习")
            deep_summary = (await client.get("/api/v1/focus/summary")).json()
            assert deep_summary["today_seconds"] == 255, deep_summary
            assert deep_summary["today_count"] == 2, deep_summary
            await record(45, False, True, "countup", "自由阅读")
            countup_summary = (await client.get("/api/v1/focus/summary")).json()
            assert countup_summary["today_seconds"] == 300, countup_summary
            assert countup_summary["today_count"] == 2, countup_summary

            new_auth = await client.post("/api/v1/auth/register", json={
                "email": "new-badge@example.com", "username": "new-badge", "password": "testpass123"
            })
            assert new_auth.status_code == 201, new_auth.text
            client.headers["Authorization"] = f"Bearer {new_auth.json()['access_token']}"
            stable_id = str(uuid.uuid4())
            first_payload = {
                "id": stable_id,
                "mode": "pomodoro", "started_at": (now - timedelta(seconds=120)).isoformat(),
                "ended_at": now.isoformat(), "duration_seconds": 120,
                "completed": True, "interrupted": False, "deck_name": "",
            }
            first_focus = await client.post("/api/v1/focus/sessions", json=first_payload)
            assert first_focus.status_code == 201, first_focus.text
            retried = await client.post("/api/v1/focus/sessions", json=first_payload)
            assert retried.status_code == 201 and retried.json()["id"] == first_focus.json()["id"]
            assert (await client.get("/api/v1/focus/summary")).json()["today_seconds"] == 120
            first_claim = (await client.post("/api/v1/stats/achievements/claim")).json()
            assert [badge["name"] for badge in first_claim] == ["番茄初心"], first_claim
        await engine.dispose()
    finally:
        for path in (db_path, Path(f"{db_path}-wal"), Path(f"{db_path}-shm")):
            path.unlink(missing_ok=True)


if __name__ == "__main__":
    asyncio.run(main())
    print("focus interrupt flow ok")

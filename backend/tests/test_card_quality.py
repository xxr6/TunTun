"""Run with: python tests/test_card_quality.py (isolated temporary database)."""
import asyncio
import os
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

import httpx


async def main() -> None:
    backend_root = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(backend_root))
    db_path = backend_root / "tests" / f"card_quality_{uuid.uuid4().hex}.db"
    os.environ["DB_DSN"] = f"sqlite+aiosqlite:///{db_path.as_posix()}"
    try:
        from app.db.init_db import init_db
        from app.db.session import AsyncSessionLocal, engine
        from app.main import app
        from app.models.card import Card

        await init_db()
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            auth = await client.post("/api/v1/auth/register", json={
                "email": "quality@example.com", "username": "quality-test", "password": "testpass123"
            })
            assert auth.status_code == 201, auth.text
            client.headers["Authorization"] = f"Bearer {auth.json()['access_token']}"
            me = (await client.get("/api/v1/auth/me")).json()
            deck = await client.post("/api/v1/decks", json={"name": "Quality"})
            assert deck.status_code == 201, deck.text
            deck_id = deck.json()["id"]

            invalid = await client.post("/api/v1/cards", json={
                "deck_id": deck_id, "front": "整段资料", "back": "  ",
            })
            assert invalid.status_code == 422, invalid.text
            table = await client.post("/api/v1/cards", json={
                "deck_id": deck_id, "front": "| 项目 | 含义 |\n| --- | --- |\n| A | B |", "back": "B",
            })
            assert table.status_code == 422, table.text

            valid = await client.post("/api/v1/cards", json={
                "deck_id": deck_id, "front": "A 是什么？", "back": "B",
            })
            assert valid.status_code == 201, valid.text
            card_id = valid.json()["id"]
            assert (await client.patch(f"/api/v1/cards/{card_id}", json={"back": ""})).status_code == 422

            # 旧数据可能绕过新校验；仍不应进入复习队列。
            async with AsyncSessionLocal() as session:
                session.add(Card(
                    user_id=uuid.UUID(me["id"]), deck_id=uuid.UUID(deck_id),
                    card_type="basic", front="旧卡", back="", state="new",
                    due=datetime.now(timezone.utc),
                ))
                await session.commit()
            queue = (await client.get("/api/v1/review/queue")).json()
            assert queue["remaining_today"] == 1, queue
            assert queue["needs_repair"] == 1, queue
            assert [item["card_id"] for item in queue["items"]] == [card_id], queue
            forecast = (await client.get("/api/v1/review/forecast?days=7")).json()
            assert sum(day["count"] for day in forecast) == 1, forecast
        await engine.dispose()
    finally:
        for path in (db_path, Path(f"{db_path}-wal"), Path(f"{db_path}-shm")):
            path.unlink(missing_ok=True)


if __name__ == "__main__":
    asyncio.run(main())
    print("card quality flow ok")

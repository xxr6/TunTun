"""Run with: python tests/test_folder_flow.py (uses an isolated temporary database)."""
import asyncio
import os
import sys
import tempfile
from pathlib import Path

import httpx


async def main() -> None:
    backend_root = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(backend_root))
    with tempfile.TemporaryDirectory(dir=backend_root) as tmp:
        os.environ["DB_DSN"] = "sqlite+aiosqlite:///./test.db"
        os.environ["STORAGE_ROOT"] = str(Path(tmp, "storage"))
        original_dir = Path.cwd()
        os.chdir(tmp)

        from app.db.init_db import init_db
        from app.main import app

        await init_db()
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            auth = await client.post("/api/v1/auth/register", json={
                "email": "folder@example.com", "username": "folder-test", "password": "testpass123"
            })
            assert auth.status_code == 201, auth.text
            client.headers["Authorization"] = f"Bearer {auth.json()['access_token']}"

            folder = await client.post("/api/v1/files/folder", json={"name": "Study"})
            assert folder.status_code == 201, folder.text
            folder_id = folder.json()["id"]
            nested = await client.post("/api/v1/files/folder", json={"name": "Notes", "parent_id": folder_id})
            assert nested.status_code == 201, nested.text
            nested_id = nested.json()["id"]

            root = (await client.get("/api/v1/files")).json()
            assert [item["name"] for item in root] == ["Study"]
            children = (await client.get("/api/v1/files", params={"parent_id": folder_id})).json()
            assert [item["name"] for item in children] == ["Notes"]
            assert len((await client.get("/api/v1/files/folders")).json()) == 2
            assert len((await client.get("/api/v1/files", params={"all": "true"})).json()) == 2

            duplicate = await client.post("/api/v1/files/folder", json={"name": "Study"})
            assert duplicate.status_code == 409, duplicate.text
            cycle = await client.patch(f"/api/v1/files/{folder_id}", json={"parent_id": nested_id})
            assert cycle.status_code == 409, cycle.text

            uploaded = await client.post(
                "/api/v1/files", params={"parent_id": nested_id},
                files={"file": ("lesson.txt", b"a short test lesson", "text/plain")},
            )
            assert uploaded.status_code == 201, uploaded.text
            file_id = uploaded.json()["id"]
            assert uploaded.json()["parent_id"] == nested_id
            assert len((await client.get("/api/v1/files", params={"all": "true"})).json()) == 3

            moved = await client.patch(f"/api/v1/files/{file_id}", json={"parent_id": None})
            assert moved.status_code == 200, moved.text
            assert moved.json()["parent_id"] is None
            root = (await client.get("/api/v1/files")).json()
            assert {item["name"] for item in root} == {"Study", "lesson.txt"}

            deck = await client.post("/api/v1/decks", json={"name": "Source review"})
            assert deck.status_code == 201, deck.text
            locator = {"start": 2, "end": 7, "quote": "short"}
            card = await client.post("/api/v1/cards", json={
                "deck_id": deck.json()["id"], "front": "Question", "back": "Answer",
                "source_file_id": file_id, "source_locator": locator,
            })
            assert card.status_code == 201, card.text
            card_id = card.json()["id"]
            assert (await client.get(f"/api/v1/cards/{card_id}")).json()["source_locator"] == locator
            queue = await client.get("/api/v1/review/queue")
            assert queue.status_code == 200, queue.text
            source = queue.json()["items"][0]
            assert source["source_file_id"] == file_id
            assert source["source_locator"] == locator
        from app.db.session import engine
        await engine.dispose()
        os.chdir(original_dir)


if __name__ == "__main__":
    asyncio.run(main())
    print("folder flow ok")

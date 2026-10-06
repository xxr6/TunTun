"""文件存储抽象：本地文件系统后端（后续可换 MinIO/S3 而不改业务代码）。

目录布局（技术文档 16 章）：{storage_root}/{user_id前2位}/{user_id}/{yyyy}/{mm}/{file_id}
避免单目录文件过多。
"""
from datetime import datetime, timezone
from pathlib import Path

from app.core.config import settings


class LocalStorage:
    def __init__(self, root: str):
        self.root = Path(root)

    def rel_path(self, user_id: str, file_id: str) -> str:
        # 防御：任一 id 为空/None 都会拼出 `.../None` 这种路径，且不报错，
        # 后果是不同文件撞到同一路径互相覆盖。宁可在这里炸，也不要静默写脏数据。
        for label, val in (("user_id", user_id), ("file_id", file_id)):
            if val is None or str(val).strip() in ("", "None"):
                raise ValueError(f"storage.rel_path: {label} 非法（{val!r}），拒绝生成存储路径")
        uid = str(user_id).replace("-", "")
        now = datetime.now(timezone.utc)
        return f"{uid[:2]}/{uid}/{now:%Y}/{now:%m}/{file_id}"

    def put(self, rel: str, data: bytes) -> None:
        p = self.root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(data)

    def get(self, rel: str) -> bytes:
        return (self.root / rel).read_bytes()

    def delete(self, rel: str) -> None:
        p = self.root / rel
        if p.exists():
            p.unlink()


storage = LocalStorage(settings.STORAGE_ROOT)

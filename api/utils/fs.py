# api/utils/fs.py
import os, json, re
from datetime import datetime, timezone

_SLUG_RE = re.compile(r"[^a-z0-9_-]+")

def slugify(name: str) -> str:
    s = name.strip().lower().replace(" ", "-")
    s = _SLUG_RE.sub("", s)
    return s or "project"

def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

def atomic_write_json(path: str, data: dict) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = f"{path}.part"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)

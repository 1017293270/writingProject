from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


def ensure_parent(path: str | Path) -> Path:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    return target


def write_json(path: str | Path, payload: dict[str, Any]) -> Path:
    target = ensure_parent(path)
    target.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return target


def read_json(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def write_text(path: str | Path, content: str) -> Path:
    target = ensure_parent(path)
    target.write_text(content, encoding="utf-8")
    return target


def read_text(path: str | Path) -> str:
    return Path(path).read_text(encoding="utf-8")


def count_words(content: str) -> int:
    cjk_chars = re.findall(r"[\u4e00-\u9fff]", content)
    latin_words = re.findall(r"[A-Za-z0-9]+(?:[-'][A-Za-z0-9]+)?", content)
    return len(cjk_chars) + len(latin_words)

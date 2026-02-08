#!/usr/bin/env python3
"""Utilities for a *flowing* public image pool.

Design goals
- Pool is metadata-only (no need to store image binaries in git).
- Each publish acts like training: extract keywords -> fetch candidates -> score -> update pool.
- Global cap: keep top N=2000 items by score/recency.

Pool file format (JSON):
{
  "version": 1,
  "updated_at": "...",
  "items": [
    {
      "key": "wikimedia:<pageid>",
      "provider": "wikimedia_commons",
      "industry": "technology",
      "title": "File:...",
      "url": "https://commons.wikimedia.org/wiki/File:...",
      "image_url": "https://upload.wikimedia.org/...",
      "license": "CC BY-SA 4.0",
      "license_url": "https://creativecommons.org/licenses/by-sa/4.0/",
      "tags": ["super bowl", "stadium", "AI"],
      "score": 123.4,
      "first_seen": 1700000000,
      "last_seen": 1700000000,
      "used_count": 0
    }
  ]
}
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any


POOL_PATH_DEFAULT = "data/public_image_pool.json"
POOL_VERSION = 1


def now_ts() -> int:
    return int(time.time())


def load_pool(path: str = POOL_PATH_DEFAULT) -> dict[str, Any]:
    p = Path(path)
    if not p.exists():
        return {"version": POOL_VERSION, "updated_at": "", "items": []}
    return json.loads(p.read_text(encoding="utf-8"))


def save_pool(doc: dict[str, Any], path: str = POOL_PATH_DEFAULT) -> None:
    doc["version"] = POOL_VERSION
    doc["updated_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(doc, ensure_ascii=False, indent=2), encoding="utf-8")


def key_for(item: dict[str, Any]) -> str:
    if item.get("provider") == "wikimedia_commons":
        return f"wikimedia:{item.get('id') or item.get('key') or ''}"
    return item.get("key") or (item.get("provider", "") + ":" + (item.get("id") or ""))


def merge_items(existing: list[dict[str, Any]], new_items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    idx: dict[str, dict[str, Any]] = {}
    for it in existing:
        k = it.get("key") or key_for(it)
        it["key"] = k
        idx[k] = it

    ts = now_ts()
    for it in new_items:
        k = it.get("key") or key_for(it)
        if not k or k.endswith(":"):
            continue
        it["key"] = k
        if k in idx:
            # update fields, keep counters
            cur = idx[k]
            cur.update({
                "industry": it.get("industry", cur.get("industry")),
                "title": it.get("title", cur.get("title")),
                "url": it.get("url", cur.get("url")),
                "image_url": it.get("image_url", cur.get("image_url")),
                "license": it.get("license", cur.get("license")),
                "license_url": it.get("license_url", cur.get("license_url")),
            })
            # tags union
            tags = list(dict.fromkeys((cur.get("tags") or []) + (it.get("tags") or [])))
            cur["tags"] = tags[:40]
            # score: keep max
            cur["score"] = max(float(cur.get("score", 0)), float(it.get("score", 0)))
            cur["last_seen"] = ts
        else:
            it.setdefault("first_seen", ts)
            it.setdefault("last_seen", ts)
            it.setdefault("used_count", 0)
            idx[k] = it

    return list(idx.values())


def cap_pool(items: list[dict[str, Any]], cap: int = 2000) -> list[dict[str, Any]]:
    cap = max(100, cap)

    def rank(it: dict[str, Any]) -> float:
        score = float(it.get("score", 0))
        last = int(it.get("last_seen", 0))
        used = int(it.get("used_count", 0))
        # prefer recent + higher score; slightly prefer items that were used before (stability)
        return score + (last / 1e9) + min(used, 10) * 0.5

    items.sort(key=rank, reverse=True)
    return items[:cap]

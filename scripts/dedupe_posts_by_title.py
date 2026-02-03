#!/usr/bin/env python3
"""Delete duplicate Hugo posts by *title* under content/posts.

User-facing goal: 如果多篇文章标题完全一致，只保留一篇（保留最新）。

Rules:
- Only scans content/posts/*.md.
- Parse YAML front matter (--- ... ---).
- Group by exact title string (case-sensitive after strip).
- Keep newest by front matter `date` (ISO-ish), else by mtime.
- Delete the rest.

Safety:
- Prints what it will delete.
- If DRY_RUN=1 env set, do not delete.
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, List, Tuple

try:
    import yaml
except Exception:  # pragma: no cover
    yaml = None

POSTS_DIR = Path("content/posts")
FM_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.S)


@dataclass
class Post:
    path: Path
    title: str
    date: Optional[datetime]
    mtime: float


def parse_yaml_front_matter(text: str) -> Dict:
    if yaml is None:
        return {}
    m = FM_RE.match(text)
    if not m:
        return {}
    try:
        return yaml.safe_load(m.group(1)) or {}
    except Exception:
        return {}


def parse_date(v) -> Optional[datetime]:
    if not v:
        return None
    if isinstance(v, datetime):
        return v
    s = str(v).strip().replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(s)
    except Exception:
        return None


def load_post(path: Path) -> Post:
    text = path.read_text(encoding="utf-8", errors="replace")
    fm = parse_yaml_front_matter(text)
    title = str(fm.get("title") or "").strip() or path.stem
    dt = parse_date(fm.get("date"))
    return Post(path=path, title=title, date=dt, mtime=path.stat().st_mtime)


def sort_key(p: Post) -> Tuple[int, float]:
    if p.date:
        return (0, p.date.timestamp())
    return (1, p.mtime)


def main() -> int:
    if not POSTS_DIR.exists():
        print("[dedupe-title] content/posts not found; skip")
        return 0

    posts = [load_post(p) for p in POSTS_DIR.glob("*.md")]
    groups: Dict[str, List[Post]] = {}
    for p in posts:
        groups.setdefault(p.title, []).append(p)

    dry = os.environ.get("DRY_RUN") in {"1", "true", "yes"}

    deleted = 0
    for title, items in groups.items():
        if len(items) <= 1:
            continue
        items_sorted = sorted(items, key=sort_key, reverse=True)
        keep = items_sorted[0]
        dups = items_sorted[1:]
        print(f"[dedupe-title] title={title!r} keep={keep.path.name} delete={[d.path.name for d in dups]}")
        if not dry:
            for d in dups:
                d.path.unlink(missing_ok=True)
                deleted += 1

    print(f"[dedupe-title] done. deleted={deleted} dry_run={dry}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

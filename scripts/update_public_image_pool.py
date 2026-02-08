#!/usr/bin/env python3
"""Update the flowing public image pool (metadata only).

- Extract keywords/queries for the current article
- Fetch candidates from Wikimedia Commons API
- Score candidates against context
- Merge into global pool (cap=2000)

This is intended to run on every publish (as training).
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from commons_fetch import search_images
from image_pool import cap_pool, load_pool, merge_items, save_pool


def maybe_cache_thumbnail(cache_dir: str, key: str, url: str) -> bool:
    if not cache_dir:
        return False
    try:
        import requests

        from pathlib import Path

        Path(cache_dir).mkdir(parents=True, exist_ok=True)
        out = Path(cache_dir) / f"{re.sub(r'[^A-Za-z0-9:_-]+', '_', key)}.jpg"
        if out.exists() and out.stat().st_size > 0:
            return True
        r = requests.get(url, timeout=20, headers={"User-Agent": "Mozilla/5.0"})
        r.raise_for_status()
        out.write_bytes(r.content)
        return True
    except Exception:
        return False


def _text(s: str) -> str:
    return (s or "").strip()


def score_candidate(ctx: str, cand: dict, tags: list[str]) -> float:
    ctx_l = ctx.lower()
    title = (cand.get("title") or "").lower()
    lic = (cand.get("license") or "").lower()

    score = 0.0

    # tag matches
    for t in tags:
        tl = t.lower()
        if tl and (tl in ctx_l):
            score += 20
        if tl and (tl in title):
            score += 10

    # bonus for having explicit CC terms
    if "cc" in lic:
        score += 10

    # small penalty for obviously weird file titles
    if "meme" in title or "cartoon" in title:
        score -= 15

    return score


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--pool", default="data/public_image_pool.json")
    ap.add_argument("--cap", type=int, default=2000)
    ap.add_argument("--industry", required=True)
    ap.add_argument("--title", required=True)
    ap.add_argument("--md", required=True)
    ap.add_argument("--news-json", default="")
    ap.add_argument("--page-size", type=int, default=20)
    # Optional local cache (metadata-only pool still lives in JSON; cache stores thumbnails for quality checks)
    ap.add_argument("--cache-dir", default="")
    ap.add_argument("--cache-max-per-run", type=int, default=30)
    args = ap.parse_args()

    md_text = Path(args.md).read_text(encoding="utf-8")

    # extract keywords (invoke script for stability in both local + GH Actions)
    try:
        import subprocess

        cmd = [
            "python3",
            "scripts/extract_keywords.py",
            "--md",
            args.md,
            "--news-json",
            args.news_json,
            "--industry",
            args.industry,
            "--title",
            args.title,
        ]
        out = subprocess.check_output(cmd, text=True)
        kw = json.loads(out)
    except Exception:
        kw = {"tags": [], "queries": []}

    tags = kw.get("tags") or []
    queries = kw.get("queries") or []

    ctx = "\n".join([
        args.title,
        "\n".join([ln for ln in md_text.splitlines() if ln.startswith("## ") or ln.startswith("### ")])[:2000],
    ])

    new_items = []
    cached = 0
    for q in queries[:10]:
        cands = search_images(q, limit=max(5, min(args.page_size, 50)))
        for c in cands:
            if not _text(c.get("image_url")):
                continue
            it = {
                "provider": "wikimedia_commons",
                "id": c.get("id"),
                "industry": args.industry,
                "title": c.get("title"),
                "url": c.get("url"),
                "image_url": c.get("image_url"),
                "license": c.get("license"),
                "license_url": c.get("license_url"),
                "tags": tags,
            }
            it["score"] = score_candidate(ctx, it, tags)
            it["key"] = f"wikimedia:{it.get('id')}"
            new_items.append(it)

            # Optional: cache thumbnail locally for future quality checks
            if args.cache_dir and cached < args.cache_max_per_run:
                thumb = _text(c.get("thumbnail")) or _text(c.get("image_url"))
                if thumb:
                    if maybe_cache_thumbnail(args.cache_dir, it["key"], thumb):
                        cached += 1

    pool = load_pool(args.pool)
    items = merge_items(pool.get("items") or [], new_items)
    items = cap_pool(items, cap=args.cap)

    save_pool({"version": 1, "items": items, "updated_at": pool.get("updated_at", "")}, path=args.pool)

    print(json.dumps({"added": len(new_items), "kept": len(items), "cached": cached, "queries": queries[:5]}, ensure_ascii=False))


if __name__ == "__main__":
    main()

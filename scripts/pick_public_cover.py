#!/usr/bin/env python3
"""Pick a public cover image from a tagged industry pool (and download it).

Used by workflow as primary cover source to reduce paid image generation.
If no match is found or download fails, workflow falls back to Jimeng.

Usage:
  python3 scripts/pick_public_cover.py --pool scripts/public_image_pool.yaml \
    --industry technology --title "..." --slug xxx --out static/images/posts/<slug>/cover.jpg \
    --md content/posts/<slug>.md --news-json data/raw/news_<slug>.json

Exit codes:
  0: success (cover downloaded and attribution printed)
  2: no suitable candidate
  3: download failed
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

import requests
import yaml


def norm(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "").strip())


def build_context_text(title: str, md_path: str | None, news_json: str | None) -> str:
    parts = [title or ""]

    # markdown headings
    if md_path:
        try:
            txt = Path(md_path).read_text(encoding="utf-8")
            for ln in txt.splitlines():
                if ln.startswith("## ") or ln.startswith("### "):
                    parts.append(ln.lstrip("# ").strip())
        except Exception:
            pass

    # news sources titles
    if news_json:
        try:
            data = json.loads(Path(news_json).read_text(encoding="utf-8"))
            for it in (data.get("items") or [])[:25]:
                t = it.get("title") or ""
                if t:
                    parts.append(t)
                src = it.get("source") or it.get("site") or ""
                if src:
                    parts.append(src)
        except Exception:
            pass

    return "\n".join([p for p in parts if p])


def score_item(item: dict, ctx: str) -> float:
    ctx_l = (ctx or "").lower()
    tags = item.get("tags") or []
    score = float(item.get("weight", 0))

    # tag substring matches (CN/EN)
    for t in tags:
        if not t:
            continue
        if t.lower() in ctx_l:
            score += 30

    # boost: AI-related
    if ("ai" in ctx_l or "人工智能" in ctx) and any((x or "").lower() in ("ai", "人工智能") for x in tags):
        score += 20

    # penalize overly generic candidates (very few tags)
    if len(tags) < 4:
        score -= 10

    return score


def download(url: str, out_path: Path) -> bool:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=30)
        r.raise_for_status()
        out_path.write_bytes(r.content)
        return True
    except Exception:
        return False


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--pool", default="scripts/public_image_pool.yaml")
    ap.add_argument("--industry", required=True)
    ap.add_argument("--title", required=True)
    ap.add_argument("--slug", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--md", default="")
    ap.add_argument("--news-json", default="")
    args = ap.parse_args()

    doc = yaml.safe_load(Path(args.pool).read_text(encoding="utf-8")) or {}
    pool = list(doc.get("pool") or [])

    ctx = build_context_text(norm(args.title), args.md or None, args.news_json or None)

    candidates = [x for x in pool if x.get("industry") == args.industry and (x.get("image_url") or "").strip()]
    if not candidates:
        raise SystemExit(2)

    candidates.sort(key=lambda x: score_item(x, ctx), reverse=True)
    pick = candidates[0]

    img_url = (pick.get("image_url") or "").strip()
    if not img_url:
        raise SystemExit(2)

    ok = download(img_url, Path(args.out))
    if not ok:
        raise SystemExit(3)

    # Write sidecar meta for attribution
    meta = {
        "mode": "public_pool",
        "picked": pick,
        "slug": args.slug,
    }
    meta_path = Path(args.out).with_suffix(".meta.json")
    meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")

    print(
        json.dumps(
            {
                "cover_rel": f"/images/posts/{args.slug}/{Path(args.out).name}",
                "source": pick.get("url", ""),
                "license": pick.get("license", ""),
                "license_url": pick.get("license_url", ""),
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()

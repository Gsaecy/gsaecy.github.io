#!/usr/bin/env python3
"""Local daily training for the flowing image pool.

Runs on the Mac mini (not in GitHub Actions):
- git pull --rebase
- scan recent posts (default: last 24h, up to N)
- for each post, call update_public_image_pool.py with local cache enabled

We keep a *local* metadata pool file (ignored by git) so it can evolve without
committing noise. The goal is to continuously improve keyword extraction and
matching quality via repeated runs.

Usage:
  python3 scripts/local_daily_image_training.py --hours 24 --limit 6 \
    --pool data/local_public_image_pool.json --cache-dir data/local_image_cache
"""

from __future__ import annotations

import argparse
import json
import subprocess
import time
from pathlib import Path


def sh(cmd: list[str], cwd: str) -> str:
    return subprocess.check_output(cmd, cwd=cwd, text=True).strip()


def parse_front_matter(md_text: str) -> dict:
    if not md_text.startswith("---\n"):
        return {}
    end = md_text.find("\n---\n", 4)
    if end == -1:
        return {}
    fm = md_text[4:end]
    out = {}
    for ln in fm.splitlines():
        if ":" in ln:
            k, v = ln.split(":", 1)
            out[k.strip()] = v.strip().strip('"')
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default="/Users/guohongyu/clawd")
    ap.add_argument("--hours", type=int, default=24)
    ap.add_argument("--limit", type=int, default=6)
    ap.add_argument("--pool", default="data/local_public_image_pool.json")
    ap.add_argument("--cap", type=int, default=2000)
    ap.add_argument("--cache-dir", default="data/local_image_cache")
    ap.add_argument("--page-size", type=int, default=25)
    args = ap.parse_args()

    repo = args.repo

    # Update repo (best-effort). If there are local changes, skip pulling.
    try:
        status = sh(["git", "status", "--porcelain"], cwd=repo)
        if status.strip():
            # avoid failing or blocking; local uncommitted changes exist
            pass
        else:
            sh(["git", "pull", "--rebase", "origin", "main"], cwd=repo)
    except Exception:
        pass

    posts_dir = Path(repo) / "content" / "posts"
    if not posts_dir.exists():
        print(json.dumps({"ok": False, "error": "missing content/posts"}, ensure_ascii=False))
        return

    cutoff = time.time() - args.hours * 3600

    # pick recent markdown posts (exclude -wechat/-quality-report)
    files = []
    for p in posts_dir.glob("*.md"):
        if p.name.endswith("-wechat.md") or p.name.endswith("-quality-report.md"):
            continue
        try:
            if p.stat().st_mtime >= cutoff:
                files.append(p)
        except FileNotFoundError:
            continue

    files.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    files = files[: max(1, args.limit)]

    trained = []
    for p in files:
        md_text = p.read_text(encoding="utf-8")
        fm = parse_front_matter(md_text)
        slug = fm.get("slug") or p.stem
        industry = (fm.get("categories") or "").strip("[]")
        industry = industry.replace('"', "").split(",")[0].strip() or "technology"
        title = fm.get("title") or p.stem

        news_json = Path(repo) / "data" / "raw" / f"news_{slug}.json"
        news_arg = str(news_json) if news_json.exists() else ""

        cmd = [
            "python3",
            "scripts/update_public_image_pool.py",
            "--industry",
            industry,
            "--title",
            title,
            "--md",
            str(p),
            "--pool",
            args.pool,
            "--cap",
            str(args.cap),
            "--page-size",
            str(args.page_size),
            "--cache-dir",
            args.cache_dir,
        ]
        if news_arg:
            cmd += ["--news-json", news_arg]

        try:
            out = subprocess.check_output(cmd, cwd=repo, text=True)
            trained.append({"post": p.name, "slug": slug, "result": json.loads(out)})
        except Exception as e:
            trained.append({"post": p.name, "slug": slug, "error": str(e)})

    print(json.dumps({"ok": True, "count": len(trained), "trained": trained[:10]}, ensure_ascii=False))


if __name__ == "__main__":
    main()

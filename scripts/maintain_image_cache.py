#!/usr/bin/env python3
"""Daily maintenance for the local flowing image cache.

What it does
- Enforce a hard size cap for data/local_image_cache (default 5GB)
- Deletes oldest files first (LRU-ish by mtime)
- Optionally compacts the metadata pool (cap=2000) without committing binaries

This is designed to run locally on the Mac mini.
"""

from __future__ import annotations

import argparse
import json
import os
import time
from pathlib import Path

from image_pool import cap_pool, load_pool, save_pool


def dir_size_bytes(p: Path) -> int:
    total = 0
    for fp in p.rglob("*"):
        if fp.is_file():
            try:
                total += fp.stat().st_size
            except FileNotFoundError:
                pass
    return total


def human(n: int) -> str:
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if n < 1024 or unit == "TB":
            return f"{n:.1f}{unit}" if unit != "B" else f"{n}{unit}"
        n /= 1024
    return str(n)


def prune_cache(cache_dir: Path, cap_bytes: int) -> dict:
    cache_dir.mkdir(parents=True, exist_ok=True)

    files = []
    for fp in cache_dir.rglob("*"):
        if fp.is_file():
            try:
                st = fp.stat()
                files.append((fp, st.st_mtime, st.st_size))
            except FileNotFoundError:
                continue

    files.sort(key=lambda x: x[1])  # oldest first

    before = sum(s for _, _, s in files)
    deleted = 0

    i = 0
    while before > cap_bytes and i < len(files):
        fp, _, sz = files[i]
        try:
            fp.unlink()
            deleted += 1
            before -= sz
        except FileNotFoundError:
            pass
        i += 1

    # delete empty dirs
    for d in sorted([x for x in cache_dir.rglob("*") if x.is_dir()], key=lambda x: len(str(x)), reverse=True):
        try:
            if not any(d.iterdir()):
                d.rmdir()
        except Exception:
            pass

    after = dir_size_bytes(cache_dir)
    return {
        "cache_dir": str(cache_dir),
        "cap": cap_bytes,
        "before": before,
        "after": after,
        "deleted_files": deleted,
    }


def compact_pool(pool_path: str, cap: int = 2000) -> dict:
    doc = load_pool(pool_path)
    items = doc.get("items") or []
    before = len(items)
    items = cap_pool(items, cap=cap)
    save_pool({"version": 1, "items": items, "updated_at": doc.get("updated_at", "")}, path=pool_path)
    after = len(items)
    return {"pool_path": pool_path, "before": before, "after": after, "cap": cap}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--cache-dir", default="data/local_image_cache")
    ap.add_argument("--cap-gb", type=float, default=5.0)
    ap.add_argument("--pool", default="data/public_image_pool.json")
    ap.add_argument("--pool-cap", type=int, default=2000)
    args = ap.parse_args()

    cap_bytes = int(args.cap_gb * 1024 * 1024 * 1024)

    cache_report = prune_cache(Path(args.cache_dir), cap_bytes)
    pool_report = None
    if Path(args.pool).exists():
        pool_report = compact_pool(args.pool, cap=args.pool_cap)

    print(
        json.dumps(
            {
                "ok": True,
                "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "cache": cache_report,
                "pool": pool_report,
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()

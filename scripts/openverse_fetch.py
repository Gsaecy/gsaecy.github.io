#!/usr/bin/env python3
"""Openverse image search helper.

Openverse API: https://api.openverse.engineering/v1/images
We use it to build a *tagged, industry-specific* public image pool.

Outputs a normalized list with license + attribution fields.

Example:
  python3 scripts/openverse_fetch.py --query "AI circuit" --limit 5
"""

from __future__ import annotations

import argparse
import json
import time
from typing import Any

import requests


def fetch(query: str, limit: int = 5, timeout: int = 25) -> list[dict[str, Any]]:
    """Fetch Openverse image results.

    NOTE: Openverse returns multiple URL-ish fields. Here we normalize:
    - url: landing page (best-effort)
    - image_url: direct image url when available
    """

    url = "https://api.openverse.engineering/v1/images"
    params = {
        "q": query,
        "page_size": max(1, min(limit, 50)),
        # prefer images that are easy to reuse
        "license_type": "commercial",  # includes CC BY / CC0; excludes NC
        "mature": "false",
    }
    r = requests.get(url, params=params, timeout=timeout)
    r.raise_for_status()
    data = r.json()
    out = []
    for it in (data.get("results") or [])[:limit]:
        out.append(
            {
                "id": it.get("id"),
                "title": it.get("title") or "",
                "url": it.get("foreign_landing_url") or it.get("url") or "",
                "image_url": it.get("url") or it.get("thumbnail") or "",
                "thumbnail": it.get("thumbnail") or "",
                "provider": it.get("provider") or "openverse",
                "license": (it.get("license") or "").upper(),
                "license_url": it.get("license_url") or "",
                "creator": it.get("creator") or "",
                "creator_url": it.get("creator_url") or "",
                "source": it.get("source") or "",
            }
        )
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--query", required=True)
    ap.add_argument("--limit", type=int, default=5)
    args = ap.parse_args()

    t0 = time.time()
    items = fetch(args.query, args.limit)
    print(json.dumps({"query": args.query, "count": len(items), "items": items, "took_ms": int((time.time()-t0)*1000)}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

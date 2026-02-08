#!/usr/bin/env python3
"""Wikimedia Commons image search helper (no API key required).

We use MediaWiki API to search images and retrieve license metadata.

API doc: https://www.mediawiki.org/wiki/API:Main_page

Example:
  python3 scripts/commons_fetch.py --query "artificial intelligence circuit" --limit 5
"""

from __future__ import annotations

import argparse
import json
import time
from typing import Any

import requests


COMMONS_API = "https://commons.wikimedia.org/w/api.php"


def _get(dct: dict, *path: str, default: str = "") -> str:
    cur: Any = dct
    for p in path:
        if not isinstance(cur, dict) or p not in cur:
            return default
        cur = cur[p]
    return cur if isinstance(cur, str) else default


def search_images(query: str, limit: int = 10, timeout: int = 25) -> list[dict[str, Any]]:
    # generator=search returns pages directly; restrict to File namespace (6)
    params = {
        "action": "query",
        "format": "json",
        "generator": "search",
        "gsrsearch": query,
        "gsrnamespace": 6,
        "gsrlimit": max(1, min(limit, 50)),
        "prop": "imageinfo",
        "iiprop": "url|extmetadata",
        "iiurlwidth": 1920,
    }
    r = requests.get(COMMONS_API, params=params, timeout=timeout, headers={"User-Agent": "clawd-bot/1.0"})
    r.raise_for_status()
    data = r.json() or {}

    pages = (data.get("query") or {}).get("pages") or {}
    out: list[dict[str, Any]] = []

    for _, page in pages.items():
        title = page.get("title") or ""
        infos = page.get("imageinfo") or []
        if not infos:
            continue
        info = infos[0]
        ext = info.get("extmetadata") or {}

        # extmetadata fields are dicts with 'value'
        license_short = _get(ext.get("LicenseShortName") or {}, "value")
        license_url = _get(ext.get("LicenseUrl") or {}, "value")
        usage = _get(ext.get("UsageTerms") or {}, "value")
        artist = _get(ext.get("Artist") or {}, "value")

        out.append(
            {
                "id": str(page.get("pageid")),
                "title": title,
                "url": info.get("descriptionurl") or "",
                "image_url": info.get("url") or "",
                "thumbnail": info.get("thumburl") or "",
                "provider": "wikimedia_commons",
                "license": (license_short or usage or "").strip(),
                "license_url": (license_url or "").strip(),
                "creator": (artist or "").strip(),
            }
        )

    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--query", required=True)
    ap.add_argument("--limit", type=int, default=5)
    args = ap.parse_args()

    t0 = time.time()
    items = search_images(args.query, args.limit)
    print(
        json.dumps(
            {"query": args.query, "count": len(items), "items": items, "took_ms": int((time.time() - t0) * 1000)},
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Fetch public-domain / freely-licensed images from Wikimedia Commons.

No API key required.

- Search by query keywords
- Pick images with usable URLs
- Download to static/images/posts/<slug>/
- Return metadata for attribution

Usage:
  python3 scripts/fetch_wikimedia_images.py --query "electric vehicle battery" --outdir static/images/posts/<slug> --limit 2

Exit codes:
  0 success (even if 0 images)
  1 invalid args
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Dict, List, Optional

import requests

API = "https://commons.wikimedia.org/w/api.php"

# Wikimedia APIs may return 403 without a proper User-Agent.
UA = "AI-Zhihui-Observer/1.0 (https://gsaecy.github.io/; contact: github.com/Gsaecy)"


def clean_filename(name: str) -> str:
    name = re.sub(r"\s+", "-", name.strip())
    name = re.sub(r"[^A-Za-z0-9._-]", "-", name)
    name = re.sub(r"-+", "-", name)
    return name[:120] or "image"


def commons_search(query: str, limit: int = 5) -> List[str]:
    params = {
        "action": "query",
        "format": "json",
        "list": "search",
        "srsearch": f"{query} filetype:bitmap",
        "srlimit": str(limit),
        "srnamespace": "6",  # File:
    }
    r = requests.get(API, params=params, timeout=30)
    r.raise_for_status()
    data = r.json()
    return [item["title"] for item in data.get("query", {}).get("search", [])]


def commons_imageinfo(titles: List[str]) -> List[Dict]:
    if not titles:
        return []
    params = {
        "action": "query",
        "format": "json",
        "prop": "imageinfo",
        "titles": "|".join(titles),
        "iiprop": "url|extmetadata",
        "iiurlwidth": "1600",
    }
    r = requests.get(API, params=params, timeout=30)
    r.raise_for_status()
    pages = r.json().get("query", {}).get("pages", {})
    out = []
    for _, page in pages.items():
        if "imageinfo" not in page:
            continue
        ii = page["imageinfo"][0]
        meta = ii.get("extmetadata", {})
        out.append(
            {
                "title": page.get("title"),
                "pageid": page.get("pageid"),
                "descriptionurl": ii.get("descriptionurl"),
                "file_page": ii.get("descriptionurl"),
                "url": ii.get("thumburl") or ii.get("url"),
                "mime": ii.get("mime"),
                "license": meta.get("LicenseShortName", {}).get("value"),
                "license_url": meta.get("LicenseUrl", {}).get("value"),
                "artist": meta.get("Artist", {}).get("value"),
                "credit": meta.get("Credit", {}).get("value"),
                "attribution": meta.get("Attribution", {}).get("value"),
            }
        )
    return out


def download(url: str, out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    r = requests.get(url, timeout=60, headers={"User-Agent": UA})
    r.raise_for_status()
    out_path.write_bytes(r.content)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--query", required=True)
    ap.add_argument("--outdir", required=True)
    ap.add_argument("--limit", type=int, default=2)
    ap.add_argument("--outfile", default="")
    args = ap.parse_args()

    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    titles = commons_search(args.query, limit=max(args.limit * 3, 6))
    infos = commons_imageinfo(titles)

    selected = []
    for info in infos:
        if len(selected) >= args.limit:
            break
        if not info.get("url"):
            continue
        # Prefer images with explicit license info
        if not info.get("license"):
            continue
        selected.append(info)

    results = []
    for idx, info in enumerate(selected, start=1):
        url = info["url"]
        ext = "jpg"
        if info.get("mime") == "image/png":
            ext = "png"
        fname = clean_filename(f"wikimedia-{idx}.{ext}")
        out_path = outdir / fname
        download(url, out_path)
        info["saved_as"] = str(out_path)
        results.append(info)

    payload = {"query": args.query, "count": len(results), "items": results}
    if args.outfile:
        Path(args.outfile).write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    else:
        print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

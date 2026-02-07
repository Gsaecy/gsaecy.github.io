#!/usr/bin/env python3
"""Collect news from RSS feeds and extract main text + a relevant cover image.

- Uses RSS feeds defined in scripts/news_sources.yaml
- Fetches each article HTML and extracts readable text
- Extracts a cover image (og:image preferred, else first meaningful <img>)
- Outputs a JSON payload for downstream generation

Usage:
  python3 scripts/collect_news.py --industry technology --hours 24 --limit 30 --out data/raw/news_XXX.json
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import feedparser
import requests
import yaml
from bs4 import BeautifulSoup
from readability import Document


@dataclass
class NewsItem:
    industry: str
    source: str
    title: str
    url: str
    published: Optional[str]
    summary: str
    content_text: str
    cover_image_url: Optional[str]


def load_sources(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def norm_space(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "").strip())


def parse_published(entry: Any) -> Optional[datetime]:
    # feedparser gives .published_parsed
    if getattr(entry, "published_parsed", None):
        return datetime.fromtimestamp(time.mktime(entry.published_parsed), tz=timezone.utc)
    if getattr(entry, "updated_parsed", None):
        return datetime.fromtimestamp(time.mktime(entry.updated_parsed), tz=timezone.utc)
    return None


def fetch_html(url: str, user_agent: str, timeout: int = 20) -> str:
    r = requests.get(url, headers={"User-Agent": user_agent}, timeout=timeout)
    r.raise_for_status()
    r.encoding = r.apparent_encoding or "utf-8"
    return r.text


def extract_readable(html: str, base_url: str) -> Tuple[str, str]:
    doc = Document(html)
    title = norm_space(doc.short_title())
    content_html = doc.summary(html_partial=True)
    soup = BeautifulSoup(content_html, "lxml")
    text = norm_space(soup.get_text("\n"))
    # Keep multi-paragraph structure (readability may collapse)
    text = "\n".join([norm_space(x) for x in text.split("\n") if norm_space(x)])
    return title, text


def pick_cover_image(html: str, base_url: str) -> Optional[str]:
    soup = BeautifulSoup(html, "lxml")
    # og:image
    og = soup.select_one('meta[property="og:image"], meta[name="og:image"], meta[property="twitter:image"], meta[name="twitter:image"]')
    if og and og.get("content"):
        return og["content"].strip()
    # first content image
    for img in soup.select("article img, main img, .article img, .post img"):
        src = img.get("src") or img.get("data-src") or img.get("data-original")
        if not src:
            continue
        src = src.strip()
        if src.startswith("data:"):
            continue
        # skip tiny icons
        w = img.get("width")
        h = img.get("height")
        try:
            if w and h and int(w) < 200 and int(h) < 200:
                continue
        except Exception:
            pass
        return src
    return None


def collect(industry: str, hours: int, limit: int, sources_yaml: Path) -> Dict[str, Any]:
    cfg = load_sources(sources_yaml)
    ua = cfg.get("global", {}).get("user_agent", "Mozilla/5.0")
    feeds = cfg.get("industries", {}).get(industry, [])
    if not feeds:
        raise SystemExit(f"No feeds configured for industry={industry}")

    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)

    candidates: List[Tuple[datetime, str, str, str, str]] = []
    # (published_dt, source, title, url, summary)

    for f in feeds:
        name = f.get("name")
        rss = f.get("rss")
        if not rss:
            continue
        try:
            # Some feeds block non-browser UAs when fetched by feedparser directly.
            # Fetch via requests with UA first, then let feedparser parse the content.
            resp = requests.get(rss, headers={"User-Agent": ua}, timeout=20)
            resp.raise_for_status()
            parsed = feedparser.parse(resp.content)
            for e in parsed.entries[: max(limit, 20)]:
                url = getattr(e, "link", None)
                if not url:
                    continue
                published_dt = parse_published(e) or datetime.now(timezone.utc)
                if published_dt < cutoff:
                    continue
                title = norm_space(getattr(e, "title", ""))
                summary = norm_space(getattr(e, "summary", ""))
                candidates.append((published_dt, name, title, url, summary))
        except Exception:
            continue

    # sort by recency
    candidates.sort(key=lambda x: x[0], reverse=True)

    seen = set()
    items: List[NewsItem] = []

    for published_dt, source, title, url, summary in candidates:
        key = hashlib.sha1(url.encode("utf-8")).hexdigest()
        if key in seen:
            continue
        seen.add(key)
        # Try to fetch full article text; if blocked/timeout, fall back to RSS summary
        page_title = title
        readable = summary
        cover = None
        try:
            html = fetch_html(url, ua)
            page_title, readable = extract_readable(html, url)
            cover = pick_cover_image(html, url)
        except Exception:
            # Keep RSS-based content so we can still publish instead of producing 0 items
            pass

        # Skip entries that are completely empty
        if not norm_space(page_title) and not norm_space(readable):
            continue

        items.append(
            NewsItem(
                industry=industry,
                source=source,
                title=page_title or title,
                url=url,
                published=published_dt.isoformat(),
                summary=(summary or "")[:4000],
                content_text=(readable or "")[:16000],
                cover_image_url=cover,
            )
        )
        if len(items) >= limit:
            break

    payload = {
        "industry": industry,
        "collected_at": datetime.now(timezone.utc).isoformat(),
        "hours": hours,
        "limit": limit,
        "count": len(items),
        "items": [asdict(x) for x in items],
    }
    return payload


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--industry", required=True)
    ap.add_argument("--hours", type=int, default=24)
    ap.add_argument("--limit", type=int, default=20)
    ap.add_argument("--out", required=True)
    ap.add_argument("--sources", default="scripts/news_sources.yaml")
    args = ap.parse_args()

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    payload = collect(args.industry, args.hours, args.limit, Path(args.sources))
    out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"✅ collected {payload['count']} items -> {out_path}")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Fetch hotboard topics from uapis.cn and build a sources payload compatible with generate_news_post.py.

This is used as a *real-time* fallback when RSS collection returns 0 items.

It:
- pulls hotboard lists from an allowlist of platforms
- filters risky/sensitive titles (very conservative)
- avoids repeating recent topics (by scanning recent post titles)
- scores candidates using platform weights + parsed hot_value
- outputs:
  - JSON payload (same shape as collect_news.py output)
  - optionally prints chosen INDUSTRY/TOPIC for shell consumption

Example:
  python3 scripts/fetch_hotboard_topics.py --out data/raw/news_x.json --shell

API:
  GET https://uapis.cn/api/v1/misc/hotboard?type=weibo

Notes:
- hot_value is often a human-readable string; we best-effort parse a numeric score.
- We only treat titles as "signals"; the article should remain analysis/method-driven.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests


DEFAULT_TYPES = ["zhihu", "36kr", "ithome", "huxiu", "sspai", "juejin"]

PLATFORM_WEIGHT = {
    "zhihu": 1.25,
    "36kr": 1.10,
    "huxiu": 1.08,
    "sspai": 1.05,
    "juejin": 1.00,
    "ithome": 0.98,
}

# Conservative deny keywords (topic/title-level)
DENY_KEYWORDS = [
    # porn/gambling/drugs
    "色情",
    "成人视频",
    "博彩",
    "赌博",
    "毒品",
    "军火",
    # violence/terror/hate
    "恐怖",
    "暴力",
    "仇恨",
    "极端",
    # fraud/illegal
    "诈骗",
    "洗钱",
    # self-harm
    "自杀",
    "自残",
    # politics / highly sensitive public affairs (extra conservative)
    "习近平",
    "总书记",
    "中央",
    "国务院",
    "人大",
    "政协",
    "台湾",
    "台独",
    "香港",
    "新疆",
    "西藏",
    "敏感",
    "游行",
    "示威",
    "战争",
    "制裁",
]


def norm_space(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "").strip())


def contains_any(s: str, words: list[str]) -> bool:
    s = s or ""
    return any(w and w in s for w in words)


def parse_hot_value(v: Any) -> float:
    """Parse hot_value to a numeric score.

    Handles:
    - "530 万热度" -> 5300000
    - "4693012播放" -> 4693012
    - "1234567" -> 1234567
    """
    if v is None:
        return 0.0
    s = str(v)
    s = s.replace(",", "").strip()

    # Extract base number
    m = re.search(r"(\d+(?:\.\d+)?)", s)
    if not m:
        return 0.0
    num = float(m.group(1))

    # Multipliers
    if "亿" in s:
        num *= 1e8
    elif "万" in s:
        num *= 1e4
    elif "千" in s:
        num *= 1e3
    return num


def recent_titles(n: int) -> list[str]:
    titles: list[str] = []
    if n <= 0:
        return titles
    posts_dir = Path("content/posts")
    if not posts_dir.exists():
        return titles

    paths = sorted(posts_dir.glob("*.md"), key=lambda p: p.stat().st_mtime, reverse=True)[:n]
    for p in paths:
        try:
            txt = p.read_text(encoding="utf-8")
        except Exception:
            continue
        m = re.match(r"^---\n(.*?)\n---\n", txt, flags=re.S)
        if not m:
            continue
        fm = m.group(1)
        for line in fm.splitlines():
            if line.startswith("title:"):
                titles.append(line.split(":", 1)[1].strip().strip('"'))
                break
    return titles


def map_industry(title: str) -> str:
    t = title or ""

    rules = [
        ("finance", ["风控", "利率", "银行", "基金", "券商", "A股", "港股", "美股", "债", "通胀", "货币"]),
        ("healthcare", ["医疗", "医院", "药", "疫苗", "诊断", "影像", "健康"]),
        ("education", ["教育", "高考", "考研", "学习", "课程", "学校"]),
        ("automotive", ["汽车", "车企", "新能源车", "智驾", "座舱", "充电", "电池"]),
        ("retail", ["零售", "消费", "品牌", "电商", "门店", "直播带货", "用户增长", "私域"]),
        ("manufacturing", ["制造", "工厂", "产线", "工业", "机器人", "供应链", "交付", "良率"]),
        ("foreign_trade", ["外贸", "出海", "跨境", "关税", "航运", "运价", "海关", "清关"]),
        ("technology", ["AI", "大模型", "芯片", "GPU", "程序", "开发", "开源", "算法", "模型", "智能"]),
    ]
    for ind, kws in rules:
        if any(k in t for k in kws):
            return ind
    return "technology"


def title_quality(title: str) -> float:
    """Heuristic: prefer question/problem statements and explanatory titles."""
    t = norm_space(title)
    if not t:
        return 0.0
    score = 1.0
    if len(t) < 10:
        score *= 0.7
    if len(t) > 40:
        score *= 1.05
    if "为什么" in t or "如何" in t or "怎么" in t or "" in t:
        score *= 1.10
    if "？" in t or "?" in t:
        score *= 1.05
    # Penalize pure person-name / gossip-like patterns (very rough)
    if re.fullmatch(r"[\u4e00-\u9fff]{2,4}.*", t) and len(t) <= 14 and ("疑似" in t or "爆" in t):
        score *= 0.7
    return score


def fetch_type(tp: str, timeout: int = 20) -> dict:
    url = "https://uapis.cn/api/v1/misc/hotboard"
    r = requests.get(url, params={"type": tp}, timeout=timeout)
    r.raise_for_status()
    return r.json()


def build_payload(industry: str, items: list[dict], meta: dict) -> dict:
    return {
        "industry": industry,
        "collected_at": datetime.now(timezone.utc).isoformat(),
        "hours": 24,
        "limit": len(items),
        "count": len(items),
        "items": items,
        "meta": meta,
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--types", default=",".join(DEFAULT_TYPES))
    ap.add_argument("--max-types", type=int, default=4, help="Fetch at most N types each run (randomly sampled)")
    ap.add_argument("--top-per-type", type=int, default=10)
    ap.add_argument("--avoid-recent", type=int, default=20)
    ap.add_argument("--shell", action="store_true", help="Print INDUSTRY/TOPIC for shell")
    ap.add_argument("--seed", default=os.getenv("SEED", ""))
    ap.add_argument("--cache", default="data/cache/hotboard_cache.json")
    args = ap.parse_args()

    if args.seed:
        random.seed(args.seed)

    types = [t.strip() for t in args.types.split(",") if t.strip()]
    if not types:
        raise SystemExit("no types")

    # sample types to limit API calls
    if args.max_types > 0 and len(types) > args.max_types:
        types = random.sample(types, args.max_types)

    recents = recent_titles(args.avoid_recent)

    candidates: list[dict] = []
    fetched_types: list[str] = []

    def add_from_doc(doc: dict, tp: str) -> None:
        lst = doc.get("list") or []
        for it in lst[: args.top_per_type]:
            title = norm_space(it.get("title", ""))
            url = (it.get("url") or "").strip()
            hot_v = it.get("hot_value")
            if not title or not url:
                continue
            if contains_any(title, DENY_KEYWORDS):
                continue
            if recents and any(title in (t or "") for t in recents):
                continue

            hv = parse_hot_value(hot_v)
            w = PLATFORM_WEIGHT.get(tp, 1.0)
            q = title_quality(title)
            score = w * (hv if hv > 0 else 1.0) * q
            candidates.append(
                {
                    "platform": tp,
                    "title": title,
                    "url": url,
                    "hot_value": hot_v,
                    "score": score,
                    "extra": it.get("extra") or {},
                }
            )

    # Try live fetch first
    live_ok = False
    try:
        for tp in types:
            doc = fetch_type(tp)
            fetched_types.append(tp)
            add_from_doc(doc, tp)
        live_ok = True
        # cache raw response (best-effort)
        cache_path = Path(args.cache)
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        cache_path.write_text(
            json.dumps({"fetched_at": time.time(), "types": fetched_types, "candidates": candidates}, ensure_ascii=False),
            encoding="utf-8",
        )
    except Exception as e:
        print(f"⚠️ hotboard live fetch failed: {e}")

    # If live failed or empty, try cache (within 6h)
    if (not candidates) and Path(args.cache).exists():
        try:
            cache = json.loads(Path(args.cache).read_text(encoding="utf-8"))
            age = time.time() - float(cache.get("fetched_at", 0))
            if age <= 6 * 3600:
                candidates = list(cache.get("candidates") or [])
                fetched_types = list(cache.get("types") or [])
        except Exception:
            pass

    if not candidates:
        raise SystemExit("no candidates from hotboard")

    # pick top by score
    candidates.sort(key=lambda x: float(x.get("score", 0.0)), reverse=True)
    pick = candidates[0]

    topic = pick["title"]
    industry = map_industry(topic)

    # build sources items (compatible with generate_news_post)
    now = datetime.now(timezone.utc).isoformat()
    items_out: list[dict] = []
    for c in candidates[:10]:
        items_out.append(
            {
                "industry": industry,
                "source": f"hotboard:{c['platform']}",
                "title": c["title"],
                "url": c["url"],
                "published": now,
                "summary": f"hot_value: {c.get('hot_value','')} platform: {c.get('platform','')}",
                "content_text": f"热榜信号：{c['title']}｜热度：{c.get('hot_value','')}｜平台：{c.get('platform','')}\n链接：{c['url']}",
                "cover_image_url": None,
            }
        )

    payload = build_payload(
        industry,
        items_out,
        meta={
            "mode": "hotboard",
            "types_fetched": fetched_types,
            "live_ok": live_ok,
            "picked": {k: pick.get(k) for k in ["platform", "title", "url", "hot_value", "score"]},
        },
    )

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    if args.shell:
        print(f"{industry}\t{topic}")


if __name__ == "__main__":
    main()

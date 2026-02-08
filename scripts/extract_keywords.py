#!/usr/bin/env python3
"""Classify article type and extract keywords/tags/queries for image search.

Input: markdown path + optional news_json
Output: json to stdout

Heuristics (fast & transparent):
- type=event if many event tokens (比赛/发布会/广告/裁员/收购/融资) or named entities present
- type=analysis if many analysis tokens (趋势/影响/风险/机会/指标/模型/原理)

Keyword extraction:
- org/person/event/place terms from news titles (simple regex for Capitalized words + known tokens)
- scene tokens based on type

This is intentionally simple to start; we iterate based on quality logs.
"""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from pathlib import Path


ANALYSIS_TOKENS = ["趋势", "影响", "风险", "机会", "指标", "模型", "原理", "机制", "方法", "重塑", "范式", "结构"]
EVENT_TOKENS = ["发布", "发布会", "融资", "估值", "裁员", "收购", "广告", "比赛", "超级碗", "事故", "禁令", "监管", "起诉"]

# lightweight entity hints
KNOWN_ENTITIES = [
    "OpenAI",
    "Anthropic",
    "Google",
    "Apple",
    "Meta",
    "Amazon",
    "Microsoft",
    "Super Bowl",
    "Levi",
    "Levi’s Stadium",
    "Washington Post",
    "Tumblr",
]


def read_headings(md: str) -> list[str]:
    hs = []
    for ln in md.splitlines():
        if ln.startswith("## ") or ln.startswith("### "):
            hs.append(ln.lstrip("# ").strip())
    return hs


def classify(text: str) -> str:
    tl = (text or "").lower()
    if "超级碗" in text or "super bowl" in tl:
        return "event"

    a = sum(1 for t in ANALYSIS_TOKENS if t in text)
    e = sum(1 for t in EVENT_TOKENS if t in text)
    if e >= a and e >= 1:
        return "event"
    if a >= 2:
        return "analysis"
    return "mixed"


def extract_entities_from_titles(titles: list[str]) -> list[str]:
    ents = []
    # Capitalized phrases (rough)
    cap_re = re.compile(r"\b([A-Z][A-Za-z0-9&’']+(?:\s+[A-Z][A-Za-z0-9&’']+)*)\b")
    for t in titles:
        for m in cap_re.finditer(t):
            s = m.group(1)
            if len(s) < 3:
                continue
            if s.lower() in {"the", "and", "for", "with", "from"}:
                continue
            ents.append(s)
    for k in KNOWN_ENTITIES:
        if any(k in t for t in titles):
            ents.append(k)
    # normalize/unique
    ents = [x.strip() for x in ents if x.strip()]
    # drop too generic
    bad = {"AI", "GitHub", "Linux", "Hacker News"}
    ents = [x for x in ents if x not in bad]
    return list(dict.fromkeys(ents))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--md", required=True)
    ap.add_argument("--news-json", default="")
    ap.add_argument("--industry", default="")
    ap.add_argument("--title", default="")
    args = ap.parse_args()

    md_text = Path(args.md).read_text(encoding="utf-8")
    headings = read_headings(md_text)

    news_titles: list[str] = []
    if args.news_json:
        try:
            data = json.loads(Path(args.news_json).read_text(encoding="utf-8"))
            for it in (data.get("items") or [])[:25]:
                if it.get("title"):
                    news_titles.append(it["title"])
        except Exception:
            pass

    ctx = "\n".join([args.title or "", *headings, *news_titles, md_text[:2000]])
    typ = classify(ctx)

    # tags
    entities = extract_entities_from_titles(news_titles)
    tags = []
    if typ == "event":
        tags += ["事件", "现场", "品牌", "广告"]
    elif typ == "analysis":
        tags += ["分析", "趋势", "框架", "原理"]
    else:
        tags += ["行业", "观察"]

    # keep prominent event tokens
    for t in EVENT_TOKENS:
        if t in ctx and t not in tags:
            tags.append(t)

    # attach entities
    tags += entities[:12]

    # query candidates
    queries = []
    if typ == "event":
        # prefer actor + scene
        scene = []
        if "广告" in ctx or "ads" in ctx.lower() or "advert" in ctx.lower():
            scene += ["advertising", "commercial"]
        if "超级碗" in ctx or "super bowl" in ctx.lower():
            scene += ["Super Bowl", "stadium"]

        # special: Super Bowl
        if "超级碗" in ctx or "super bowl" in ctx.lower():
            queries += [
                "Super Bowl AI advertising",
                "Super Bowl ads AI",
                "Levi's Stadium Super Bowl",
            ]

        for e in entities[:8]:
            if any(x.lower() in e.lower() for x in ["openai", "anthropic", "google", "apple", "meta", "amazon", "microsoft"]):
                queries.append(f"{e} advertising")
                if scene:
                    queries.append(f"{e} {' '.join(scene[:2])}")

        # generic event fallback
        queries.append(f"{args.industry} conference stage audience")
    else:
        base = (args.title or "").strip() or (headings[0] if headings else "")
        if base:
            queries.append(base)
        queries.append(f"{args.industry} diagram")

    # final clean
    queries = [q for q in queries if q and len(q) >= 4]
    queries = list(dict.fromkeys(queries))[:12]

    print(
        json.dumps(
            {
                "type": typ,
                "industry": args.industry,
                "tags": list(dict.fromkeys(tags))[:30],
                "entities": entities[:20],
                "queries": queries,
                "headings": headings[:20],
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()

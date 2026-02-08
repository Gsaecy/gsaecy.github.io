#!/usr/bin/env python3
"""Generate a Hugo post from collected news payload.

Input: JSON from scripts/collect_news.py
Output:
- content/posts/<slug>.md
- downloads cover image into static/images/posts/<slug>/cover.(jpg|png|webp) when possible

Guarantees:
- Adds YAML front matter
- Includes citations with URLs
- Instructs model: do NOT fabricate data; only use provided sources

Usage:
  python3 scripts/generate_news_post.py --in data/raw/news.json --slug technology-20260203-080000 --title "..." --out content/posts/<slug>.md
"""

from __future__ import annotations

import argparse
import json
import os
import re
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import requests


def slugify(s: str) -> str:
    s = s.lower().strip()
    s = re.sub(r"[^a-z0-9\-\s]", "", s)
    s = re.sub(r"\s+", "-", s)
    s = re.sub(r"-+", "-", s)
    return s[:80].strip("-")


def download_cover(url: str, out_dir: Path) -> Optional[str]:
    if not url:
        return None
    out_dir.mkdir(parents=True, exist_ok=True)

    # guess extension
    ext = "jpg"
    m = re.search(r"\.(jpg|jpeg|png|webp)(\?|$)", url.lower())
    if m:
        ext = "jpg" if m.group(1) == "jpeg" else m.group(1)

    out_path = out_dir / f"cover.{ext}"

    try:
        r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=25)
        r.raise_for_status()
        out_path.write_bytes(r.content)
        return f"/images/posts/{out_dir.name}/{out_path.name}"
    except Exception:
        return None


def build_prompt(payload: Dict[str, Any], title: str, industry: str) -> str:
    items = payload.get("items", [])[:10]
    # Keep context small but rich: title, source, url, published, key excerpts
    def clip(s: str, n: int) -> str:
        s = (s or "").strip()
        return s[:n] + ("..." if len(s) > n else "")

    source_blocks = []
    for i, it in enumerate(items, 1):
        source_blocks.append(
            f"[{i}] {it.get('title','').strip()}\n"
            f"source: {it.get('source','')}\n"
            f"published: {it.get('published','')}\n"
            f"url: {it.get('url','')}\n"
            f"excerpt: {clip(it.get('content_text','') or it.get('summary',''), 1200)}\n"
        )

    return (
        "你是一个严谨的行业研究编辑。请基于【提供的素材】写一篇高质量行业文章，并适配微信公众号排版。"
        "如果【提供的素材】为空（items=0），请改写为‘趋势解读/方法论/框架型’文章：围绕主题给出背景、核心矛盾、关键变量、可操作建议，并明确说明‘今日素材为空，以下为基于公开常识与历史趋势的分析’。\n\n"
        "注意：封面图由系统另行生成并插入，请不要在正文中输出任何封面图/图片占位符/‘图1’之类说明。\n\n"
        "硬性规则（非常重要）：\n"
        "1) 只允许使用素材里出现的事实/数字/结论；不要编造任何数据、公司动作、政策细节。\n"
        "2) 文中出现的数据/结论必须在段尾用[编号]标注引用来源（例如：[1][3]）。\n"
        "3) 文末给出“来源列表”，按[编号]列出标题+URL。\n"
        "4) 文章不少于 1800 字，结构清晰：\n"
        "   - 核心摘要（3-5条）\n"
        "   - 今日要点（按主题分3-5节）\n"
        "   - 数据与指标（至少2节，尽量用素材里的数字；如果素材无数字，要明确写‘来源未披露具体数值’）\n"
        "   - 影响与机会（企业/从业者/投资者分别给建议）\n"
        "5) 语言：中文，专业但易读。\n\n"
        f"文章主题/标题：{title}\n"
        f"行业：{industry}\n\n"
        "素材如下（最多10条）：\n\n"
        + "\n---\n".join(source_blocks)
    )


def call_deepseek(prompt: str) -> str:
    api_key = os.getenv("DEEPSEEK_API_KEY")
    if not api_key:
        raise RuntimeError("DEEPSEEK_API_KEY not set")

    url = "https://api.deepseek.com/chat/completions"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    payload = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "system", "content": "你是严谨的行业研究编辑与事实核查员。"},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.4,
        "max_tokens": 4000,
    }

    # Network/API can occasionally timeout on GitHub runners.
    # Retry a few times with backoff to keep scheduled publishing stable.
    last_err: Exception | None = None
    for attempt in range(1, 4):
        try:
            r = requests.post(url, headers=headers, json=payload, timeout=180)
            r.raise_for_status()
            data = r.json()
            return data["choices"][0]["message"]["content"].strip()
        except (requests.exceptions.Timeout, requests.exceptions.ConnectionError, requests.exceptions.ChunkedEncodingError) as e:
            last_err = e
            sleep_s = 5 * attempt
            print(f"⚠️ deepseek request failed (attempt {attempt}/3), retry in {sleep_s}s: {e}")
            time.sleep(sleep_s)

    raise RuntimeError(f"DeepSeek request failed after retries: {last_err}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="inp", required=True)
    ap.add_argument("--slug", required=True)
    ap.add_argument("--title", required=True)
    ap.add_argument("--industry", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument(
        "--cover",
        required=False,
        default="",
        help="Optional cover image URL path (e.g. /images/posts/<slug>/cover.jpg). Overrides downloaded cover.",
    )
    args = ap.parse_args()

    payload = json.loads(Path(args.inp).read_text(encoding="utf-8"))

    if not payload.get("items"):
        # Soft-fallback: still generate an evergreen/analysis-style post driven by the topic/title.
        # This prevents the whole scheduled publish from failing when RSS temporarily returns 0 items.
        payload["items"] = []

    # cover
    cover_rel = (args.cover or "").strip() or None

    # If not provided, pick first available from sources and download.
    if not cover_rel:
        cover_url = None
        for it in payload.get("items", [])[:10]:
            if it.get("cover_image_url"):
                cover_url = it["cover_image_url"]
                break
        if cover_url:
            cover_rel = download_cover(cover_url, Path("static/images/posts") / args.slug)

    prompt = build_prompt(payload, args.title, args.industry)
    article_md = call_deepseek(prompt)

    now_cn = datetime.now(timezone(timedelta(hours=8)))
    front = {
        "title": args.title,
        "date": now_cn.isoformat(timespec="seconds"),
        "draft": False,
        "categories": [args.industry],
        "tags": [args.industry, "news", "AI分析"],
        "author": "AI智汇观察",
        "slug": args.slug,
    }
    if cover_rel:
        front["image"] = cover_rel

    # YAML front matter
    fm_lines = ["---"]
    for k, v in front.items():
        if isinstance(v, bool):
            fm_lines.append(f"{k}: {'true' if v else 'false'}")
        elif isinstance(v, list):
            fm_lines.append(f"{k}: {json.dumps(v, ensure_ascii=False)}")
        else:
            fm_lines.append(f"{k}: {json.dumps(v, ensure_ascii=False)}")
    fm_lines.append("---\n")

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    # Prepend cover to body to ensure consistent rendering
    body = article_md.strip()
    if cover_rel:
        body = f"![封面图]({cover_rel})\n\n" + body

    out_path.write_text("\n".join(fm_lines) + body + "\n", encoding="utf-8")
    print(f"✅ wrote post -> {out_path}")


if __name__ == "__main__":
    main()

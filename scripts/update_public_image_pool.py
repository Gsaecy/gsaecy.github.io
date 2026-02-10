#!/usr/bin/env python3
"""Update the flowing public image pool (metadata only).

- Extract keywords/queries for the current article
- Fetch candidates from Wikimedia Commons API
- Score candidates against context
- Merge into global pool (cap=2000)

This is intended to run on every publish (as training).
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from commons_fetch import search_images
from image_pool import cap_pool, load_pool, merge_items, save_pool


def maybe_cache_thumbnail(cache_dir: str, key: str, url: str) -> bool:
    if not cache_dir:
        return False
    try:
        import requests

        from pathlib import Path

        Path(cache_dir).mkdir(parents=True, exist_ok=True)
        out = Path(cache_dir) / f"{re.sub(r'[^A-Za-z0-9:_-]+', '_', key)}.jpg"
        if out.exists() and out.stat().st_size > 0:
            return True
        r = requests.get(url, timeout=20, headers={"User-Agent": "Mozilla/5.0"})
        r.raise_for_status()
        out.write_bytes(r.content)
        return True
    except Exception:
        return False


def get_image_metadata(image_id: str) -> dict:
    """获取 Wikimedia Commons 图片的元数据（描述、分类、标签）"""
    try:
        import requests
        # Wikimedia API: https://commons.wikimedia.org/w/api.php
        url = "https://commons.wikimedia.org/w/api.php"
        params = {
            "action": "query",
            "prop": "categories|info|imageinfo",
            "titles": f"File:{image_id}",
            "cllimit": "max",
            "iiprop": "extmetadata|url",
            "format": "json",
            "formatversion": "2",
        }
        r = requests.get(url, params=params, timeout=15)
        r.raise_for_status()
        data = r.json()
        pages = data.get("query", {}).get("pages", [])
        if not pages:
            return {}
        page = pages[0]
        
        metadata = {
            "description": "",
            "categories": [],
            "tags": [],
        }
        
        # 获取描述
        imageinfo = page.get("imageinfo", [{}])[0]
        extmetadata = imageinfo.get("extmetadata", {})
        if "ImageDescription" in extmetadata:
            metadata["description"] = extmetadata["ImageDescription"].get("value", "")
        
        # 获取分类
        categories = page.get("categories", [])
        metadata["categories"] = [cat["title"].replace("Category:", "") for cat in categories]
        
        # 从描述和分类中提取关键词作为标签
        all_text = metadata["description"] + " " + " ".join(metadata["categories"])
        # 简单的关键词提取：移除常见停用词，取有意义的单词
        words = re.findall(r'\b[a-zA-Z]{3,}\b', all_text.lower())
        stopwords = {"the", "and", "for", "with", "from", "this", "that", "are", "was", "were", "has", "have", "had"}
        metadata["tags"] = [w for w in words if w not in stopwords][:20]
        
        return metadata
    except Exception as e:
        print(f"获取图片元数据失败 {image_id}: {e}")
        return {}


def calculate_match_score(tags: list[str], image_tags: list[str], title: str, image_title: str) -> float:
    """计算文章关键词与图片标签的匹配度分数 (0-1)"""
    if not image_tags:
        return 0.3  # 没有标签的图片给基础分
    
    # 简单计算：共同标签比例
    tags_lower = [t.lower() for t in tags]
    image_tags_lower = [t.lower() for t in image_tags]
    
    common = set(tags_lower) & set(image_tags_lower)
    if not common:
        return 0.3
    
    # 匹配度 = 共同标签数 / (文章标签数 + 图片标签数 - 共同标签数)
    score = len(common) / (len(tags_lower) + len(image_tags_lower) - len(common))
    
    # 标题关键词匹配加分
    title_words = set(re.findall(r'\b[a-zA-Z]{3,}\b', title.lower()))
    image_title_words = set(re.findall(r'\b[a-zA-Z]{3,}\b', image_title.lower()))
    title_match = len(title_words & image_title_words) / max(len(title_words), 1)
    
    return min(0.3 + score * 0.5 + title_match * 0.2, 1.0)


def _text(s: str) -> str:
    return (s or "").strip()


def score_candidate(ctx: str, cand: dict, tags: list[str]) -> float:
    ctx_l = ctx.lower()
    title = (cand.get("title") or "").lower()
    lic = (cand.get("license") or "").lower()

    score = 0.0

    # tag matches
    for t in tags:
        tl = t.lower()
        if tl and (tl in ctx_l):
            score += 20
        if tl and (tl in title):
            score += 10

    # bonus for having explicit CC terms
    if "cc" in lic:
        score += 10

    # small penalty for obviously weird file titles
    if "meme" in title or "cartoon" in title:
        score -= 15

    return score


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--pool", default="data/public_image_pool.json")
    ap.add_argument("--cap", type=int, default=2000)
    ap.add_argument("--industry", required=True)
    ap.add_argument("--title", required=True)
    ap.add_argument("--md", required=True)
    ap.add_argument("--news-json", default="")
    ap.add_argument("--page-size", type=int, default=20)
    # Optional local cache (metadata-only pool still lives in JSON; cache stores thumbnails for quality checks)
    ap.add_argument("--cache-dir", default="")
    ap.add_argument("--cache-max-per-run", type=int, default=30)
    args = ap.parse_args()

    md_text = Path(args.md).read_text(encoding="utf-8")

    # extract keywords (invoke script for stability in both local + GH Actions)
    try:
        import subprocess

        cmd = [
            "python3",
            "scripts/extract_keywords.py",
            "--md",
            args.md,
            "--news-json",
            args.news_json,
            "--industry",
            args.industry,
            "--title",
            args.title,
        ]
        out = subprocess.check_output(cmd, text=True)
        kw = json.loads(out)
    except Exception:
        kw = {"tags": [], "queries": []}

    tags = kw.get("tags") or []
    queries = kw.get("queries") or []

    ctx = "\n".join([
        args.title,
        "\n".join([ln for ln in md_text.splitlines() if ln.startswith("## ") or ln.startswith("### ")])[:2000],
    ])

    new_items = []
    cached = 0
    for q in queries[:10]:
        cands = search_images(q, limit=max(5, min(args.page_size, 50)))
        for c in cands:
            if not _text(c.get("image_url")):
                continue
            
            # 获取图片元数据并计算匹配度
            image_id = c.get("id", "")
            image_meta = get_image_metadata(image_id) if image_id else {}
            image_tags = image_meta.get("tags", [])
            match_score = calculate_match_score(tags, image_tags, args.title, c.get("title", ""))
            
            it = {
                "provider": "wikimedia_commons",
                "id": image_id,
                "industry": args.industry,
                "title": c.get("title"),
                "url": c.get("url"),
                "image_url": c.get("image_url"),
                "license": c.get("license"),
                "license_url": c.get("license_url"),
                "tags": tags,
                "image_tags": image_tags,
                "match_score": match_score,  # 新增：关键词-标签匹配度
                "meta_description": image_meta.get("description", "")[:200],
                "meta_categories": image_meta.get("categories", [])[:10],
            }
            it["score"] = score_candidate(ctx, it, tags)
            it["key"] = f"wikimedia:{it.get('id')}"
            new_items.append(it)

            # Optional: cache thumbnail locally for future quality checks
            if args.cache_dir and cached < args.cache_max_per_run:
                thumb = _text(c.get("thumbnail")) or _text(c.get("image_url"))
                if thumb:
                    if maybe_cache_thumbnail(args.cache_dir, it["key"], thumb):
                        cached += 1

    pool = load_pool(args.pool)
    items = merge_items(pool.get("items") or [], new_items)
    items = cap_pool(items, cap=args.cap)

    save_pool({"version": 1, "items": items, "updated_at": pool.get("updated_at", "")}, path=args.pool)

    print(json.dumps({"added": len(new_items), "kept": len(items), "cached": cached, "queries": queries[:5]}, ensure_ascii=False))


if __name__ == "__main__":
    main()

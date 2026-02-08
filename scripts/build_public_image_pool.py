#!/usr/bin/env python3
"""Build/refresh the public image pool via Openverse API.

Goal: expand the pool to N images per industry with tags.
We use Openverse (open-license) as the primary cover source.

Usage:
  python3 scripts/build_public_image_pool.py --pool scripts/public_image_pool.yaml --per-industry 30
"""

from __future__ import annotations

import argparse
import time
from pathlib import Path

import yaml

from commons_fetch import search_images as fetch


QUERY_HINTS = {
    "technology": {
        "tags": ["AI", "人工智能", "chip", "circuit", "semiconductor", "data center", "cloud", "robot"],
        "queries": [
            "AI circuit board",
            "data center servers",
            "machine learning abstract",
            "robot arm factory ai",
            "cloud computing infrastructure",
        ],
    },
    "finance": {
        "tags": ["金融", "风控", "risk", "compliance", "fintech", "payment", "bank"],
        "queries": ["banking technology", "risk management", "fintech payment", "financial dashboard", "fraud detection"],
    },
    "healthcare": {
        "tags": ["医疗", "healthcare", "medtech", "diagnosis", "imaging", "AI"],
        "queries": ["medical technology AI", "diagnostic imaging", "hospital digital", "health data", "clinical laboratory"],
    },
    "education": {
        "tags": ["教育", "learning", "edtech", "课程", "online learning"],
        "queries": ["online learning", "education technology", "classroom technology", "training", "skills learning"],
    },
    "automotive": {
        "tags": ["汽车", "EV", "新能源", "battery", "charging", "autonomous"],
        "queries": ["electric vehicle charging", "EV battery", "autonomous driving", "car factory", "vehicle technology"],
    },
    "retail": {
        "tags": ["零售", "retail", "ecommerce", "warehouse", "inventory", "supply chain"],
        "queries": ["retail store", "ecommerce warehouse", "inventory management", "checkout", "consumer shopping"],
    },
    "manufacturing": {
        "tags": ["制造", "factory", "automation", "robot", "quality", "industrial"],
        "queries": ["smart factory", "industrial automation", "robotic arm factory", "manufacturing quality", "industrial iot"],
    },
    "foreign_trade": {
        "tags": ["外贸", "export", "shipping", "logistics", "customs", "tariff"],
        "queries": ["shipping containers port", "logistics supply chain", "cargo ship", "international trade", "customs inspection"],
    },
    "scientific_instruments": {
        "tags": ["科研", "仪器", "lab", "microscope", "spectrometer", "research"],
        "queries": ["laboratory microscope", "scientific instrument lab", "research laboratory equipment", "spectrometer", "laboratory automation"],
    },
    "reagents": {
        "tags": ["试剂", "reagent", "biotech", "PCR", "protein", "lab"],
        "queries": ["biotechnology laboratory", "PCR lab", "reagent bottles", "molecular biology", "cell culture"],
    },
}

def is_permissive(lic: str) -> bool:
    lic = (lic or "").strip().lower()
    if not lic:
        return False
    # commons license strings are often like: "CC BY-SA 4.0", "CC BY 4.0", "CC0 1.0"...
    allow_sub = [
        "cc0",
        "cc by",
        "cc-by",
        "cc by-sa",
        "cc-by-sa",
        "public domain",
        "pd-",
    ]
    return any(s in lic for s in allow_sub)


def _tokenize_tags(s: str) -> list[str]:
    s = (s or "").strip()
    if not s:
        return []
    # keep simple: split by non-word, preserve Chinese fragments as-is by not lowercasing them
    import re

    parts = re.split(r"[^A-Za-z0-9\u4e00-\u9fff\-]+", s)
    out = []
    for p in parts:
        p = p.strip()
        if len(p) < 2:
            continue
        out.append(p)
    return out


def _mk_item(industry: str, base_tags: list[str], ov: dict, weight: int) -> dict:
    title = ov.get("title") or ""
    tags = list(dict.fromkeys(base_tags + _tokenize_tags(title)))  # dedupe keep order
    return {
        "id": ov.get("id"),
        "industry": industry,
        "tags": tags[:30],
        "title": title,
        "url": ov.get("url") or "",
        "image_url": ov.get("image_url") or "",
        "license": (ov.get("license") or "").upper(),
        "license_url": ov.get("license_url") or "",
        "provider": ov.get("provider") or "openverse",
        "weight": weight,
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--pool", default="scripts/public_image_pool.yaml")
    ap.add_argument("--per-industry", type=int, default=30)
    ap.add_argument("--page-size", type=int, default=50)
    args = ap.parse_args()

    target = max(5, min(args.per_industry, 60))
    doc = {"version": 1, "source": "wikimedia_commons", "generated": True, "pool": []}

    for industry, cfg in QUERY_HINTS.items():
        print(f"[pool] building {industry} ...")
        base_tags = cfg.get("tags") or []
        queries = cfg.get("queries") or []

        picked: list[dict] = []
        seen = set()

        for qi, q in enumerate(queries):
            # fetch many results via larger page_size
            res = fetch(q, limit=min(args.page_size, 50))
            # keep permissive licenses only
            for ov in res:
                if len(picked) >= target:
                    break
                oid = ov.get("id")
                if not oid or oid in seen:
                    continue
                lic = ov.get("license") or ""
                if not is_permissive(lic):
                    continue
                if not (ov.get("image_url") or "").strip():
                    continue
                weight = 100 - qi  # earlier query gets slightly higher
                picked.append(_mk_item(industry, base_tags + _tokenize_tags(q), ov, weight))
                seen.add(oid)
            if len(picked) >= target:
                break
            print(f"[pool] {industry}: {len(picked)}/{target} after query {qi+1}/{len(queries)}")
            time.sleep(0.12)

        # If still not enough, relax: accept any license that is at least explicitly Creative Commons.
        if len(picked) < target:
            for q in queries[:2] or [industry]:
                res = fetch(q, limit=min(args.page_size, 50))
                for ov in res:
                    if len(picked) >= target:
                        break
                    oid = ov.get("id")
                    if not oid or oid in seen:
                        continue
                    lic = (ov.get("license") or "")
                    if "cc" not in lic.lower() and "public domain" not in lic.lower():
                        continue
                    if not (ov.get("image_url") or "").strip():
                        continue
                    picked.append(_mk_item(industry, base_tags + _tokenize_tags(q), ov, 50))
                    seen.add(oid)
                if len(picked) >= target:
                    break
                time.sleep(0.12)

        print(f"[pool] done {industry}: {len(picked)}")
        doc["pool"].extend(picked)

    Path(args.pool).write_text(yaml.safe_dump(doc, allow_unicode=True, sort_keys=False), encoding="utf-8")
    print(f"generated pool items={len(doc['pool'])} -> {args.pool}")


if __name__ == "__main__":
    main()

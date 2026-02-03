#!/usr/bin/env python3
"""Auto-illustrate Hugo posts with data-driven charts.

Goal:
- When a post contains a markdown table with numeric data, generate a simple chart image
  from that table (via QuickChart) and save into static/images/posts/<slug>/.
- Insert the chart markdown right after the table, with a clear caption and source note.

Constraints:
- No API keys.
- Always include an image source statement (data source + chart renderer).

Usage:
  python3 scripts/auto_illustrate.py content/posts/my-post.md

Outputs:
  - Updates the markdown file in-place (adds image + caption)
  - Writes images under static/images/posts/<slug>/chart-<n>.png
"""

from __future__ import annotations

import json
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Tuple

import requests

QUICKCHART_ENDPOINT = "https://quickchart.io/chart"


@dataclass
class Table:
    header: List[str]
    rows: List[List[str]]
    start_idx: int
    end_idx: int


def slug_from_filename(path: Path) -> str:
    return path.stem


def looks_like_year_or_quarter(s: str) -> bool:
    s = s.strip()
    return bool(re.search(r"\b(19|20)\d{2}\b", s)) or bool(re.search(r"\bQ[1-4]\b", s, re.IGNORECASE))


def parse_markdown_tables(lines: List[str]) -> List[Table]:
    """Very small markdown table parser.

    Detect blocks of lines that look like:
      | a | b |
      |---|---|
      | 1 | 2 |

    Returns tables with indices [start_idx, end_idx) in lines.
    """

    tables: List[Table] = []
    i = 0
    while i < len(lines) - 1:
        line = lines[i]
        if line.lstrip().startswith("|") and "|" in line:
            # candidate header line
            if i + 1 < len(lines) and re.match(r"^\|\s*:?[-]+", lines[i + 1].strip()):
                start = i
                header = [c.strip() for c in line.strip().strip("|").split("|")]
                i += 2
                rows: List[List[str]] = []
                while i < len(lines) and lines[i].lstrip().startswith("|"):
                    row = [c.strip() for c in lines[i].strip().strip("|").split("|")]
                    # normalize row length
                    if len(row) < len(header):
                        row += [""] * (len(header) - len(row))
                    rows.append(row)
                    i += 1
                end = i
                if rows:
                    tables.append(Table(header=header, rows=rows, start_idx=start, end_idx=end))
                continue
        i += 1
    return tables


def pick_series_from_table(t: Table) -> Optional[Tuple[List[str], List[float], str]]:
    """Pick a reasonable label/value series from a table.

    Strategy:
    - Use first column as labels.
    - Find first column (from 2nd onward) that contains mostly numeric values.

    Returns (labels, values, value_col_name) or None.
    """

    if len(t.header) < 2:
        return None

    labels = [r[0].strip() for r in t.rows if r and r[0].strip()]
    if not labels:
        return None

    # find numeric column
    def to_float(x: str) -> Optional[float]:
        x = x.strip()
        if not x:
            return None
        # handle percentages and commas and chinese units very roughly
        x = x.replace(",", "")
        mult = 1.0
        if x.endswith("%"):
            x = x[:-1]
        if x.endswith("万"):
            x = x[:-1]
            mult = 10000.0
        if x.endswith("亿"):
            x = x[:-1]
            mult = 100000000.0
        try:
            return float(x) * mult
        except ValueError:
            return None

    best = None
    for col in range(1, len(t.header)):
        vals_raw = [r[col] if col < len(r) else "" for r in t.rows]
        vals = [to_float(v) for v in vals_raw]
        numeric = [v for v in vals if v is not None]
        if len(numeric) >= max(3, int(0.6 * len(vals))):
            best = (labels, [v if v is not None else 0.0 for v in vals], t.header[col])
            break

    return best


def detect_data_source(t: Table) -> str:
    # if there is a column that contains 来源
    for idx, h in enumerate(t.header):
        if "来源" in h:
            # collect unique sources
            srcs = set()
            for r in t.rows:
                if idx < len(r) and r[idx].strip():
                    srcs.add(r[idx].strip())
            if srcs:
                return "、".join(sorted(srcs))
    return "文中表格"


def build_chart_config(labels: List[str], values: List[float], title: str) -> dict:
    chart_type = "bar"
    if any(looks_like_year_or_quarter(x) for x in labels[: min(6, len(labels))]):
        chart_type = "line"

    cfg = {
        "type": chart_type,
        "data": {
            "labels": labels,
            "datasets": [
                {
                    "label": title,
                    "data": values,
                    "borderColor": "#2563eb",
                    "backgroundColor": "rgba(37,99,235,0.2)",
                    "fill": chart_type == "line",
                }
            ],
        },
        "options": {
            "plugins": {"legend": {"display": True}, "title": {"display": True, "text": title}},
            "scales": {"y": {"beginAtZero": True}},
        },
    }
    return cfg


def download_chart_png(cfg: dict, out_path: Path, width: int = 1200, height: int = 630) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)

    params = {
        "c": json.dumps(cfg, ensure_ascii=False),
        "format": "png",
        "width": str(width),
        "height": str(height),
        "backgroundColor": "white",
        "devicePixelRatio": "2",
    }
    r = requests.get(QUICKCHART_ENDPOINT, params=params, timeout=60)
    r.raise_for_status()
    out_path.write_bytes(r.content)


def already_has_chart_after(lines: List[str], end_idx: int) -> bool:
    # look ahead 6 lines for an image under /images/posts/
    look = "\n".join(lines[end_idx : min(len(lines), end_idx + 8)])
    return "/images/posts/" in look and ("![" in look or "<img" in look)


def insert_chart_markdown(lines: List[str], table: Table, rel_img_url: str, fig_index: int, caption: str) -> List[str]:
    insert_at = table.end_idx
    block = [
        "",
        f"![{caption}]({rel_img_url})",
        f"图{fig_index}：{caption}",
        "",
    ]
    return lines[:insert_at] + block + lines[insert_at:]


def is_key_table(t: Table) -> bool:
    joined = " ".join(" ".join(r) for r in t.rows)
    # placeholder tables should not be considered key tables
    if "待更新" in joined:
        return False

    header_text = " ".join(t.header)
    if any(k in header_text for k in ["来源", "数据来源"]):
        return True
    if any(k in header_text for k in ["销量", "市场", "份额", "增长", "渗透", "规模", "收入", "用户", "装机"]):
        return True
    joined = " ".join(" ".join(r) for r in t.rows)
    if "待更新" in joined:
        return False
    return len(t.rows) >= 3 and bool(re.search(r"\d", joined))


def process_post(md_path: Path, key_only: bool = True) -> int:
    text = md_path.read_text(encoding="utf-8")
    lines = text.splitlines()

    tables = parse_markdown_tables(lines)
    if not tables:
        return 0

    slug = slug_from_filename(md_path)
    static_dir = md_path.parent.parent.parent / "static"  # repo-root/static
    # If script is run from repo root, md_path is content/posts/.. and static exists.
    # But to be safe, resolve relative to repo root by walking up.
    # Detect repo root: find directory containing 'static' and 'content'.
    repo_root = md_path
    for _ in range(6):
        repo_root = repo_root.parent
        if (repo_root / "content").exists() and (repo_root / "static").exists():
            break
    else:
        repo_root = Path.cwd()

    img_dir = repo_root / "static" / "images" / "posts" / slug

    fig = 0
    # We will rebuild lines iteratively; indices shift after insertion
    offset = 0
    for t in tables:
        if key_only and (not is_key_table(t)):
            continue
        t2 = Table(t.header, t.rows, t.start_idx + offset, t.end_idx + offset)
        if already_has_chart_after(lines, t2.end_idx):
            continue
        series = pick_series_from_table(t2)
        if not series:
            continue
        labels, values, value_col = series
        fig += 1
        data_source = detect_data_source(t2)
        title = value_col if value_col else "数据"
        cfg = build_chart_config(labels, values, title)

        img_name = f"chart-{fig}.png"
        out_path = img_dir / img_name
        download_chart_png(cfg, out_path)

        rel_url = f"/images/posts/{slug}/{img_name}"
        caption = f"{title}（数据来源：{data_source}；图表生成：QuickChart）"
        lines = insert_chart_markdown(lines, t2, rel_url, fig, caption)
        offset += 4

    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return fig


def main() -> None:
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument("--all", action="store_true", help="Illustrate all numeric tables (default: key tables only)")
    ap.add_argument("posts", nargs="+", help="Markdown post paths")
    args = ap.parse_args()

    total = 0
    for p in args.posts:
        md = Path(p)
        if not md.exists():
            print(f"Skip missing: {md}")
            continue
        n = process_post(md, key_only=(not args.all))
        print(f"Illustrated {md}: {n} chart(s)")
        total += n

    print(f"Done. Total charts: {total}")


if __name__ == "__main__":
    main()

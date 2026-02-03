#!/usr/bin/env python3
"""Validate illustration requirements for a post.

Rules (per user):
- At least 1 public image with attribution (Wikimedia Commons) in the article.
- Each key table must have 1 chart image inserted after it.

Usage:
  python3 scripts/validate_illustrations.py content/posts/my-post.md

Exit codes:
  0 pass
  2 fail
"""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import List


@dataclass
class Table:
    header: List[str]
    rows: List[List[str]]
    start_idx: int
    end_idx: int


def parse_markdown_tables(lines: List[str]) -> List[Table]:
    tables: List[Table] = []
    i = 0
    while i < len(lines) - 1:
        line = lines[i]
        if line.lstrip().startswith("|") and "|" in line:
            if i + 1 < len(lines) and re.match(r"^\|\s*:?[-]+", lines[i + 1].strip()):
                start = i
                header = [c.strip() for c in line.strip().strip("|").split("|")]
                i += 2
                rows: List[List[str]] = []
                while i < len(lines) and lines[i].lstrip().startswith("|"):
                    row = [c.strip() for c in lines[i].strip().strip("|").split("|")]
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
    # if table has >=3 rows and at least one cell contains a digit and not just placeholders
    joined = " ".join(" ".join(r) for r in t.rows)
    if "待更新" in joined:
        return False
    return len(t.rows) >= 3 and bool(re.search(r"\d", joined))


def has_chart_after(lines: List[str], end_idx: int) -> bool:
    look = "\n".join(lines[end_idx : min(len(lines), end_idx + 10)])
    return "/images/posts/" in look and "chart-" in look and "![" in look


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: python3 scripts/validate_illustrations.py <post.md>")
        sys.exit(2)

    md_path = Path(sys.argv[1])
    text = md_path.read_text(encoding="utf-8")
    lines = text.splitlines()

    ok = True

    # Rule 1: at least one public image attribution line
    if not re.search(r"图片来源：Wikimedia Commons", text):
        print("FAIL: missing public image (Wikimedia Commons) with attribution")
        ok = False

    # Rule 2: each key table has a chart
    tables = parse_markdown_tables(lines)
    key_tables = [t for t in tables if is_key_table(t)]
    for idx, t in enumerate(key_tables, start=1):
        if not has_chart_after(lines, t.end_idx):
            print(f"FAIL: key table #{idx} missing chart after table")
            ok = False

    if ok:
        print("PASS: illustration requirements satisfied")
        sys.exit(0)
    sys.exit(2)


if __name__ == "__main__":
    main()

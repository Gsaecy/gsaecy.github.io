#!/usr/bin/env python3
"""Apply WeChat formatting to ALL Hugo posts in content/posts.

Goal: Make the blog content consistent with the WeChat-friendly style,
while preserving Hugo front matter.

- Skips files ending with -wechat.md or -quality-report.md
- Preserves YAML (---) or TOML (+++) front matter blocks
- Formats only the body with WeChatFormatter
"""

from __future__ import annotations

import re
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from format_wechat import WeChatFormatter  # local module shim

POSTS_DIR = ROOT / "content" / "posts"

FRONT_MATTER_DELIMS = ("---", "+++")


def split_front_matter(text: str):
    lines = text.splitlines(True)
    if not lines:
        return "", ""

    first = lines[0].strip()
    if first not in FRONT_MATTER_DELIMS:
        return "", text

    delim = first
    # find closing delimiter
    for i in range(1, len(lines)):
        if lines[i].strip() == delim:
            fm = "".join(lines[: i + 1]).rstrip("\n")
            body = "".join(lines[i + 1 :]).lstrip("\n")
            return fm, body

    # malformed front matter -> treat as no front matter
    return "", text


def main() -> int:
    if not POSTS_DIR.exists():
        raise SystemExit(f"Missing dir: {POSTS_DIR}")

    formatter = WeChatFormatter()

    changed = 0
    for path in sorted(POSTS_DIR.glob("*.md")):
        name = path.name
        if name.endswith("-wechat.md") or name.endswith("-quality-report.md"):
            continue

        raw = path.read_text(encoding="utf-8")
        fm, body = split_front_matter(raw)

        # Avoid double-appending the standard footer if it already exists.
        if "本文由AI智汇观察系统自动生成" in body:
            # still normalize formatting so the page looks consistent
            pass

        formatted_body = formatter.format_article(body)

        out = (fm + "\n\n" if fm else "") + formatted_body.strip() + "\n"
        if out != raw:
            path.write_text(out, encoding="utf-8")
            changed += 1

    print(f"Updated {changed} post(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

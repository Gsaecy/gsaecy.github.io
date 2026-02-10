#!/usr/bin/env python3
"""Add public images (Wikimedia Commons) to a Hugo post.

No API keys.

Behavior:
- Extract a few keyword queries from title/headings (very simple heuristic)
- Fetch 1-2 relevant images from Wikimedia Commons
- Save into static/images/posts/<slug>/
- Insert markdown images near the beginning and near a key section
- Always add attribution (source + license + file page)

Usage:
  python3 scripts/auto_add_public_images.py content/posts/my-post.md
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path
from typing import List, Tuple


def repo_root_from(path: Path) -> Path:
    p = path.resolve()
    for _ in range(8):
        if (p / "content").exists() and (p / "static").exists():
            return p
        p = p.parent
    return Path.cwd()


def extract_front_matter_title(md_text: str) -> str:
    # YAML front matter between --- ... ---
    m = re.match(r"^---\n(.*?)\n---\n", md_text, flags=re.S)
    if not m:
        return ""
    fm = m.group(1)
    for line in fm.splitlines():
        if line.startswith("title:"):
            return line.split(":", 1)[1].strip().strip('"')
    return ""


def extract_queries(md_text: str) -> List[str]:
    # Prefer front matter title (we may remove H1 from body), then fall back to headings.
    lines = md_text.splitlines()
    title = extract_front_matter_title(md_text)
    headings = []
    for ln in lines[:160]:
        if (not title) and ln.startswith("# "):
            title = ln[2:].strip()
        if ln.startswith("## "):
            headings.append(ln[3:].strip())

    base = title or "industry analysis"

    # crude domain mapping based on Chinese keywords
    # keep it minimal and predictable
    mapping = [
        ("新能源汽车", "electric vehicle"),
        ("电池", "battery"),
        ("充电", "charging station"),
        ("智能驾驶", "autonomous driving"),
        ("医疗", "medical technology"),
        ("金融", "financial technology"),
        ("教育", "online learning"),
    ]

    hints = []
    for zh, en in mapping:
        if zh in md_text:
            hints.append(en)

    # Build up to 3 queries
    queries = []
    if hints:
        queries.append(" ".join(hints[:2]))

    # Title keywords (strip punctuation). Also add a stable "AI" hint if present.
    base2 = re.sub(r"[\W_]+", " ", base)
    if "AI" in md_text or "人工智能" in md_text:
        base2 = ("AI " + base2).strip()

    if base2.strip():
        queries.append(base2.strip())

    if headings:
        h = re.sub(r"[\W_]+", " ", headings[0])
        if h.strip():
            queries.append(h.strip())

    # dedupe
    out = []
    for q in queries:
        q = q.strip()
        if q and q not in out:
            out.append(q)
    return out[:3]


def already_has_public_images(md_text: str) -> bool:
    # Treat either Wikimedia-inserted images or default cover as “has image”.
    return (
        ("/images/posts/" in md_text and "图片来源" in md_text)
        or ("/images/default-cover." in md_text)
    )


def insert_near_explainer_section(lines: List[str], block: List[str]) -> List[str]:
    """Insert block *not* at the very top.

    Hard rule:
    - The beginning of the article should contain ONLY ONE image (the cover).

    Strategy (in order):
    1) If a cover image line exists ("![封面图](...)"), insert AFTER that cover line.
    2) Else insert after the first matching H2 section among: 数据/指标/原理/方法/机制
    3) Else insert after the 2nd H2
    4) Else insert after the first non-empty paragraph line (never right after front matter)

    Important: never insert inside YAML front matter.
    """

    # find end of front matter
    fm_end = 0
    if lines and lines[0].strip() == "---":
        for i in range(1, min(len(lines), 200)):
            if lines[i].strip() == "---":
                fm_end = i + 1
                break

    # 1) detect cover image line (but DO NOT insert immediately after it;
    # we must keep the beginning with only one image.)
    cover_idx = -1
    for i in range(fm_end, min(len(lines), fm_end + 120)):
        ln = lines[i].strip()
        if ln.startswith("![封面图]") and "(/images/posts/" in ln:
            cover_idx = i
            break

    # find H2 anchors (after cover if present)
    h2_idx = []
    for i, ln in enumerate(lines):
        if cover_idx != -1 and i <= cover_idx:
            continue
        if ln.startswith("## "):
            h2_idx.append(i)

    # 2) preferred keywords
    keywords = ["数据", "指标", "原理", "机制", "方法", "模型", "技术栈"]
    for i in h2_idx:
        if any(k in lines[i] for k in keywords):
            return lines[: i + 1] + [""] + block + [""] + lines[i + 1 :]

    # 3) after 2nd H2
    if len(h2_idx) >= 2:
        i = h2_idx[1]
        return lines[: i + 1] + [""] + block + [""] + lines[i + 1 :]

    # 4) after first non-empty paragraph that is NOT a heading (H2/H3) or image
    # 硬规则：公共图必须与封面图至少间隔一个自然段落（非标题、非图片）
    start = fm_end
    if cover_idx != -1:
        start = cover_idx + 1
    
    # 跳过空白行
    while start < len(lines) and not lines[start].strip():
        start += 1
    
    # 如果封面后直接是标题（## 或 ###）或另一个图片，继续往下找
    while start < len(lines):
        line = lines[start].strip()
        if not line:
            start += 1
            continue
        # 如果是标题或图片，跳过
        if line.startswith("## ") or line.startswith("### ") or line.startswith("![") or line == "---":
            start += 1
            # 跳过可能的空白行
            while start < len(lines) and not lines[start].strip():
                start += 1
            continue
        # 找到第一个非标题、非图片的行（应该是正文段落）
        break
    
    # 如果没找到合适的插入点，放到文件末尾
    if start >= len(lines):
        return lines + [""] + block
    
    # 插入在这个段落之后
    return lines[: start + 1] + [""] + block + [""] + lines[start + 1 :]


def build_block(rel_url: str, alt: str, fig_no: int, source_line: str) -> List[str]:
    return [
        f"![{alt}]({rel_url})",
        f"图{fig_no}：{alt}",
        source_line,
    ]


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: python3 scripts/auto_add_public_images.py <post.md>")
        sys.exit(1)

    md_path = Path(sys.argv[1])
    txt = md_path.read_text(encoding="utf-8")
    if already_has_public_images(txt):
        print("Skip: already has public images with attribution")
        return

    root = repo_root_from(md_path)
    slug = md_path.stem
    outdir = root / "static" / "images" / "posts" / slug

    queries = extract_queries(txt)
    picked = None

    for q in queries:
        meta_path = outdir / "wikimedia-meta.json"
        cmd = [
            sys.executable,
            str(root / "scripts" / "fetch_wikimedia_images.py"),
            "--query",
            q,
            "--outdir",
            str(outdir),
            "--limit",
            "1",
            "--outfile",
            str(meta_path),
        ]
        subprocess.run(cmd, check=False)
        if meta_path.exists():
            data = json.loads(meta_path.read_text(encoding="utf-8"))
            if data.get("count"):
                picked = data["items"][0]
                break

    if not picked:
        # Fallback: insert a default cover image (user-provided) so every post has a visual.
        default_cover = root / "static" / "images" / "default-cover.png"
        if default_cover.exists():
            rel_url = "/images/default-cover.png"
            alt = "封面图"
            source_line = "图片来源：自制封面图（AI智汇观察）"

            lines = txt.splitlines()
            fig_no = 1
            m = re.findall(r"图(\d+)：", txt)
            if m:
                fig_no = max(int(x) for x in m) + 1

            block = build_block(rel_url, alt, fig_no, source_line)
            lines2 = insert_near_explainer_section(lines, block)
            md_path.write_text("\n".join(lines2) + "\n", encoding="utf-8")
            print(f"Inserted default cover image into {md_path}")
            return

        print("No suitable Wikimedia image found and no default cover present")
        return

    # Build insertion
    saved = Path(picked["saved_as"]).name
    rel_url = f"/images/posts/{slug}/{saved}"

    license_name = (picked.get("license") or "")
    license_url = (picked.get("license_url") or "")
    file_page = (picked.get("file_page") or picked.get("descriptionurl") or "")

    alt = "相关配图（公共素材）"
    source_line = f"图片来源：Wikimedia Commons（{file_page}）；许可：{license_name}（{license_url}）"

    lines = txt.splitlines()

    # Determine next figure number based on existing 图N
    fig_no = 1
    m = re.findall(r"图(\d+)：", txt)
    if m:
        fig_no = max(int(x) for x in m) + 1

    block = build_block(rel_url, alt, fig_no, source_line)
    lines2 = insert_near_explainer_section(lines, block)

    md_path.write_text("\n".join(lines2) + "\n", encoding="utf-8")
    print(f"Inserted 1 public image into {md_path}")


if __name__ == "__main__":
    main()

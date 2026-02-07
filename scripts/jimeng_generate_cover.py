#!/usr/bin/env python3
"""Generate a cover image via Volcengine Jimeng (text-to-image v3.0).

This script:
- submits an async task (CVSync2AsyncSubmitTask)
- polls for result (CVSync2AsyncGetResult)
- downloads the first returned image url (jpeg)

Auth:
- Uses Volcengine signature v4 (same scheme as AWS SigV4)
- Requires env: VOLC_ACCESS_KEY_ID, VOLC_SECRET_ACCESS_KEY

Usage:
  python3 scripts/jimeng_generate_cover.py --slug xxx --title "..." --industry retail --out static/images/posts/xxx/cover.jpg
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import hmac
import json
import os
import time
from pathlib import Path
from typing import Any, Dict, Tuple

import requests

HOST = "visual.volcengineapi.com"
ENDPOINT = f"https://{HOST}"
REGION = "cn-north-1"
SERVICE = "cv"
VERSION = "2022-08-31"


def _sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _hmac_sha256(key: bytes, msg: str) -> bytes:
    return hmac.new(key, msg.encode("utf-8"), hashlib.sha256).digest()


def _sign_v4(method: str, path: str, query: str, headers: Dict[str, str], body: bytes, ak: str, sk: str) -> Dict[str, str]:
    """Return headers including Authorization for Volcengine."""
    # Dates
    t = dt.datetime.utcnow()
    amz_date = t.strftime("%Y%m%dT%H%M%SZ")
    date_stamp = t.strftime("%Y%m%d")

    # Required headers
    headers = {k.lower(): v.strip() for k, v in headers.items()}
    headers["host"] = HOST
    headers["x-date"] = amz_date
    payload_hash = _sha256_hex(body)
    headers["x-content-sha256"] = payload_hash

    # Canonical headers
    sorted_header_keys = sorted(headers.keys())
    canonical_headers = "".join([f"{k}:{headers[k]}\n" for k in sorted_header_keys])
    signed_headers = ";".join(sorted_header_keys)

    canonical_request = "\n".join(
        [
            method.upper(),
            path,
            query,
            canonical_headers,
            signed_headers,
            payload_hash,
        ]
    )

    algorithm = "HMAC-SHA256"
    credential_scope = f"{date_stamp}/{REGION}/{SERVICE}/request"
    string_to_sign = "\n".join(
        [
            algorithm,
            amz_date,
            credential_scope,
            _sha256_hex(canonical_request.encode("utf-8")),
        ]
    )

    # Derive signing key
    k_date = _hmac_sha256(sk.encode("utf-8"), date_stamp)
    k_region = hmac.new(k_date, REGION.encode("utf-8"), hashlib.sha256).digest()
    k_service = hmac.new(k_region, SERVICE.encode("utf-8"), hashlib.sha256).digest()
    k_signing = hmac.new(k_service, b"request", hashlib.sha256).digest()

    signature = hmac.new(k_signing, string_to_sign.encode("utf-8"), hashlib.sha256).hexdigest()

    authorization = (
        f"{algorithm} Credential={ak}/{credential_scope}, SignedHeaders={signed_headers}, Signature={signature}"
    )

    out = {k.title(): v for k, v in headers.items()}
    out["Authorization"] = authorization
    return out


def _post(action: str, body_json: Dict[str, Any]) -> Dict[str, Any]:
    ak = os.getenv("VOLC_ACCESS_KEY_ID")
    sk = os.getenv("VOLC_SECRET_ACCESS_KEY")
    if not ak or not sk:
        raise RuntimeError("VOLC_ACCESS_KEY_ID / VOLC_SECRET_ACCESS_KEY not set")

    path = "/"
    query = f"Action={action}&Version={VERSION}"
    url = f"{ENDPOINT}?{query}"
    body = json.dumps(body_json, ensure_ascii=False).encode("utf-8")

    base_headers = {
        "Content-Type": "application/json",
    }
    signed = _sign_v4("POST", path, query, base_headers, body, ak, sk)

    r = requests.post(url, headers=signed, data=body, timeout=60)
    r.raise_for_status()
    return r.json()


def submit_task(prompt: str, width: int, height: int, seed: int = -1) -> str:
    resp = _post(
        "CVSync2AsyncSubmitTask",
        {
            "req_key": "jimeng_t2i_v30",
            "prompt": prompt,
            "seed": seed,
            "width": width,
            "height": height,
            "use_pre_llm": True,
        },
    )
    if resp.get("code") != 10000:
        raise RuntimeError(f"submit_task failed: {resp}")
    task_id = (resp.get("data") or {}).get("task_id")
    if not task_id:
        raise RuntimeError(f"submit_task no task_id: {resp}")
    return task_id


def get_result(task_id: str, return_url: bool = True) -> Dict[str, Any]:
    req_json = json.dumps({"return_url": bool(return_url)}, ensure_ascii=False)
    resp = _post(
        "CVSync2AsyncGetResult",
        {
            "req_key": "jimeng_t2i_v30",
            "task_id": task_id,
            "req_json": req_json,
        },
    )
    return resp


def build_prompt(title: str, industry: str) -> str:
    # Style: safe, professional, consistent
    return (
        "为一个行业资讯博客生成封面图。风格：现代、专业、科技感扁平插画，干净背景，低饱和配色，细节适中。"
        "画面包含抽象的行业元素与数据可视化符号（折线/柱状/网格）。不要出现具体品牌Logo。"
        "不要出现长段文字；如需文字，只允许 6-10 个中文以内的短标题。"
        f"主题：{title}。行业：{industry}。"
        "构图：居中主体，留白充足，适合作为文章封面。"
    )


def download_image(url: str, out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    r = requests.get(url, timeout=60)
    r.raise_for_status()
    out_path.write_bytes(r.content)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--slug", required=True)
    ap.add_argument("--title", required=True)
    ap.add_argument("--industry", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--width", type=int, default=1664)
    ap.add_argument("--height", type=int, default=936)
    ap.add_argument("--poll-seconds", type=int, default=120)
    args = ap.parse_args()

    prompt = build_prompt(args.title, args.industry)
    task_id = submit_task(prompt, args.width, args.height)

    deadline = time.time() + args.poll_seconds
    last = None
    while time.time() < deadline:
        last = get_result(task_id, return_url=True)
        if last.get("code") == 10000 and (last.get("data") or {}).get("status") == "done":
            data = last.get("data") or {}
            urls = data.get("image_urls") or []
            if urls:
                download_image(urls[0], Path(args.out))
                print(f"✅ jimeng cover saved -> {args.out}")
                return
            b64s = data.get("binary_data_base64") or []
            if b64s:
                import base64

                Path(args.out).parent.mkdir(parents=True, exist_ok=True)
                Path(args.out).write_bytes(base64.b64decode(b64s[0]))
                print(f"✅ jimeng cover saved(base64) -> {args.out}")
                return
            raise RuntimeError(f"done but no images: {last}")

        time.sleep(3)

    raise RuntimeError(f"timeout waiting jimeng result: {last}")


if __name__ == "__main__":
    main()

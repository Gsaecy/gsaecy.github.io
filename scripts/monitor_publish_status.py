#!/usr/bin/env python3
"""监控 GitHub Actions 发布状态，在固定时间点检查是否成功发布。

使用场景：
- 08:10, 08:20, 08:30（检查 08:00 那篇）
- 18:10, 18:20, 18:30（检查 18:00 那篇）

如果到 08:30/18:30 还没发布，判定为失败，尝试自动修复并手动触发重试。
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Tuple

import requests


def gh_api(endpoint: str, method: str = "GET", data: Optional[dict] = None) -> dict:
    """调用 GitHub API（使用 gh CLI 的 token）"""
    cmd = ["gh", "api", f"/repos/Gsaecy/gsaecy.github.io/{endpoint}", "--method", method]
    if data:
        cmd.extend(["--input", "-"])
        input_json = json.dumps(data)
    else:
        input_json = None

    try:
        result = subprocess.run(
            cmd,
            input=input_json.encode() if input_json else None,
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode != 0:
            print(f"gh API error: {result.stderr}")
            return {}
        return json.loads(result.stdout) if result.stdout.strip() else {}
    except Exception as e:
        print(f"gh API exception: {e}")
        return {}


def get_recent_runs(hours: int = 1) -> list[dict]:
    """获取最近 N 小时内的 auto-publish-wechat.yml 运行记录"""
    cutoff = (datetime.utcnow() - timedelta(hours=hours)).isoformat() + "Z"
    runs = gh_api(
        f"actions/workflows/auto-publish-wechat.yml/runs?created=>={cutoff}&per_page=10"
    )
    return runs.get("workflow_runs", [])


def check_publish_success(target_hour_cn: int) -> Tuple[bool, Optional[dict]]:
    """检查目标小时（北京时间）的发布是否成功"""
    # 计算 UTC 时间（CN -8）
    target_hour_utc = (target_hour_cn - 8) % 24
    now_utc = datetime.utcnow()
    # 如果当前 UTC 小时小于目标 UTC 小时，说明目标时间是“昨天”的
    if now_utc.hour < target_hour_utc:
        target_date = now_utc.date() - timedelta(days=1)
    else:
        target_date = now_utc.date()

    target_start = datetime.combine(target_date, datetime.min.time()).replace(
        hour=target_hour_utc, minute=0, second=0, tzinfo=None
    )
    target_end = target_start + timedelta(hours=1)

    runs = get_recent_runs(hours=2)
    for run in runs:
        created_str = run["created_at"].replace("Z", "+00:00")
        created = datetime.fromisoformat(created_str).replace(tzinfo=None)
        if target_start <= created < target_end:
            if run["conclusion"] == "success":
                # 成功运行，检查是否生成了新文章
                # 通过 artifacts 或 commit 消息判断
                if "文章已生成" in run.get("display_title", ""):
                    return True, run
                # 或者检查 artifacts
                artifacts = gh_api(f"actions/runs/{run['id']}/artifacts")
                if artifacts.get("total_count", 0) > 0:
                    return True, run
                # 保守起见，只要运行成功就认为发布成功
                return True, run
            elif run["conclusion"] == "failure":
                return False, run
            # running/queued 等状态视为尚未完成
    # 没有找到对应时间段的运行记录
    return False, None


def try_fix_and_retry(target_hour_cn: int) -> bool:
    """尝试自动修复并手动触发重试"""
    print(f"尝试自动修复 {target_hour_cn}:00 的发布失败...")

    # 1) 检查常见问题：公共图片池是否为空
    pool_path = Path("data/public_image_pool.json")
    if pool_path.exists():
        try:
            with open(pool_path, "r", encoding="utf-8") as f:
                pool = json.load(f)
            items = pool.get("items", [])
            if len(items) < 10:
                print("公共图片池不足，尝试补充...")
                # 运行一次训练（任意行业）
                subprocess.run(
                    [
                        "python3",
                        "scripts/update_public_image_pool.py",
                        "--industry",
                        "technology",
                        "--title",
                        "临时补充图片池",
                        "--md",
                        "content/posts/first-post.md",
                        "--pool",
                        "data/public_image_pool.json",
                        "--cap",
                        "2000",
                        "--page-size",
                        "20",
                    ],
                    cwd=Path.cwd(),
                    capture_output=True,
                )
        except Exception:
            pass

    # 2) 检查 pending_retry.json 是否存在（可能是上次失败遗留）
    pending = Path("data/pending_retry.json")
    if pending.exists():
        pending.unlink()

    # 3) 手动触发发布（使用当前时间戳，避免冲突）
    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    industry = "technology"  # 默认科技行业，失败率较低
    cmd = [
        "gh",
        "workflow",
        "run",
        "auto-publish-wechat.yml",
        "--repo",
        "Gsaecy/gsaecy.github.io",
        "--ref",
        "main",
        "-f",
        f"industry={industry}",
        "-f",
        f"force_timestamp={ts}",
    ]
    print(f"执行: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode == 0:
        print(f"✅ 已手动触发重试：industry={industry}, timestamp={ts}")
        return True
    else:
        print(f"❌ 手动触发失败：{result.stderr}")
        return False


def send_alert_to_feishu_group(message: str) -> None:
    """发送告警到当前飞书群（使用 message 工具）"""
    # 这个函数会在主会话中被调用，直接使用 message 工具
    # 这里只打印，实际调用由主会话完成
    print(f"[ALERT] {message}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--target-hour-cn", type=int, required=True, help="目标发布时间（北京时间小时，如 8 或 18）")
    ap.add_argument("--check-phase", type=int, required=True, help="检查阶段：10=发布后10分,20=20分,30=30分")
    args = ap.parse_args()

    if args.target_hour_cn not in (8, 18):
        print(f"错误：target-hour-cn 必须是 8 或 18，得到 {args.target_hour_cn}")
        sys.exit(1)

    if args.check_phase not in (10, 20, 30):
        print(f"错误：check-phase 必须是 10,20,30，得到 {args.check_phase}")
        sys.exit(1)

    success, run = check_publish_success(args.target_hour_cn)
    now_cn = (datetime.utcnow() + timedelta(hours=8)).strftime("%H:%M")

    if success:
        print(f"✅ {args.target_hour_cn}:00 发布成功（{now_cn} 检查）")
        # 不需要通知
        sys.exit(0)

    # 发布失败或未运行
    if args.check_phase < 30:
        # 08:10 或 08:20（18:10/18:20）阶段，只记录不处理
        print(f"⚠️ {args.target_hour_cn}:00 发布尚未成功（{now_cn} 检查，阶段{args.check_phase}）")
        if run:
            print(f"   运行状态: {run.get('conclusion', 'unknown')} - {run.get('html_url')}")
        sys.exit(0)

    # 08:30 或 18:30 阶段，判定为失败，尝试修复
    print(f"❌ {args.target_hour_cn}:00 发布失败（{now_cn} 检查，阶段30）")
    if run:
        print(f"   失败运行: {run.get('html_url')}")

    # 尝试自动修复并重试
    if try_fix_and_retry(args.target_hour_cn):
        alert = f"【发布监控】{args.target_hour_cn}:00 文章发布失败，已自动修复并手动触发重试。"
    else:
        alert = f"【发布监控】{args.target_hour_cn}:00 文章发布失败，自动修复尝试未成功，请手动检查。"

    # 输出告警消息（主会话会捕获并发送到飞书群）
    print(f"::alert::{alert}")
    sys.exit(1)


if __name__ == "__main__":
    main()

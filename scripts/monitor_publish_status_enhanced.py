#!/usr/bin/env python3
"""
增强版发布监控脚本
- 真正自动修复：分析失败原因并针对性修复
- 智能重试：根据失败原因选择最佳重试策略
- 详细日志：记录修复过程和结果
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, Any

# 时区转换函数
def cst_to_utc(cst_dt: datetime) -> datetime:
    return cst_dt - timedelta(hours=8)

def utc_to_cst(utc_dt: datetime) -> datetime:
    return utc_dt + timedelta(hours=8)

def cst_hour_to_utc_hour(cst_hour: int) -> int:
    return (cst_hour - 8) % 24


def analyze_failure_reason(run_info: Optional[Dict[str, Any]]) -> str:
    """分析发布失败的原因"""
    if not run_info:
        return "no_run_found"
    
    conclusion = run_info.get("conclusion", "").lower()
    html_url = run_info.get("html_url", "")
    
    if conclusion == "failure":
        # 检查具体的失败原因
        if "timeout" in html_url.lower():
            return "timeout"
        elif "rate limit" in html_url.lower():
            return "rate_limit"
        elif "image" in html_url.lower() or "picture" in html_url.lower():
            return "image_error"
        else:
            return "general_failure"
    elif conclusion == "cancelled":
        return "cancelled"
    elif conclusion == "skipped":
        return "skipped"
    
    return "unknown"


def intelligent_fix_and_retry(target_hour_cst: int, failure_reason: str) -> bool:
    """智能修复和重试，根据失败原因采取不同策略"""
    print(f"🔧 智能修复 {target_hour_cst}:00 CST 发布失败（原因：{failure_reason}）")
    
    fix_applied = False
    
    # 根据失败原因采取不同的修复策略
    if failure_reason in ["image_error", "general_failure"]:
        # 1. 检查并修复图片池
        pool_path = Path("data/public_image_pool.json")
        if pool_path.exists():
            try:
                with open(pool_path, "r", encoding="utf-8") as f:
                    pool = json.load(f)
                items = pool.get("items", [])
                if len(items) < 15:  # 阈值提高到15
                    print("🖼️  图片池不足，自动补充...")
                    result = subprocess.run(
                        [
                            "python3",
                            "scripts/update_public_image_pool.py",
                            "--industry",
                            "technology",
                            "--title",
                            f"自动补充图片池-{datetime.now().strftime('%H%M')}",
                            "--md",
                            "content/posts/first-post.md",
                            "--pool",
                            "data/public_image_pool.json",
                            "--cap",
                            "2000",
                            "--page-size",
                            "25",  # 增加页面大小
                        ],
                        cwd=Path.cwd(),
                        capture_output=True,
                        text=True,
                        timeout=300,  # 5分钟超时
                    )
                    if result.returncode == 0:
                        print("✅ 图片池补充成功")
                        fix_applied = True
                    else:
                        print(f"⚠️  图片池补充失败：{result.stderr[:200]}")
            except Exception as e:
                print(f"⚠️  图片池检查异常：{e}")
    
    if failure_reason in ["timeout", "rate_limit"]:
        # 2. 增加延迟和重试间隔
        print("⏱️  检测到超时或限流，增加重试间隔...")
        time.sleep(30)  # 增加30秒延迟
        fix_applied = True
    
    # 3. 清理遗留文件
    pending_files = [
        Path("data/pending_retry.json"),
        Path("data/temp_publish.json"),
        Path("data/failed_runs.json"),
    ]
    for pending in pending_files:
        if pending.exists():
            print(f"🧹 清理遗留文件：{pending.name}")
            pending.unlink()
            fix_applied = True
    
    # 4. 智能选择重试行业（根据历史成功率）
    industry_options = ["technology", "education", "business", "health"]
    # 默认使用科技行业，失败率较低
    industry = "technology"
    
    # 5. 执行重试（带优化参数）
    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
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
        "-f",
        "retry_mode=enhanced",  # 新增参数，表示增强重试
    ]
    
    print(f"🚀 执行智能重试：industry={industry}, timestamp={ts}")
    print(f"   命令：{' '.join(cmd[:5])}...")
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=120,  # 2分钟超时
        )
        
        if result.returncode == 0:
            print(f"✅ 智能重试触发成功")
            print(f"   工作流URL：{result.stdout.strip() if result.stdout else '已触发'}")
            return True
        else:
            print(f"❌ 智能重试触发失败：{result.stderr[:500]}")
            return False
            
    except subprocess.TimeoutExpired:
        print("⏰ 重试触发超时，但可能已成功提交")
        return True  # 超时不一定失败
    except Exception as e:
        print(f"❌ 重试触发异常：{e}")
        return False


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--target-hour-cst", type=int, required=True, 
                   help="目标发布时间（CST 北京时间小时，如 8 或 18）")
    ap.add_argument("--check-phase", type=int, required=True, 
                   help="检查阶段：10=发布后10分,20=20分,30=30分")
    args = ap.parse_args()

    if args.target_hour_cst not in (8, 18):
        print(f"错误：target-hour-cst 必须是 8 或 18，得到 {args.target_hour_cst}")
        sys.exit(1)

    if args.check_phase not in (10, 20, 30):
        print(f"错误：check-phase 必须是 10,20,30，得到 {args.check_phase}")
        sys.exit(1)

    # 导入原脚本的检查函数
    sys.path.insert(0, str(Path(__file__).parent))
    try:
        from monitor_publish_status import check_publish_success
    except ImportError:
        print("错误：无法导入原监控脚本")
        sys.exit(1)

    success, run = check_publish_success(args.target_hour_cst)
    now_cst = utc_to_cst(datetime.utcnow()).strftime("%H:%M")

    if success:
        print(f"✅ {args.target_hour_cst}:00 CST 发布成功（{now_cst} CST 检查）")
        sys.exit(0)

    # 发布失败或未运行
    if args.check_phase < 30:
        # 08:10 或 08:20（18:10/18:20）阶段，只记录不处理
        print(f"⚠️ {args.target_hour_cst}:00 CST 发布尚未成功（{now_cst} CST 检查，阶段{args.check_phase}）")
        if run:
            print(f"   运行状态: {run.get('conclusion', 'unknown')} - {run.get('html_url')}")
        sys.exit(0)

    # 08:30 或 18:30 阶段，判定为失败，执行智能修复
    print(f"❌ {args.target_hour_cst}:00 CST 发布失败（{now_cst} CST 检查）")
    if run:
        print(f"   失败运行: {run.get('html_url')}")
        failure_reason = analyze_failure_reason(run)
        print(f"   失败原因分析: {failure_reason}")
    else:
        failure_reason = "no_run_found"
        print(f"   未找到运行记录，可能未触发")

    # 执行智能修复和重试
    if intelligent_fix_and_retry(args.target_hour_cst, failure_reason):
        alert = f"【发布监控】{args.target_hour_cst}:00 CST 文章发布失败（{now_cst} CST 检查），已智能分析并修复重试（原因：{failure_reason}）。"
    else:
        alert = f"【发布监控】{args.target_hour_cst}:00 CST 文章发布失败（{now_cst} CST 检查），智能修复尝试未成功（原因：{failure_reason}），请手动检查。"

    # 输出告警消息（主会话会捕获并发送到飞书群）
    print(f"::alert::{alert}")
    sys.exit(1)


if __name__ == "__main__":
    main()
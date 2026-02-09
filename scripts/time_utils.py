#!/usr/bin/env python3
"""时间转换工具：CST（北京时间） ↔ UTC

所有用户输入/输出时间都是 CST（Asia/Shanghai）。
内部处理（GitHub Actions cron、API 查询等）使用 UTC。
"""

from __future__ import annotations

import argparse
from datetime import datetime, timedelta
from typing import Optional


def cst_to_utc(cst_dt: datetime) -> datetime:
    """CST（北京时间）转 UTC"""
    # CST = UTC+8
    return cst_dt - timedelta(hours=8)


def utc_to_cst(utc_dt: datetime) -> datetime:
    """UTC 转 CST（北京时间）"""
    # CST = UTC+8
    return utc_dt + timedelta(hours=8)


def parse_cst_time(
    time_str: str, date_str: Optional[str] = None, fmt: str = "%H:%M"
) -> datetime:
    """解析 CST 时间字符串（如 "08:00"）"""
    now = datetime.now()
    if date_str:
        full_str = f"{date_str} {time_str}"
        dt = datetime.strptime(full_str, "%Y-%m-%d %H:%M")
    else:
        # 使用今天日期
        today = now.strftime("%Y-%m-%d")
        full_str = f"{today} {time_str}"
        dt = datetime.strptime(full_str, "%Y-%m-%d %H:%M")
    return dt


def format_cst(dt: datetime) -> str:
    """格式化 CST 时间输出"""
    return dt.strftime("%Y-%m-%d %H:%M:%S CST")


def format_utc(dt: datetime) -> str:
    """格式化 UTC 时间输出"""
    return dt.strftime("%Y-%m-%d %H:%M:%S UTC")


def cst_hour_to_utc_hour(cst_hour: int) -> int:
    """CST 小时数转 UTC 小时数"""
    return (cst_hour - 8) % 24


def utc_hour_to_cst_hour(utc_hour: int) -> int:
    """UTC 小时数转 CST 小时数"""
    return (utc_hour + 8) % 24


def main() -> None:
    ap = argparse.ArgumentParser(description="CST ↔ UTC 时间转换工具")
    ap.add_argument("--cst", help="CST 时间（格式: HH:MM 或 YYYY-MM-DD HH:MM）")
    ap.add_argument("--utc", help="UTC 时间（格式: HH:MM 或 YYYY-MM-DD HH:MM）")
    ap.add_argument("--hour-only", action="store_true", help="只转换小时数")
    args = ap.parse_args()

    if args.cst and args.utc:
        print("错误：不能同时指定 --cst 和 --utc")
        return

    if args.hour_only:
        if args.cst:
            try:
                hour = int(args.cst)
                if 0 <= hour <= 23:
                    utc_hour = cst_hour_to_utc_hour(hour)
                    print(f"CST {hour:02d}:00 → UTC {utc_hour:02d}:00")
                else:
                    print(f"错误：小时数必须在 0-23 之间，得到 {hour}")
            except ValueError:
                print(f"错误：'{args.cst}' 不是有效的小时数")
        elif args.utc:
            try:
                hour = int(args.utc)
                if 0 <= hour <= 23:
                    cst_hour = utc_hour_to_cst_hour(hour)
                    print(f"UTC {hour:02d}:00 → CST {cst_hour:02d}:00")
                else:
                    print(f"错误：小时数必须在 0-23 之间，得到 {hour}")
            except ValueError:
                print(f"错误：'{args.utc}' 不是有效的小时数")
        else:
            now_cst = datetime.now()
            now_utc = cst_to_utc(now_cst)
            print(f"当前时间：{format_cst(now_cst)} / {format_utc(now_utc)}")
        return

    if args.cst:
        try:
            if " " in args.cst:
                cst_dt = datetime.strptime(args.cst, "%Y-%m-%d %H:%M")
            else:
                cst_dt = parse_cst_time(args.cst)
            utc_dt = cst_to_utc(cst_dt)
            print(f"CST: {format_cst(cst_dt)}")
            print(f"UTC: {format_utc(utc_dt)}")
        except ValueError as e:
            print(f"解析错误：{e}")
            print("格式应为：HH:MM 或 YYYY-MM-DD HH:MM")
    elif args.utc:
        try:
            if " " in args.utc:
                utc_dt = datetime.strptime(args.utc, "%Y-%m-%d %H:%M")
            else:
                today = datetime.now().strftime("%Y-%m-%d")
                utc_dt = datetime.strptime(f"{today} {args.utc}", "%Y-%m-%d %H:%M")
            cst_dt = utc_to_cst(utc_dt)
            print(f"UTC: {format_utc(utc_dt)}")
            print(f"CST: {format_cst(cst_dt)}")
        except ValueError as e:
            print(f"解析错误：{e}")
            print("格式应为：HH:MM 或 YYYY-MM-DD HH:MM")
    else:
        now_cst = datetime.now()
        now_utc = cst_to_utc(now_cst)
        print(f"当前时间：{format_cst(now_cst)} / {format_utc(now_utc)}")
        print(f"GitHub Actions cron 对应关系：")
        print(f"  CST 08:00 → UTC 00:00")
        print(f"  CST 18:00 → UTC 10:00")


if __name__ == "__main__":
    main()

#!/bin/bash
# 检查18:00文章发布状态（30分）

# 切换到工作目录
cd /Users/guohongyu/clawd

# 执行监控脚本
echo "执行监控脚本..."
output=$(python3 scripts/monitor_publish_status.py --target-hour-cst 18 --check-phase 30 2>&1)

echo "脚本输出："
echo "$output"

# 检查是否包含alert行
if echo "$output" | grep -q "::alert::"; then
    alert_message=$(echo "$output" | grep "::alert::" | sed 's/::alert:://')
    echo "检测到告警消息：$alert_message"
    echo "请手动将此消息发送到飞书群（oc_88d707b078ea9bd990cced07272b28e5）"
else
    echo "没有检测到告警消息，无需发送通知。"
fi
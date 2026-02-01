#!/bin/bash

# 持续推送脚本
# 策略：推送 → 失败 → 等待2分钟 → 重试 → 直到成功

echo "🔄 开始持续推送策略..."
echo "每次失败后等待2分钟重试"
echo "========================="

SUCCESS=false
ATTEMPT=1

while [ "$SUCCESS" = false ]; do
    echo ""
    echo "尝试 #${ATTEMPT} - $(date '+%H:%M:%S')"
    
    # 尝试推送
    if git push origin main 2>&1; then
        echo "✅ 推送成功!"
        SUCCESS=true
    else
        echo "❌ 推送失败"
        ATTEMPT=$((ATTEMPT + 1))
        
        echo "⏳ 等待2分钟重试..."
        sleep 120
    fi
done

echo ""
echo "🎉 推送成功完成!"
echo "总尝试次数: ${ATTEMPT}"
echo "完成时间: $(date)"
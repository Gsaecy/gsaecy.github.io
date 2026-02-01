#!/bin/bash

# 带重试的推送脚本
# 策略：失败后等待2分钟再重试，直到成功

echo "🚀 开始带重试的推送..."
echo "策略: 失败 → 等待2分钟 → 重试"
echo "=============================="

MAX_RETRIES=10
RETRY_COUNT=0
SUCCESS=false

while [ $RETRY_COUNT -lt $MAX_RETRIES ] && [ "$SUCCESS" = false ]; do
    RETRY_COUNT=$((RETRY_COUNT + 1))
    
    echo ""
    echo "尝试 #${RETRY_COUNT} - $(date '+%H:%M:%S')"
    
    # 尝试推送
    if git push origin main 2>&1 | tee /tmp/push-output.txt; then
        echo "✅ 推送成功!"
        SUCCESS=true
        break
    else
        echo "❌ 推送失败"
        
        # 检查错误信息
        if grep -q "fast-forward" /tmp/push-output.txt; then
            echo "⚠️  需要先拉取远程变更"
            echo "执行: git pull --rebase origin main"
            git pull --rebase origin main
        fi
        
        if [ $RETRY_COUNT -lt $MAX_RETRIES ]; then
            echo "⏳ 等待2分钟重试..."
            sleep 120
        else
            echo "❌ 达到最大重试次数 (${MAX_RETRIES})"
        fi
    fi
done

if [ "$SUCCESS" = true ]; then
    echo ""
    echo "🎉 推送成功完成!"
    echo "重试次数: ${RETRY_COUNT}"
    echo "完成时间: $(date)"
    
    # 显示推送后的状态
    echo ""
    echo "📋 推送后的工作流:"
    ls -la .github/workflows/ 2>/dev/null || echo "无工作流文件"
    
    echo ""
    echo "🚀 下一步: 测试终极工作流"
    echo "运行命令:"
    echo "  gh workflow run \"Ultimate Blog Workflow\" --repo Gsaecy/Gsaecy.github.io --field action=verify"
else
    echo ""
    echo "⚠️  推送失败，建议:"
    echo "1. 检查网络连接"
    echo "2. 在GitHub页面手动创建工作流"
    echo "3. 稍后重试"
fi
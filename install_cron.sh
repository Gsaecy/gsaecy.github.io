#!/bin/bash
# 安装定时任务脚本

echo "🔧 开始安装定时任务..."
echo ""

# 检查当前cron任务
echo "📋 当前cron任务:"
crontab -l 2>/dev/null || echo "   (无)"

echo ""
echo "📝 准备安装新的定时任务..."

# 创建临时cron文件
TEMP_CRON=$(mktemp)

# 添加新的定时任务
cat > "$TEMP_CRON" << 'EOF'
# AI博客自动化定时任务
# 每天发布3篇文章

# 10:00发布 - 科技行业
0 10 * * * cd /Users/guohongyu/clawd && ./scripts/enhanced_daily_publishing.sh >> logs/cron_10_00.log 2>&1

# 14:00发布 - 电商行业
0 14 * * * cd /Users/guohongyu/clawd && ./scripts/enhanced_daily_publishing.sh >> logs/cron_14_00.log 2>&1

# 18:00发布 - 制造行业
0 18 * * * cd /Users/guohongyu/clawd && ./scripts/enhanced_daily_publishing.sh >> logs/cron_18_00.log 2>&1

# 监控任务（每30分钟检查一次）
*/30 * * * * cd /Users/guohongyu/clawd && python3 scripts/monitor_publish_status_enhanced.py --target-hour-cst 18 --check-phase 30 >> logs/monitor.log 2>&1
EOF

echo "✅ 创建临时cron文件: $TEMP_CRON"
echo ""

# 安装cron任务
echo "🚀 安装定时任务..."
if crontab "$TEMP_CRON"; then
    echo "✅ 定时任务安装成功！"
else
    echo "❌ 定时任务安装失败"
    echo "请尝试手动安装:"
    echo "  crontab $TEMP_CRON"
    exit 1
fi

echo ""
echo "🔍 验证安装:"
crontab -l

echo ""
echo "📊 定时任务详情:"
echo "   1. 10:00 - 科技行业发布"
echo "   2. 14:00 - 电商行业发布"  
echo "   3. 18:00 - 制造行业发布"
echo "   4. 每30分钟 - 发布状态监控"
echo ""
echo "📁 日志文件:"
echo "   - logs/cron_10_00.log"
echo "   - logs/cron_14_00.log"
echo "   - logs/cron_18_00.log"
echo "   - logs/monitor.log"
echo ""
echo "🎉 安装完成！定时任务将在指定时间自动执行。"

# 清理临时文件
rm -f "$TEMP_CRON"
echo ""
echo "🧹 临时文件已清理"
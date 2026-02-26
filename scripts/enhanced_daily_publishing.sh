#!/bin/bash
# 增强版每日发布脚本
# 每天发布3篇文章：10:00, 14:00, 18:00

set -e  # 遇到错误时退出

echo "🚀 开始每日三篇文章发布流程..."
echo "当前时间: $(date '+%Y-%m-%d %H:%M:%S')"
echo ""

# 设置工作目录
cd "$(dirname "$0")/.."
echo "工作目录: $(pwd)"
echo ""

# 检查依赖
echo "🔍 检查系统依赖..."
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 未安装"
    exit 1
fi

if ! command -v git &> /dev/null; then
    echo "❌ Git 未安装"
    exit 1
fi

echo "✅ 系统依赖检查通过"
echo ""

# 检查环境变量
echo "🔍 检查环境变量..."
if [ -z "$DEEPSEEK_API_KEY" ]; then
    echo "⚠️  DEEPSEEK_API_KEY 未设置，使用模拟数据模式"
fi

echo "✅ 环境检查完成"
echo ""

# 获取当前时间决定执行哪个发布
current_hour=$(date +%H)
current_minute=$(date +%M)

echo "⏰ 当前时间: ${current_hour}:${current_minute}"
echo ""

# 根据时间执行不同的发布
case "${current_hour}" in
    "09"|"10"|"11")
        echo "📅 执行10:00科技行业发布..."
        python3 scripts/simple_automation.py --industry technology --time "10:00"
        echo "✅ 10:00发布完成"
        ;;
        
    "13"|"14"|"15")
        echo "📅 执行14:00电商行业发布..."
        python3 scripts/simple_automation.py --industry ecommerce --time "14:00"
        echo "✅ 14:00发布完成"
        ;;
        
    "17"|"18"|"19")
        echo "📅 执行18:00制造行业发布..."
        python3 scripts/simple_automation.py --industry manufacturing --time "18:00"
        echo "✅ 18:00发布完成"
        ;;
        
    *)
        echo "⏸️  非发布时段，跳过执行"
        echo "发布时段: 10:00, 14:00, 18:00"
        exit 0
        ;;
esac

echo ""
echo "📊 发布结果检查..."
echo ""

# 检查是否生成了新文章
new_posts=$(find content/posts -name "*.md" -mmin -60 2>/dev/null | wc -l)

if [ "$new_posts" -gt 0 ]; then
    echo "🎉 成功生成 ${new_posts} 篇新文章"
    
    # 显示生成的文章
    echo "📝 生成的文章:"
    find content/posts -name "*.md" -mmin -60 2>/dev/null | while read post; do
        filename=$(basename "$post")
        echo "  - ${filename}"
    done
    
    # 提交更改
    echo ""
    echo "💾 提交更改到Git..."
    git add content/posts/ data/ logs/ -f
    
    if git diff --cached --quiet; then
        echo "📝 没有需要提交的更改"
    else
        timestamp=$(date +"%Y%m%d-%H%M%S")
        git commit -m "🤖 AI自动生成文章 [${timestamp}]"
        git push origin main
        echo "✅ 更改已提交并推送"
    fi
else
    echo "⚠️  未检测到新文章生成"
    echo "可能需要检查:"
    echo "  1. API密钥配置"
    echo "  2. 网络连接"
    echo "  3. 脚本执行权限"
fi

echo ""
echo "🏁 脚本执行完成"
echo "完成时间: $(date '+%Y-%m-%d %H:%M:%S')"

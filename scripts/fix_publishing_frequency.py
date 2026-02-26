#!/usr/bin/env python3
"""
修复发布频率问题
- 确保每天发布3篇文章
- 优化发布时间安排
- 修复相关配置
"""

import os
import sys
import yaml
from pathlib import Path
import datetime

def update_config_max_posts():
    """更新配置文件中的最大发布数量"""
    config_path = Path("config/config.yaml")
    
    if not config_path.exists():
        print(f"❌ 配置文件不存在: {config_path}")
        return False
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        # 更新最大发布数量
        if 'publishing' in config and 'hugo' in config['publishing']:
            config['publishing']['hugo']['max_posts_per_day'] = 3
            print("✅ 更新 max_posts_per_day: 3")
        
        # 更新内容生成计划
        if 'content_generation' in config and 'daily_schedule' in config['content_generation']:
            config['content_generation']['daily_schedule'] = [
                {"time": "10:00", "type": "行业日报", "length": "中等（800-1200字）", "industries": ["科技"]},
                {"time": "14:00", "type": "深度分析", "length": "较长（1500-2000字）", "industries": ["电商"]},
                {"time": "18:00", "type": "晚间简报", "length": "简短（300-500字）", "industries": ["制造"]}
            ]
            print("✅ 更新 daily_schedule: 3个时间段")
        
        # 保存更新后的配置
        with open(config_path, 'w', encoding='utf-8') as f:
            yaml.dump(config, f, allow_unicode=True, sort_keys=False)
        
        print("✅ 配置文件更新完成")
        return True
        
    except Exception as e:
        print(f"❌ 更新配置文件失败: {e}")
        return False

def create_enhanced_publishing_script():
    """创建增强版发布脚本"""
    script_content = '''#!/bin/bash
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
'''
    
    script_path = Path("scripts/enhanced_daily_publishing.sh")
    
    try:
        with open(script_path, 'w', encoding='utf-8') as f:
            f.write(script_content)
        
        # 设置执行权限
        os.chmod(script_path, 0o755)
        
        print(f"✅ 创建增强版发布脚本: {script_path}")
        print(f"   执行权限已设置: 755")
        return True
        
    except Exception as e:
        print(f"❌ 创建脚本失败: {e}")
        return False

def setup_cron_jobs():
    """设置定时任务"""
    cron_content = '''# AI博客自动化定时任务
# 每天发布3篇文章

# 10:00发布 - 科技行业
0 10 * * * cd /Users/guohongyu/clawd && ./scripts/enhanced_daily_publishing.sh >> logs/cron_10_00.log 2>&1

# 14:00发布 - 电商行业
0 14 * * * cd /Users/guohongyu/clawd && ./scripts/enhanced_daily_publishing.sh >> logs/cron_14_00.log 2>&1

# 18:00发布 - 制造行业
0 18 * * * cd /Users/guohongyu/clawd && ./scripts/enhanced_daily_publishing.sh >> logs/cron_18_00.log 2>&1

# 监控任务（每30分钟检查一次）
*/30 * * * * cd /Users/guohongyu/clawd && python3 scripts/monitor_publish_status_enhanced.py --target-hour-cst 18 --check-phase 30 >> logs/monitor.log 2>&1
'''
    
    cron_file = Path("cron_jobs.txt")
    
    try:
        with open(cron_file, 'w', encoding='utf-8') as f:
            f.write(cron_content)
        
        print(f"✅ 创建定时任务配置: {cron_file}")
        print("")
        print("📋 请手动安装定时任务:")
        print(f"   1. 查看配置: cat {cron_file}")
        print(f"   2. 安装到crontab: crontab {cron_file}")
        print(f"   3. 验证安装: crontab -l")
        print("")
        print("⚠️  注意：需要确保脚本有执行权限")
        
        return True
        
    except Exception as e:
        print(f"❌ 创建定时任务配置失败: {e}")
        return False

def main():
    """主函数"""
    print("🔧 开始修复发布频率问题...")
    print("=" * 50)
    
    # 切换到项目目录
    original_dir = os.getcwd()
    project_dir = Path("/Users/guohongyu/clawd")
    
    try:
        os.chdir(project_dir)
        print(f"📁 切换到项目目录: {project_dir}")
    except Exception as e:
        print(f"❌ 无法切换到项目目录: {e}")
        return False
    
    success_count = 0
    total_steps = 3
    
    # 步骤1: 更新配置
    print("")
    print("1️⃣ 更新配置文件...")
    if update_config_max_posts():
        success_count += 1
    
    # 步骤2: 创建发布脚本
    print("")
    print("2️⃣ 创建增强版发布脚本...")
    if create_enhanced_publishing_script():
        success_count += 1
    
    # 步骤3: 设置定时任务
    print("")
    print("3️⃣ 设置定时任务配置...")
    if setup_cron_jobs():
        success_count += 1
    
    # 返回原目录
    os.chdir(original_dir)
    
    print("")
    print("=" * 50)
    print(f"📊 修复完成: {success_count}/{total_steps} 个步骤成功")
    
    if success_count == total_steps:
        print("🎉 所有修复步骤完成！")
        print("")
        print("🚀 下一步操作:")
        print("   1. 测试发布脚本: ./scripts/enhanced_daily_publishing.sh")
        print("   2. 安装定时任务: crontab cron_jobs.txt")
        print("   3. 监控发布结果: tail -f logs/*.log")
        return True
    else:
        print("⚠️  部分步骤失败，请检查错误信息")
        return False

if __name__ == "__main__":
    if main():
        sys.exit(0)
    else:
        sys.exit(1)
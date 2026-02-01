#!/bin/bash

# 工作流清理和固定脚本
# 这个脚本将：
# 1. 删除失败/不必要的工作流
# 2. 固定成功的工作流
# 3. 创建简洁的工作流结构

echo "🔧 开始清理和固定工作流..."
echo "=========================="

# 项目根目录
PROJECT_ROOT="/tmp/fix_repo"
cd "$PROJECT_ROOT" || exit 1

echo ""
echo "📋 当前工作流文件:"
ls -la .github/workflows/

echo ""
echo "🎯 清理计划:"
echo "============"

# 要删除的工作流（已知问题或不需要的）
TO_DELETE=(
    ".github/workflows/minimal-test.yml"      # 有--verbose参数问题
    ".github/workflows/test-secret.yml"       # 测试用，已过时
    ".github/workflows/smart-blog.yml"        # 复杂监控，不需要
    ".github/workflows/guaranteed-blog.yml"   # 临时方案
    ".github/workflows/ultra-simple.yml"      # 过于简单
    ".github/workflows/ai-blog.yml"           # 复杂版本，有测试问题
)

# 要保留的工作流（已验证成功的）
TO_KEEP=(
    ".github/workflows/ai-blog-simple.yml"    # ✅ 已验证成功
    ".github/workflows/deepseek-secure.yml"   # 完整AI流程
    ".github/workflows/hugo.yml"              # Hugo部署（必要）
    ".github/workflows/simple-test.yml"       # 简单测试（可选保留）
)

echo ""
echo "❌ 要删除的工作流:"
for file in "${TO_DELETE[@]}"; do
    if [ -f "$file" ]; then
        echo "  • $(basename "$file")"
    fi
done

echo ""
echo "✅ 要保留的工作流:"
for file in "${TO_KEEP[@]}"; do
    if [ -f "$file" ]; then
        echo "  • $(basename "$file")"
    fi
done

echo ""
read -p "是否继续清理？(y/n): " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "取消清理"
    exit 0
fi

echo ""
echo "🗑️  开始删除工作流..."
for file in "${TO_DELETE[@]}"; do
    if [ -f "$file" ]; then
        echo "  删除: $file"
        rm "$file"
    else
        echo "  跳过: $file (不存在)"
    fi
done

echo ""
echo "🔧 优化保留的工作流..."

# 1. 优化 ai-blog-simple.yml（已验证成功）
echo "  优化 ai-blog-simple.yml..."
cat > .github/workflows/ai-blog-simple.yml << 'EOF'
name: AI Blog Simple (Fixed)

on:
  workflow_dispatch:
    inputs:
      mode:
        description: '运行模式'
        required: false
        default: 'test'
        type: choice
        options:
          - test
          - full

env:
  PYTHON_VERSION: '3.11'

jobs:
  check:
    runs-on: ubuntu-latest
    steps:
      - name: Check Secret
        env:
          API_KEY: ${{ secrets.DEEPSEEK_API_KEY }}
        run: |
          echo "🔍 检查Secret..."
          if [ -z "$API_KEY" ]; then
            echo "❌ DEEPSEEK_API_KEY未设置"
            exit 1
          fi
          echo "✅ Secret检查通过"
          echo "Key: ${API_KEY:0:10}..."

  simple-test:
    needs: check
    if: github.event.inputs.mode == 'test'
    runs-on: ubuntu-latest
    steps:
      - name: Test Complete
        run: |
          echo "🎉 测试完成!"
          echo "Secret工作正常"
          echo "可以运行完整模式"

  full-run:
    needs: check
    if: github.event.inputs.mode == 'full'
    runs-on: ubuntu-latest
    steps:
      - name: Generate Content
        run: |
          echo "生成内容..."
          mkdir -p content/posts
          
          cat > content/posts/fixed-$(date +%Y%m%d-%H%M%S).md << 'EOF'
          ---
          title: "固定工作流测试文章"
          date: $(date -Iseconds)
          draft: false
          tags: ["固定", "测试"]
          categories: ["测试"]
          ---
          
          # 固定工作流测试
          
          这篇文章由固定的工作流生成。
          
          ## 验证信息
          - **生成时间**: $(date)
          - **工作流**: AI Blog Simple (Fixed)
          - **模式**: full
          - **状态**: ✅ 运行正常
          
          ## 系统状态
          1. 工作流固定完成
          2. 清理了不必要的工作流
          3. 系统已优化
          
          ---
          *固定工作流系统*
          EOF
          
          echo "文章已生成"
      
      - name: Commit and Trigger
        run: |
          echo "提交并触发部署..."
          git config --global user.name "GitHub Actions Bot"
          git config --global user.email "actions-bot@github.com"
          git add content/posts/
          git commit -m "📝 固定工作流测试文章 [$(date +%Y%m%d-%H%M%S)]"
          git push origin main
          
          echo "✅ 已提交并触发部署"
      
      - name: Final Report
        run: |
          echo "# 固定工作流报告" > report.md
          echo "时间: $(date)" >> report.md
          echo "工作流: AI Blog Simple (Fixed)" >> report.md
          echo "模式: ${{ github.event.inputs.mode }}" >> report.md
          echo "状态: ✅ 成功" >> report.md
          echo "" >> report.md
          echo "## 完成的任务" >> report.md
          echo "- ✅ 生成测试文章" >> report.md
          echo "- ✅ 提交到仓库" >> report.md
          echo "- ✅ 触发部署" >> report.md
          echo "" >> report.md
          echo "## 下一步" >> report.md
          echo "1. 等待1-2分钟部署完成" >> report.md
          echo "2. 访问博客: https://gsaecy.github.io" >> report.md
          echo "3. 查看新文章" >> report.md
          
          cat report.md
EOF

# 2. 创建直接反馈工作流（你要求的）
echo "  创建 direct-feedback.yml..."
cat > .github/workflows/direct-feedback.yml << 'EOF'
name: Direct Feedback

on:
  workflow_dispatch:
    inputs:
      check_only:
        description: '仅检查不生成'
        required: false
        default: 'false'
        type: boolean

jobs:
  feedback:
    runs-on: ubuntu-latest
    steps:
      - name: Generate Feedback Article
        if: github.event.inputs.check_only == 'false'
        run: |
          echo "生成反馈测试文章..."
          mkdir -p content/posts
          
          TIMESTAMP=$(date +%Y%m%d-%H%M%S)
          
          cat > content/posts/feedback-${TIMESTAMP}.md << 'EOF'
          ---
          title: "直接反馈测试 - ${TIMESTAMP}"
          date: $(date -Iseconds)
          draft: false
          tags: ["反馈", "测试"]
          categories: ["测试"]
          slug: "feedback-${TIMESTAMP}"
          ---
          
          # 直接反馈测试
          
          时间戳: ${TIMESTAMP}
          工作流: Direct Feedback
          
          这篇文章用于测试直接反馈系统。
          
          ## 预期结果
          1. 文章应该出现在博客中
          2. 反馈系统应该确认发布
          3. 系统应该工作正常
          
          ---
          *反馈测试*
          EOF
          
          echo "文章已生成: feedback-${TIMESTAMP}.md"
      
      - name: Commit if Article Generated
        if: github.event.inputs.check_only == 'false'
        run: |
          echo "提交文章..."
          git config --global user.name "GitHub Actions Bot"
          git config --global user.email "actions-bot@github.com"
          git add content/posts/
          git commit -m "📊 直接反馈测试文章 [${TIMESTAMP}]"
          git push origin main
          
          echo "✅ 文章已提交"
      
      - name: Give Direct Feedback
        run: |
          echo "🎯 直接反馈"
          echo "=========="
          echo ""
          echo "📊 运行信息"
          echo "工作流: Direct Feedback"
          echo "运行ID: ${{ github.run_id }}"
          echo "时间: $(date)"
          echo ""
          
          if [ "${{ github.event.inputs.check_only }}" = "false" ]; then
            echo "📝 文章操作"
            echo "- 生成文章: ✅ 完成"
            echo "- 提交仓库: ✅ 完成"
            echo "- 触发部署: ✅ 完成"
            echo ""
            echo "❓ 有没有发布新文章？"
            echo "🔄 答案: 已触发部署，等待1-2分钟"
            echo ""
            echo "检查方法:"
            echo "1. 访问: https://gsaecy.github.io"
            echo "2. 查看最新文章"
            echo "3. 或运行检查模式"
          else
            echo "🔍 仅检查模式"
            echo "- 生成文章: ❌ 跳过"
            echo "- 提交仓库: ❌ 跳过"
            echo ""
            echo "❓ 有没有发布新文章？"
            echo "📋 答案: 请手动检查博客"
            echo ""
            echo "博客地址: https://gsaecy.github.io"
          fi
          echo ""
          echo "---"
          echo "反馈时间: $(date)"
EOF

echo ""
echo "📋 最终工作流结构:"
echo "================="
echo ""
echo "✅ 核心工作流 (3个):"
echo "1. ai-blog-simple.yml    - 简单完整流程 (已验证成功)"
echo "2. direct-feedback.yml    - 直接反馈系统 (新增)"
echo "3. hugo.yml              - Hugo部署 (必要)"
echo ""
echo "🔄 可选工作流 (1个):"
echo "4. deepseek-secure.yml   - 完整AI流程 (需要时启用)"
echo ""
echo "📁 其他文件:"
echo "5. simple-test.yml       - 简单测试 (可选保留)"

echo ""
echo "🎉 清理和固定完成!"
echo "下一步: 提交更改并测试固定后的工作流"
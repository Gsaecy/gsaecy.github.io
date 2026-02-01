#!/usr/bin/env python3
"""
GitHub Actions Secrets 配置脚本
用于在GitHub Actions中安全地使用DeepSeek API Key
"""

import os
import sys
import base64
from pathlib import Path

def setup_environment():
    """设置环境变量"""
    print("设置GitHub Actions环境变量...")
    
    # 项目根目录
    project_root = Path(__file__).parent.parent.parent
    
    # 创建.env文件（用于本地测试）
    env_file = project_root / ".env"
    env_template = project_root / ".env.example"
    
    if not env_file.exists() and env_template.exists():
        print("创建.env文件从模板...")
        env_file.write_text(env_template.read_text())
    
    # 设置Python路径
    scripts_dir = project_root / "scripts"
    if scripts_dir.exists():
        sys.path.insert(0, str(scripts_dir))
    
    print("环境设置完成")

def check_required_secrets():
    """检查必要的Secrets"""
    print("检查必要的GitHub Secrets...")
    
    required_secrets = [
        "DEEPSEEK_API_KEY"
    ]
    
    missing_secrets = []
    
    for secret in required_secrets:
        if not os.getenv(secret):
            missing_secrets.append(secret)
    
    if missing_secrets:
        print(f"⚠️  缺少以下Secrets: {', '.join(missing_secrets)}")
        print("请在GitHub仓库中设置:")
        print("1. 访问: https://github.com/Gsaecy/Gsaecy.github.io/settings/secrets/actions")
        print("2. 点击'New repository secret'")
        print("3. 添加以下Secrets:")
        for secret in missing_secrets:
            if secret == "DEEPSEEK_API_KEY":
                print(f"   - {secret}: 你的DeepSeek API Key")
        return False
    
    print("✅ 所有必要的Secrets都已配置")
    return True

def create_config_from_secrets():
    """从Secrets创建配置文件"""
    print("从环境变量创建配置文件...")
    
    project_root = Path(__file__).parent.parent.parent
    config_dir = project_root / "config"
    config_dir.mkdir(exist_ok=True)
    
    # 读取DeepSeek API Key
    deepseek_key = os.getenv("DEEPSEEK_API_KEY")
    
    if not deepseek_key:
        print("❌ 未找到DEEPSEEK_API_KEY环境变量")
        return False
    
    # 创建生产环境配置
    prod_config = {
        "version": "2.1",
        "environment": "production",
        "analysis": {
            "ai_model": {
                "provider": "deepseek",
                "model": "deepseek-chat",
                "api_base": "https://api.deepseek.com",
                # API Key将通过环境变量注入，不直接写在配置文件中
                "temperature": 0.7,
                "max_tokens": 2000,
                "timeout": 30
            }
        },
        "collectors": {
            "sources": [
                {
                    "name": "36氪快讯",
                    "url": "https://36kr.com/newsflashes",
                    "type": "tech",
                    "method": "web",
                    "enabled": True
                },
                {
                    "name": "虎嗅网",
                    "url": "https://www.huxiu.com",
                    "type": "tech",
                    "method": "web",
                    "enabled": True
                },
                {
                    "name": "亿邦动力",
                    "url": "https://www.ebrun.com",
                    "type": "ecommerce",
                    "method": "web",
                    "enabled": True
                },
                {
                    "name": "工控网资讯",
                    "url": "https://news.gongkong.com",
                    "type": "manufacturing",
                    "method": "web",
                    "enabled": True
                }
            ]
        },
        "industries": {
            "priority": [
                {"name": "科技", "weight": 30},
                {"name": "电商", "weight": 25},
                {"name": "制造", "weight": 20},
                {"name": "金融", "weight": 15},
                {"name": "教育", "weight": 5},
                {"name": "医疗", "weight": 5}
            ]
        },
        "logging": {
            "level": "INFO",
            "file": "./logs/system.log"
        }
    }
    
    # 保存配置文件
    import yaml
    config_file = config_dir / "config.prod.yaml"
    
    with open(config_file, 'w', encoding='utf-8') as f:
        yaml.dump(prod_config, f, allow_unicode=True, sort_keys=False)
    
    print(f"✅ 生产配置文件已创建: {config_file}")
    
    # 创建GitHub Actions工作流配置
    create_github_actions_config(deepseek_key)
    
    return True

def create_github_actions_config(api_key: str):
    """创建GitHub Actions配置"""
    print("创建GitHub Actions配置...")
    
    workflows_dir = Path(__file__).parent.parent / "workflows"
    workflows_dir.mkdir(exist_ok=True)
    
    # 创建带Secrets的工作流
    workflow_content = f"""name: AI Blog with DeepSeek

on:
  schedule:
    - cron: '0 2 * * *'  # 每天10:00（UTC+8）
    - cron: '0 6 * * *'  # 每天14:00（UTC+8）
  
  workflow_dispatch:
    inputs:
      analysis_type:
        description: '分析类型'
        required: true
        default: 'daily'
        type: choice
        options:
          - daily
          - weekly
          - test

env:
  DEEPSEEK_API_KEY: ${{{{ secrets.DEEPSEEK_API_KEY }}}}
  PYTHON_VERSION: '3.11'
  HUGO_VERSION: 'latest'

jobs:
  collect-and-analyze:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout repository
        uses: actions/checkout@v4
        with:
          submodules: recursive
      
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: ${{{{ env.PYTHON_VERSION }}}}
      
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
          pip install openai beautifulsoup4 requests feedparser
      
      - name: Setup environment
        run: python .github/scripts/setup_secrets.py
      
      - name: Run data collection
        run: |
          echo "开始数据采集..."
          python scripts/collectors/real_news_collector.py 2>&1 | tee logs/collection.log
          echo "数据采集完成"
      
      - name: Run AI analysis with DeepSeek
        env:
          DEEPSEEK_API_KEY: ${{{{ secrets.DEEPSEEK_API_KEY }}}}
        run: |
          echo "开始DeepSeek AI分析..."
          python scripts/analyzers/deepseek_analyzer.py 2>&1 | tee logs/analysis.log
          echo "AI分析完成"
      
      - name: Generate content
        run: |
          echo "生成博客内容..."
          python scripts/generators/article_generator.py 2>&1 | tee logs/generation.log
      
      - name: Upload logs
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: logs-${{{{ github.run_id }}}}
          path: logs/
          retention-days: 7
  
  build-and-deploy:
    needs: collect-and-analyze
    runs-on: ubuntu-latest
    permissions:
      contents: write
      pages: write
      id-token: write
    
    steps:
      - name: Checkout repository
        uses: actions/checkout@v4
        with:
          submodules: recursive
      
      - name: Setup Hugo
        uses: peaceiris/actions-hugo@v2
        with:
          hugo-version: ${{{{ env.HUGO_VERSION }}}}
          extended: true
      
      - name: Build with Hugo
        run: hugo --minify
      
      - name: Setup Pages
        uses: actions/configure-pages@v4
      
      - name: Upload artifact
        uses: actions/upload-pages-artifact@v4
        with:
          path: ./public
      
      - name: Deploy to GitHub Pages
        id: deployment
        uses: actions/deploy-pages@v4
  
  notify:
    needs: build-and-deploy
    runs-on: ubuntu-latest
    if: always()
    steps:
      - name: Check deployment status
        run: |
          echo "部署状态: ${{{{ needs.build-and-deploy.result }}}}"
          echo "博客地址: https://gsaecy.github.io"
          echo "运行完成时间: $(date)"
"""
    
    workflow_file = workflows_dir / "deepseek-blog.yml"
    workflow_file.write_text(workflow_content)
    
    print(f"✅ GitHub Actions工作流已创建: {workflow_file}")

def main():
    """主函数"""
    print("=" * 60)
    print("GitHub Actions Secrets 配置工具")
    print("=" * 60)
    
    # 设置环境
    setup_environment()
    
    # 检查Secrets
    if not check_required_secrets():
        print("\n请先配置GitHub Secrets，然后重新运行此脚本。")
        sys.exit(1)
    
    # 创建配置
    if create_config_from_secrets():
        print("\n✅ 配置完成！")
        print("\n下一步:")
        print("1. 确保GitHub Secrets已配置")
        print("2. 工作流将自动在指定时间运行")
        print("3. 访问 https://gsaecy.github.io 查看结果")
        print("4. 查看GitHub Actions日志了解运行详情")
    else:
        print("\n❌ 配置失败")
        sys.exit(1)

if __name__ == "__main__":
    main()
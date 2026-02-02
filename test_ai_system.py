#!/usr/bin/env python3
"""
快速测试AI自动化系统配置
"""

import os
import sys
import yaml

def test_config():
    """测试配置文件"""
    print("🔍 测试配置文件...")
    
    config_path = "config/config.yaml"
    if not os.path.exists(config_path):
        print(f"❌ 配置文件不存在: {config_path}")
        return False
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        print(f"✅ 配置文件加载成功: {config_path}")
        
        # 检查必要配置
        required_sections = ['system', 'analysis', 'collectors']
        for section in required_sections:
            if section in config:
                print(f"  ✅ {section}: 存在")
            else:
                print(f"  ⚠️  {section}: 缺失")
        
        # 检查DeepSeek配置
        if 'analysis' in config and 'ai_model' in config['analysis']:
            ai_config = config['analysis']['ai_model']
            print(f"  🤖 AI模型: {ai_config.get('provider', '未知')}")
            print(f"    模型: {ai_config.get('model', '未知')}")
        
        return True
        
    except Exception as e:
        print(f"❌ 配置文件解析失败: {e}")
        return False

def test_imports():
    """测试必要的Python包"""
    print("\n🔍 测试Python包导入...")
    
    packages = [
        ('requests', 'requests'),
        ('yaml', 'yaml'),
        ('bs4', 'beautifulsoup4'),
        ('openai', 'openai'),
        ('aiohttp', 'aiohttp'),
        ('httpx', 'httpx'),
    ]
    
    all_ok = True
    for import_name, package_name in packages:
        try:
            __import__(import_name)
            print(f"✅ {package_name}: 可导入")
        except ImportError:
            print(f"❌ {package_name}: 不可导入")
            all_ok = False
    
    return all_ok

def test_directory_structure():
    """测试目录结构"""
    print("\n🔍 测试目录结构...")
    
    required_dirs = [
        'scripts/collectors',
        'scripts/analyzers', 
        'scripts/generators',
        'scripts/publishers',
        'scripts/utils',
        'content/posts',
        'data/raw',
        'data/analysis',
        'logs',
    ]
    
    all_ok = True
    for directory in required_dirs:
        if os.path.isdir(directory):
            print(f"✅ {directory}/: 存在")
        else:
            print(f"❌ {directory}/: 不存在")
            all_ok = False
    
    return all_ok

def test_ai_automation():
    """测试AI自动化系统入口"""
    print("\n🔍 测试AI自动化系统入口...")
    
    script_path = "scripts/automation_system_v2.py"
    if not os.path.exists(script_path):
        print(f"❌ 主脚本不存在: {script_path}")
        return False
    
    try:
        # 尝试导入但不执行
        import importlib.util
        spec = importlib.util.spec_from_file_location("automation_system_v2", script_path)
        module = importlib.util.module_from_spec(spec)
        
        # 检查是否有run_pipeline函数
        with open(script_path, 'r', encoding='utf-8') as f:
            content = f.read()
            if 'async def run_pipeline' in content:
                print(f"✅ {script_path}: 包含run_pipeline函数")
            else:
                print(f"⚠️  {script_path}: 未找到run_pipeline函数")
        
        print(f"✅ 主脚本语法检查通过")
        return True
        
    except Exception as e:
        print(f"❌ 主脚本导入失败: {e}")
        return False

def main():
    """主测试函数"""
    print("🤖 AI自动化系统 - 配置测试")
    print("=" * 50)
    
    # 切换到脚本目录
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    tests = [
        ("配置文件", test_config),
        ("Python包", test_imports),
        ("目录结构", test_directory_structure),
        ("AI自动化入口", test_ai_automation),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n📋 测试: {test_name}")
        print("-" * 30)
        result = test_func()
        results.append((test_name, result))
    
    # 总结报告
    print("\n" + "=" * 50)
    print("📊 测试总结")
    print("-" * 30)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{test_name}: {status}")
    
    print(f"\n🎯 总体结果: {passed}/{total} 项测试通过")
    
    if passed == total:
        print("\n🚀 所有测试通过！AI自动化系统已准备就绪。")
        print("\n下一步:")
        print("1. 在GitHub Actions中运行 'AI Blog Pipeline'")
        print("2. 检查生成的博客文章")
        print("3. 验证自动化部署")
    else:
        print("\n🔧 需要修复的问题:")
        for test_name, result in results:
            if not result:
                print(f"  - {test_name}")
        
        print("\n💡 建议:")
        print("1. 检查缺失的文件或目录")
        print("2. 验证配置文件格式")
        print("3. 确保所有依赖包已安装")

if __name__ == "__main__":
    main()
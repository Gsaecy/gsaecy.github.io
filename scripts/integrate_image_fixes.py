#!/usr/bin/env python3
"""
集成图片修复到现有系统
- 更新 auto_add_public_images.py
- 修改相关配置
- 创建备份和测试
"""

import os
import shutil
from pathlib import Path
import re

def backup_original_script():
    """备份原始脚本"""
    original_path = Path("scripts/auto_add_public_images.py")
    backup_path = Path("scripts/auto_add_public_images.py.backup")
    
    if original_path.exists():
        shutil.copy2(original_path, backup_path)
        print(f"✅ 备份原始脚本: {backup_path}")
        return True
    else:
        print(f"❌ 原始脚本不存在: {original_path}")
        return False

def update_auto_add_images_script():
    """更新自动添加图片脚本"""
    
    # 读取增强版图片选择器的关键函数
    enhance_script = Path("scripts/enhance_image_selection.py")
    if not enhance_script.exists():
        print(f"❌ 增强脚本不存在: {enhance_script}")
        return False
    
    with open(enhance_script, 'r', encoding='utf-8') as f:
        enhance_content = f.read()
    
    # 提取关键函数
    functions_to_extract = [
        "extract_article_keywords",
        "generate_search_queries", 
        "calculate_relevance_score"
    ]
    
    extracted_code = ""
    for func_name in functions_to_extract:
        pattern = rf'def {func_name}\(.*?\):(.*?)(?=\n\ndef|\nclass|\Z)'
        match = re.search(pattern, enhance_content, re.DOTALL)
        if match:
            extracted_code += f"\n# 从 enhance_image_selection.py 导入的 {func_name} 函数\n"
            extracted_code += f"def {func_name}{match.group(0)[len(func_name)+4:]}\n"
    
    # 读取原始脚本
    original_path = Path("scripts/auto_add_public_images.py")
    if not original_path.exists():
        print(f"❌ 原始脚本不存在: {original_path}")
        return False
    
    with open(original_path, 'r', encoding='utf-8') as f:
        original_content = f.read()
    
    # 查找并替换 extract_queries 函数
    old_extract_queries = '''def extract_queries(md_text: str) -> List[str]:
    # Prefer front matter title (we may remove H1 from body), then fall back to headings.
    lines = md_text.splitlines()
    title = extract_front_matter_title(md_text)
    headings = []
    for ln in lines[:160]:
        if (not title) and ln.startswith("# "):
            title = ln[2:].strip()
        if ln.startswith("## "):
            headings.append(ln[3:].strip())

    base = title or "industry analysis"

    # crude domain mapping based on Chinese keywords
    # keep it minimal and predictable
    mapping = [
        ("新能源汽车", "electric vehicle"),
        ("电池", "battery"),
        ("充电", "charging station"),
        ("智能驾驶", "autonomous driving"),
        ("医疗", "medical technology"),
        ("金融", "financial technology"),
        ("教育", "online learning"),
    ]

    hints = []
    for zh, en in mapping:
        if zh in md_text:
            hints.append(en)

    # Build up to 3 queries
    queries = []
    if hints:
        queries.append(" ".join(hints[:2]))

    # Title keywords (strip punctuation). Also add a stable "AI" hint if present.
    base2 = re.sub(r"[\\W_]+", " ", base)
    if "AI" in md_text or "人工智能" in md_text:
        base2 = ("AI " + base2).strip()

    if base2.strip():
        queries.append(base2.strip())

    if headings:
        h = re.sub(r"[\\W_]+", " ", headings[0])
        if h.strip():
            queries.append(h.strip())

    # dedupe
    out = []
    for q in queries:
        q = q.strip()
        if q and q not in out:
            out.append(q)

    return out[:3]'''
    
    # 新的 extract_queries 函数
    new_extract_queries = '''def extract_queries(md_text: str) -> List[str]:
    """增强版查询提取，考虑行业和主题相关性"""
    
    # 首先尝试从front matter获取行业信息
    industry = "technology"  # 默认行业
    
    # 从front matter提取categories
    fm_match = re.match(r"^---\\n(.*?)\\n---\\n", md_text, flags=re.S)
    if fm_match:
        fm_text = fm_match.group(1)
        # 查找categories
        cat_match = re.search(r'categories:\\s*\\[.*?(technology|ecommerce|manufacturing|finance|education|health).*?\\]', fm_text, re.IGNORECASE)
        if cat_match:
            industry = cat_match.group(1).lower()
    
    # 使用增强版关键词提取
    keywords = extract_article_keywords(md_text, industry)
    
    # 生成搜索查询
    queries = generate_search_queries(keywords, industry)
    
    return queries[:5]  # 最多5个查询'''
    
    # 替换函数
    if old_extract_queries in original_content:
        updated_content = original_content.replace(old_extract_queries, new_extract_queries)
        
        # 在文件开头添加导入和辅助函数
        imports_to_add = '''from typing import List, Dict, Any
import re

# 行业关键词映射
INDUSTRY_KEYWORDS = {
    "technology": {
        "primary": ["AI", "artificial intelligence", "machine learning", "cloud computing"],
        "secondary": ["software", "hardware", "robot", "digital", "tech"],
        "visual": ["computer", "server", "circuit", "chip", "data center"]
    },
    "ecommerce": {
        "primary": ["ecommerce", "online shopping", "digital marketing", "logistics"],
        "secondary": ["delivery", "package", "store", "payment", "shopping cart"],
        "visual": ["warehouse", "truck", "credit card", "mobile shopping"]
    },
    "manufacturing": {
        "primary": ["manufacturing", "factory", "industrial", "automation"],
        "secondary": ["production", "assembly", "machine", "robot", "quality control"],
        "visual": ["factory floor", "assembly line", "industrial robot", "3d printer"]
    }
}

def extract_article_keywords(md_text: str, industry: str = "technology") -> List[str]:
    """从文章内容提取关键词"""
    
    keywords = []
    
    # 提取标题
    title_match = re.search(r'title:\\s*["\\']?(.+?)["\\']?\\s*$', md_text, re.MULTILINE | re.IGNORECASE)
    if title_match:
        title = title_match.group(1)
        # 从标题提取关键词
        title_words = re.findall(r'\\b\\w+\\b', title.lower())
        stop_words = {"the", "and", "for", "with", "about", "analysis", "report", "daily", "weekly"}
        meaningful = [w for w in title_words if w not in stop_words and len(w) > 3]
        keywords.extend(meaningful[:5])
    
    # 提取H1和H2标题
    headings = re.findall(r'^#+\\s+(.+)$', md_text, re.MULTILINE)
    for heading in headings[:3]:
        heading_words = re.findall(r'\\b\\w+\\b', heading.lower())
        meaningful = [w for w in heading_words if len(w) > 3]
        keywords.extend(meaningful[:3])
    
    # 添加行业特定关键词
    if industry in INDUSTRY_KEYWORDS:
        industry_info = INDUSTRY_KEYWORDS[industry]
        keywords.extend(industry_info["primary"][:2])
        keywords.extend(industry_info["visual"][:2])
    
    # 去重并限制数量
    unique_keywords = []
    seen = set()
    for kw in keywords:
        kw_lower = kw.lower()
        if kw_lower not in seen and len(kw_lower) > 2:
            seen.add(kw_lower)
            unique_keywords.append(kw)
    
    return unique_keywords[:10]

def generate_search_queries(keywords: List[str], industry: str = "technology") -> List[str]:
    """生成图片搜索查询"""
    
    queries = []
    
    # 组合关键词查询
    if keywords:
        # 主要关键词组合
        if len(keywords) >= 2:
            queries.append(f"{keywords[0]} {keywords[1]}")
        
        # 单个重要关键词
        for kw in keywords[:3]:
            if len(kw.split()) == 1:
                queries.append(kw)
        
        # 行业特定查询
        if industry in INDUSTRY_KEYWORDS:
            industry_info = INDUSTRY_KEYWORDS[industry]
            queries.append(" ".join(industry_info["primary"][:2]))
            queries.append(" ".join(industry_info["visual"][:2]))
    
    # 确保有足够的查询
    if not queries:
        queries = ["technology", "innovation", "digital transformation"]
    
    return queries[:5]

def calculate_image_relevance(image_info: dict, keywords: List[str], industry: str) -> float:
    """计算图片相关性评分"""
    
    score = 0.0
    
    # 检查图片标题和描述
    image_text = f"{image_info.get('title', '')} {image_info.get('description', '')}".lower()
    
    # 关键词匹配
    for keyword in keywords:
        keyword_lower = keyword.lower()
        if keyword_lower in image_text:
            if f" {keyword_lower} " in f" {image_text} ":
                score += 2.0
            else:
                score += 1.0
    
    # 行业特定匹配
    if industry in INDUSTRY_KEYWORDS:
        industry_info = INDUSTRY_KEYWORDS[industry]
        
        for term in industry_info["primary"]:
            if term.lower() in image_text:
                score += 1.5
        
        for term in industry_info["visual"]:
            if term.lower() in image_text:
                score += 2.0
    
    # 图片质量考虑
    width = image_info.get('width', 0)
    height = image_info.get('height', 0)
    
    if width >= 800 and height >= 600:
        score += 1.0
    elif width >= 400 and height >= 300:
        score += 0.5
    
    return score
'''
        
        # 在原始内容中找到合适的位置插入
        # 通常在导入之后，第一个函数之前
        lines = updated_content.split('\n')
        insert_index = 0
        
        # 找到第一个函数定义
        for i, line in enumerate(lines):
            if line.strip().startswith('def '):
                insert_index = i
                break
        
        # 插入增强代码
        lines.insert(insert_index, imports_to_add)
        updated_content = '\n'.join(lines)
        
        # 保存更新后的脚本
        updated_path = Path("scripts/auto_add_public_images_enhanced.py")
        with open(updated_path, 'w', encoding='utf-8') as f:
            f.write(updated_content)
        
        print(f"✅ 创建增强版脚本: {updated_path}")
        print(f"   原始脚本已备份: scripts/auto_add_public_images.py.backup")
        
        return True
    else:
        print("❌ 未找到原始 extract_queries 函数")
        return False

def create_integration_test():
    """创建集成测试"""
    
    test_content = '''#!/usr/bin/env python3
"""
集成测试脚本
测试增强版图片选择功能
"""

import sys
from pathlib import Path

# 添加脚本目录到路径
sys.path.insert(0, str(Path(__file__).parent))

def test_enhanced_image_selection():
    """测试增强版图片选择"""
    
    print("🧪 测试增强版图片选择集成...")
    print("=" * 50)
    
    # 测试文章
    test_articles = [
        {
            "title": "人工智能在制造业的应用与前景分析",
            "content": """---
title: "人工智能在制造业的应用与前景分析"
date: 2026-02-25
categories: ["technology", "manufacturing"]
---

# 人工智能在制造业的应用与前景分析

## 智能制造的发展趋势

随着人工智能技术的快速发展，制造业正在经历一场深刻的数字化转型。
""",
            "expected_industry": "manufacturing"
        },
        {
            "title": "跨境电商平台发展趋势",
            "content": """---
title: "跨境电商平台发展趋势"
date: 2026-02-25  
categories: ["ecommerce", "technology"]
---

# 跨境电商平台发展趋势

## 市场现状分析

全球跨境电商市场持续增长，新技术正在改变传统贸易模式。
""",
            "expected_industry": "ecommerce"
        },
        {
            "title": "云计算技术在企业数字化转型中的作用",
            "content": """---
title: "云计算技术在企业数字化转型中的作用"
date: 2026-02-25
categories: ["technology"]
---

# 云计算技术在企业数字化转型中的作用

## 技术优势分析

云计算提供了弹性、可扩展的IT基础设施，支持企业快速创新。
""",
            "expected_industry": "technology"
        }
    ]
    
    # 导入增强版脚本
    try:
        from auto_add_public_images_enhanced import extract_queries, extract_article_keywords, generate_search_queries
        print("✅ 成功导入增强版函数")
    except ImportError as e:
        print(f"❌ 导入失败: {e}")
        return False
    
    # 测试每个文章
    for i, article in enumerate(test_articles, 1):
        print(f"\\n📝 测试文章 {i}: {article['title']}")
        print(f"   预期行业: {article['expected_industry']}")
        
        # 测试关键词提取
        keywords = extract_article_keywords(article['content'], article['expected_industry'])
        print(f"   提取关键词: {', '.join(keywords[:5])}")
        
        # 测试查询生成
        queries = extract_queries(article['content'])
        print(f"   生成查询: {', '.join(queries)}")
        
        # 验证查询质量
        if queries:
            print(f"   ✅ 查询生成成功 ({len(queries)} 个查询)")
            
            # 检查查询是否包含行业相关词汇
            industry = article['expected_industry']
            industry_terms = {
                "technology": ["ai", "tech", "digital", "cloud"],
                "ecommerce": ["ecommerce", "shopping", "online", "delivery"],
                "manufacturing": ["manufacturing", "factory", "industrial", "production"]
            }
            
            if industry in industry_terms:
                found_terms = []
                for term in industry_terms[industry]:
                    for query in queries:
                        if term in query.lower():
                            found_terms.append(term)
                            break
                
                if found_terms:
                    print(f"   ✅ 查询包含行业词汇: {', '.join(found_terms)}")
                else:
                    print(f"   ⚠️  查询未包含明显的行业词汇")
        else:
            print(f"   ❌ 查询生成失败")
    
    print("\\n" + "=" * 50)
    print("✅ 集成测试完成")
    
    return True

def compare_with_original():
    """与原始版本对比"""
    
    print("\\n📊 与原始版本对比...")
    print("=" * 50)
    
    # 测试文章
    test_content = """---
title: "新能源汽车电池技术创新报告"
date: 2026-02-25
categories: ["technology", "manufacturing"]
---

# 新能源汽车电池技术创新报告

## 技术发展趋势

固态电池、快充技术、电池管理系统等创新正在推动行业发展。
"""
    
    # 导入两个版本
    try:
        # 原始版本
        sys.path.insert(0, str(Path(__file__).parent))
        from auto_add_public_images import extract_queries as original_extract_queries
        
        # 增强版本
        from auto_add_public_images_enhanced import extract_queries as enhanced_extract_queries
        from auto_add_public_images_enhanced import extract_article_keywords
        
        print("✅ 成功导入两个版本")
        
        # 原始版本结果
        print("\\n🔍 原始版本结果:")
        original_queries = original_extract_queries(test_content)
        print(f"   查询: {original_queries}")
        
        # 增强版本结果
        print("\\n🔍 增强版本结果:")
        enhanced_queries = enhanced_extract_queries(test_content)
        print(f"   查询: {enhanced_queries}")
        
        # 关键词提取
        keywords = extract_article_keywords(test_content, "manufacturing")
        print(f"   关键词: {', '.join(keywords[:5])}")
        
        print("\\n📈 改进分析:")
        print(f"   原始查询数量: {len(original_queries)}")
        print(f"   增强查询数量: {len(enhanced_queries)}")
        
        # 检查查询相关性
        relevant_terms = ["battery", "electric vehicle", "manufacturing", "technology"]
        original_relevant = sum(1 for q in original_queries if any(term in q.lower() for term in relevant_terms))
        enhanced_relevant = sum(1 for q in enhanced_queries if any(term in q.lower() for term in relevant_terms))
        
        print(f"   原始相关查询: {original_relevant}/{len(original_queries)}")
        print(f"   增强相关查询: {enhanced_relevant}/{len(enhanced_queries)}
#!/usr/bin/env python3
"""
简化版图片修复测试
测试核心逻辑，不依赖外部API
"""

import re
from typing import List, Dict, Any

def extract_article_keywords_simple(md_text: str, industry: str = "technology") -> List[str]:
    """简化版关键词提取"""
    
    keywords = []
    
    # 提取标题
    title_match = re.search(r'title:\s*["\']?(.+?)["\']?\s*$', md_text, re.MULTILINE | re.IGNORECASE)
    if title_match:
        title = title_match.group(1)
        # 简单分词
        words = re.findall(r'[a-zA-Z\u4e00-\u9fff]+', title)
        keywords.extend(words[:5])
    
    # 行业关键词
    industry_map = {
        "technology": ["AI", "tech", "digital", "software", "hardware"],
        "ecommerce": ["ecommerce", "shopping", "online", "store", "delivery"],
        "manufacturing": ["manufacturing", "factory", "production", "industrial", "automation"]
    }
    
    if industry in industry_map:
        keywords.extend(industry_map[industry][:3])
    
    # 去重
    seen = set()
    unique = []
    for kw in keywords:
        kw_lower = kw.lower()
        if kw_lower not in seen:
            seen.add(kw_lower)
            unique.append(kw)
    
    return unique[:8]

def generate_search_queries_simple(keywords: List[str], industry: str) -> List[str]:
    """简化版查询生成"""
    
    queries = []
    
    # 英文关键词组合
    english_keywords = [k for k in keywords if re.match(r'^[a-zA-Z\s]+$', k)]
    
    if english_keywords:
        # 主要关键词
        queries.append(" ".join(english_keywords[:2]))
        
        # 单个关键词
        for kw in english_keywords[:3]:
            if len(kw.split()) == 1:
                queries.append(kw)
    
    # 行业特定查询
    industry_queries = {
        "technology": ["artificial intelligence", "machine learning", "computer technology"],
        "ecommerce": ["online shopping", "digital commerce", "ecommerce business"],
        "manufacturing": ["industrial manufacturing", "factory automation", "production line"]
    }
    
    if industry in industry_queries:
        queries.extend(industry_queries[industry][:2])
    
    # 确保有查询
    if not queries:
        queries = ["technology", "innovation"]
    
    return list(set(queries))[:5]

def calculate_relevance_simple(image_title: str, image_desc: str, keywords: List[str], industry: str) -> float:
    """简化版相关性计算"""
    
    score = 0.0
    text = f"{image_title} {image_desc}".lower()
    
    # 关键词匹配
    for keyword in keywords:
        kw_lower = keyword.lower()
        if kw_lower in text:
            score += 1.0
    
    # 行业匹配
    industry_terms = {
        "technology": ["computer", "digital", "tech", "software", "hardware"],
        "ecommerce": ["shop", "store", "buy", "sell", "market"],
        "manufacturing": ["factory", "produce", "machine", "industrial", "assembly"]
    }
    
    if industry in industry_terms:
        for term in industry_terms[industry]:
            if term in text:
                score += 1.5
    
    return score

def test_core_logic():
    """测试核心逻辑"""
    
    print("🧪 测试图片选择核心逻辑...")
    print("=" * 50)
    
    # 测试文章
    test_cases = [
        {
            "title": "人工智能在制造业的应用分析",
            "content": """---
title: "人工智能在制造业的应用分析"
date: 2026-02-25
categories: ["technology", "manufacturing"]
---

AI技术正在改变传统制造业。
""",
            "industry": "manufacturing",
            "expected_keywords": ["人工智能", "制造业", "应用分析", "AI", "manufacturing"]
        },
        {
            "title": "跨境电商发展趋势报告",
            "content": """---
title: "跨境电商发展趋势报告"
date: 2026-02-25
categories: ["ecommerce"]
---

全球跨境电商市场快速增长。
""",
            "industry": "ecommerce",
            "expected_keywords": ["跨境电商", "发展趋势", "报告", "ecommerce", "shopping"]
        },
        {
            "title": "云计算技术在企业数字化转型中的作用",
            "content": """---
title: "云计算技术在企业数字化转型中的作用"
date: 2026-02-25
categories: ["technology"]
---

云计算提供弹性IT基础设施。
""",
            "industry": "technology",
            "expected_keywords": ["云计算", "技术", "企业", "数字化转型", "作用", "tech"]
        }
    ]
    
    all_passed = True
    
    for i, test in enumerate(test_cases, 1):
        print(f"\n📝 测试用例 {i}: {test['title']}")
        print(f"   行业: {test['industry']}")
        
        # 测试关键词提取
        keywords = extract_article_keywords_simple(test['content'], test['industry'])
        print(f"   提取关键词: {', '.join(keywords)}")
        
        # 验证关键词
        expected_found = 0
        for expected in test['expected_keywords']:
            if any(expected.lower() in kw.lower() for kw in keywords):
                expected_found += 1
        
        if expected_found >= 2:  # 至少找到2个预期关键词
            print(f"   ✅ 关键词提取通过 ({expected_found}/{len(test['expected_keywords'])})")
        else:
            print(f"   ❌ 关键词提取不足 ({expected_found}/{len(test['expected_keywords'])})")
            all_passed = False
        
        # 测试查询生成
        queries = generate_search_queries_simple(keywords, test['industry'])
        print(f"   生成查询: {', '.join(queries)}")
        
        if queries:
            print(f"   ✅ 查询生成成功 ({len(queries)} 个查询)")
            
            # 检查查询是否包含行业词汇
            industry_indicators = {
                "technology": ["ai", "tech", "digital", "computer"],
                "ecommerce": ["ecommerce", "shopping", "online"],
                "manufacturing": ["manufacturing", "factory", "industrial"]
            }
            
            industry = test['industry']
            if industry in industry_indicators:
                found = False
                for indicator in industry_indicators[industry]:
                    for query in queries:
                        if indicator in query.lower():
                            found = True
                            break
                    if found:
                        break
                
                if found:
                    print(f"   ✅ 查询包含行业词汇")
                else:
                    print(f"   ⚠️  查询未包含明显的行业词汇")
        else:
            print(f"   ❌ 查询生成失败")
            all_passed = False
        
        # 测试相关性计算
        test_images = [
            {"title": "Factory automation robot", "desc": "Industrial robot in manufacturing plant"},
            {"title": "Office building", "desc": "Modern office building architecture"},
            {"title": "Shopping cart online", "desc": "Ecommerce shopping cart icon"}
        ]
        
        print(f"   测试图片相关性:")
        for img in test_images:
            score = calculate_relevance_simple(
                img['title'], img['desc'], keywords, test['industry']
            )
            print(f"     - {img['title']}: {score:.1f}分")
    
    print("\n" + "=" * 50)
    
    if all_passed:
        print("✅ 所有核心逻辑测试通过！")
        print("\n🚀 下一步:")
        print("   1. 将核心逻辑集成到现有脚本")
        print("   2. 测试实际图片搜索")
        print("   3. 监控改进效果")
        return True
    else:
        print("⚠️  部分测试失败，需要调整逻辑")
        return False

def create_integration_template():
    """创建集成模板"""
    
    template = '''# 图片选择增强集成模板

## 核心改进

### 1. 关键词提取优化
- 基于文章标题和行业提取关键词
- 考虑中英文混合内容
- 行业特定词汇增强

### 2. 查询生成优化  
- 组合相关关键词
- 行业特定查询
- 英文查询优先（API兼容性）

### 3. 相关性评分
- 关键词匹配度
- 行业相关性
- 图片标题和描述分析

## 集成步骤

### 步骤1: 更新 extract_queries 函数
```python
def extract_queries_enhanced(md_text: str, default_industry: str = "technology") -> List[str]:
    """增强版查询提取"""
    
    # 提取行业信息
    industry = extract_industry_from_frontmatter(md_text) or default_industry
    
    # 提取关键词
    keywords = extract_article_keywords_simple(md_text, industry)
    
    # 生成查询
    queries = generate_search_queries_simple(keywords, industry)
    
    return queries
```

### 步骤2: 更新图片选择逻辑
```python
def select_images_with_relevance(images: List[Dict], keywords: List[str], industry: str) -> List[Dict]:
    """基于相关性选择图片"""
    
    scored_images = []
    for img in images:
        score = calculate_relevance_simple(
            img.get('title', ''),
            img.get('description', ''),
            keywords,
            industry
        )
        img['relevance_score'] = score
        scored_images.append(img)
    
    # 按评分排序
    scored_images.sort(key=lambda x: x['relevance_score'], reverse=True)
    
    return scored_images[:2]  # 返回最佳2张图片
```

### 步骤3: 集成到现有流程
1. 在 `auto_add_public_images.py` 中替换 `extract_queries` 函数
2. 在图片选择后添加相关性评分
3. 基于评分选择最佳图片

## 测试验证

### 单元测试
```python
def test_enhanced_image_selection():
    # 测试不同行业的查询生成
    # 测试相关性评分
    # 验证图片选择结果
```

### 集成测试
1. 使用真实文章测试
2. 对比新旧版本结果
3. 验证图片相关性改进
'''

    with open("图片选择增强集成指南.md", "w", encoding="utf-8") as f:
        f.write(template)
    
    print("📝 创建集成指南: 图片选择增强集成指南.md")

if __name__ == "__main__":
    print("🔧 图片选择优化 - 简化版测试")
    print("=" * 50)
    
    # 测试核心逻辑
    if test_core_logic():
        # 创建集成指南
        create_integration_template()
        
        print("\n🎉 准备就绪！")
        print("核心逻辑已验证，可以开始集成到现有系统。")
    else:
        print("\n⚠️  需要先修复核心逻辑问题")
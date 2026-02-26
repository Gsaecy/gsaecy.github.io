#!/usr/bin/env python3
"""
优化图片选择算法
- 改进图片与主题的匹配度
- 增加行业相关性评分
- 优化图片查询关键词
"""

import re
import json
from pathlib import Path
from typing import List, Dict, Any
import requests
from urllib.parse import quote

class SmartImageSelector:
    """智能图片选择器"""
    
    def __init__(self, industry: str = "technology"):
        self.industry = industry
        self.cache_dir = Path("data/local_image_cache")
        self.cache_dir.mkdir(exist_ok=True)
        
        # 行业关键词映射
        self.industry_keywords = {
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
            },
            "finance": {
                "primary": ["finance", "banking", "investment", "trading"],
                "secondary": ["stock market", "cryptocurrency", "blockchain", "economy"],
                "visual": ["stock chart", "bank building", "coins", "calculator"]
            },
            "education": {
                "primary": ["education", "learning", "online course", "classroom"],
                "secondary": ["student", "teacher", "school", "university", "training"],
                "visual": ["classroom", "books", "graduation", "online learning"]
            },
            "health": {
                "primary": ["healthcare", "medical", "hospital", "doctor"],
                "secondary": ["medicine", "patient", "treatment", "research"],
                "visual": ["hospital", "medical equipment", "doctor patient", "laboratory"]
            }
        }
    
    def extract_article_keywords(self, md_text: str) -> List[str]:
        """从文章内容提取关键词"""
        
        keywords = []
        
        # 提取标题
        title_match = re.search(r'title:\s*["\']?(.+?)["\']?\s*$', md_text, re.MULTILINE | re.IGNORECASE)
        if title_match:
            title = title_match.group(1)
            # 从标题提取关键词
            title_words = re.findall(r'\b\w+\b', title.lower())
            stop_words = {"the", "and", "for", "with", "about", "analysis", "report", "daily", "weekly"}
            meaningful = [w for w in title_words if w not in stop_words and len(w) > 3]
            keywords.extend(meaningful[:5])
        
        # 提取H1和H2标题
        headings = re.findall(r'^#+\s+(.+)$', md_text, re.MULTILINE)
        for heading in headings[:3]:  # 最多取前3个标题
            heading_words = re.findall(r'\b\w+\b', heading.lower())
            meaningful = [w for w in heading_words if len(w) > 3]
            keywords.extend(meaningful[:3])
        
        # 添加行业特定关键词
        if self.industry in self.industry_keywords:
            industry_info = self.industry_keywords[self.industry]
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
        
        return unique_keywords[:10]  # 最多10个关键词
    
    def generate_search_queries(self, keywords: List[str]) -> List[str]:
        """生成图片搜索查询"""
        
        queries = []
        
        # 组合关键词查询
        if keywords:
            # 主要关键词组合
            if len(keywords) >= 2:
                queries.append(f"{keywords[0]} {keywords[1]}")
            
            # 单个重要关键词
            for kw in keywords[:3]:
                if len(kw.split()) == 1:  # 单个词
                    queries.append(kw)
            
            # 行业特定查询
            if self.industry in self.industry_keywords:
                industry_info = self.industry_keywords[self.industry]
                queries.append(" ".join(industry_info["primary"][:2]))
                queries.append(" ".join(industry_info["visual"][:2]))
        
        # 确保有足够的查询
        if not queries:
            queries = ["technology", "innovation", "digital transformation"]
        
        return queries[:5]  # 最多5个查询
    
    def search_wikimedia_images(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """从Wikimedia Commons搜索图片"""
        
        try:
            # Wikimedia Commons API
            url = "https://commons.wikimedia.org/w/api.php"
            params = {
                "action": "query",
                "format": "json",
                "generator": "search",
                "gsrnamespace": "6",  # File namespace
                "gsrsearch": query,
                "gsrlimit": limit,
                "prop": "imageinfo|pageterms",
                "iiprop": "url|size|mime|extmetadata",
                "iiurlwidth": 800,
                "iiextmetadatafilter": "ImageDescription|LicenseShortName|Artist",
                "wbptterms": "label"
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            images = []
            if "query" in data and "pages" in data["query"]:
                for page_id, page_info in data["query"]["pages"].items():
                    if "imageinfo" in page_info and len(page_info["imageinfo"]) > 0:
                        img_info = page_info["imageinfo"][0]
                        
                        image_data = {
                            "title": page_info.get("title", "").replace("File:", ""),
                            "url": img_info.get("url", ""),
                            "thumbnail_url": img_info.get("thumburl", ""),
                            "width": img_info.get("width", 0),
                            "height": img_info.get("height", 0),
                            "description": img_info.get("extmetadata", {}).get("ImageDescription", {}).get("value", ""),
                            "license": img_info.get("extmetadata", {}).get("LicenseShortName", {}).get("value", "Unknown"),
                            "artist": img_info.get("extmetadata", {}).get("Artist", {}).get("value", "Unknown"),
                            "source": "wikimedia",
                            "query_used": query
                        }
                        
                        images.append(image_data)
            
            return images
            
        except Exception as e:
            print(f"⚠️  Wikimedia搜索失败 ({query}): {e}")
            return []
    
    def calculate_relevance_score(self, image: Dict[str, Any], keywords: List[str]) -> float:
        """计算图片相关性评分"""
        
        score = 0.0
        
        # 检查图片标题和描述
        image_text = f"{image.get('title', '')} {image.get('description', '')}".lower()
        
        # 关键词匹配
        for keyword in keywords:
            keyword_lower = keyword.lower()
            if keyword_lower in image_text:
                # 完全匹配加分更多
                if f" {keyword_lower} " in f" {image_text} ":
                    score += 2.0
                else:
                    score += 1.0
        
        # 行业特定匹配
        if self.industry in self.industry_keywords:
            industry_info = self.industry_keywords[self.industry]
            
            # 检查主要关键词
            for term in industry_info["primary"]:
                if term.lower() in image_text:
                    score += 1.5
            
            # 检查视觉关键词
            for term in industry_info["visual"]:
                if term.lower() in image_text:
                    score += 2.0  # 视觉匹配更重要
        
        # 图片质量考虑
        width = image.get('width', 0)
        height = image.get('height', 0)
        
        if width >= 800 and height >= 600:
            score += 1.0  # 高分辨率
        elif width >= 400 and height >= 300:
            score += 0.5  # 中等分辨率
        
        # 来源可靠性
        if image.get('source') == 'wikimedia':
            score += 0.5  # Wikimedia图片质量较高
        
        # 许可证考虑（优先使用自由许可证）
        license_text = image.get('license', '').lower()
        free_licenses = ['cc-by', 'cc-by-sa', 'public domain', 'creative commons']
        if any(license in license_text for license in free_licenses):
            score += 0.5
        
        return score
    
    def select_best_images(self, md_text: str, num_images: int = 2) -> List[Dict[str, Any]]:
        """选择最相关的图片"""
        
        print(f"🔍 为{self.industry}行业文章选择图片...")
        
        # 提取关键词
        keywords = self.extract_article_keywords(md_text)
        print(f"   提取关键词: {', '.join(keywords[:5])}")
        
        # 生成搜索查询
        queries = self.generate_search_queries(keywords)
        print(f"   搜索查询: {', '.join(queries)}")
        
        # 搜索图片
        all_candidates = []
        for query in queries:
            print(f"   搜索: {query}")
            candidates = self.search_wikimedia_images(query, limit=3)
            all_candidates.extend(candidates)
        
        if not all_candidates:
            print("⚠️  未找到图片，使用备用查询...")
            # 备用查询
            backup_queries = ["technology", "business", "innovation"]
            for query in backup_queries:
                candidates = self.search_wikimedia_images(query, limit=2)
                all_candidates.extend(candidates)
        
        # 计算相关性评分
        for candidate in all_candidates:
            candidate['relevance_score'] = self.calculate_relevance_score(candidate, keywords)
        
        # 按评分排序
        all_candidates.sort(key=lambda x: x['relevance_score'], reverse=True)
        
        # 选择最佳图片
        selected = all_candidates[:num_images]
        
        # 输出结果
        print(f"✅ 找到 {len(all_candidates)} 张候选图片")
        for i, img in enumerate(selected[:3], 1):
            print(f"   {i}. {img.get('title', 'Unknown')[:50]}... (评分: {img['relevance_score']:.1f})")
        
        return selected
    
    def update_image_pool(self, selected_images: List[Dict[str, Any]]):
        """更新本地图片池"""
        
        pool_path = Path("data/public_image_pool.json")
        
        try:
            if pool_path.exists():
                with open(pool_path, 'r', encoding='utf-8') as f:
                    pool = json.load(f)
            else:
                pool = {"items": [], "last_updated": ""}
            
            # 添加新图片
            for img in selected_images:
                # 检查是否已存在
                existing = False
                for item in pool["items"]:
                    if item.get("url") == img.get("url"):
                        existing = True
                        break
                
                if not existing:
                    pool["items"].append(img)
            
            # 限制数量
            if len(pool["items"]) > 1000:
                pool["items"] = pool["items"][-1000:]
            
            pool["last_updated"] = datetime.datetime.now().isoformat()
            
            # 保存
            with open(pool_path, 'w', encoding='utf-8') as f:
                json.dump(pool, f, ensure_ascii=False, indent=2)
            
            print(f"✅ 图片池已更新，现有 {len(pool['items'])} 张图片")
            
        except Exception as e:
            print(f"⚠️  更新图片池失败: {e}")

def test_image_selection():
    """测试图片选择功能"""
    
    print("🧪 测试图片选择算法...")
    print("=" * 50)
    
    # 测试文章内容
    test_article = """
---
title: "人工智能在制造业的应用与前景分析"
date: 2026-02-25
categories: ["technology", "manufacturing"]
---

# 人工智能在制造业的应用与前景分析

## 智能制造的发展趋势

随着人工智能技术的快速发展，制造业正在经历一场深刻的数字化转型。从自动化生产线到智能质量控制，AI技术正在重塑制造业的各个环节。

## 关键技术应用

### 1. 机器视觉检测
基于深度学习的机器视觉系统可以实时检测产品缺陷，提高质量控制效率。

### 2. 预测性维护
通过分析设备传感器数据，AI可以预测设备故障，减少停机时间。

### 3. 智能供应链优化
AI算法可以优化库存管理、物流调度和生产计划。
"""
    
    # 测试不同行业
    test_industries = ["technology", "manufacturing", "ecommerce"]
    
    for industry in test_industries:
        print(f"\n📊 测试 {industry} 行业...")
        
        selector = SmartImageSelector(industry)
        
        # 提取关键词
        keywords = selector.extract_article_keywords(test_article)
        print(f"   关键词: {', '.join(keywords[:5])}")
        
        # 生成查询
        queries = selector.generate_search_queries(keywords)
        print(f"   查询: {', '.join(queries)}")
        
        # 选择图片
        images = selector.select_best_images(test_article, num_images=2)
        
        if images:
            print(f"   选择 {len(images)} 张图片:")
            for img in images:
                score = img.get('relevance_score', 0)
                title = img.get('title', 'Unknown')[:40]
                print(f"     - {title}... (评分: {score:.1f})")
        else:
            print("   ❌ 未找到合适图片")
    
    print("\n" + "=" * 50)
    print("✅ 测试完成")

if __name__ == "__main__":
    import datetime
    
    # 运行测试
    test_image_selection()
    
    print("\n🚀 使用说明:")
    print("   1. 在自动化脚本中集成:")
    print("      selector = SmartImageSelector(industry='technology')")
    print("      images = selector.select_best_images(article_text)")
    print("")
    print("   2. 更新现有脚本:")
    print("      python3 scripts/enhance_image_selection.py --integrate")
    print("")
    print("   3. 批量测试:")
    print("      python3 scripts/enhance_image_selection.py --test-all")
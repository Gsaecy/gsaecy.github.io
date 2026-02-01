#!/usr/bin/env python3
"""
真实新闻采集器
从实际网站采集行业新闻和数据
"""

import requests
from bs4 import BeautifulSoup
import logging
from datetime import datetime
from typing import List, Dict, Optional
import time
import random
from urllib.parse import urljoin
import feedparser

class RealNewsCollector:
    """真实新闻采集器"""
    
    def __init__(self, config):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # 用户代理列表，避免被屏蔽
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36',
        ]
        
        # 配置数据源
        self.sources = self.load_sources()
        self.logger.info(f"初始化采集器，配置了 {len(self.sources)} 个数据源")
    
    def load_sources(self) -> List[Dict]:
        """加载数据源配置"""
        sources_config = self.config.get('collectors', {}).get('sources', [])
        
        # 默认数据源（如果配置为空）
        if not sources_config:
            sources_config = [
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
        
        return [source for source in sources_config if source.get('enabled', True)]
    
    def collect(self) -> List[Dict]:
        """执行采集任务"""
        self.logger.info("开始采集新闻数据...")
        all_articles = []
        
        for source in self.sources:
            try:
                self.logger.info(f"采集源: {source['name']}")
                articles = self.collect_from_source(source)
                
                if articles:
                    all_articles.extend(articles)
                    self.logger.info(f"从 {source['name']} 采集到 {len(articles)} 篇文章")
                else:
                    self.logger.warning(f"从 {source['name']} 未采集到文章")
                
                # 避免请求过于频繁
                time.sleep(random.uniform(1, 3))
                
            except Exception as e:
                self.logger.error(f"采集源 {source.get('name')} 失败: {e}")
                continue
        
        self.logger.info(f"采集完成，总计 {len(all_articles)} 篇文章")
        return all_articles
    
    def collect_from_source(self, source: Dict) -> List[Dict]:
        """从单个源采集"""
        method = source.get('method', 'web')
        
        if method == 'rss':
            return self.collect_from_rss(source)
        elif method == 'api':
            return self.collect_from_api(source)
        else:  # web scraping
            return self.collect_from_web(source)
    
    def collect_from_web(self, source: Dict) -> List[Dict]:
        """通过网页爬虫采集"""
        url = source.get('url', '')
        if not url:
            return []
        
        try:
            headers = {
                'User-Agent': random.choice(self.user_agents),
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive',
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            response.encoding = 'utf-8'
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 根据网站类型使用不同的解析方法
            source_name = source.get('name', '')
            if '36kr' in source_name.lower():
                return self.parse_36kr(soup, source)
            elif 'huxiu' in source_name.lower():
                return self.parse_huxiu(soup, source)
            elif 'ebrun' in source_name.lower():
                return self.parse_ebrun(soup, source)
            elif 'gongkong' in source_name.lower():
                return self.parse_gongkong(soup, source)
            else:
                return self.parse_generic(soup, source)
                
        except Exception as e:
            self.logger.error(f"网页采集失败 {source.get('name')}: {e}")
            return []
    
    def collect_from_rss(self, source: Dict) -> List[Dict]:
        """通过RSS采集"""
        url = source.get('url', '')
        if not url:
            return []
        
        try:
            feed = feedparser.parse(url)
            articles = []
            
            for entry in feed.entries[:10]:  # 最多10条
                article = {
                    'title': entry.get('title', ''),
                    'content': entry.get('summary', entry.get('description', '')),
                    'url': entry.get('link', ''),
                    'source': source.get('name', 'RSS源'),
                    'publish_time': self.parse_rss_date(entry.get('published', '')),
                    'industry': source.get('type', 'general'),
                    'collected_at': datetime.now().isoformat()
                }
                
                # 清理内容
                article['content'] = self.clean_content(article['content'])
                
                if article['title'] and article['content']:
                    articles.append(article)
            
            return articles
            
        except Exception as e:
            self.logger.error(f"RSS采集失败 {source.get('name')}: {e}")
            return []
    
    def collect_from_api(self, source: Dict) -> List[Dict]:
        """通过API采集"""
        # 这里可以集成NewsAPI等第三方服务
        # 暂时返回空，需要配置API密钥
        return []
    
    def parse_36kr(self, soup: BeautifulSoup, source: Dict) -> List[Dict]:
        """解析36氪"""
        articles = []
        
        # 尝试多种选择器
        selectors = [
            '.newsflash-item',
            '.article-item',
            '.hotlist-item',
            'div[class*="news"]',
            'div[class*="article"]'
        ]
        
        for selector in selectors:
            items = soup.select(selector)
            if items:
                break
        
        for item in items[:15]:  # 最多15条
            try:
                # 提取标题
                title_elem = item.find(['h3', 'h4', 'a', 'div'], class_=lambda x: x and ('title' in x or 'tit' in x))
                title = title_elem.get_text(strip=True) if title_elem else ''
                
                # 提取内容
                content_elem = item.find(['p', 'div', 'span'], class_=lambda x: x and ('desc' in x or 'summary' in x or 'content' in x))
                content = content_elem.get_text(strip=True) if content_elem else ''
                
                # 提取链接
                link_elem = item.find('a', href=True)
                url = link_elem['href'] if link_elem else ''
                if url and not url.startswith('http'):
                    url = urljoin(source['url'], url)
                
                # 提取时间
                time_elem = item.find(['time', 'span', 'div'], class_=lambda x: x and ('time' in x or 'date' in x))
                publish_time = time_elem.get_text(strip=True) if time_elem else ''
                
                if title and content:
                    article = {
                        'title': title[:200],
                        'content': content[:500],
                        'url': url,
                        'source': source['name'],
                        'publish_time': publish_time or datetime.now().strftime('%Y-%m-%d %H:%M'),
                        'industry': source.get('type', 'tech'),
                        'collected_at': datetime.now().isoformat(),
                        'importance': self.calculate_importance(title, content)
                    }
                    articles.append(article)
                    
            except Exception as e:
                self.logger.debug(f"解析36氪文章失败: {e}")
                continue
        
        return articles
    
    def parse_huxiu(self, soup: BeautifulSoup, source: Dict) -> List[Dict]:
        """解析虎嗅网"""
        articles = []
        
        # 虎嗅的文章选择器
        items = soup.select('.article-item, .mod-art, .article-card')
        
        for item in items[:10]:  # 最多10条
            try:
                title_elem = item.select_one('.article-title, h2, h3, a[class*="title"]')
                title = title_elem.get_text(strip=True) if title_elem else ''
                
                content_elem = item.select_one('.article-summary, .desc, .excerpt')
                content = content_elem.get_text(strip=True) if content_elem else ''
                
                link_elem = item.find('a', href=True)
                url = link_elem['href'] if link_elem else ''
                if url and not url.startswith('http'):
                    url = urljoin(source['url'], url)
                
                if title:
                    article = {
                        'title': title[:200],
                        'content': content[:500] or title,  # 如果没有内容，用标题
                        'url': url,
                        'source': source['name'],
                        'publish_time': datetime.now().strftime('%Y-%m-%d'),
                        'industry': source.get('type', 'tech'),
                        'collected_at': datetime.now().isoformat(),
                        'importance': self.calculate_importance(title, content)
                    }
                    articles.append(article)
                    
            except Exception as e:
                self.logger.debug(f"解析虎嗅文章失败: {e}")
                continue
        
        return articles
    
    def parse_ebrun(self, soup: BeautifulSoup, source: Dict) -> List[Dict]:
        """解析亿邦动力（电商新闻）"""
        articles = []
        
        items = soup.select('.news-item, .article-item, .list-item')
        
        for item in items[:10]:
            try:
                title_elem = item.select_one('.title, h3, h4, a')
                title = title_elem.get_text(strip=True) if title_elem else ''
                
                content_elem = item.select_one('.summary, .desc, .content')
                content = content_elem.get_text(strip=True) if content_elem else ''
                
                # 电商相关关键词增强
                if any(keyword in title.lower() for keyword in ['电商', '跨境', '亚马逊', 'shopify', '直播']):
                    content = f"[电商焦点] {content}"
                
                if title:
                    article = {
                        'title': title[:200],
                        'content': content[:500] or title,
                        'url': source['url'],  # 亿邦可能需要特殊处理
                        'source': source['name'],
                        'publish_time': datetime.now().strftime('%Y-%m-%d'),
                        'industry': 'ecommerce',
                        'collected_at': datetime.now().isoformat(),
                        'importance': self.calculate_importance(title, content)
                    }
                    articles.append(article)
                    
            except Exception as e:
                self.logger.debug(f"解析亿邦动力文章失败: {e}")
                continue
        
        return articles
    
    def parse_gongkong(self, soup: BeautifulSoup, source: Dict) -> List[Dict]:
        """解析工控网（制造业新闻）"""
        articles = []
        
        items = soup.select('.news-list li, .article-item, .list-item')
        
        for item in items[:10]:
            try:
                title_elem = item.select_one('a, .title, h3')
                title = title_elem.get_text(strip=True) if title_elem else ''
                
                # 制造业相关关键词增强
                if any(keyword in title.lower() for keyword in ['智能制', '工业', '机器人', '自动化', '工厂']):
                    content = f"[制造前沿] {title}"
                else:
                    content = title
                
                if title:
                    article = {
                        'title': title[:200],
                        'content': content[:500],
                        'url': source['url'],
                        'source': source['name'],
                        'publish_time': datetime.now().strftime('%Y-%m-%d'),
                        'industry': 'manufacturing',
                        'collected_at': datetime.now().isoformat(),
                        'importance': self.calculate_importance(title, content)
                    }
                    articles.append(article)
                    
            except Exception as e:
                self.logger.debug(f"解析工控网文章失败: {e}")
                continue
        
        return articles
    
    def parse_generic(self, soup: BeautifulSoup, source: Dict) -> List[Dict]:
        """通用解析方法"""
        articles = []
        
        # 尝试常见的选择器
        common_selectors = [
            'article', '.article', '.post', '.news-item',
            '.item', '.entry', '.card', '.list-item'
        ]
        
        for selector in common_selectors:
            items = soup.select(selector)
            if items:
                break
        
        for item in items[:8]:  # 最多8条
            try:
                # 尝试提取标题
                title = ''
                for tag in ['h1', 'h2', 'h3', 'h4', 'h5']:
                    title_elem = item.find(tag)
                    if title_elem:
                        title = title_elem.get_text(strip=True)
                        break
                
                # 尝试提取内容
                content = ''
                for class_name in ['content', 'summary', 'excerpt', 'description']:
                    content_elem = item.find(class_=class_name)
                    if content_elem:
                        content = content_elem.get_text(strip=True)
                        break
                
                if not content and title:
                    content = title
                
                if title:
                    article = {
                        'title': title[:200],
                        'content': content[:500],
                        'url': source['url'],
                        'source': source['name'],
                        'publish_time': datetime.now().strftime('%Y-%m-%d'),
                        'industry': source.get('type', 'general'),
                        'collected_at': datetime.now().isoformat(),
                        'importance': 'medium'
                    }
                    articles.append(article)
                    
            except Exception as e:
                self.logger.debug(f"通用解析失败: {e}")
                continue
        
        return articles
    
    def parse_rss_date(self, date_str: str) -> str:
        """解析RSS日期"""
        try:
            if date_str:
                # 尝试解析常见格式
                for fmt in ['%a, %d %b %Y %H:%M:%S %z', '%Y-%m-%dT%H:%M:%SZ', '%Y-%m-%d %H:%M:%S']:
                    try:
                        dt = datetime.strptime(date_str, fmt)
                        return dt.strftime('%Y-%m-%d %H:%M:%S')
                    except:
                        continue
        except:
            pass
        
        return datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    def clean_content(self, content: str) -> str:
        """清理内容"""
        if not content:
            return ''
        
        # 移除HTML标签
        soup = BeautifulSoup(content, 'html.parser')
        text = soup.get_text()
        
        # 移除多余空白
        text = ' '.join(text.split())
        
        # 截断长度
        return text[:1000]
    
    def calculate_importance(self, title: str, content: str) -> str:
        """计算文章重要性"""
        text = (title + ' ' + content).lower()
        
        # 重要关键词
        important_keywords = [
            '突破', '重大', '首次', '革命', '颠覆', '暴涨', '暴跌',
            '紧急', '警告', '危机', '机遇', '万亿', '千亿'
        ]
        
        # 检查关键词
        for keyword in important_keywords:
            if keyword in text:
                return 'high'
        
        # 检查长度和内容质量
        if len(title) > 20 and len(content) > 100:
            return 'medium'
        else:
            return 'low'

if __name__ == "__main__":
    # 测试代码
    import logging
    
    logging.basicConfig(level=logging.INFO)
    
    test_config = {
        "collectors": {
            "sources": [
                {
                    "name": "36氪测试",
                    "url": "https://36kr.com",
                    "type": "tech",
                    "method": "web",
                    "enabled": True
                }
            ]
        }
    }
    
    collector = RealNewsCollector(test_config)
    articles = collector.collect()
    
    print(f"采集到 {len(articles)} 篇文章")
    for article in articles[:3]:
        print(f"- {article['title'][:50]}...")
#!/usr/bin/env python3
"""
微信公众号文章自动排版工具
将Markdown转换为微信公众号友好格式
"""

import re
import yaml
from datetime import datetime
from typing import Dict, List, Tuple

class WeChatFormatter:
    def __init__(self, rules_file="wechat-style-rules.yml"):
        """初始化格式化器"""
        with open(rules_file, 'r', encoding='utf-8') as f:
            self.rules = yaml.safe_load(f)

        # 兼容 wechat-style-rules.yml 的结构：顶层包含 rules
        if isinstance(self.rules, dict) and "rules" in self.rules and isinstance(self.rules["rules"], dict):
            self.rules = self.rules["rules"]
        
        # 编译正则表达式
        self.patterns = {
            'emoji': re.compile(r'[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U0001F1E0-\U0001F1FF]'),
            'markdown_headers': re.compile(r'^(#{1,6})\s+(.*)$', re.MULTILINE),
            'markdown_links': re.compile(r'\[([^\]]+)\]\(([^)]+)\)'),
            'markdown_bold': re.compile(r'\*\*(.*?)\*\*'),
            'markdown_italic': re.compile(r'\*(.*?)\*'),
            'code_blocks': re.compile(r'```[\s\S]*?```'),
            'inline_code': re.compile(r'`([^`]+)`'),
            'tables': re.compile(r'^\|.*\|$', re.MULTILINE),
            'multiple_spaces': re.compile(r' {2,}'),
            'multiple_newlines': re.compile(r'\n{3,}'),
        }
    
    def format_article(self, markdown_content: str) -> str:
        """将Markdown转换为微信公众号格式"""
        content = markdown_content
        
        # 1. 移除表情符号
        content = self.remove_emojis(content)
        
        # 2. 转换标题格式
        content = self.format_headers(content)
        
        # 3. 转换链接格式
        content = self.format_links(content)
        
        # 4. 转换粗体和斜体
        content = self.format_text_styles(content)
        
        # 5. 处理代码块（转换为纯文本）
        content = self.format_code_blocks(content)
        
        # 6. 处理表格（简化格式）
        content = self.format_tables(content)
        
        # 7. 规范化空格和换行
        content = self.normalize_whitespace(content)
        
        # 8. 添加微信公众号特定格式
        content = self.add_wechat_formatting(content)
        
        # 9. 验证内容质量
        self.validate_content(content)
        
        return content
    
    def remove_emojis(self, content: str) -> str:
        """移除所有表情符号"""
        return self.patterns['emoji'].sub('', content)
    
    def format_headers(self, content: str) -> str:
        """转换Markdown标题为微信公众号格式"""
        def replace_header(match):
            level = len(match.group(1))
            text = match.group(2).strip()
            
            if level == 1:  # 一级标题
                return f"【{text}】\n\n"
            elif level == 2:  # 二级标题
                return f"【{text}】\n\n"
            elif level == 3:  # 三级标题
                return f"{text}\n\n"
            else:
                return f"{text}\n\n"
        
        return self.patterns['markdown_headers'].sub(replace_header, content)
    
    def format_links(self, content: str) -> str:
        """转换Markdown链接为纯文本"""
        def replace_link(match):
            text = match.group(1)
            url = match.group(2)
            return f"{text}（{url}）"
        
        return self.patterns['markdown_links'].sub(replace_link, content)
    
    def format_text_styles(self, content: str) -> str:
        """转换粗体和斜体"""
        # 粗体 -> 加粗标记
        content = self.patterns['markdown_bold'].sub(r'【\1】', content)
        
        # 斜体 -> 移除标记（微信公众号不支持斜体）
        content = self.patterns['markdown_italic'].sub(r'\1', content)
        
        return content
    
    def format_code_blocks(self, content: str) -> str:
        """处理代码块"""
        # 移除代码块标记
        content = self.patterns['code_blocks'].sub('【代码示例】\n（建议使用截图展示代码）\n', content)
        
        # 内联代码 -> 等宽标记
        content = self.patterns['inline_code'].sub(r'【\1】', content)
        
        return content
    
    def format_tables(self, content: str) -> str:
        """简化表格格式"""
        def simplify_table(match):
            table = match.group(0)
            lines = table.strip().split('\n')
            
            if len(lines) <= 3:  # 简单表格保留
                return table
            else:  # 复杂表格建议使用图片
                return "【数据表格】\n（建议使用图片展示复杂表格）\n"
        
        return self.patterns['tables'].sub(simplify_table, content)
    
    def normalize_whitespace(self, content: str) -> str:
        """规范化空格和换行"""
        # 多个空格 -> 一个空格
        content = self.patterns['multiple_spaces'].sub(' ', content)
        
        # 多个换行 -> 两个换行
        content = self.patterns['multiple_newlines'].sub('\n\n', content)
        
        return content.strip()
    
    def add_wechat_formatting(self, content: str) -> str:
        """添加微信公众号特定格式"""
        lines = content.split('\n')
        formatted_lines = []
        
        for line in lines:
            if line.strip():
                # 添加段落标记
                if line.startswith('【') and line.endswith('】'):
                    formatted_lines.append(f"\n{line}\n")
                else:
                    formatted_lines.append(line)
            else:
                formatted_lines.append('')
        
        # 添加分割线
        formatted_content = '\n'.join(formatted_lines)
        formatted_content = formatted_content.replace('\n\n\n', '\n\n---\n\n')
        
        # 添加页脚
        footer = self.generate_footer()
        formatted_content += f"\n\n{footer}"
        
        return formatted_content
    
    def generate_footer(self) -> str:
        """生成标准页脚"""
        return f"""
---
本文由AI智汇观察系统自动生成
生成时间：{datetime.now().strftime('%Y年%m月%d日 %H:%M')}
数据来源：文中已标注
使用建议：数据仅供参考，投资需谨慎

关注「AI智汇观察」获取最新行业分析
        """.strip()
    
    def validate_content(self, content: str) -> Dict:
        """验证内容质量"""
        validation_results = {
            "passed": True,
            "issues": [],
            "stats": {}
        }
        
        # 统计基本信息
        words = len(content)
        paragraphs = len([p for p in content.split('\n\n') if p.strip()])
        lines = len(content.split('\n'))
        
        validation_results["stats"] = {
            "总字数": words,
            "段落数": paragraphs,
            "行数": lines
        }
        
        # 检查表情符号
        if self.patterns['emoji'].search(content):
            validation_results["issues"].append("❌ 发现表情符号")
            validation_results["passed"] = False
        
        # 检查代码块
        if self.patterns['code_blocks'].search(content):
            validation_results["issues"].append("⚠️ 发现代码块（建议使用截图）")
        
        # 检查复杂表格
        tables = list(self.patterns['tables'].finditer(content))
        if len(tables) > 3:
            validation_results["issues"].append("⚠️ 表格过多（建议简化）")
        
        # 检查长度
        min_words = self.rules["content_quality"]["length"]["min_words"]
        max_words = self.rules["content_quality"]["length"]["max_words"]
        
        if words < min_words:
            validation_results["issues"].append(f"❌ 字数不足（{words}/{min_words}）")
            validation_results["passed"] = False
        elif words > max_words:
            validation_results["issues"].append(f"⚠️ 字数超出建议（{words}/{max_words}）")
        
        return validation_results
    
    def generate_quality_report(self, validation_results: Dict) -> str:
        """生成质量报告"""
        report = []
        report.append("# 微信公众号文章质量报告")
        report.append(f"生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")
        
        if validation_results["passed"]:
            report.append("## ✅ 验证通过")
        else:
            report.append("## ❌ 验证失败")
        
        report.append("")
        report.append("## 📊 统计数据")
        for key, value in validation_results["stats"].items():
            report.append(f"- {key}: {value}")
        
        report.append("")
        report.append("## 🔍 检查结果")
        
        if validation_results["issues"]:
            for issue in validation_results["issues"]:
                report.append(f"- {issue}")
        else:
            report.append("- ✅ 所有检查通过")
        
        report.append("")
        report.append("## 📋 改进建议")
        
        # 根据规则给出建议
        rules = self.rules["content_quality"]
        
        report.append(f"1. 建议字数：{rules['length']['ideal_words']}字左右")
        report.append(f"2. 建议段落：{rules['length']['min_paragraphs']}-{rules['length']['max_paragraphs']}段")
        report.append(f"3. 建议图片：{self.rules['visual_elements']['images']['min_count']}-{self.rules['visual_elements']['images']['max_count']}张")
        report.append("4. 确保所有数据都有来源标注")
        report.append("5. 在微信公众号编辑器中预览效果")
        
        return "\n".join(report)

def main():
    """主函数"""
    import sys
    
    if len(sys.argv) < 2:
        print("使用方法: python format-wechat.py <markdown文件>")
        print("示例: python format-wechat.py article.md")
        sys.exit(1)
    
    input_file = sys.argv[1]
    
    # 读取Markdown文件
    with open(input_file, 'r', encoding='utf-8') as f:
        markdown_content = f.read()
    
    # 创建格式化器
    formatter = WeChatFormatter()
    
    # 格式化文章
    print("🔄 正在格式化文章...")
    wechat_content = formatter.format_article(markdown_content)
    
    # 验证内容
    print("🔍 正在验证内容质量...")
    validation = formatter.validate_content(wechat_content)
    
    # 生成输出文件
    output_file = input_file.replace('.md', '-wechat.md')
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(wechat_content)
    
    # 生成质量报告
    report_file = input_file.replace('.md', '-quality-report.md')
    report = formatter.generate_quality_report(validation)
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"✅ 格式化完成！")
    print(f"📄 微信公众号格式文章: {output_file}")
    print(f"📊 质量报告: {report_file}")
    
    # 显示验证结果
    if validation["passed"]:
        print("🎉 文章通过所有质量检查！")
    else:
        print("⚠️ 文章存在需要改进的问题，请查看质量报告")

if __name__ == "__main__":
    main()
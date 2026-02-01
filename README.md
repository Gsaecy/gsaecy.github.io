# AI行业观察站 🤖

一个由AI驱动的自动化行业分析博客，每天自动搜集、分析并发布各行业最新动态。

## 🌐 在线访问

访问地址：https://Gsaecy.github.io

## ✨ 功能特色

- **全自动更新**：每天自动采集、分析、发布
- **多行业覆盖**：科技、金融、教育、医疗、电商等
- **AI深度分析**：使用GPT模型进行趋势分析和洞察
- **数据可视化**：关键数据图表展示
- **开源可定制**：完全开源，可根据需求定制

## 🚀 技术架构

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   信息采集       │    │   AI分析        │    │   内容生成      │
│  - 科技新闻     │───▶│  - 趋势分析     │───▶│  - Markdown     │
│  - 金融数据     │    │  - 机会识别     │    │  - 元数据       │
│  - 社交趋势     │    │  - 风险预警     │    │  - 格式化       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                                                │
         ▼                                                ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   数据存储       │    │   自动发布      │    │   GitHub Pages  │
│  - 原始数据     │    │  - Hugo集成     │    │  - 免费托管     │
│  - 处理数据     │    │  - 定时任务     │    │  - 自动部署     │
│  - 分析结果     │    │  - 监控告警     │    │  - CDN加速      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 📁 项目结构

```
.
├── .github/workflows/   # GitHub Actions自动化
├── content/             # Hugo内容目录
│   ├── posts/          # 博客文章
│   └── about.md        # 关于页面
├── scripts/            # 自动化脚本
│   ├── collectors/     # 信息采集
│   ├── analyzers/      # AI分析
│   ├── generators/     # 文章生成
│   ├── publishers/     # 发布脚本
│   └── main.py         # 主控制脚本
├── config/             # 配置文件
├── data/               # 数据存储
├── themes/             # Hugo主题
└── static/             # 静态资源
```

## 🛠️ 快速开始

### 1. 本地开发

```bash
# 克隆项目
git clone https://github.com/Gsaecy/Gsaecy.github.io.git
cd Gsaecy.github.io

# 安装Hugo（Mac）
brew install hugo

# 安装Python依赖
pip install -r requirements.txt

# 本地运行
hugo server -D
```

### 2. 配置自动化

1. 复制配置文件：
```bash
cp config/config.example.yaml config/config.yaml
```

2. 编辑 `config/config.yaml`：
```yaml
openai:
  api_key: "your-openai-api-key"
  
sources:
  tech:
    - name: "36氪"
      url: "https://36kr.com"
```

3. 测试运行：
```bash
python scripts/main.py --test
```

### 3. 部署到GitHub Pages

项目已配置GitHub Actions，推送代码到main分支会自动部署。

## ⚙️ 配置说明

### 数据源配置

```yaml
sources:
  tech:
    - name: "36氪"
      url: "https://36kr.com"
    - name: "虎嗅"
      url: "https://huxiu.com"
  
  finance:
    - name: "华尔街见闻"
      url: "https://wallstreetcn.com"
```

### 分析配置

```yaml
analysis:
  industries: ["科技", "金融", "教育", "医疗"]
  depth: "medium"  # low/medium/high
  include_trends: true
  include_forecast: true
```

### 发布配置

```yaml
publish:
  blog_path: "./content/posts"
  max_posts_per_day: 5
  schedule: "10:00"  # 每天发布时间
  auto_deploy: true
```

## 📅 自动化计划

- **每日10:00**：自动采集和分析
- **每周日20:00**：生成周度总结报告
- **每月最后一天**：生成月度趋势报告

## 🔧 自定义开发

### 添加新的数据源

1. 在 `scripts/collectors/` 创建新的采集器
2. 在 `config/config.yaml` 中添加配置
3. 在 `scripts/main.py` 中注册采集器

### 修改分析逻辑

1. 编辑 `scripts/analyzers/` 中的分析器
2. 调整AI提示词和参数
3. 测试分析效果

### 更换博客主题

1. 在 `themes/` 目录添加新主题
2. 修改 `hugo.toml` 中的主题配置
3. 调整布局和样式

## 🐛 故障排除

### 常见问题

1. **GitHub Pages不更新**
   - 检查GitHub Actions运行状态
   - 查看构建日志中的错误信息
   - 确保 `hugo.toml` 配置正确

2. **采集器失败**
   - 检查网络连接
   - 验证网站结构是否变化
   - 更新解析规则

3. **AI分析质量差**
   - 调整提示词
   - 增加上下文信息
   - 使用更高级的模型

### 日志查看

```bash
# 查看GitHub Actions日志
# 在仓库页面点击 Actions → 选择工作流 → 查看运行详情

# 查看本地日志
cat logs/app.log
```

## 📈 性能优化

- 使用缓存减少API调用
- 并行处理多个数据源
- 增量更新避免重复分析
- 压缩静态资源加速访问

## 🤝 贡献指南

欢迎贡献代码、报告问题或提出建议！

1. Fork本仓库
2. 创建功能分支
3. 提交更改
4. 发起Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 📞 联系支持

- GitHub Issues: [问题反馈](https://github.com/Gsaecy/Gsaecy.github.io/issues)
- 博客地址: https://Gsaecy.github.io

---

*让AI为你解读行业，洞察未来趋势！*
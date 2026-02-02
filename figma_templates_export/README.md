# AI智汇观察 - Figma模板导出包

## 🎯 包含内容

### 1. 设计模板文件
- `ai_blog_templates.fig` - 完整的Figma模板文件

### 2. 节点ID映射表
- `node_mapping.csv` - 所有关键元素的节点ID
- `node_mapping.json` - JSON格式的节点映射

### 3. 配置更新文件
- `config_update.yaml` - 更新好的配置文件（直接替换）

### 4. 使用指南
- `import_guide.md` - 导入和使用指南
- `design_specs.md` - 设计规范文档

## 📋 导入步骤

### 第一步：导入Figma文件
1. 登录 Figma (https://www.figma.com)
2. 点击左上角菜单 → "File" → "Import"
3. 选择 `ai_blog_templates.fig` 文件
4. 文件将作为新文件导入

### 第二步：复制到你的文件
1. 打开你导入的文件
2. 打开你的 `AI-Blog-Templates` 文件
3. 在导入文件中，选择页面标签：
   - "公众号模板"
   - "小红书模板" 
   - "微博模板"
4. 右键点击页面 → "Copy"
5. 切换到你的文件 → 右键 → "Paste"

### 第三步：验证节点ID
1. 运行节点获取脚本：
   ```bash
   export FIGMA_ACCESS_TOKEN=你的token
   python get_figma_nodes.py GHZFIC9s6XJsNWKlA6XOl3
   ```
2. 确认节点ID与映射表一致

### 第四步：更新配置
1. 复制 `config_update.yaml` 内容
2. 替换 `config/config.yaml` 中的 `figma` 部分
3. 确保 `enabled: true`

## 🎨 模板设计特色

### 公众号模板 (900px宽)
- **标题区**：科技蓝渐变背景，大字体
- **内容区**：结构化布局，清晰的信息层次
- **数据区**：可视化卡片，美观的数据展示
- **CTA区**：专业二维码和关注引导

### 小红书模板 (1242×1660px)
- **封面区**：吸引眼球的大图设计
- **内容区**：竖版信息流，适合手机阅读
- **标签区**：便于搜索和分类
- **个人资料**：品牌信息展示

### 微博模板 (1080px宽)
- **标题区**：信息密度高，适合快速浏览
- **趋势区**：卡片式呈现关键趋势
- **数据区**：快速获取核心信息
- **互动区**：话题标签和二维码

## 🔧 自动化配置

### 节点映射示例：
```yaml
wechat_article:
  file_key: "GHZFIC9s6XJsNWKlA6XOl3"
  node_map:
    title: "10:1"           # 主标题
    subtitle: "10:2"        # 副标题/日期
    content: "10:3"         # 正文内容
    data_card_1: "10:4"     # 数据卡片1
    data_card_2: "10:5"     # 数据卡片2
    key_points: "10:6"      # 关键点
    recommendations: "10:7" # 建议
    qrcode: "10:8"          # 二维码
```

### 自动化流程：
1. AI生成内容 → 2. Figma填充模板 → 3. 导出图片 → 4. 多平台发布

## 🚀 快速测试

### 测试连接：
```bash
# 设置环境变量
export FIGMA_ACCESS_TOKEN=你的token

# 测试API连接
python test_figma_api.py

# 获取节点结构
python get_figma_nodes.py GHZFIC9s6XJsNWKlA6XOl3
```

### 测试设计生成：
```bash
# 运行设计测试
python scripts/design/figma_client.py --test

# 测试多平台发布
python scripts/publishers/multi_platform_publisher.py --test
```

## 📞 支持

如有问题，请参考：
1. `design_specs.md` - 详细设计规范
2. `troubleshooting.md` - 常见问题解决
3. 联系技术支持

---

**现在开始导入模板，开启自动化发布之旅！** 🎨🚀
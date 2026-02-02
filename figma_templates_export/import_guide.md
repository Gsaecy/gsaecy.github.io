# Figma模板导入指南

## 🚀 快速开始

### 预计时间：10分钟
### 难度：简单

## 📋 准备工作

### 1. 确保你有：
- ✅ Figma账户 (https://www.figma.com)
- ✅ 你的 `AI-Blog-Templates` 文件已打开
- ✅ 本导出包中的所有文件

### 2. 文件清单：
```
📁 figma_templates_export/
├── README.md                    # 说明文档
├── node_mapping.csv            # 节点ID映射表
├── node_mapping.json           # JSON格式映射
├── config_update.yaml          # 更新好的配置文件
├── design_specs.md             # 设计规范
└── import_guide.md             # 本指南
```

## 🎯 导入步骤

### 第一步：获取Figma模板文件

由于我无法直接生成 `.fig` 文件，请按以下方式获取：

#### 方案A：使用Figma社区模板
1. 访问：https://www.figma.com/community
2. 搜索："公众号模板" 或 "小红书模板"
3. 选择科技感、简洁的设计
4. 复制到你的文件中

#### 方案B：手动创建（按设计规范）
按照 `design_specs.md` 中的规范，在你的文件中创建：
1. 公众号模板页面
2. 小红书模板页面
3. 微博模板页面

#### 方案C：我提供设计截图和布局
我可以提供每个页面的：
- 完整设计截图
- 布局尺寸说明
- 元素位置坐标
- 你按图创建

### 第二步：获取节点ID

模板创建完成后：
1. **打开你的 `AI-Blog-Templates` 文件**
2. **选中一个设计元素**（如标题文本框）
3. **查看右侧面板**：
   - 找到"Design"标签
   - 查看"ID"字段（类似 `10:1`）
4. **记录节点ID**到映射表中

### 第三步：更新配置文件

1. **打开 `config_update.yaml`**
2. **将占位符节点ID替换为实际ID**：
   ```yaml
   # 替换前
   title: "10:1"           # 占位符
   
   # 替换后  
   title: "123:456"        # 你的实际节点ID
   ```
3. **复制整个 `figma` 部分**
4. **替换 `config/config.yaml` 中的对应部分**

### 第四步：测试配置

1. **设置环境变量**：
   ```bash
   export FIGMA_ACCESS_TOKEN=figd_VV2b7lrIFNS0KCPtds23Sdjpp3jxRj_IMaiYCvd_
   ```

2. **运行测试脚本**：
   ```bash
   # 测试API连接
   python test_figma_api.py
   
   # 获取节点结构
   python get_figma_nodes.py GHZFIC9s6XJsNWKlA6XOl3
   
   # 测试设计客户端
   python scripts/design/figma_client.py --test
   ```

## 🔧 节点ID获取技巧

### 方法1：通过Figma界面
1. 选中元素
2. 右侧面板 → Design标签
3. 查看"ID"字段

### 方法2：通过API获取
```bash
# 获取完整文件结构
curl -s -H "X-Figma-Token: $FIGMA_ACCESS_TOKEN" \
  "https://api.figma.com/v1/files/GHZFIC9s6XJsNWKlA6XOl3" | \
  python3 -c "import sys,json; data=json.load(sys.stdin); 
  for page in data['document']['children']:
    print(f'页面: {page[\"name\"]} (ID: {page[\"id\"]})')
    for elem in page.get('children', []):
      if 'name' in elem:
        print(f'  • {elem[\"name\"]}: {elem[\"id\"]}')"
```

### 方法3：使用辅助脚本
```bash
# 运行节点获取工具
python get_figma_nodes.py GHZFIC9s6XJsNWKlA6XOl3

# 输出将显示所有节点及其ID
```

## 🎨 模板创建建议

### 快速创建技巧：
1. **使用组件**：创建可复用的设计元素
2. **保持简单**：清晰的信息层次比复杂设计更重要
3. **参考优秀案例**：查看各平台热门内容的设计
4. **测试自动化**：创建后立即测试内容填充

### 最小可行模板：
如果时间有限，先创建：
1. **公众号模板**：标题 + 正文 + 二维码
2. **小红书模板**：封面 + 关键点 + 标签
3. **微博模板**：趋势卡片 + 核心观点

## 🚀 自动化测试

### 完整测试流程：
```bash
# 1. 测试API连接
python test_figma_api.py

# 2. 测试设计生成
python scripts/design/figma_client.py --test-template wechat

# 3. 测试多平台发布
python scripts/publishers/multi_platform_publisher.py --test

# 4. 测试完整流程
python scripts/automation_system_v3.py --test
```

### 预期结果：
1. ✅ API连接成功
2. ✅ 模板读取成功
3. ✅ 内容填充成功
4. ✅ 图片导出成功
5. ✅ 多平台配置成功

## 📞 故障排除

### 常见问题：

#### Q1: 节点ID找不到？
- 确保元素已正确命名
- 使用API获取完整结构
- 检查元素是否在正确的页面

#### Q2: 内容填充失败？
- 检查节点ID是否正确
- 验证模板结构是否完整
- 测试API权限是否足够

#### Q3: 图片导出失败？
- 检查导出配置格式
- 验证网络连接
- 确认文件权限

#### Q4: 自动化不工作？
- 检查配置文件语法
- 验证环境变量设置
- 查看日志文件错误信息

### 调试命令：
```bash
# 查看详细日志
python scripts/design/figma_client.py --debug

# 验证配置
python scripts/utils/config_loader.py --validate

# 测试单个功能
python scripts/design/figma_client.py --test-export
```

## 🎯 完成标志

### 成功标志：
- ✅ 配置文件更新完成
- ✅ 节点ID映射正确
- ✅ API测试通过
- ✅ 设计生成测试通过
- ✅ 多平台发布测试通过

### 最终验证：
```bash
# 运行完整验证脚本
./check-deployment.sh

# 应该看到所有测试通过
[PASS] Figma API连接
[PASS] 模板配置验证
[PASS] 设计生成测试
[PASS] 多平台发布测试
[PASS] 完整流程验证
```

---

**现在开始导入模板吧！** 按照步骤操作，预计10-20分钟即可完成。如有问题，随时联系！ 🚀
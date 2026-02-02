#!/bin/bash
# 完整Figma自动化设置测试脚本

set -e  # 遇到错误退出

echo "🎯 Figma自动化设置完整测试"
echo "========================================"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 检查环境变量
echo -e "\n1. ${YELLOW}检查环境变量...${NC}"
if [ -z "$FIGMA_ACCESS_TOKEN" ]; then
    echo -e "${RED}❌ FIGMA_ACCESS_TOKEN 未设置${NC}"
    echo "请运行: export FIGMA_ACCESS_TOKEN=你的token"
    exit 1
else
    echo -e "${GREEN}✅ FIGMA_ACCESS_TOKEN 已设置${NC}"
fi

# 检查Python环境
echo -e "\n2. ${YELLOW}检查Python环境...${NC}"
if command -v python3 &> /dev/null; then
    echo -e "${GREEN}✅ Python3 已安装${NC}"
else
    echo -e "${RED}❌ Python3 未安装${NC}"
    exit 1
fi

# 检查依赖
echo -e "\n3. ${YELLOW}检查Python依赖...${NC}"
if python3 -c "import requests" &> /dev/null; then
    echo -e "${GREEN}✅ requests 库已安装${NC}"
else
    echo -e "${YELLOW}⚠️  requests 库未安装，尝试安装...${NC}"
    pip3 install requests || echo -e "${RED}❌ 安装失败，请手动安装: pip3 install requests${NC}"
fi

# 测试API连接
echo -e "\n4. ${YELLOW}测试Figma API连接...${NC}"
python3 -c "
import os, requests, sys
token = os.getenv('FIGMA_ACCESS_TOKEN')
if not token:
    print('❌ Token未设置')
    sys.exit(1)

headers = {'X-Figma-Token': token}
try:
    resp = requests.get('https://api.figma.com/v1/me', headers=headers, timeout=10)
    if resp.status_code == 200:
        data = resp.json()
        print('✅ API连接成功')
        print(f'   用户: {data.get(\"email\")}')
        print(f'   用户名: {data.get(\"handle\")}')
    else:
        print(f'❌ API连接失败: {resp.status_code}')
        sys.exit(1)
except Exception as e:
    print(f'❌ 连接错误: {e}')
    sys.exit(1)
"

# 测试文件访问
echo -e "\n5. ${YELLOW}测试文件访问...${NC}"
FILE_ID="GHZFIC9s6XJsNWKlA6XOl3"
python3 -c "
import os, requests, sys, json
token = os.getenv('FIGMA_ACCESS_TOKEN')
headers = {'X-Figma-Token': token}

try:
    resp = requests.get(f'https://api.figma.com/v1/files/{'$FILE_ID'}', headers=headers, timeout=10)
    if resp.status_code == 200:
        data = resp.json()
        print('✅ 文件访问成功')
        print(f'   文件名: {data.get(\"name\")}')
        
        # 检查页面
        pages = data.get('document', {}).get('children', [])
        print(f'   页面数量: {len(pages)}')
        
        for page in pages:
            page_name = page.get('name', '未命名')
            elements = len(page.get('children', []))
            print(f'   - {page_name}: {elements}个元素')
            
    elif resp.status_code == 404:
        print('❌ 文件不存在或无权访问')
        sys.exit(1)
    else:
        print(f'❌ 文件访问失败: {resp.status_code}')
        print(f'   响应: {resp.text[:100]}')
        sys.exit(1)
except Exception as e:
    print(f'❌ 文件访问错误: {e}')
    sys.exit(1)
"

# 测试配置文件
echo -e "\n6. ${YELLOW}测试配置文件...${NC}"
if [ -f "../config/config.yaml" ]; then
    echo -e "${GREEN}✅ 配置文件存在${NC}"
    
    # 检查figma配置
    if grep -q "figma:" "../config/config.yaml"; then
        echo -e "${GREEN}✅ Figma配置存在${NC}"
        
        # 检查是否启用
        if grep -q "enabled: true" "../config/config.yaml"; then
            echo -e "${GREEN}✅ Figma已启用${NC}"
        else
            echo -e "${YELLOW}⚠️  Figma未启用，请检查配置${NC}"
        fi
    else
        echo -e "${RED}❌ Figma配置不存在${NC}"
    fi
else
    echo -e "${RED}❌ 配置文件不存在${NC}"
fi

# 测试设计客户端
echo -e "\n7. ${YELLOW}测试设计客户端...${NC}"
if [ -f "../scripts/design/figma_client.py" ]; then
    echo -e "${GREEN}✅ 设计客户端脚本存在${NC}"
    
    # 简单测试导入
    python3 -c "
import sys
sys.path.append('..')
try:
    from scripts.design.figma_client import FigmaClient
    print('✅ FigmaClient 可正常导入')
except ImportError as e:
    print(f'❌ 导入失败: {e}')
except Exception as e:
    print(f'❌ 其他错误: {e}')
"
else
    echo -e "${RED}❌ 设计客户端脚本不存在${NC}"
fi

# 测试多平台发布器
echo -e "\n8. ${YELLOW}测试多平台发布器...${NC}"
if [ -f "../scripts/publishers/multi_platform_publisher.py" ]; then
    echo -e "${GREEN}✅ 多平台发布器脚本存在${NC}"
    
    python3 -c "
import sys
sys.path.append('..')
try:
    from scripts.publishers.multi_platform_publisher import MultiPlatformPublisher
    print('✅ MultiPlatformPublisher 可正常导入')
except ImportError as e:
    print(f'❌ 导入失败: {e}')
except Exception as e:
    print(f'❌ 其他错误: {e}')
"
else
    echo -e "${RED}❌ 多平台发布器脚本不存在${NC}"
fi

# 生成测试报告
echo -e "\n${GREEN}========================================${NC}"
echo -e "${GREEN}🎉 测试完成！${NC}"
echo -e "${GREEN}========================================${NC}"

echo -e "\n📋 下一步建议："
echo "1. 按照 import_guide.md 导入模板"
echo "2. 获取节点ID并更新配置"
echo "3. 运行完整自动化测试"
echo "4. 开始多平台自动化发布"

echo -e "\n🔧 调试命令："
echo "  # 获取节点ID"
echo "  python get_figma_nodes.py GHZFIC9s6XJsNWKlA6XOl3"
echo ""
echo "  # 测试设计生成"
echo "  python scripts/design/figma_client.py --test"
echo ""
echo "  # 完整流程测试"
echo "  python scripts/automation_system_v3.py --test"

echo -e "\n🚀 现在开始你的自动化发布之旅吧！"
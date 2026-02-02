#!/usr/bin/env python3
"""
快速测试Figma API连接
"""

import os
import requests
import json

def test_figma_api():
    """测试Figma API连接"""
    # 使用你提供的token
    token = "figd_VV2b7lrIFNS0KCPtds23Sdjpp3jxRj_IMaiYCvd_"
    
    headers = {
        'X-Figma-Token': token,
        'Content-Type': 'application/json'
    }
    
    print("🔗 测试Figma API连接...")
    print(f"Token: {token[:10]}...{token[-10:]}")
    
    try:
        # 测试1: 获取用户信息（验证token有效性）
        print("\n1. 测试用户信息API...")
        user_response = requests.get(
            'https://api.figma.com/v1/me',
            headers=headers,
            timeout=10
        )
        
        if user_response.status_code == 200:
            user_data = user_response.json()
            print(f"✅ 用户信息获取成功!")
            print(f"   用户ID: {user_data.get('id')}")
            print(f"   邮箱: {user_data.get('email')}")
            print(f"   用户名: {user_data.get('handle')}")
        else:
            print(f"❌ 用户信息获取失败: {user_response.status_code}")
            print(f"   响应: {user_response.text}")
            return False
        
        # 测试2: 获取团队/项目列表
        print("\n2. 测试团队信息API...")
        teams_response = requests.get(
            'https://api.figma.com/v1/teams',
            headers=headers,
            timeout=10
        )
        
        if teams_response.status_code == 200:
            teams_data = teams_response.json()
            teams = teams_data.get('teams', [])
            print(f"✅ 找到 {len(teams)} 个团队:")
            for team in teams[:3]:  # 显示前3个团队
                print(f"   - {team.get('name')} (ID: {team.get('id')})")
        else:
            print(f"⚠️  团队信息获取失败（可能是个人账户）: {teams_response.status_code}")
        
        # 测试3: 获取项目列表
        print("\n3. 测试项目信息API...")
        # 如果有团队，获取团队项目
        if teams:
            team_id = teams[0]['id']
            projects_response = requests.get(
                f'https://api.figma.com/v1/teams/{team_id}/projects',
                headers=headers,
                timeout=10
            )
            
            if projects_response.status_code == 200:
                projects_data = projects_response.json()
                projects = projects_data.get('projects', [])
                print(f"✅ 找到 {len(projects)} 个项目:")
                for project in projects[:3]:
                    print(f"   - {project.get('name')} (ID: {project.get('id')})")
            else:
                print(f"⚠️  项目信息获取失败: {projects_response.status_code}")
        else:
            # 个人账户获取文件
            print("\n4. 测试文件列表API...")
            files_response = requests.get(
                'https://api.figma.com/v1/files',
                headers=headers,
                timeout=10
            )
            
            if files_response.status_code == 200:
                files_data = files_response.json()
                files = files_data.get('files', [])
                print(f"✅ 找到 {len(files)} 个文件:")
                for file in files[:5]:
                    print(f"   - {file.get('name')}")
                    print(f"     文件ID: {file.get('key')}")
                    print(f"     最后修改: {file.get('last_modified')}")
            else:
                print(f"⚠️  文件列表获取失败: {files_response.status_code}")
        
        print("\n" + "=" * 50)
        print("🎉 Figma API测试完成!")
        print("\n📋 下一步:")
        print("1. 在Figma中创建模板文件")
        print("2. 获取文件ID（从URL中复制）")
        print("3. 配置 config/config.yaml")
        print("4. 运行自动化测试")
        
        return True
        
    except requests.exceptions.Timeout:
        print("❌ 请求超时，请检查网络连接")
        return False
    except requests.exceptions.ConnectionError:
        print("❌ 连接错误，请检查网络")
        return False
    except Exception as e:
        print(f"❌ 测试过程中出错: {e}")
        return False

def create_sample_config():
    """创建示例配置文件"""
    config = {
        'figma': {
            'access_token': 'figd_VV2b7lrIFNS0KCPtds23Sdjpp3jxRj_IMaiYCvd_',
            'enabled': True,
            'templates': {
                'wechat_article': {
                    'file_key': 'YOUR_WECHAT_TEMPLATE_FILE_ID',  # 需要替换
                    'node_map': {
                        'title': 'NODE_ID_FOR_TITLE',
                        'content': 'NODE_ID_FOR_CONTENT',
                        'author': 'NODE_ID_FOR_AUTHOR',
                        'date': 'NODE_ID_FOR_DATE'
                    }
                },
                'xiaohongshu_note': {
                    'file_key': 'YOUR_XIAOHONGSHU_TEMPLATE_FILE_ID',
                    'node_map': {
                        'cover': 'NODE_ID_FOR_COVER',
                        'title': 'NODE_ID_FOR_TITLE',
                        'content': 'NODE_ID_FOR_CONTENT'
                    }
                }
            }
        }
    }
    
    print("\n📝 示例配置文件:")
    print("=" * 50)
    print(json.dumps(config, indent=2, ensure_ascii=False))
    
    print("\n💡 配置说明:")
    print("1. 将 YOUR_*_FILE_ID 替换为实际文件ID")
    print("2. 将 NODE_ID_FOR_* 替换为实际节点ID")
    print("3. 保存到 config/config.yaml 的 figma 部分")

def get_node_ids_guide():
    """获取节点ID的指南"""
    print("\n🔧 如何获取节点ID:")
    print("=" * 50)
    print("""
方法1: 通过Figma API获取
1. 获取文件信息:
   GET https://api.figma.com/v1/files/{FILE_KEY}
   
2. 查找节点ID:
   - 在返回的JSON中查找 'document' -> 'children'
   - 每个元素都有 'id' 字段

方法2: 通过Figma界面查看（简化版）
1. 在Figma中选中元素
2. 右侧面板查看属性
3. 或使用Figma插件获取ID

方法3: 使用我们的辅助脚本
运行: python scripts/design/figma_client.py --file {FILE_KEY}
    """)

if __name__ == "__main__":
    print("🤖 Figma API 连接测试工具")
    print("=" * 50)
    
    # 测试API连接
    if test_figma_api():
        # 创建示例配置
        create_sample_config()
        
        # 显示节点ID获取指南
        get_node_ids_guide()
        
        print("\n🚀 现在可以开始:")
        print("1. 在Figma中创建模板文件")
        print("2. 运行: python scripts/design/figma_client.py 测试连接")
        print("3. 配置自动化系统")
    else:
        print("\n🔧 需要修复:")
        print("1. 检查token是否正确")
        print("2. 检查网络连接")
        print("3. 确认Figma账户状态")
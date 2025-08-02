#!/usr/bin/env python3
"""
构建脚本：处理环境变量替换
将 manifest.json 和 config.js 中的占位符替换为实际值
"""

import os
import json
from pathlib import Path
from dotenv import load_dotenv

def build_manifest():
    """构建 manifest.json，替换环境变量"""
    
    # 加载环境变量
    load_dotenv()
    
    # 获取项目根目录
    project_root = Path(__file__).parent
    
    # 读取 manifest 模板
    template_path = project_root / "frontend" / "manifest.template.json"
    output_path = project_root / "frontend" / "manifest.json"
    
    if not template_path.exists():
        print(f"错误：找不到模板文件 {template_path}")
        return False
    
    try:
        with open(template_path, 'r', encoding='utf-8') as f:
            manifest = json.load(f)
        
        # 替换环境变量
        client_id = os.getenv('GOOGLE_CLIENT_ID')
        if not client_id:
            print("错误：未找到 GOOGLE_CLIENT_ID 环境变量")
            print("请确保 .env 文件存在并包含正确的配置")
            return False
        
        manifest['oauth2']['client_id'] = client_id
        
        # 写入最终文件
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(manifest, f, indent=2, ensure_ascii=False)
        
        print(f"✅ 成功生成 {output_path}")
        print(f"使用 Client ID: {client_id[:20]}...")
        return True
        
    except Exception as e:
        print(f"错误：生成 manifest.json 失败 - {e}")
        return False

def build_config():
    """构建 config.js，替换环境变量"""
    
    # 获取项目根目录
    project_root = Path(__file__).parent
    
    # 读取 config 模板
    template_path = project_root / "frontend" / "config.template.js"
    output_path = project_root / "frontend" / "config.js"
    
    if not template_path.exists():
        print(f"错误：找不到模板文件 {template_path}")
        return False
    
    try:
        with open(template_path, 'r', encoding='utf-8') as f:
            config_content = f.read()
        
        # 获取环境变量并映射到配置
        environment = os.getenv('ENVIRONMENT', 'local').lower()
        
        # 映射环境到配置值
        environment_mapping = {
            'local': 'LOCAL',
            'development': 'LOCAL',
            'prod': 'RAILWAY',
            'production': 'RAILWAY',
            'railway': 'RAILWAY'
        }
        
        target = environment_mapping.get(environment, 'LOCAL')
        
        # 替换占位符
        config_content = config_content.replace('${ENVIRONMENT_TARGET}', f'"{target}"')
        
        # 写入最终文件
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(config_content)
        
        print(f"✅ 成功生成 {output_path} (环境: {environment} -> {target})")
        return True
        
    except Exception as e:
        print(f"错误：生成 config.js 失败 - {e}")
        return False

def main():
    """主构建函数"""
    print("🔨 开始构建配置文件...")
    
    # 加载环境变量
    load_dotenv()
    
    success = True
    
    # 构建 manifest.json
    if not build_manifest():
        success = False
    
    # 构建 config.js
    if not build_config():
        success = False
    
    if success:
        print("🎉 所有配置文件构建完成！")
        
        # 显示当前配置摘要
        environment = os.getenv('ENVIRONMENT', 'local')
        client_id = os.getenv('GOOGLE_CLIENT_ID', '未设置')
        print(f"\n📋 当前配置摘要:")
        print(f"   环境: {environment}")
        print(f"   Google Client ID: {client_id[:20]}..." if len(client_id) > 20 else f"   Google Client ID: {client_id}")
    else:
        print("❌ 构建过程中出现错误")
        exit(1)

if __name__ == "__main__":
    main()

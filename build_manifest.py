#!/usr/bin/env python3
"""
构建脚本：处理环境变量替换
将 manifest.json 中的占位符替换为实际值
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
        print(f"错误：{e}")
        return False

if __name__ == "__main__":
    if build_manifest():
        print("构建完成！")
    else:
        print("构建失败！")
        exit(1)

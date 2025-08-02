import os
import json
import tempfile
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

def get_gmail_credentials_path():
    """
    根据环境返回Gmail凭据文件路径
    - 本地环境：使用GMAIL_MCP_CREDS_PATH指定的文件路径
    - Railway生产环境：从GMAIL_MCP_CREDS_JSON创建临时文件
    
    Returns:
        str: Gmail凭据文件的绝对路径
    """
    # ===== 详细的环境变量调试信息 =====
    print("=" * 80)
    print("🔧 [CREDENTIALS_MANAGER] 环境变量调试信息:")
    print(f"   📍 当前工作目录: {os.getcwd()}")
    print(f"   🐍 Python进程ID: {os.getpid()}")
    
    # 检查所有相关的环境变量
    print("🌍 核心环境变量:")
    print(f"   ENVIRONMENT: '{os.environ.get('ENVIRONMENT', 'NOT_SET')}'")
    print(f"   RAILWAY_ENVIRONMENT: '{os.environ.get('RAILWAY_ENVIRONMENT', 'NOT_SET')}'")
    print(f"   RAILWAY_PROJECT_ID: '{os.environ.get('RAILWAY_PROJECT_ID', 'NOT_SET')}'")
    print(f"   PORT: '{os.environ.get('PORT', 'NOT_SET')}'")
    
    print("🔑 Gmail凭据相关变量:")
    gmail_creds_path = os.environ.get('GMAIL_MCP_CREDS_PATH')
    gmail_creds_json = os.environ.get('GMAIL_MCP_CREDS_JSON')
    print(f"   GMAIL_MCP_CREDS_PATH: {'存在' if gmail_creds_path else '不存在'}")
    if gmail_creds_path:
        print(f"   └── 路径: {gmail_creds_path}")
        print(f"   └── 文件存在: {os.path.exists(gmail_creds_path) if gmail_creds_path else 'N/A'}")
    
    print(f"   GMAIL_MCP_CREDS_JSON: {'存在' if gmail_creds_json else '不存在'}")
    if gmail_creds_json:
        print(f"   └── 长度: {len(gmail_creds_json)} 字符")
        print(f"   └── 前50字符: {gmail_creds_json[:50]}...")
    
    # 显示所有包含关键字的环境变量
    print("📋 所有相关环境变量:")
    relevant_keys = ['GMAIL', 'CREDS', 'RAILWAY', 'ENVIRONMENT', 'SMITHERY', 'OPENAI']
    relevant_vars = {}
    for key, value in os.environ.items():
        if any(keyword in key.upper() for keyword in relevant_keys):
            # 对于敏感信息只显示前几个字符
            if 'SECRET' in key.upper() or 'KEY' in key.upper() or 'TOKEN' in key.upper():
                display_value = f"{value[:10]}..." if value else "NOT_SET"
            else:
                display_value = value
            relevant_vars[key] = display_value
    
    for key, value in sorted(relevant_vars.items()):
        print(f"   {key}: {value}")
    
    print("=" * 80)
    
    try:
        environment = os.environ.get('ENVIRONMENT', 'local')
        print(f"🎯 检测到的环境: '{environment}'")
        
        if environment == 'local':
            print("🏠 进入本地环境分支")
            # 本地开发环境：使用文件路径
            creds_path = os.environ.get('GMAIL_MCP_CREDS_PATH')
            if not creds_path:
                print("❌ 本地环境缺少 GMAIL_MCP_CREDS_PATH")
                raise ValueError("GMAIL_MCP_CREDS_PATH environment variable is not set")
            
            print(f"📂 检查本地凭据文件: {creds_path}")
            # 检查文件是否存在
            if not os.path.exists(creds_path):
                print(f"❌ 本地凭据文件不存在: {creds_path}")
                raise FileNotFoundError(f"Gmail credentials file not found: {creds_path}")
            
            print(f"✅ 本地凭据文件验证成功: {creds_path}")
            logger.info(f"Using local Gmail credentials file: {creds_path}")
            return creds_path
            
        else:
            print(f"🚀 进入生产环境分支 (环境值: '{environment}')")
            # 生产环境：从JSON环境变量创建临时文件
            creds_json = os.environ.get('GMAIL_MCP_CREDS_JSON')
            
            print(f"🔍 检查 GMAIL_MCP_CREDS_JSON: {'存在' if creds_json else '❌ 不存在'}")
            if creds_json:
                print(f"   JSON长度: {len(creds_json)} 字符")
                print(f"   JSON开头: {creds_json[:100]}...")
                try:
                    # 尝试解析JSON以验证格式
                    test_json = json.loads(creds_json)
                    print(f"   ✅ JSON格式验证成功，包含 {len(test_json)} 个顶级键")
                    if 'web' in test_json:
                        print(f"   ✅ 包含 'web' 配置节")
                    else:
                        print(f"   ⚠️ 缺少 'web' 配置节")
                except json.JSONDecodeError as e:
                    print(f"   ❌ JSON格式错误: {e}")
            
            if not creds_json:
                print("❌ 生产环境缺少 GMAIL_MCP_CREDS_JSON 环境变量")
                print("💡 请检查Railway Variables是否正确设置了此环境变量")
                raise ValueError("GMAIL_MCP_CREDS_JSON environment variable is not set for production")
            
            print("📝 创建临时凭据文件...")
            temp_path = _create_temp_credentials_file(creds_json)
            print(f"✅ 临时凭据文件创建成功: {temp_path}")
            print(f"✅ 临时凭据文件创建成功: {temp_path}")
            return temp_path
            
    except Exception as e:
        print(f"❌ [CREDENTIALS_MANAGER] 发生错误: {e}")
        print(f"   错误类型: {type(e).__name__}")
        print("=" * 80)
        logger.error(f"Failed to get Gmail credentials path: {e}")
        raise

def _create_temp_credentials_file(creds_json_str):
    """
    从JSON字符串创建临时凭据文件
    
    Args:
        creds_json_str: JSON格式的凭据字符串
        
    Returns:
        str: 临时文件的绝对路径
    """
    print("📝 [_create_temp_credentials_file] 开始创建临时文件...")
    try:
        print(f"   输入JSON长度: {len(creds_json_str)} 字符")
        print(f"   临时目录: {tempfile.gettempdir()}")
        
        # 解析JSON字符串
        print("   🔍 解析JSON字符串...")
        creds_data = json.loads(creds_json_str)
        print(f"   ✅ JSON解析成功，包含键: {list(creds_data.keys())}")
        
        # 创建临时文件
        print("   📄 创建临时文件...")
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as temp_file:
            json.dump(creds_data, temp_file, indent=2)
            temp_path = temp_file.name
        
        print(f"   ✅ 临时文件写入成功: {temp_path}")
        print(f"   📊 文件大小: {os.path.getsize(temp_path)} 字节")
        logger.info(f"Created temporary Gmail credentials file: {temp_path}")
        return temp_path
        
    except json.JSONDecodeError as e:
        print(f"   ❌ JSON解析失败: {e}")
        print(f"   🔍 问题JSON片段: {creds_json_str[:200]}...")
        raise ValueError(f"Invalid JSON in GMAIL_MCP_CREDS_JSON: {e}")
    except Exception as e:
        print(f"   ❌ 创建临时文件失败: {e}")
        print(f"   错误类型: {type(e).__name__}")
        raise RuntimeError(f"Failed to create temporary credentials file: {e}")

def cleanup_temp_credentials_file(file_path):
    """
    清理临时凭据文件（可选，用于资源清理）
    
    Args:
        file_path: 要删除的文件路径
    """
    try:
        if file_path and os.path.exists(file_path) and file_path.startswith(tempfile.gettempdir()):
            os.unlink(file_path)
            logger.info(f"Cleaned up temporary credentials file: {file_path}")
    except Exception as e:
        logger.warning(f"Failed to cleanup temporary file {file_path}: {e}")

def validate_credentials_file(file_path):
    """
    验证凭据文件格式是否正确
    
    Args:
        file_path: 凭据文件路径
        
    Returns:
        bool: 文件是否有效
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            creds_data = json.load(f)
        
        # 基本验证：检查是否包含必要的字段
        if 'web' in creds_data:
            web_config = creds_data['web']
            required_fields = ['client_id', 'client_secret', 'auth_uri', 'token_uri']
            missing_fields = [field for field in required_fields if field not in web_config]
            
            if missing_fields:
                logger.error(f"Missing required fields in credentials: {missing_fields}")
                return False
            
            logger.info("Gmail credentials file validation passed")
            return True
        else:
            logger.error("Invalid credentials format: missing 'web' section")
            return False
            
    except Exception as e:
        logger.error(f"Failed to validate credentials file: {e}")
        return False

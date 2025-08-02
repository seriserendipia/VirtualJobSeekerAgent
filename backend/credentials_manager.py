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
    try:
        environment = os.environ.get('ENVIRONMENT', 'local')
        
        if environment == 'local':
            # 本地开发环境：使用文件路径
            creds_path = os.environ.get('GMAIL_MCP_CREDS_PATH')
            if not creds_path:
                raise ValueError("GMAIL_MCP_CREDS_PATH environment variable is not set")
            
            # 检查文件是否存在
            if not os.path.exists(creds_path):
                raise FileNotFoundError(f"Gmail credentials file not found: {creds_path}")
            
            logger.info(f"Using local Gmail credentials file: {creds_path}")
            return creds_path
            
        else:
            # 生产环境：从JSON环境变量创建临时文件
            creds_json = os.environ.get('GMAIL_MCP_CREDS_JSON')
            if not creds_json:
                raise ValueError("GMAIL_MCP_CREDS_JSON environment variable is not set for production")
            
            return _create_temp_credentials_file(creds_json)
            
    except Exception as e:
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
    try:
        # 解析JSON字符串
        creds_data = json.loads(creds_json_str)
        
        # 创建临时文件
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as temp_file:
            json.dump(creds_data, temp_file, indent=2)
            temp_path = temp_file.name
        
        logger.info(f"Created temporary Gmail credentials file: {temp_path}")
        return temp_path
        
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in GMAIL_MCP_CREDS_JSON: {e}")
    except Exception as e:
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

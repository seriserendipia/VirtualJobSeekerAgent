import os
import json
import logging
import traceback
import sys

from flask import Flask, request, jsonify
from flask_cors import CORS

from mcp.types import TextContent

# ===== 应用程序启动时打印所有环境变量 =====
print("=" * 100)
print("🌍 [APPLICATION STARTUP] 完整环境变量列表:")
print(f"📍 应用启动时间: {__import__('datetime').datetime.now()}")
print(f"🐍 Python 进程ID: {os.getpid()}")
print(f"📂 当前工作目录: {os.getcwd()}")
print("=" * 100)

# 按分类显示环境变量
def print_env_vars():
    all_env_vars = dict(os.environ)
    
    # 分类显示
    categories = {
        "🚂 Railway相关": ['RAILWAY_', 'PORT'],
        "🔑 API密钥": ['API_KEY', 'SECRET', 'TOKEN'],
        "📧 Gmail凭据": ['GMAIL_', 'GOOGLE_'],
        "🎯 应用配置": ['ENVIRONMENT', 'DEBUG', 'HOST'],
        "🔧 其他重要": ['PATH', 'HOME', 'USER', 'PYTHONPATH']
    }
    
    for category, keywords in categories.items():
        print(f"\n{category}:")
        found_vars = {}
        for key, value in all_env_vars.items():
            if any(keyword in key.upper() for keyword in keywords):
                # 对敏感信息进行脱敏处理
                if any(sensitive in key.upper() for sensitive in ['SECRET', 'KEY', 'TOKEN', 'PASSWORD']):
                    if len(value) > 20:
                        display_value = f"{value[:10]}...{value[-5:]}"
                    else:
                        display_value = f"{value[:5]}..."
                else:
                    display_value = value
                found_vars[key] = display_value
        
        if found_vars:
            for key, value in sorted(found_vars.items()):
                print(f"   {key}: {value}")
        else:
            print(f"   (无相关变量)")
    
    # 显示所有环境变量的数量
    print(f"\n📊 环境变量统计:")
    print(f"   总数: {len(all_env_vars)} 个")
    print(f"   Railway相关: {len([k for k in all_env_vars.keys() if 'RAILWAY' in k.upper()])} 个")
    print(f"   API密钥相关: {len([k for k in all_env_vars.keys() if any(x in k.upper() for x in ['KEY', 'SECRET', 'TOKEN'])])} 个")
    
    # 关键检查项
    print(f"\n🔍 关键配置检查:")
    critical_vars = {
        'ENVIRONMENT': '应用环境',
        'PORT': 'HTTP端口',
        'RAILWAY_ENVIRONMENT': 'Railway环境',
        'OPENAI_API_KEY': 'OpenAI API密钥',
        'SMITHERY_API_KEY': 'Smithery API密钥',
        'GMAIL_MCP_CREDS_PATH': 'Gmail凭据路径(本地)',
        'GMAIL_MCP_CREDS_JSON': 'Gmail凭据JSON(生产)'
    }
    
    for var_name, description in critical_vars.items():
        value = os.environ.get(var_name)
        status = "✅ 存在" if value else "❌ 缺失"
        if value and any(sensitive in var_name.upper() for sensitive in ['SECRET', 'KEY', 'TOKEN']):
            length_info = f" (长度: {len(value)}字符)"
        else:
            length_info = f" (值: {value})" if value else ""
        print(f"   {var_name}: {status}{length_info} - {description}")

print_env_vars()
print("=" * 100)

print("🔄 开始导入模块...")
try:
    from generate_followup_email import generate_email
    print("✅ generate_followup_email 导入成功")
    
    from email_handling import send_email_via_aurite
    print("✅ email_handling 导入成功")
    
    from aurite_service import get_aurite
    print("✅ aurite_service 导入成功")
    
    from credentials_manager import get_gmail_credentials_path, validate_credentials_file
    print("✅ credentials_manager 导入成功")
    
    # 验证Gmail凭据配置
    try:
        creds_path = get_gmail_credentials_path()
        if validate_credentials_file(creds_path):
            print(f"✅ Gmail凭据验证成功: {creds_path}")
        else:
            print(f"⚠️ Gmail凭据验证失败: {creds_path}")
    except Exception as e:
        print(f"⚠️ Gmail凭据配置问题: {e}")
    
except Exception as e:
    print(f"❌ 模块导入失败: {e}")
    import traceback
    traceback.print_exc()

app = Flask(__name__)

@app.before_request
def log_all_requests():
    """在所有请求处理前记录详细信息"""
    print("=" * 60)
    print(f"🌐 [INCOMING REQUEST] {request.method} {request.path}")
    print(f"📍 Remote Address: {request.remote_addr}")
    print(f"🌍 Host: {request.host}")
    print(f"🔗 URL: {request.url}")
    print(f"📋 Headers:")
    for header, value in request.headers:
        print(f"   {header}: {value}")
    
    # 检查是否是 CORS 预检请求
    if request.method == 'OPTIONS':
        print("🔄 这是一个 CORS 预检请求")
    
    print("=" * 60)
    
    # 强制刷新输出
    sys.stdout.flush()

@app.after_request
def log_response(response):
    """记录响应信息"""
    print("=" * 60)
    print(f"📤 [RESPONSE] Status: {response.status_code}")
    print(f"📋 Response Headers:")
    for header, value in response.headers:
        print(f"   {header}: {value}")
    print("=" * 60)
    sys.stdout.flush()
    return response

# 环境配置函数
def get_environment_config():
    """
    根据环境变量检测和返回当前环境配置
    """
    # 检查环境变量
    environment = os.environ.get('ENVIRONMENT')
    
    # 如果没有设置ENVIRONMENT，进行自动检测
    if not environment:
        # 检测Railway环境
        if os.environ.get('RAILWAY_ENVIRONMENT') or os.environ.get('RAILWAY_PROJECT_ID'):
            environment = 'production'
        # 检测是否有非默认端口（云端特征）
        elif os.environ.get('PORT') and os.environ.get('PORT') != '5000':
            environment = 'production'
        else:
            environment = 'local'
    
    # 根据环境返回配置
    if environment == 'local':
        return {
            'environment': 'local',
            'host': '127.0.0.1',
            'port': int(os.environ.get('PORT', 5000)),
            'debug': True,
            'cors_origins': [
                "http://localhost:3000",
                "http://localhost:5000", 
                "http://127.0.0.1:5000",
                "chrome-extension://*",
            ]
        }
    else:  # production
        return {
            'environment': 'production',
            'host': '0.0.0.0',
            'port': int(os.environ.get('PORT', 5000)),
            'debug': False,
            'cors_origins': [
                "https://virtualjobseekeragent-production.up.railway.app",
                "chrome-extension://*",
            ]
        }

# 获取当前环境配置
config = get_environment_config()

# CORS配置 - 临时使用宽松配置进行调试
CORS(app, resources={
    r"/*": {
        "origins": ["*"],  # 临时允许所有来源进行调试
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type", "X-From-Extension", "Authorization"],
        "supports_credentials": False
    }
})


# Configure logging for Flask
logging.basicConfig(level=logging.INFO, format='[%(asctime)s] [Server] %(message)s')


@app.route('/health', methods=['GET'])
def health_check():
    """健康检查端点"""
    return jsonify({
        "status": "healthy", 
        "environment": config['environment'],
        "timestamp": "2025-08-01",
        "cors_origins": config['cors_origins'],
        "host": config['host'],
        "port": config['port']
    }), 200


@app.route('/health', methods=['OPTIONS'])
def handle_health_options():
    """处理 health 的 OPTIONS 预检请求"""
    print("🔄 处理 health 的 OPTIONS 预检请求")
    return '', 200


@app.route('/generate_email', methods=['OPTIONS'])
def handle_generate_email_options():
    """处理 generate_email 的 OPTIONS 预检请求"""
    print("🔄 处理 generate_email 的 OPTIONS 预检请求")
    return '', 200


@app.route('/generate_email', methods=['POST'])
async def handle_generate_email():
    """
    处理生成邮件的 POST 请求
    """
    logging.info(f'Received generate_email request from {request.remote_addr}')

    if request.headers.get('X-From-Extension') != 'true':
        logging.warning("Request missing 'X-From-Extension: true' header.")
        return jsonify({"error": "Forbidden"}), 403

    try:
        payload = request.get_json(force=True)
        if not payload:
            logging.error("Request body is empty or not valid JSON.")
            return jsonify({"error": "Invalid JSON in request body."}), 400

        job_description = payload.get('job_description')
        resume = payload.get('resume')
        user_prompt = payload.get('user_prompt')

        print(f"Received payload: {payload}")

        # TODO:用户自定义的邮件 prompt 
        # if not all([job_description, resume, user_prompt]):
        #     logging.error("Missing required fields in request payload.")
        #     return jsonify({"error": "Missing required fields in request payload."}), 400

        # 调用生成邮件的方法
        aurite = get_aurite()
        await aurite.initialize()
        generated_email = await generate_email(resume, job_description)

        return jsonify({
            "generated_email": generated_email
        }), 200

    except Exception as e:
        logging.error(f'Failed to process generate_email request: {e}', exc_info=True)
        return jsonify({"error": str(e)}), 500


def validate_request():
    """
    验证发邮件请求的基本格式和权限，并整合access_token到邮件数据中
    Returns: (is_valid, error_response, email_data_with_token)
    """
    # 验证扩展头
    if request.headers.get('X-From-Extension') != 'true':
        logging.warning("Request missing 'X-From-Extension: true' header.")
        return False, (jsonify({'error': 'Forbidden'}), 403), None
    
    # 验证邮件格式是否是JSON数据
    try:
        data = request.get_json(force=True)
        if not data:
            logging.error("Request body is empty or not valid JSON.")
            return False, (jsonify({'error': 'Invalid JSON in request body.'}), 400), None
    except Exception as e:
        logging.error(f"JSON parsing error: {e}")
        return False, (jsonify({'error': 'Invalid JSON in request body.'}), 400), None
    
    # 验证是否有用户邮箱的access_token
    access_token = data.get('access_token')
    if not access_token:
        logging.error("Missing required access_token in request.")
        return False, (jsonify({'error': 'Missing required access_token'}), 400), None
    
    # 验证邮件内容
    email_data = data.get('emailData', {})
    if not email_data or not email_data.get('subject') or not email_data.get('body'):
        logging.error(f"Invalid email data structure: {email_data}")
        return False, (jsonify({'error': 'Invalid email data. Please generate a proper email first.'}), 400), None
    
    # 创建包含access_token的完整邮件数据字典
    email_data_with_token = data.copy()
    # 确保access_token在邮件数据中（如果原来就有则保持，如果没有则添加）
    email_data_with_token['access_token'] = access_token
    
    return True, None, email_data_with_token

@app.route('/send-email', methods=['POST'])
async def handle_send_email():
    logging.info(f'Received send-email request from {request.remote_addr}')

    # 使用统一的验证函数，现在返回整合了access_token的邮件数据
    is_valid, error_response, email_data_with_token = validate_request()
    if not is_valid:
        return error_response
    
    logging.info(f'Parsed email data with token: {email_data_with_token}')
    # 安全地显示access_token前缀用于调试
    if 'access_token' in email_data_with_token:
        logging.info(f'Processing email with access_token: {email_data_with_token["access_token"][:20]}...')

    try:
        logging.info("Calling send_email_via_aurite...")
        success, mcp_response = await send_email_via_aurite(email_data_with_token)
        logging.info(f"Email sending result - Success: {success}, Response: {type(mcp_response)}")

        # Handle CallToolResult object for JSON serialization (this part remains in server.py)
        json_serializable_mcp_response = None
        # mcp_response might be a string (error) or CallToolResult (success/tool error)
        if hasattr(mcp_response, 'content') and hasattr(mcp_response.content, '__getitem__') and isinstance(mcp_response.content[0], TextContent):
            json_serializable_mcp_response = mcp_response.content[0].text
        elif hasattr(mcp_response, 'isError') and mcp_response.isError: # Check if it's an error result object
             json_serializable_mcp_response = str(mcp_response.content) # Convert error content to string
        else: # Fallback if it's not a CallToolResult or has unexpected content, or is already a string
            json_serializable_mcp_response = str(mcp_response)

        logging.info(f"Serialized response: {json_serializable_mcp_response}")

        if success:
            return jsonify({"success": True, "message": "Email sent successfully with OAuth", "mcp_response": json_serializable_mcp_response}), 200
        else:
            return jsonify({"success": False, "message": "Failed to send email via OAuth", "error": json_serializable_mcp_response}), 500

    except Exception as e:
        logging.error(f'Failed to process send-email request: {e}')
        logging.error(f'Exception traceback: {traceback.format_exc()}')
        return jsonify({"success": False, "message": "Internal Server Error", "error": str(e)}), 500

# send email from a JSON file for now, because we don't have the receiver's email, future will get it from frontend
@app.route('/send-email-from-file', methods=['POST']) 
async def send_email_from_file():
    logging.info(f'Received request to send email from file from {request.remote_addr}')
    
    # 使用统一的验证函数，现在返回整合了access_token的邮件数据
    is_valid, error_response, email_content_data_with_token = validate_request()
    if not is_valid:
        return error_response

    try:
        logging.info(f'Parsed email data with token: {email_content_data_with_token}')

        email_file_name = 'email_content.json'
        current_dir = os.path.dirname(os.path.abspath(__file__))
        file_path = os.path.join(current_dir, email_file_name)

        if not os.path.exists(file_path):
            logging.error(f"Email content file '{email_file_name}' not found at: {file_path}")
            return jsonify({"message": f"Error: '{email_file_name}' not found."}), 404

        with open(file_path, 'r', encoding='utf-8') as f:
            email_data_from_file = json.load(f)

        logging.info(f"Loaded email data from file: {email_data_from_file}， content from frontend: {email_content_data_with_token}")
        
        # 整合文件数据、前端数据和access_token
        if isinstance(email_data_from_file, dict):
            # 从文件获取基础邮件结构
            final_email_data = email_data_from_file.copy()
            # 用前端传来的邮件数据更新主题和正文
            if "emailData" in email_content_data_with_token:
                email_data = email_content_data_with_token["emailData"]
                final_email_data["subject"] = email_data.get("subject", "")
                final_email_data["body"] = email_data.get("body", "")
            # 确保包含access_token
            final_email_data["access_token"] = email_content_data_with_token["access_token"]
        else:
            final_email_data = email_content_data_with_token

        # 使用OAuth方式发送邮件
        if 'access_token' in final_email_data:
            logging.info(f'Processing file email with access_token: {final_email_data["access_token"][:20]}...')
        success, mcp_response = await send_email_via_aurite(final_email_data)

        # Handle CallToolResult object for JSON serialization (this part remains in server.py)
        json_serializable_mcp_response = None
        if hasattr(mcp_response, 'content') and hasattr(mcp_response.content, '__getitem__') and isinstance(mcp_response.content[0], TextContent):
            json_serializable_mcp_response = mcp_response.content[0].text
        elif hasattr(mcp_response, 'isError') and mcp_response.isError: # Check if it's an error result object
             json_serializable_mcp_response = str(mcp_response.content) # Convert error content to string
        else: # Fallback if it's not a CallToolResult or has unexpected content, or is already a string
            json_serializable_mcp_response = str(mcp_response)

        if success:
            return jsonify({"success": True, "message": "Email sent successfully from file data with OAuth", "mcp_response": json_serializable_mcp_response}), 200
        else:
            return jsonify({"success": False, "message": "Failed to send email from file data via OAuth", "error": json_serializable_mcp_response}), 500

    except json.JSONDecodeError as e:
        logging.error(f"Error decoding JSON from '{email_file_name}': {e}", exc_info=True)
        return jsonify({"success": False, "message": f"Error: Invalid JSON format in '{email_file_name}'."}), 400
    except Exception as e:
        logging.error(f"Error processing request to send email from file: {e}", exc_info=True)
        return jsonify({"success": False, "message": "Internal Server Error", "error": str(e)}), 500


@app.route('/', methods=['GET'])
def handle_root():
    logging.info(f'Received GET request to root from {request.remote_addr}')
    if request.headers.get('X-From-Extension') == 'true':
        return "Aloha from Python backend!", 200
    else:
        logging.warning("GET request missing 'X-From-Extension: true' header for root.")
        return "Forbidden", 403

if __name__ == '__main__':
    print("🔧 开始启动服务器...")
    print(f"Python 版本: {sys.version}")
    print(f"Flask 版本: {app.__class__.__module__}")
    print(f"当前工作目录: {os.getcwd()}")
    
    # 环境变量检查
    print("🌍 环境变量:")
    railway_vars = [k for k in os.environ.keys() if 'RAILWAY' in k]
    for var in railway_vars:
        print(f"   {var}: {os.environ.get(var)}")
    print(f"   PORT: {os.environ.get('PORT')}")
    print(f"   ENVIRONMENT: {os.environ.get('ENVIRONMENT')}")
    
    # 使用配置中的环境设置
    HOST = config['host']
    PORT = config['port']
    DEBUG = config['debug']
    
    print(f"🚀 服务器配置:")
    print(f"   Host: {HOST}")
    print(f"   Port: {PORT}")
    print(f"   Debug: {DEBUG}")
    print(f"   Environment: {config['environment']}")
    print(f"   CORS Origins: {config['cors_origins']}")
    
    if config['environment'] == 'production':
        print(f"🚀 生产环境服务器启动在: {HOST}:{PORT}")
        logging.info(f"Production environment detected, starting server on {HOST}:{PORT}")
    else:
        print(f"🏠 本地开发服务器启动在: http://{HOST}:{PORT}")
        logging.info(f"Local development environment, starting server on {HOST}:{PORT}")
    
    # 显示CORS配置用于调试
    print(f"📡 CORS允许的来源: {config['cors_origins']}")
    print(f"🌍 当前环境: {config['environment']}")
    
    print("⏳ 正在启动 Flask 应用...")
    sys.stdout.flush()
    
    try:
        app.run(host=HOST, port=PORT, debug=DEBUG)
    except Exception as e:
        logging.error(f"Failed to start server: {e}")
        print(f"❌ 服务器启动失败: {e}")
        import traceback
        traceback.print_exc()
        sys.stdout.flush()
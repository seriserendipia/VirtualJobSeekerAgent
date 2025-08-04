import os
import json
import logging
import traceback

from flask import Flask, request, jsonify
from flask_cors import CORS

from mcp.types import TextContent

from generate_followup_email import generate_followup_email
from email_handling import send_email_via_aurite

app = Flask(__name__)
CORS(app) # Enable CORS for all routes
# TODO: 修改 cors 只允许 Chrome 扩展和特定域名访问
# CORS(app, resources={r"/*": {
#     "origins": [
#         "http://localhost:3000", 
#         "https://your-frontend-domain.com",
#         "chrome-extension://*",
##         "chrome-extension://<your-extension-id>"  # 这里记得要配置扩展 id
#     ]
# }})


# Configure logging for Flask
logging.basicConfig(level=logging.INFO, format='[%(asctime)s] [Server] %(message)s')


@app.route('/generate_email', methods=['POST'])
def handle_generate_email():
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
        generated_email = generate_followup_email(resume, job_description)

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
    HOST = '127.0.0.1'
    PORT = 5000
    app.run(host=HOST, port=PORT, debug=True)
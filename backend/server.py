import os
import json
import logging
import traceback

from flask import Flask, request, jsonify
from flask_cors import CORS

from mcp.types import TextContent
from generate_followup_email import generate_email, modify_email, extract_company_name_from_jd, extract_job_title_from_jd, extract_email_from_jd
from web_search_agent import find_recruiter_email_via_web_search, setup_aurite_for_recruiter_search
from email_handling import send_email_via_google_api
from aurite_service import get_aurite

app = Flask(__name__)
CORS(app) # Enable CORS for all routes
# TODO: Modify CORS to allow only Chrome extension and specific domains
# CORS(app, resources={r"/*": {
#     "origins": [
#         "http://localhost:3000",
#         "https://your-frontend-domain.com",
#         "chrome-extension://*",
##         "chrome-extension://<your-extension-id>"  # Remember to configure extension ID here
#     ]
# }})


# Configure logging for Flask
logging.basicConfig(level=logging.INFO, format='[%(asctime)s] [Server] %(message)s')


@app.route('/generate_and_modify_email', methods=['POST'])
async def handle_generate_and_modify_email():
    """
    Handles email generation and modification requests.
    Initial requests typically contain resume and job_description.
    Subsequent requests will contain current_subject, current_body, and user_feedback.
    Outputs only the email subject and body.
    """
    logging.info(f'Received generate_and_modify_email request from {request.remote_addr}')

    if request.headers.get('X-From-Extension') != 'true':
        logging.warning("Request missing 'X-From-Extension: true' header.")
        return jsonify({"error": "Forbidden"}), 403

    try:
        payload = request.get_json(force=True)
        if not payload:
            logging.error("Request body is empty or not valid JSON.")
            return jsonify({"error": "Invalid JSON in request body."}), 400

        # Get and initialize Aurite instance for each request
        aurite = get_aurite()
        await aurite.initialize()

        current_subject = payload.get('current_subject')
        current_body = payload.get('current_body')
        user_feedback = payload.get('user_feedback')

        if current_subject and current_body and user_feedback:
            # This is an email modification request
            logging.info("Attempting to modify existing email.")
            revised_email = await modify_email(current_subject, current_body, user_feedback)
            return jsonify({
                "subject": revised_email.get("subject", ""),
                "body": revised_email.get("body", "")
            }), 200
        else:
            # This is an initial email generation request
            job_description = payload.get('job_description')
            resume = payload.get('resume')

            if not all([job_description, resume]):
                logging.error("Missing required fields (job_description, resume) for initial generation.")
                return jsonify({"error": "Missing required fields for initial email generation."}), 400

            logging.info("Attempting to generate initial email.")
            generation_result = await generate_email(resume, job_description)

            if generation_result["status"] == "email_generated":
                logging.info("Email generated successfully.")
                generated_email = generation_result["email"]
                return jsonify({
                    "subject": generated_email.get("subject", ""),
                    "body": generated_email.get("body", "")
                }), 200
            elif generation_result["status"] == "needs_web_search":
                logging.info("Recipient email not found in JD, web search is needed. Returning partial email for now.")
                # If web search is needed, we still return the generated email (if any)
                # and let the frontend decide to call /find_recruiter_email
                generated_email = generation_result.get("email", {"subject": "", "body": ""})
                return jsonify({
                    "subject": generated_email.get("subject", ""),
                    "body": generated_email.get("body", ""),
                    "message": "Recipient email not found in JD. Please call /find_recruiter_email to search for contact information."
                }), 200 # Return 200 even if web search is needed, as email generation was successful to some extent
            else:
                logging.error(f"Unexpected status from generate_email: {generation_result['status']}")
                return jsonify({"error": "An unexpected error occurred during email generation."}), 500

    except Exception as e:
        logging.error(f'Failed to process email generation/modification request: {e}', exc_info=True)
        return jsonify({"error": str(e)}), 500

@app.route('/find_recruiter_email', methods=['POST'])
async def handle_find_recruiter_email():
    """
    Handles requests to find recruiter email via web search.
    Outputs success/fail status and either the found email or relevant URLs.
    """
    logging.info(f'Received find_recruiter_email request from {request.remote_addr}')

    if request.headers.get('X-From-Extension') != 'true':
        logging.warning("Request missing 'X-From-Extension: true' header.")
        return jsonify({"error": "Forbidden"}), 403

    try:
        payload = request.get_json(force=True)
        if not payload:
            logging.error("Request body is empty or not valid JSON.")
            # Changed to "status" and "result" for error cases as well for consistency
            return jsonify({"status": "Fail", "result": "Invalid JSON in request body."}), 400

        job_description = payload.get('job_description')
        company_name = payload.get('company_name') # These variables will be passed from the frontend.
        job_title = payload.get('job_title')     # They are kept as is.

        if not job_description and not (company_name and job_title):
            logging.error("Missing required fields: either 'job_description' or both 'company_name' and 'job_title' are needed for web search.")
            # Changed to "status" and "result"
            return jsonify({"status": "Fail", "result": "Missing required input for search (job_description or company_name/job_title)."}), 400

        # --- NEW LOGIC: Prioritize extracting email from job_description ---
        found_email_in_jd = None
        if job_description:
            found_email_in_jd = extract_email_from_jd(job_description)
            if found_email_in_jd:
                logging.info(f"Found email in job description: {found_email_in_jd}. Skipping web search.")
                return jsonify({
                    "status": "Success",
                    "result": found_email_in_jd # Directly return the email as the result
                }), 200
        # --- END NEW LOGIC ---

        # If only job_description is provided (and no email was found in it), try to extract company and job title from it
        if job_description and not (company_name and job_title):
            company_name = extract_company_name_from_jd(job_description)
            job_title = extract_job_title_from_jd(job_description)
            if not company_name:
                logging.warning("Could not extract company name from JD for web search.")
                # Changed to "status" and "result"
                return jsonify({"status": "Fail", "result": "Could not extract company name from job description for web search."}), 400

        # Get and initialize Aurite instance for each request
        aurite = get_aurite()
        await aurite.initialize()
        await setup_aurite_for_recruiter_search() # Ensure the web search agent is set up

        logging.info(f"Initiating web search for company: {company_name}, job: {job_title}")
        web_search_results = await find_recruiter_email_via_web_search(company_name, job_title)

        found_email_from_web = web_search_results.get("found_email")
        relevant_urls_from_web = web_search_results.get("relevant_urls", [])

        if found_email_from_web:
            return jsonify({
                "status": "Success",
                "result": found_email_from_web # Return the found email
            }), 200
        else:
            return jsonify({
                "status": "Fail",
                "result": relevant_urls_from_web # Return relevant URLs if no email found
            }), 200

    except Exception as e:
        logging.error(f'Failed to process recruiter email search request: {e}', exc_info=True)
        # Changed to "status" and "result"
        return jsonify({"status": "Fail", "result": str(e)}), 500
    
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
        success, mcp_response = await send_email_via_google_api(email_data_with_token)
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
        success, mcp_response = await send_email_via_google_api(final_email_data)

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
    # 移除这里对 aurite_instance.initialize() 的全局调用
    # asyncio.run(aurite_instance.initialize())
    # asyncio.run(setup_aurite_for_recruiter_search()) # 如果存在的话，也移除
    app.run(host=HOST, port=PORT, debug=True)

import os
import json
import logging
import traceback
import re

from flask import Flask, request, jsonify
from flask_cors import CORS

from mcp.types import TextContent
from generate_followup_email import generate_email, modify_email
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

        # Get all fields, frontend always sends all fields
        current_subject = payload.get('current_subject')
        current_body = payload.get('current_body')
        user_prompt = payload.get('user_prompt')  # Changed to user_prompt
        job_description = payload.get('job_description')
        resume = payload.get('resume')

        logging.info(f"[DEBUG] Payload analysis:")
        logging.info(f"  current_subject: '{current_subject}' (length: {len(current_subject) if current_subject else 0})")
        logging.info(f"  current_body: '{current_body[:100] if current_body else 'None'}...' (length: {len(current_body) if current_body else 0})")
        logging.info(f"  user_prompt: '{user_prompt}' (length: {len(user_prompt) if user_prompt else 0})")
        logging.info(f"  job_description: length {len(job_description) if job_description else 0}")
        logging.info(f"  resume: length {len(resume) if resume else 0}")

        # Check if it's a modification request (all three fields are not empty)
        if current_subject and current_body and user_prompt:
            # This is an email modification request
            logging.info("Attempting to modify existing email.")
            revised_email = await modify_email(resume, job_description, current_subject, current_body, user_prompt)
            
            logging.info(f"[DEBUG] modify_email result: {revised_email}")
            
            # Check modify_email return format
            if isinstance(revised_email, dict) and revised_email.get("status") == "success":
                # Extract email content from nested data structure
                email_data = revised_email.get("data", {}).get("email", {})
                logging.info(f"[DEBUG] Extracted email data: {email_data}")
                
                # Unified return format, including message field
                return jsonify({
                    "subject": email_data.get("subject", ""),
                    "body": email_data.get("body", ""),
                    "message": revised_email.get("message", "")
                }), 200
            elif isinstance(revised_email, dict) and revised_email.get("status") == "fail":
                error_message = revised_email.get("message", "Unknown error occurred")
                logging.error(f"Error from modify_email: {error_message}")
                return jsonify({"error": error_message}), 500
            else:
                logging.error(f"Unexpected output from modify_email: {revised_email}")
                return jsonify({"error": "An unexpected error occurred during email modification."}), 500
        else:
            # This is an initial email generation request
            if not all([job_description, resume]):
                logging.error("Missing required fields (job_description, resume) for initial generation.")
                return jsonify({"error": "Missing required fields for initial email generation."}), 400

            logging.info("Attempting to generate initial email.")
            generation_result = await generate_email(resume, job_description)

            # Use status field for judgment
            if isinstance(generation_result, dict) and generation_result.get("status") == "success":
                # Extract email content from nested data structure
                email_data = generation_result.get("data", {}).get("email", {})
                logging.info("Email generated successfully.")
                
                # Unified return format, including message field
                return jsonify({
                    "subject": email_data.get("subject", ""),
                    "body": email_data.get("body", ""),
                    "message": generation_result.get("message", "")  # Return message even on success
                }), 200
            elif isinstance(generation_result, dict) and generation_result.get("status") == "fail":
                error_message = generation_result.get("message", "Unknown error occurred")
                logging.error(f"Error from generate_email: {error_message}")
                return jsonify({"error": error_message}), 500
            else:
                logging.error(f"Unexpected output from generate_email: {generation_result}")
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
            # Simple email regex extraction
            email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
            email_matches = re.findall(email_pattern, job_description)
            if email_matches:
                found_email_in_jd = email_matches[0]  # Take the first found email
                logging.info(f"Found email in job description: {found_email_in_jd}. Skipping web search.")
                return jsonify({
                    "status": "Success",
                    "result": found_email_in_jd # Directly return the email as the result
                }), 200
        # --- END NEW LOGIC ---

        # If only job_description is provided (and no email was found in it), try to extract company and job title from it
        if job_description and not (company_name and job_title):
            logging.warning("Company name and job title not provided, and automatic extraction from JD is not implemented.")
            return jsonify({"status": "Fail", "result": "Company name and job title are required when not provided in the request."}), 400

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
             # TODO: Frontend needs special handling for this return result!
            # When status="Fail", result could be:
            # 1. String (error message)
            # 2. Array (URL object list, format: [{"url": "...", "title": "..."}])
            # Frontend must check Array.isArray(data.result) to distinguish types
            # If used directly as string, it will display "[object Object],[object Object]"
            # Recommended frontend code:
            # if (Array.isArray(data.result)) {
            #     // Handle URL array, create clickable links
            #     data.result.forEach(item => console.log(item.title, item.url));
            # } else {
            #     // Handle error message string
            #     console.error(data.result);
            # }
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
    Validate basic format and permissions for email sending request, validate flattened email data structure
    Frontend sends format: {subject: "...", body: "...", to: "...", access_token: "..."}
    Returns: (is_valid, error_response, email_data_with_token)
    """
    logging.info("[validate_request] Starting email request validation")
    
    # Validate extension header
    if request.headers.get('X-From-Extension') != 'true':
        logging.warning("[validate_request] Request missing 'X-From-Extension: true' header.")
        return False, (jsonify({'error': 'Forbidden'}), 403), None
    
    logging.info("[validate_request] Extension header validation passed")
    
    # Validate if email format is JSON data
    try:
        data = request.get_json(force=True)
        if not data:
            logging.error("[validate_request] Request body is empty or not valid JSON.")
            return False, (jsonify({'error': 'Invalid JSON in request body.'}), 400), None
        
        logging.info(f"[validate_request] Received data structure: {data}")
        logging.info(f"[validate_request] Data keys: {list(data.keys())}")
        
    except Exception as e:
        logging.error(f"[validate_request] JSON parsing error: {e}")
        return False, (jsonify({'error': 'Invalid JSON in request body.'}), 400), None
    

    access_token = data.get('access_token')
    if not access_token:
        logging.error("[validate_request] Missing required access_token in request.")
        return False, (jsonify({'error': 'Missing required access_token'}), 400), None
    
    logging.info(f"[validate_request] Found access_token: {access_token[:20]}...")
    logging.debug(f"[validate_request] Full access_token: {access_token}")
    subject = data.get('subject')
    body = data.get('body')
    to = data.get('to')
    
    logging.info(f"[validate_request] Email fields validation:")
    logging.info(f"  - subject: '{subject}' (length: {len(subject) if subject else 0})")
    logging.info(f"  - body: '{body[:100] if body else 'None'}...' (length: {len(body) if body else 0})")
    logging.info(f"  - to: '{to}'")
    
    # 检查必填字段
    missing_fields = []
    if not subject:
        missing_fields.append('subject')
    if not body:
        missing_fields.append('body')
    if not to:
        missing_fields.append('to')
    
    if missing_fields:
        logging.error(f"[validate_request] Missing required fields: {missing_fields}")
        return False, (jsonify({'error': f"Missing required fields: {', '.join(missing_fields)}"}), 400), None
    
    
    email_data_with_token = {
        'subject': subject,
        'body': body,
        'to': to,
        'access_token': access_token
    }
    
    logging.info(f"[validate_request] Validation successful, returning email data")
    logging.info(f"[validate_request] Final email data structure: subject='{subject}', body_length={len(body)}, to='{to}', has_token={bool(access_token)}")
    
    return True, None, email_data_with_token

@app.route('/send-email', methods=['POST'])
async def handle_send_email():
    logging.info(f'Received send-email request from {request.remote_addr}')

    is_valid, error_response, email_data_with_token = validate_request()
    if not is_valid:
        return error_response
    
    logging.info(f'Parsed email data with token: {email_data_with_token}')

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


@app.route('/', methods=['GET'])
def handle_root():
    logging.info(f'Received GET request to root from {request.remote_addr}')
    if request.headers.get('X-From-Extension') == 'true':
        return "Aloha from Python backend!", 200
    else:
        logging.warning("GET request missing 'X-From-Extension: true' header for root.")
        return "Forbidden", 403

if __name__ == '__main__':
    HOST = '0.0.0.0'
    PORT = 5000
    app.run(host=HOST, port=PORT, debug=True)

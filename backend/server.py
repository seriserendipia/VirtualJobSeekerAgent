import os
import datetime
import json
import asyncio
from flask import Flask, request, jsonify, send_from_directory, abort, make_response
from flask_cors import CORS 
import logging
from mcp.types import CallToolResult, TextContent 



from email_handling import send_email_via_mcp 

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

SMITHERY_API_KEY = "334a9cb0-9b76-4fe0-89e3-e206bb32fa93"
# TODO: 这个密钥暴露了，要删掉

# Gmail AutoAuth MCP Server 
MCP_SERVER_COMMAND_LIST = ["npx", "@smithery/cli@latest", "run", "@gongrzhe/server-gmail-autoauth-mcp"]

# Configure logging for Flask
logging.basicConfig(level=logging.INFO, format='[%(asctime)s] [Server] %(message)s')




@app.route('/send-email', methods=['POST'])
async def handle_send_email():
    logging.info(f'Received send-email request from {request.remote_addr}')

    if request.headers.get('X-From-Extension') != 'true':
        logging.warning("Request missing 'X-From-Extension: true' header.")
        return "Forbidden", 403

    try:
        email_data = request.get_json(force=True)
        if not email_data:
            logging.error("Request body is empty or not valid JSON.")
            return "Invalid JSON in request body.", 400
        
        logging.info(f'Parsed email data: {email_data}')

        # Call the imported function, passing necessary parameters
        success, mcp_response = await send_email_via_mcp(
            email_data, 
            SMITHERY_API_KEY, 
            MCP_SERVER_COMMAND_LIST
        )

        # Handle CallToolResult object for JSON serialization (this part remains in server.py)
        json_serializable_mcp_response = None
        # mcp_response might be a string (error) or CallToolResult (success/tool error)
        if hasattr(mcp_response, 'content') and hasattr(mcp_response.content, '__getitem__') and isinstance(mcp_response.content[0], TextContent):
            json_serializable_mcp_response = mcp_response.content[0].text
        elif hasattr(mcp_response, 'isError') and mcp_response.isError: # Check if it's an error result object
             json_serializable_mcp_response = str(mcp_response.content) # Convert error content to string
        else: # Fallback if it's not a CallToolResult or has unexpected content, or is already a string
            json_serializable_mcp_response = str(mcp_response)


        if success:
            return jsonify({"message": "Email sent successfully", "mcp_response": json_serializable_mcp_response}), 200
        else:
            return jsonify({"message": "Failed to send email via MCP", "error": json_serializable_mcp_response}), 500

    except Exception as e:
        logging.error(f'Failed to process send-email request: {e}', exc_info=True)
        return jsonify({"message": "Internal Server Error", "error": str(e)}), 500
        

# send email from a JSON file for now, future will be from frontend? 
@app.route('/send-email-from-file', methods=['GET']) 
async def send_email_from_file():
    logging.info(f'Received request to send email from file from {request.remote_addr}')
    
    email_file_name = 'email_content.json'
    current_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(current_dir, email_file_name)

    if not os.path.exists(file_path):
        logging.error(f"Email content file '{email_file_name}' not found at: {file_path}")
        return jsonify({"message": f"Error: '{email_file_name}' not found."}), 404

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            email_data_from_file = json.load(f)
        
        logging.info(f"Loaded email data from file: {email_data_from_file}")

        # Call the imported function, passing necessary parameters
        success, mcp_response = await send_email_via_mcp(
            email_data_from_file, 
            SMITHERY_API_KEY, 
            MCP_SERVER_COMMAND_LIST
        )

        # Handle CallToolResult object for JSON serialization (this part remains in server.py)
        json_serializable_mcp_response = None
        if hasattr(mcp_response, 'content') and hasattr(mcp_response.content, '__getitem__') and isinstance(mcp_response.content[0], TextContent):
            json_serializable_mcp_response = mcp_response.content[0].text
        elif hasattr(mcp_response, 'isError') and mcp_response.isError: # Check if it's an error result object
             json_serializable_mcp_response = str(mcp_response.content) # Convert error content to string
        else: # Fallback if it's not a CallToolResult or has unexpected content, or is already a string
            json_serializable_mcp_response = str(mcp_response)

        if success:
            return jsonify({"message": "Email sent successfully from file data", "mcp_response": json_serializable_mcp_response}), 200
        else:
            return jsonify({"message": "Failed to send email from file data", "error": json_serializable_mcp_response}), 500

    except json.JSONDecodeError as e:
        logging.error(f"Error decoding JSON from '{email_file_name}': {e}", exc_info=True)
        return jsonify({"message": f"Error: Invalid JSON format in '{email_file_name}'."}), 400
    except Exception as e:
        logging.error(f"Error processing request to send email from file: {e}", exc_info=True)
        return jsonify({"message": "Internal Server Error", "error": str(e)}), 500


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
import os
import asyncio
import logging
from contextlib import AsyncExitStack


# # ######用MCP发送邮件########

# # Imports from the mcp library
# from mcp import ClientSession, StdioServerParameters
# from mcp.client.stdio import stdio_client
# from mcp.types import CallToolResult, TextContent 


# async def send_email_via_mcp(email_data: dict, api_key: str, mcp_command_list: list):
#     """
#     Asynchronously sends an email by interacting with the MCP server
#     using the mcp.ClientSession.
    
#     Args:
#         email_data (dict): Dictionary containing 'to', 'subject', 'body' for the email.
#         api_key (str): The API key for Smithery.
#         mcp_command_list (list): The command list to start the MCP server (e.g., ["npx", "@smithery/cli@latest", ...]).
    
#     Returns:
#         tuple: A tuple (success_boolean, result_or_error_message).
#     """
#     logging.info(f"[EmailService] Attempting to send email via MCP client: {email_data}")
#     try:
#         if 'to' in email_data and isinstance(email_data['to'], str):
#             email_data['to'] = [email_data['to']]
#         elif 'to' in email_data and not isinstance(email_data['to'], list):
#             email_data['to'] = [str(email_data['to'])]

#         server_params = StdioServerParameters(
#             command=mcp_command_list[0],
#             args=mcp_command_list[1:],
#             env=os.environ.copy() # Pass current environment variables
#         )

#         async with AsyncExitStack() as exit_stack:
#             stdio_transport = await exit_stack.enter_async_context(stdio_client(server_params))
#             stdio_read_stream, stdio_write_stream = stdio_transport
            
#             client_session = await exit_stack.enter_async_context(ClientSession(stdio_read_stream, stdio_write_stream))

#             logging.info("[EmailService] MCP client session established. Calling 'send_email' tool...")
            
#             result = await client_session.call_tool("send_email", email_data)
            
#             logging.info(f"[EmailService] Email sent successfully via MCP. Result: {result}")
#             return True, result
#     except Exception as e:
#         logging.error(f"[EmailService] Failed to send email via MCP: {e}", exc_info=True)
#         return False, str(e)
    

# ######用aurite发送邮件########

from aurite import Aurite, AgentConfig
from getpass import getpass
from pathlib import Path

# 配置日志记录
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] [AuriteEmailAgent] %(message)s'
)
logger = logging.getLogger(__name__)
async def initialize_aurite_environment():
    """初始化环境变量和Aurite"""
    try:
        # # 尝试从Colab获取环境变量（如果在Colab中运行）
        # try:
        #     from google.colab import userdata  # type: ignore
        #     os.environ['OPENAI_API_KEY'] = userdata.get('OPENAI_API_KEY')
        #     os.environ["SMITHERY_API_KEY"] = userdata.get('SMITHERY_API_KEY')

        # except ImportError:
        #     # 如果不在Colab中运行，则使用dotenv加载环境变量
        #     from dotenv import load_dotenv
        #     load_dotenv()
    
        # 初始化Aurite实例
        aurite = Aurite()
        await aurite.initialize()
        
        logger.info("Environment initialized successfully")
        return aurite
        
    except Exception as e:
        logger.error(f"Failed to initialize environment: {e}", exc_info=True)
        raise



# async def register_gmail_server(aurite):
#     """注册gongrzhe 的 单用户 Gmail MCP服务器"""
#     try:
#         # 创建并注册Gmail MCP服务器配置
#         gmail_config = {
#             "name": "gmail_server",
#             "command": "npx",
#             "args": [
#                 "-y",
#                 "@smithery/cli@latest",
#                 "run",
#                 "@gongrzhe/server-gmail-autoauth-mcp",
#                 "--key",
#                 os.getenv("SMITHERY_API_KEY", "default_key")
#             ],
#             "capabilities": ["tools"],
#             "timeout": 20.0,
#         }
        
#         # 创建ClientConfig对象
#         from aurite import ClientConfig
#         client_config = ClientConfig(**gmail_config)
        
#         # 注册客户端
#         await aurite.register_client(client_config)
#         logger.info("Successfully registered Gmail MCP server")
        
#         return client_config.name
        
#     except Exception as e:
#         logger.error(f"Failed to register Gmail server: {e}", exc_info=True)
#         return None


async def register_gmail_server_with_token(aurite):
    """注册 Multi-User Gmail MCP服务器 - 使用本地的gmail-mcp-server"""
    try:
        # 获取当前脚本的绝对路径
        current_dir = os.path.dirname(os.path.abspath(__file__))
        mcp_server_path = os.path.join(current_dir, "..", "multi-user_gmail-mcp-server", "gmail_mcp_server.py")
        mcp_server_path = os.path.abspath(mcp_server_path)
        
        # 创建并注册Gmail MCP服务器配置
        gmail_config = {
            "name": "gmail_server_with_token",
            "command": "python",
            "args": [
                mcp_server_path,
                "--creds-file-path",
                os.getenv("GMAIL_MCP_CREDS_PATH", "")  # 从.env读取路径
            ],
            "capabilities": ["tools"],
            "timeout": 30.0,  # 增加超时时间
        }
        
        # 创建ClientConfig对象
        from aurite import ClientConfig
        client_config = ClientConfig(**gmail_config)
        
        # 注册客户端
        await aurite.register_client(client_config)
        logger.info(f"Successfully registered Gmail MCP server with token support at: {mcp_server_path}")
        
        return client_config.name
        
    except Exception as e:
        logger.error(f"Failed to register Gmail server with token: {e}", exc_info=True)
        return None


async def register_email_sender_agent(aurite, mcp_server_name):
    """定义和注册使用Gmail服务器的代理"""
    try:
        # 创建代理配置
        email_agent_config = AgentConfig(
            name="Email Sender Agent",
            system_prompt="""You are an email sending agent that uses the Gmail MCP server to send emails.

                            When given email data, you MUST:
                            1. Parse the email data from the user message
                            2. IMMEDIATELY call the send-email tool (not just return JSON)
                            3. Use these exact parameter mappings:
                               - access_token: use the provided access_token
                               - recipient_id: use the 'to' field from email data
                               - subject: use the 'subject' field from email data  
                               - message: use the 'body' field from email data

                            Do NOT just return formatted JSON. You MUST actually call the send-email tool to send the email.
                            
                            Always call the tool immediately after receiving the email data."""
        )
        
        # 添加MCP服务器支持
        email_agent_config.mcp_servers = [mcp_server_name]
        
        # 注册代理
        await aurite.register_agent(email_agent_config)
        logger.info(f"Successfully registered agent: {email_agent_config.name}")
        
        return email_agent_config.name
        
    except Exception as e:
        logger.error(f"Failed to register email agent: {e}", exc_info=True)
        return None


async def call_email_sender_agent_with_email_data(aurite, agent_name, email_data):
    """
    使用Aurite发送邮件
    
    Args:
        aurite: Aurite实例
        agent_name: 代理名称
        email_data: 邮件数据字典，包含to、subject、body、access_token等字段
        
    Returns:
        tuple: (success_boolean, result_or_error_message)
    """
    logger.info(f"Attempting to send email: {email_data}")
    
    try:
        # 格式化邮件数据为字符串，以便代理能够解析
        formatted_message = f"""Please send an email with the following details:


                                Use the send-email tool with:
                                - access_token: {email_data['access_token']}
                                - recipient_id: {email_data['to']}
                                - subject: {email_data['subject']}
                                - message: {email_data['body']}"""
        
        # 运行代理发送邮件
        result = await aurite.run_agent(
            agent_name=agent_name,
            user_message=formatted_message
        )
        
        logger.info(f"Email sent successfully. Result: {result}")
        return True, result
    except Exception as e:
        logger.error(f"Failed to send email: {e}", exc_info=True)
        return False, str(e)



async def send_email_via_aurite(email_data=None):
    """
    主函数 - 使用Aurite通过本地多用户MCP服务器发送邮件
    
    Args:
        email_data: 邮件数据字典，应包含:
            - to: 收件人邮箱
            - subject: 邮件主题  
            - body: 邮件内容
            - access_token: Google OAuth 2.0 访问令牌 (必需)
    """
    logger.info(f"[EmailService] Attempting to send email via Aurite: {email_data}")

    try:
        # 验证email_data格式
        if not email_data:
            return False, "email_data is required"
        
        if not isinstance(email_data, dict):
            return False, "email_data must be a dictionary"
            
        # 验证必需字段
        required_fields = ['to', 'subject', 'body', 'access_token']
        missing_fields = [field for field in required_fields if not email_data.get(field)]
        if missing_fields:
            return False, f"Missing required fields: {', '.join(missing_fields)}"

        # 1. 初始化环境和Aurite
        aurite = await initialize_aurite_environment()
        
        # 2. 注册Gmail服务器
        mcp_server_name = await register_gmail_server_with_token(aurite)
        if not mcp_server_name:
            error_msg = "Failed to register Gmail server"
            logger.error(error_msg)
            return False, error_msg
        logger.info(f"Gmail MCP server registered as: {mcp_server_name}")
            
        # 3. 注册邮件代理
        agent_name = await register_email_sender_agent(aurite, mcp_server_name)
        if not agent_name:
            error_msg = "Failed to register email agent"
            logger.error(error_msg)
            return False, error_msg
        logger.info(f"Email agent registered as: {agent_name}")
            
        # 4. 发送邮件
        result = await call_email_sender_agent_with_email_data(aurite, agent_name, email_data)
        logger.info(f"Email sending result: {result}")
        return result

    except Exception as e:
        error_msg = f"Critical error occurred: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return False, str(e)


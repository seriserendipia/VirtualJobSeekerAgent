import os
import asyncio
import logging
from contextlib import AsyncExitStack

# Imports from the mcp library
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.types import CallToolResult, TextContent 


async def send_email_via_mcp(email_data: dict, api_key: str, mcp_command_list: list):
    """
    Asynchronously sends an email by interacting with the MCP server
    using the mcp.ClientSession.
    
    Args:
        email_data (dict): Dictionary containing 'to', 'subject', 'body' for the email.
        api_key (str): The API key for Smithery.
        mcp_command_list (list): The command list to start the MCP server (e.g., ["npx", "@smithery/cli@latest", ...]).
    
    Returns:
        tuple: A tuple (success_boolean, result_or_error_message).
    """
    logging.info(f"[EmailService] Attempting to send email via MCP client: {email_data}")
    try:
        if 'to' in email_data and isinstance(email_data['to'], str):
            email_data['to'] = [email_data['to']]
        elif 'to' in email_data and not isinstance(email_data['to'], list):
            email_data['to'] = [str(email_data['to'])]

        server_params = StdioServerParameters(
            command=mcp_command_list[0],
            args=mcp_command_list[1:],
            env=os.environ.copy() # Pass current environment variables
        )

        async with AsyncExitStack() as exit_stack:
            stdio_transport = await exit_stack.enter_async_context(stdio_client(server_params))
            stdio_read_stream, stdio_write_stream = stdio_transport
            
            client_session = await exit_stack.enter_async_context(ClientSession(stdio_read_stream, stdio_write_stream))

            logging.info("[EmailService] MCP client session established. Calling 'send_email' tool...")
            
            result = await client_session.call_tool("send_email", email_data)
            
            logging.info(f"[EmailService] Email sent successfully via MCP. Result: {result}")
            return True, result
    except Exception as e:
        logging.error(f"[EmailService] Failed to send email via MCP: {e}", exc_info=True)
        return False, str(e)
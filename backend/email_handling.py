import os
import logging
import base64
import asyncio
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# 配置日志记录
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] [EmailService] %(message)s'
)
logger = logging.getLogger(__name__)


def create_gmail_service(access_token):
    """
    使用访问令牌创建Gmail API服务对象
    
    Args:
        access_token: Google OAuth 2.0 访问令牌
        
    Returns:
        gmail service对象
    """
    try:
        # 创建凭据对象
        creds = Credentials(token=access_token)
        
        # 构建Gmail服务
        service = build('gmail', 'v1', credentials=creds)
        logger.info("Gmail service created successfully")
        return service
        
    except Exception as e:
        logger.error(f"Failed to create Gmail service: {e}")
        raise


def create_message(to, subject, body):
    """
    创建邮件消息
    
    Args:
        to: 收件人邮箱
        subject: 邮件主题
        body: 邮件内容（纯文本）
        
    Returns:
        base64编码的邮件消息
    """
    try:
        # 构建原始邮件字符串
        message = f"To: {to}\r\n"
        message += f"Subject: {subject}\r\n"
        message += f"Content-Type: text/plain; charset=utf-8\r\n"
        message += f"\r\n{body}"
        
        # Base64编码
        raw_message = base64.urlsafe_b64encode(message.encode('utf-8')).decode('utf-8')
        
        return {'raw': raw_message}
        
    except Exception as e:
        logger.error(f"Failed to create message: {e}")
        raise


def send_message(service, message):
    """
    发送邮件消息
    
    Args:
        service: Gmail API服务对象
        message: 邮件消息字典
        
    Returns:
        发送结果
    """
    try:
        # 发送邮件
        result = service.users().messages().send(userId='me', body=message).execute()
        logger.info(f"Email sent successfully. Message ID: {result.get('id')}")
        return result
        
    except HttpError as error:
        logger.error(f"Gmail API error: {error}")
        raise
    except Exception as e:
        logger.error(f"Failed to send message: {e}")
        raise



async def send_email_via_aurite(email_data=None):
    """
    主函数 - 使用Google Gmail API直接发送邮件
    
    Args:
        email_data: 邮件数据字典，应包含:
            - to: 收件人邮箱
            - subject: 邮件主题  
            - body: 邮件内容
            - access_token: Google OAuth 2.0 访问令牌 (必需)
    """
    logger.info(f"[EmailService] Attempting to send email via Gmail API: {email_data}")

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

        # 提取邮件数据
        to = email_data['to']
        subject = email_data['subject']
        body = email_data['body']
        access_token = email_data['access_token']

        # 在异步上下文中运行同步的Gmail API调用
        def _send_email_sync():
            # 1. 创建Gmail服务
            service = create_gmail_service(access_token)
            
            # 2. 创建邮件消息
            message = create_message(to, subject, body)
            
            # 3. 发送邮件
            result = send_message(service, message)
            
            return result

        # 使用线程池执行同步代码
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, _send_email_sync)
        
        success_msg = f"Email sent successfully to {to}. Message ID: {result.get('id')}"
        logger.info(success_msg)
        return True, success_msg

    except HttpError as e:
        error_msg = f"Gmail API error: {e}"
        logger.error(error_msg)
        return False, error_msg
    except Exception as e:
        error_msg = f"Failed to send email: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return False, error_msg


import os
import logging
import base64
import asyncio
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] [EmailService] %(message)s'
)
logger = logging.getLogger(__name__)


def create_gmail_service(access_token):
    """
    Create Gmail API service object using access token
    
    Args:
        access_token: Google OAuth 2.0 access token
        
    Returns:
        gmail service object
    """
    try:
        # Create credentials object
        creds = Credentials(token=access_token)
        
        # Build Gmail service
        service = build('gmail', 'v1', credentials=creds)
        logger.info("Gmail service created successfully")
        return service
        
    except Exception as e:
        logger.error(f"Failed to create Gmail service: {e}")
        raise


def create_message(to, subject, body):
    """
    Create email message
    
    Args:
        to: Recipient email address
        subject: Email subject
        body: Email content (plain text)
        
    Returns:
        base64 encoded email message
    """
    try:
        # Build raw email string
        message = f"To: {to}\r\n"
        message += f"Subject: {subject}\r\n"
        message += f"Content-Type: text/plain; charset=utf-8\r\n"
        message += f"\r\n{body}"
        
        # Base64 encoding
        raw_message = base64.urlsafe_b64encode(message.encode('utf-8')).decode('utf-8')
        
        return {'raw': raw_message}
        
    except Exception as e:
        logger.error(f"Failed to create message: {e}")
        raise


def send_message(service, message):
    """
    Send email message
    
    Args:
        service: Gmail API service object
        message: Email message dictionary
        
    Returns:
        Send result
    """
    try:
        # Send email
        result = service.users().messages().send(userId='me', body=message).execute()
        logger.info(f"Email sent successfully. Message ID: {result.get('id')}")
        return result
        
    except HttpError as error:
        logger.error(f"Gmail API error: {error}")
        raise
    except Exception as e:
        logger.error(f"Failed to send message: {e}")
        raise



async def send_email_via_google_api(email_data=None):
    """
    Main function - Send email directly using Google Gmail API
    
    Args:
        email_data: Email data dictionary, should contain:
            - to: Recipient email address
            - subject: Email subject  
            - body: Email content
            - access_token: Google OAuth 2.0 access token (required)
    """
    logger.info(f"[EmailService] Attempting to send email via Gmail API: {email_data}")

    try:
        # Validate email_data format
        if not email_data:
            return False, "email_data is required"
        
        if not isinstance(email_data, dict):
            return False, "email_data must be a dictionary"
            
        # Validate required fields
        required_fields = ['to', 'subject', 'body', 'access_token']
        missing_fields = [field for field in required_fields if not email_data.get(field)]
        if missing_fields:
            return False, f"Missing required fields: {', '.join(missing_fields)}"

        # Extract email data
        to = email_data['to']
        subject = email_data['subject']
        body = email_data['body']
        access_token = email_data['access_token']

        # Run synchronous Gmail API calls in async context
        def _send_email_sync():
            # 1. Create Gmail service
            service = create_gmail_service(access_token)
            
            # 2. Create email message
            message = create_message(to, subject, body)
            
            # 3. Send email
            result = send_message(service, message)
            
            return result

        # Use thread pool to execute synchronous code
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


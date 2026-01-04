"""
Notification Service - AWS SES & SNS Integration.

This service handles all patient communications during onboarding:
- Welcome emails with temporary credentials
- SMS notifications
- Onboarding reminder emails
- Password reset notifications

Features:
- Email via AWS SES
- SMS via AWS SNS
- Template support
- Delivery tracking
- Retry logic

Usage:
    from services import NotificationService
    
    notification_service = NotificationService()
    await notification_service.send_welcome_email(
        email="patient@example.com",
        first_name="John",
        temp_password="abc123",
    )
"""

import os
from typing import Optional, Dict, Any, List
from datetime import datetime

import boto3
from botocore.exceptions import ClientError

from core.config import settings
from core.logging import get_logger
from core.exceptions import ExternalServiceError

logger = get_logger(__name__)


class NotificationService:
    """
    AWS SES/SNS notification service.
    
    Provides:
    - Welcome email with login credentials
    - Welcome SMS with app link
    - Onboarding reminder notifications
    - General email/SMS sending
    """
    
    def __init__(
        self,
        ses_client: Optional[Any] = None,
        sns_client: Optional[Any] = None,
    ):
        """
        Initialize the notification service.
        
        Args:
            ses_client: AWS SES client (optional)
            sns_client: AWS SNS client (optional)
        """
        self._ses_client = ses_client
        self._sns_client = sns_client
        self.aws_region = settings.aws_region
        self.sender_email = settings.ses_sender_email
        self.sender_name = settings.ses_sender_name
    
    @property
    def ses_client(self):
        """Get or create SES client."""
        if self._ses_client is None:
            self._ses_client = boto3.client(
                "ses",
                region_name=self.aws_region,
            )
        return self._ses_client
    
    @property
    def sns_client(self):
        """Get or create SNS client."""
        if self._sns_client is None:
            self._sns_client = boto3.client(
                "sns",
                region_name=self.aws_region,
            )
        return self._sns_client
    
    # =========================================================================
    # WELCOME NOTIFICATIONS
    # =========================================================================
    
    async def send_welcome_email(
        self,
        email: str,
        first_name: str,
        temp_password: str,
        physician_name: Optional[str] = None,
        login_url: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Send welcome email to new patient.
        
        Args:
            email: Patient's email address
            first_name: Patient's first name
            temp_password: Temporary password
            physician_name: Referring physician's name
            login_url: URL to login page
            
        Returns:
            Dict with message_id and status
        """
        logger.info(f"Sending welcome email to: {email}")
        
        login_url = login_url or "https://app.oncolife.com/login"
        
        subject = "Welcome to OncoLife - Your Personal Health Companion"
        
        html_body = self._get_welcome_email_html(
            first_name=first_name,
            email=email,
            temp_password=temp_password,
            physician_name=physician_name,
            login_url=login_url,
        )
        
        text_body = self._get_welcome_email_text(
            first_name=first_name,
            email=email,
            temp_password=temp_password,
            physician_name=physician_name,
            login_url=login_url,
        )
        
        return await self._send_email(
            to_address=email,
            subject=subject,
            html_body=html_body,
            text_body=text_body,
        )
    
    async def send_welcome_sms(
        self,
        phone_number: str,
        first_name: str,
        login_url: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Send welcome SMS to new patient.
        
        Args:
            phone_number: Patient's phone number
            first_name: Patient's first name
            login_url: URL to login page
            
        Returns:
            Dict with message_id and status
        """
        logger.info(f"Sending welcome SMS to: {phone_number}")
        
        login_url = login_url or "https://app.oncolife.com"
        
        message = (
            f"Hi {first_name}, welcome to OncoLife! "
            f"Your doctor has enrolled you in our care program. "
            f"Check your email for login details. "
            f"Questions? Reply to this message."
        )
        
        return await self._send_sms(
            phone_number=phone_number,
            message=message,
        )
    
    # =========================================================================
    # REMINDER NOTIFICATIONS
    # =========================================================================
    
    async def send_onboarding_reminder(
        self,
        email: str,
        first_name: str,
        days_since_registration: int,
        login_url: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Send reminder to complete onboarding.
        
        Args:
            email: Patient's email
            first_name: Patient's first name
            days_since_registration: Days since account was created
            login_url: URL to login page
            
        Returns:
            Dict with message_id and status
        """
        logger.info(f"Sending onboarding reminder to: {email}")
        
        login_url = login_url or "https://app.oncolife.com/login"
        
        subject = f"Complete Your OncoLife Setup, {first_name}"
        
        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #6B46C1; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 30px 20px; }}
                .button {{ 
                    display: inline-block; 
                    background-color: #6B46C1; 
                    color: white !important; 
                    padding: 12px 30px; 
                    text-decoration: none; 
                    border-radius: 5px; 
                    margin: 20px 0;
                }}
                .footer {{ font-size: 12px; color: #666; padding: 20px; border-top: 1px solid #eee; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>OncoLife</h1>
                </div>
                <div class="content">
                    <h2>Hi {first_name},</h2>
                    <p>We noticed you haven't completed your OncoLife setup yet.</p>
                    <p>Your care team is waiting to help you track your symptoms and stay connected during your treatment. It only takes a few minutes to complete!</p>
                    <p style="text-align: center;">
                        <a href="{login_url}" class="button">Complete Setup Now</a>
                    </p>
                    <p>What you'll set up:</p>
                    <ul>
                        <li>✓ Your secure password</li>
                        <li>✓ Review important health information</li>
                        <li>✓ Set your reminder preferences</li>
                    </ul>
                    <p>If you need help, just reply to this email or call us at 1-855-ONCOLIFE.</p>
                </div>
                <div class="footer">
                    <p>OncoLife Care Team</p>
                    <p>This message was sent because your doctor enrolled you in OncoLife.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        text_body = f"""
Hi {first_name},

We noticed you haven't completed your OncoLife setup yet.

Your care team is waiting to help you track your symptoms and stay connected during your treatment. It only takes a few minutes to complete!

Click here to complete your setup: {login_url}

What you'll set up:
- Your secure password
- Review important health information  
- Set your reminder preferences

If you need help, just reply to this email or call us at 1-855-ONCOLIFE.

OncoLife Care Team
        """
        
        return await self._send_email(
            to_address=email,
            subject=subject,
            html_body=html_body,
            text_body=text_body,
        )
    
    # =========================================================================
    # EMAIL TEMPLATES
    # =========================================================================
    
    def _get_welcome_email_html(
        self,
        first_name: str,
        email: str,
        temp_password: str,
        physician_name: Optional[str],
        login_url: str,
    ) -> str:
        """Generate HTML body for welcome email."""
        physician_text = f" referred by Dr. {physician_name}" if physician_name else ""
        
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #6B46C1; color: white; padding: 30px; text-align: center; }}
                .header h1 {{ margin: 0; font-size: 28px; }}
                .content {{ padding: 30px 20px; background: #fff; }}
                .credentials {{ 
                    background-color: #f7f7f7; 
                    padding: 20px; 
                    border-radius: 8px; 
                    margin: 20px 0;
                    border-left: 4px solid #6B46C1;
                }}
                .credentials p {{ margin: 5px 0; }}
                .credentials strong {{ color: #333; }}
                .button {{ 
                    display: inline-block; 
                    background-color: #6B46C1; 
                    color: white !important; 
                    padding: 15px 40px; 
                    text-decoration: none; 
                    border-radius: 5px; 
                    margin: 20px 0;
                    font-weight: bold;
                }}
                .steps {{ background: #f9f9f9; padding: 20px; border-radius: 8px; }}
                .steps h3 {{ color: #6B46C1; margin-top: 0; }}
                .steps ol {{ padding-left: 20px; }}
                .steps li {{ margin: 10px 0; }}
                .footer {{ 
                    font-size: 12px; 
                    color: #666; 
                    padding: 20px; 
                    border-top: 1px solid #eee;
                    text-align: center;
                }}
                .warning {{ 
                    background: #fff3cd; 
                    border: 1px solid #ffc107; 
                    padding: 15px; 
                    border-radius: 5px; 
                    margin: 15px 0;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🏥 Welcome to OncoLife</h1>
                    <p style="margin: 10px 0 0 0; opacity: 0.9;">Your Personal Health Companion</p>
                </div>
                
                <div class="content">
                    <h2>Hi {first_name},</h2>
                    
                    <p>Your healthcare team{physician_text} has enrolled you in <strong>OncoLife</strong> — a personal health companion designed to help you track symptoms and stay connected with your care team during your treatment.</p>
                    
                    <div class="credentials">
                        <h3 style="margin-top: 0; color: #6B46C1;">🔐 Your Login Credentials</h3>
                        <p><strong>Username:</strong> {email}</p>
                        <p><strong>Temporary Password:</strong> {temp_password}</p>
                    </div>
                    
                    <div class="warning">
                        ⚠️ <strong>Important:</strong> You will be asked to create a new password when you first log in.
                    </div>
                    
                    <p style="text-align: center;">
                        <a href="{login_url}" class="button">Log In to OncoLife →</a>
                    </p>
                    
                    <div class="steps">
                        <h3>📋 First-Time Setup (Takes ~3 minutes)</h3>
                        <ol>
                            <li><strong>Create Your Password</strong> — Set a secure password you'll remember</li>
                            <li><strong>Read Important Information</strong> — Understand how OncoLife helps (not replaces) your care team</li>
                            <li><strong>Accept Terms</strong> — Review and accept our terms and privacy policy</li>
                            <li><strong>Set Reminders</strong> — Choose how and when you'd like to be reminded to check in</li>
                        </ol>
                    </div>
                    
                    <h3 style="margin-top: 30px;">What is OncoLife?</h3>
                    <p>OncoLife is a simple tool that lets you:</p>
                    <ul>
                        <li>📝 Report how you're feeling each day</li>
                        <li>🔔 Get smart alerts if symptoms need attention</li>
                        <li>📊 Share updates with your care team automatically</li>
                        <li>📅 Track your treatment journey</li>
                    </ul>
                    
                    <p><strong>Questions?</strong> Reply to this email or call us at <strong>1-855-ONCOLIFE</strong>.</p>
                </div>
                
                <div class="footer">
                    <p>OncoLife Care Team</p>
                    <p>You received this email because your healthcare provider enrolled you in OncoLife.</p>
                    <p>© 2026 OncoLife Health, Inc. All rights reserved.</p>
                </div>
            </div>
        </body>
        </html>
        """
    
    def _get_welcome_email_text(
        self,
        first_name: str,
        email: str,
        temp_password: str,
        physician_name: Optional[str],
        login_url: str,
    ) -> str:
        """Generate plain text body for welcome email."""
        physician_text = f" referred by Dr. {physician_name}" if physician_name else ""
        
        return f"""
Welcome to OncoLife!
====================

Hi {first_name},

Your healthcare team{physician_text} has enrolled you in OncoLife — a personal health companion designed to help you track symptoms and stay connected with your care team during your treatment.

YOUR LOGIN CREDENTIALS
-----------------------
Username: {email}
Temporary Password: {temp_password}

IMPORTANT: You will be asked to create a new password when you first log in.

Log in here: {login_url}

FIRST-TIME SETUP (Takes ~3 minutes)
------------------------------------
1. Create Your Password — Set a secure password you'll remember
2. Read Important Information — Understand how OncoLife helps (not replaces) your care team
3. Accept Terms — Review and accept our terms and privacy policy
4. Set Reminders — Choose how and when you'd like to be reminded to check in

WHAT IS ONCOLIFE?
-----------------
OncoLife is a simple tool that lets you:
• Report how you're feeling each day
• Get smart alerts if symptoms need attention
• Share updates with your care team automatically
• Track your treatment journey

Questions? Reply to this email or call us at 1-855-ONCOLIFE.

OncoLife Care Team

---
You received this email because your healthcare provider enrolled you in OncoLife.
© 2026 OncoLife Health, Inc. All rights reserved.
        """
    
    # =========================================================================
    # CORE EMAIL/SMS SENDING
    # =========================================================================
    
    async def _send_email(
        self,
        to_address: str,
        subject: str,
        html_body: str,
        text_body: str,
    ) -> Dict[str, Any]:
        """
        Send an email via AWS SES.
        
        Args:
            to_address: Recipient email address
            subject: Email subject
            html_body: HTML content
            text_body: Plain text content
            
        Returns:
            Dict with message_id and status
        """
        try:
            response = self.ses_client.send_email(
                Source=f"{self.sender_name} <{self.sender_email}>",
                Destination={"ToAddresses": [to_address]},
                Message={
                    "Subject": {"Data": subject, "Charset": "UTF-8"},
                    "Body": {
                        "Text": {"Data": text_body, "Charset": "UTF-8"},
                        "Html": {"Data": html_body, "Charset": "UTF-8"},
                    },
                },
            )
            
            message_id = response["MessageId"]
            logger.info(f"Email sent: {to_address} (MessageId: {message_id})")
            
            return {
                "success": True,
                "message_id": message_id,
                "recipient": to_address,
            }
            
        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            error_message = e.response["Error"]["Message"]
            logger.error(f"SES error: {error_code} - {error_message}")
            
            raise ExternalServiceError(
                message=f"Failed to send email: {error_message}",
                service_name="AWS SES",
            )
    
    async def _send_sms(
        self,
        phone_number: str,
        message: str,
    ) -> Dict[str, Any]:
        """
        Send an SMS via AWS SNS.
        
        Args:
            phone_number: Recipient phone number (E.164 format preferred)
            message: SMS message content
            
        Returns:
            Dict with message_id and status
        """
        # Ensure E.164 format
        if not phone_number.startswith("+"):
            phone_number = f"+1{phone_number.replace('-', '').replace(' ', '')}"
        
        try:
            response = self.sns_client.publish(
                PhoneNumber=phone_number,
                Message=message,
                MessageAttributes={
                    "AWS.SNS.SMS.SenderID": {
                        "DataType": "String",
                        "StringValue": "OncoLife",
                    },
                    "AWS.SNS.SMS.SMSType": {
                        "DataType": "String",
                        "StringValue": "Transactional",
                    },
                },
            )
            
            message_id = response["MessageId"]
            logger.info(f"SMS sent: {phone_number} (MessageId: {message_id})")
            
            return {
                "success": True,
                "message_id": message_id,
                "recipient": phone_number,
            }
            
        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            error_message = e.response["Error"]["Message"]
            logger.error(f"SNS error: {error_code} - {error_message}")
            
            raise ExternalServiceError(
                message=f"Failed to send SMS: {error_message}",
                service_name="AWS SNS",
            )
    
    # =========================================================================
    # BULK SENDING
    # =========================================================================
    
    async def send_bulk_emails(
        self,
        emails: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """
        Send multiple emails.
        
        Args:
            emails: List of email configs with keys:
                - to_address
                - subject
                - html_body
                - text_body
                
        Returns:
            List of results for each email
        """
        results = []
        
        for email_config in emails:
            try:
                result = await self._send_email(**email_config)
                results.append(result)
            except Exception as e:
                results.append({
                    "success": False,
                    "recipient": email_config.get("to_address"),
                    "error": str(e),
                })
        
        return results




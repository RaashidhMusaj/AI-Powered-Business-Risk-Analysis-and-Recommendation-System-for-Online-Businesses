import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Tuple
from app.config.settings import settings
from app.utils.logger import api_logger


def send_otp_email(to_email: str, otp_code: str) -> Tuple[bool, str]:
    """
    Sends a 6-digit OTP verification code to the specified email address.
    Returns (True, message) if sent via SMTP, or (False, demo_message) if offline/unconfigured.
    """
    if not settings.SMTP_USER or not settings.SMTP_PASSWORD:
        demo_msg = f"[DEMO MODE] Verification Code for {to_email} is: {otp_code} (Expires in 15 mins)"
        api_logger.info(demo_msg)
        return False, demo_msg

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"{otp_code} is your Password Reset Verification Code"
        msg["From"] = f"{settings.EMAILS_FROM_NAME} <{settings.EMAILS_FROM_EMAIL}>"
        msg["To"] = to_email

        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
        </head>
        <body style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f4f6f9; margin: 0; padding: 30px;">
            <div style="max-width: 520px; margin: 0 auto; background: #ffffff; border-radius: 12px; padding: 32px; box-shadow: 0 4px 12px rgba(0,0,0,0.05); border: 1px solid #e2e8f0;">
                <div style="text-align: center; margin-bottom: 24px;">
                    <h2 style="color: #0d6efd; margin: 0; font-size: 22px;">Business Risk Analysis System</h2>
                    <p style="color: #64748b; font-size: 14px; margin-top: 4px;">Password Recovery Verification</p>
                </div>
                <hr style="border: none; border-top: 1px solid #e2e8f0; margin: 20px 0;">
                <p style="color: #334155; font-size: 15px; line-height: 1.5;">Hello,</p>
                <p style="color: #334155; font-size: 15px; line-height: 1.5;">You requested to reset your password. Use the 6-digit verification code below to complete your reset process:</p>
                
                <div style="background-color: #f8fafc; border: 2px dashed #cbd5e1; text-align: center; padding: 18px; margin: 24px 0; border-radius: 8px;">
                    <span style="font-size: 36px; font-weight: 800; letter-spacing: 8px; color: #198754; font-family: monospace;">{otp_code}</span>
                </div>

                <p style="color: #64748b; font-size: 13px; line-height: 1.5; margin-bottom: 0;">
                    ⏱️ This verification code is valid for <strong>15 minutes</strong>.<br>
                    🔒 If you did not request a password reset, please ignore this email.
                </p>
            </div>
        </body>
        </html>
        """

        msg.attach(MIMEText(html_content, "html"))

        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=10) as server:
            server.starttls()
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.sendmail(settings.EMAILS_FROM_EMAIL, to_email, msg.as_string())

        api_logger.info(f"Successfully sent OTP verification email to {to_email}")
        return True, f"A 6-digit verification code has been sent to {to_email}."

    except Exception as e:
        err_msg = f"Failed to send email to {to_email}: {str(e)}"
        api_logger.error(err_msg)
        demo_fallback = f"[DEMO FALLBACK] Verification Code for {to_email} is: {otp_code}"
        return False, demo_fallback

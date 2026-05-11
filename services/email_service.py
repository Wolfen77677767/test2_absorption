import logging
from flask_mail import Mail, Message

mail = Mail()
logger = logging.getLogger(__name__)

def build_email_layout(title, content_html, content_text):
    """Build a professional HTML email layout matching the app's dark theme."""
    html = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>""" + title + """</title>
    <style>
        body {
            margin: 0;
            padding: 0;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .email-container {
            max-width: 600px;
            margin: 20px auto;
            background: rgba(30, 41, 59, 0.95);
            border-radius: 16px;
            box-shadow: 0 20px 40px rgba(0, 0, 0, 0.3);
            overflow: hidden;
            border: 1px solid rgba(255, 255, 255, 0.1);
        }
        .email-header {
            background: linear-gradient(135deg, #0066FF 0%, #00D9FF 100%);
            padding: 32px 40px;
            text-align: center;
            color: white;
        }
        .email-header h1 {
            margin: 0;
            font-size: 24px;
            font-weight: 700;
            letter-spacing: -0.02em;
        }
        .email-header p {
            margin: 8px 0 0;
            font-size: 14px;
            opacity: 0.9;
            font-weight: 400;
        }
        .email-body {
            padding: 40px;
            color: #f0f5fa;
            line-height: 1.6;
        }
        .email-body h2 {
            margin: 0 0 16px;
            font-size: 20px;
            font-weight: 600;
            color: #00D9FF;
        }
        .email-body p {
            margin: 0 0 20px;
            color: #a8b5c8;
            font-size: 16px;
        }
        .code-block {
            background: rgba(0, 102, 255, 0.1);
            border: 2px solid #0066FF;
            border-radius: 8px;
            padding: 24px;
            text-align: center;
            margin: 24px 0;
            font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
        }
        .code-text {
            font-size: 32px;
            font-weight: 700;
            color: #00D9FF;
            letter-spacing: 4px;
            margin: 0;
            text-shadow: 0 0 20px rgba(0, 217, 255, 0.3);
        }
        .expiry-notice {
            background: rgba(255, 193, 7, 0.1);
            border-left: 4px solid #ffc107;
            padding: 16px 20px;
            margin: 20px 0;
            color: #ffc107;
            font-size: 14px;
            font-weight: 500;
        }
        .email-footer {
            background: rgba(15, 23, 42, 0.8);
            padding: 24px 40px;
            text-align: center;
            border-top: 1px solid rgba(255, 255, 255, 0.1);
        }
        .email-footer p {
            margin: 0;
            font-size: 12px;
            color: #64748b;
        }
        .security-notice {
            background: rgba(239, 68, 68, 0.1);
            border-left: 4px solid #ef4444;
            padding: 16px 20px;
            margin: 20px 0;
            color: #ef4444;
            font-size: 14px;
            font-weight: 500;
        }
    </style>
</head>
<body>
    <div class="email-container">
        <div class="email-header">
            <h1>Gas Absorption Analysis</h1>
            <p>Advanced Chemical Engineering Solutions</p>
        </div>
        <div class="email-body">
            """ + content_html + """
        </div>
        <div class="email-footer">
            <p>This email was sent by Gas Absorption Analysis. Please do not reply to this message.</p>
        </div>
    </div>
</body>
</html>
"""
    return html, content_text


def send_email_message(subject, recipient_email, html_body, text_body):
    msg = Message(
        subject,
        recipients=[recipient_email],
        html=html_body,
        body=text_body
    )
    try:
        mail.send(msg)
        logger.info("Email sent to %s with subject '%s'", recipient_email, subject)
    except Exception:
        logger.exception("Failed to send email to %s with subject '%s'", recipient_email, subject)
        raise


def send_verification_email(recipient_email, first_name, code):
    """Send a professional verification email with HTML template."""
    greeting = first_name if first_name else "there"

    content_html = """
    <h2>Welcome to Gas Absorption Analysis!</h2>
    <p>Hi """ + greeting + """,</p>
    <p>Thank you for creating your account. To complete your registration and start using our advanced gas absorption analysis tools, please verify your email address using the code below:</p>

    <div class="code-block">
        <div class="code-text">""" + code + """</div>
    </div>

    <div class="expiry-notice">
        <strong>⏰ This code expires in 15 minutes</strong> for security reasons.
    </div>

    <p>Enter this code on the verification page to activate your account. If you didn't create this account, you can safely ignore this email.</p>
    """

    content_text = f"""
Hi {greeting},

Welcome to Gas Absorption Analysis!

Your verification code is: {code}

This code expires in 15 minutes.

Enter this code on the verification page to activate your account.

If you didn't create this account, you can safely ignore this email.
"""

    html_body, text_body = build_email_layout("Verify Your Account", content_html, content_text)

    send_email_message(
        "Verify Your Account - Gas Absorption Analysis",
        recipient_email,
        html_body,
        text_body
    )


def send_reset_password_email(recipient_email, first_name, code):
    """Send a professional password reset email with HTML template."""
    greeting = first_name if first_name else "there"

    content_html = """
    <h2>Password Reset Request</h2>
    <p>Hi """ + greeting + """,</p>
    <p>We received a request to reset your password for your Gas Absorption Analysis account. Use the code below to securely reset your password:</p>

    <div class="code-block">
        <div class="code-text">""" + code + """</div>
    </div>

    <div class="expiry-notice">
        <strong>⏰ This code expires in 15 minutes</strong> for security reasons.
    </div>

    <div class="security-notice">
        <strong>🔒 Security Notice:</strong> If you didn't request this password reset, please ignore this email and consider changing your password if you suspect unauthorized access.
    </div>

    <p>Enter this code on the password reset page to create a new password. For your security, this link will expire soon.</p>
    """

    content_text = f"""
Hi {greeting},

We received a request to reset your password for your Gas Absorption Analysis account.

Your reset code is: {code}

This code expires in 15 minutes.

If you didn't request this password reset, please ignore this email.

Enter this code on the password reset page to create a new password.
"""

    html_body, text_body = build_email_layout("Reset Your Password", content_html, content_text)

    send_email_message(
        "Reset Your Password - Gas Absorption Analysis",
        recipient_email,
        html_body,
        text_body
    )
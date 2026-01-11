"""Email functionality for sending Duolingo Family League reports"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from typing import Any


def send_email(
    report: str,
    email_config: dict[str, Any],
    subject_prefix: str = "",
    recipient_list: list[str] | None = None,
) -> bool:
    """Send report via email

    Args:
        report: The report content to send
        email_config: Email configuration dictionary
        subject_prefix: Prefix for the email subject
        recipient_list: Optional override for recipients (defaults to family_email_list)
    """
    try:
        recipients = recipient_list or email_config.get("family_email_list")
        if not all(
            [
                email_config.get("smtp_server"),
                email_config.get("sender_email"),
                email_config.get("sender_password"),
                recipients,
            ]
        ):
            print(
                "❌ Email configuration incomplete. Please check environment variables or config file."
            )
            return False

        msg = MIMEMultipart()
        msg["From"] = email_config["sender_email"]
        msg["To"] = ", ".join(recipients)
        msg["Subject"] = (
            f"Duolingo Family League - {subject_prefix}{datetime.now().strftime('%B %d, %Y')}"
        )

        msg.attach(MIMEText(report, "plain"))

        server = smtplib.SMTP(email_config["smtp_server"], email_config["smtp_port"])
        server.starttls()
        server.login(email_config["sender_email"], email_config["sender_password"])
        text = msg.as_string()
        server.sendmail(email_config["sender_email"], recipients, text)
        server.quit()

        print(f"✅ {subject_prefix}report email sent successfully!")
        return True

    except Exception as e:
        print(f"❌ Failed to send email: {e}")
        return False


def should_send_daily(email_config: dict[str, Any]) -> bool:
    """Check if daily emails are enabled"""
    return email_config.get("send_daily", False)


def should_send_weekly(email_config: dict[str, Any]) -> bool:
    """Check if weekly emails are enabled"""
    return email_config.get("send_weekly", True)

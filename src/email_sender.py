"""Email functionality for sending Duolingo Family League reports"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime


def send_email(report, email_config, subject_prefix=""):
    """Send report via email"""
    try:
        if not all(
            [
                email_config.get("smtp_server"),
                email_config.get("sender_email"),
                email_config.get("sender_password"),
                email_config.get("family_email_list"),
            ]
        ):
            print(
                "❌ Email configuration incomplete. Please check environment variables or config file."
            )
            return False

        msg = MIMEMultipart()
        msg["From"] = email_config["sender_email"]
        msg["To"] = ", ".join(email_config["family_email_list"])
        msg["Subject"] = (
            f"Duolingo Family League - {subject_prefix}{datetime.now().strftime('%B %d, %Y')}"
        )

        msg.attach(MIMEText(report, "plain"))

        server = smtplib.SMTP(email_config["smtp_server"], email_config["smtp_port"])
        server.starttls()
        server.login(email_config["sender_email"], email_config["sender_password"])
        text = msg.as_string()
        server.sendmail(
            email_config["sender_email"], email_config["family_email_list"], text
        )
        server.quit()

        print(f"✅ {subject_prefix}report email sent successfully!")
        return True

    except Exception as e:
        print(f"❌ Failed to send email: {e}")
        return False


def should_send_daily(email_config):
    """Check if daily emails are enabled"""
    return email_config.get("send_daily", False)


def should_send_weekly(email_config):
    """Check if weekly emails are enabled"""
    return email_config.get("send_weekly", True)

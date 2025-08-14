"""Configuration management for Duolingo Family League"""

import os
import re
from typing import Any
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def validate_username(username: str) -> bool:
    """Validate username format"""
    if not username:
        raise ValueError("Username cannot be empty")

    # Check for valid characters (alphanumeric, underscore, hyphen, dot)
    if not re.match(r"^[a-zA-Z0-9._-]+$", username):
        raise ValueError(
            f"Invalid username '{username}': only letters, numbers, dots, underscores and hyphens are allowed"
        )

    # Check length constraints
    if len(username) < 3 or len(username) > 30:
        raise ValueError(
            f"Invalid username '{username}': must be between 3 and 30 characters"
        )

    return True


def validate_email(email: str) -> bool:
    """Validate email format"""
    if not email:
        return False

    # Basic email regex pattern
    email_pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return re.match(email_pattern, email) is not None


def load_config() -> dict[str, Any] | None:
    """Load family league configuration from environment variables"""
    # Parse usernames from comma-separated list (required)
    usernames_env = os.getenv("DUOLINGO_USERNAMES", "")
    usernames = (
        [u.strip() for u in usernames_env.split(",") if u.strip()]
        if usernames_env
        else []
    )

    # Parse display names from comma-separated list (optional)
    display_names_env = os.getenv("DUOLINGO_DISPLAY_NAMES", "")
    display_names = (
        [d.strip() for d in display_names_env.split(",") if d.strip()]
        if display_names_env
        else []
    )

    # Create family members dictionary from usernames
    family_members = {}
    if usernames:
        print(f"🌟 Tracking usernames: {', '.join(usernames)}")
        for i, username in enumerate(usernames):
            try:
                validate_username(username)
                # Use display name if provided, otherwise use username
                display_name = display_names[i] if i < len(display_names) else username
                family_members[display_name] = {
                    "username": username,
                    "display_name": display_name,
                }
            except ValueError as e:
                print(f"❌ Invalid username: {e}")
                return None

    # Get goals from environment variables
    goals = {
        "weekly_xp_goal": int(os.getenv("WEEKLY_XP_GOAL", 500)),
        "streak_goal": int(os.getenv("STREAK_GOAL", 7)),
    }

    # Email settings from environment variables
    sender_email = os.getenv("SENDER_EMAIL")
    if sender_email and not validate_email(sender_email):
        print(f"❌ Invalid sender email format: {sender_email}")
        return None

    email_settings = {
        "smtp_server": os.getenv("SMTP_SERVER", "smtp.gmail.com"),
        "smtp_port": int(os.getenv("SMTP_PORT", 587)),
        "sender_email": sender_email,
        "sender_password": os.getenv("SENDER_PASSWORD"),
        "family_email_list": get_validated_email_list(),
        "send_daily": os.getenv("SEND_DAILY", "false").lower() == "true",
        "send_weekly": os.getenv("SEND_WEEKLY", "true").lower() == "true",
    }

    return {
        "family_members": family_members,
        "email_settings": email_settings,
        "goals": goals,
    }


def get_email_config(config: dict[str, Any] | None) -> dict[str, Any]:
    """Extract email configuration from config"""
    if not config:
        return {}
    return config.get("email_settings", {})


def get_email_list() -> list[str]:
    """Get email list from environment variable"""
    email_list_env = os.getenv("FAMILY_EMAIL_LIST", "")
    if email_list_env:
        return [email.strip() for email in email_list_env.split(",")]
    return []


def get_validated_email_list() -> list[str]:
    """Get email list with validation"""
    email_list_env = os.getenv("FAMILY_EMAIL_LIST", "")
    if not email_list_env:
        return []

    validated_emails: list[str] = []
    for email in email_list_env.split(","):
        email = email.strip()
        if email:
            if validate_email(email):
                validated_emails.append(email)
            else:
                print(f"⚠️ Skipping invalid email: {email}")

    return validated_emails

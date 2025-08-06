"""Configuration management for Duolingo Family League"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def load_config():
    """Load family league configuration from environment variables"""
    # Parse usernames from comma-separated list (required)
    usernames_env = os.getenv('DUOLINGO_USERNAMES', '')
    usernames = [u.strip() for u in usernames_env.split(',') if u.strip()] if usernames_env else []
    
    # Create family members dictionary from usernames
    family_members = {}
    if usernames:
        print(f"🌟 Tracking usernames: {', '.join(usernames)}")
        for username in usernames:
            # Use username as the display name if no nickname is provided
            family_members[username] = {
                'username': username
            }
    
    # Get goals from environment variables
    goals = {
        'weekly_xp_goal': int(os.getenv('WEEKLY_XP_GOAL', 500)),
        'streak_goal': int(os.getenv('STREAK_GOAL', 7))
    }
    
    # Email settings from environment variables
    email_settings = {
        'smtp_server': os.getenv('SMTP_SERVER', 'smtp.gmail.com'),
        'smtp_port': int(os.getenv('SMTP_PORT', 587)),
        'sender_email': os.getenv('SENDER_EMAIL'),
        'sender_password': os.getenv('SENDER_PASSWORD'),
        'family_email_list': get_email_list(),
        'send_daily': os.getenv('SEND_DAILY', 'false').lower() == 'true',
        'send_weekly': os.getenv('SEND_WEEKLY', 'true').lower() == 'true'
    }
    
    return {
        'family_members': family_members,
        'email_settings': email_settings,
        'goals': goals
    }


def get_email_config(config):
    """Extract email configuration from config"""
    if not config:
        return {}
    return config.get('email_settings', {})


def get_email_list():
    """Get email list from environment variable"""
    email_list_env = os.getenv('FAMILY_EMAIL_LIST', '')
    if email_list_env:
        return [email.strip() for email in email_list_env.split(',')]
    return []
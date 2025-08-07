#!/usr/bin/env python3
"""
Test suite for Duolingo Family League using pytest
"""

import json
import os
import sys
import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import tempfile

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.config import load_config, get_email_config, validate_username, validate_email
from src.duolingo_api import get_user_progress
from src.data_storage import DataStorage
from src.report_generator import (
    generate_leaderboard,
    generate_daily_report,
    generate_weekly_report,
)
from src.email_sender import send_email


@pytest.fixture
def env_setup():
    """Set up environment variables for testing"""
    original_env = {}
    test_env = {
        "DUOLINGO_USERNAMES": "test_user_1,test_user_2",
        "WEEKLY_XP_GOAL": "500",
        "STREAK_GOAL": "7",
        "SMTP_SERVER": "smtp.test.com",
        "SMTP_PORT": "587",
        "SENDER_EMAIL": "sender@test.com",
        "SENDER_PASSWORD": "test_password",
        "FAMILY_EMAIL_LIST": "family@test.com",
        "SEND_DAILY": "false",
        "SEND_WEEKLY": "true",
    }

    # Save original values and set test values
    for key, value in test_env.items():
        original_env[key] = os.environ.get(key)
        os.environ[key] = value

    yield

    # Restore original values
    for key, original_value in original_env.items():
        if original_value is None:
            os.environ.pop(key, None)
        else:
            os.environ[key] = original_value


@pytest.fixture
def test_config(env_setup):
    """Load test configuration from environment"""
    return load_config()


class TestConfiguration:
    """Test configuration loading and validation"""

    def test_load_config_from_env(self, test_config):
        """Test loading configuration from environment variables"""
        assert test_config is not None
        assert "family_members" in test_config
        assert "email_settings" in test_config
        assert "goals" in test_config

        # Check family members
        assert "test_user_1" in test_config["family_members"]
        assert "test_user_2" in test_config["family_members"]

        # Check goals
        assert test_config["goals"]["weekly_xp_goal"] == 500
        assert test_config["goals"]["streak_goal"] == 7

        # Check email settings
        assert test_config["email_settings"]["smtp_server"] == "smtp.test.com"
        assert test_config["email_settings"]["send_weekly"]
        assert not test_config["email_settings"]["send_daily"]

    def test_missing_usernames(self):
        """Test that config returns empty family_members when usernames are missing"""
        os.environ.pop("DUOLINGO_USERNAMES", None)
        config = load_config()
        assert config is not None
        assert config["family_members"] == {}

    def test_email_config_extraction(self, test_config):
        """Test email configuration extraction"""
        email_config = get_email_config(test_config)

        assert email_config["smtp_server"] == "smtp.test.com"
        assert email_config["sender_email"] == "sender@test.com"
        assert email_config["sender_password"] == "test_password"
        assert email_config["family_email_list"] == ["family@test.com"]

    def test_username_validation(self):
        """Test username validation"""
        # Valid usernames
        assert validate_username("test_user")
        assert validate_username("test.user")
        assert validate_username("test-user")
        assert validate_username("test_123")

        # Invalid usernames
        with pytest.raises(ValueError):
            validate_username("")  # Empty
        with pytest.raises(ValueError):
            validate_username("ab")  # Too short
        with pytest.raises(ValueError):
            validate_username("a" * 31)  # Too long
        with pytest.raises(ValueError):
            validate_username("test@user")  # Invalid character
        with pytest.raises(ValueError):
            validate_username("test user")  # Space not allowed

    def test_email_validation(self):
        """Test email validation"""
        # Valid emails
        assert validate_email("test@example.com")
        assert validate_email("user.name@domain.co.uk")
        assert validate_email("test+tag@example.org")

        # Invalid emails
        assert not validate_email("")
        assert not validate_email("invalid")
        assert not validate_email("@example.com")
        assert not validate_email("test@")
        assert not validate_email("test@.com")


class TestDuolingoIntegration:
    """Test Duolingo API integration"""

    @patch("src.duolingo_api.requests.get")
    def test_get_user_progress_success(self, mock_get):
        """Test successful user progress retrieval"""
        mock_response = Mock()
        mock_response.json.return_value = {
            "users": [
                {
                    "name": "Test User",
                    "totalXp": 10000,
                    "streakData": {"currentStreak": {"length": 5}},
                    "courses": [
                        {
                            "title": "Spanish",
                            "xp": 5000,
                            "crowns": 10,
                            "fromLanguage": "en",
                            "learningLanguage": "es",
                        },
                        {
                            "title": "French",
                            "xp": 3000,
                            "crowns": 8,
                            "fromLanguage": "en",
                            "learningLanguage": "fr",
                        },
                    ],
                    "hasPlus": True,
                }
            ]
        }
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        progress = get_user_progress("test_user")

        assert progress["username"] == "test_user"
        assert progress["name"] == "Test User"
        assert progress["streak"] == 5
        assert progress["total_xp"] == 10000
        assert "Spanish" in progress["language_progress"]
        assert "French" in progress["language_progress"]
        assert progress["language_progress"]["Spanish"]["xp"] == 5000
        assert progress["profile_public"]
        assert "Spanish" in progress["active_languages"]
        assert "French" in progress["active_languages"]
        assert progress["has_plus"]

    @patch("src.duolingo_api.requests.get")
    def test_get_user_progress_error(self, mock_get):
        """Test error handling in user progress retrieval"""
        mock_get.side_effect = Exception("API Error")

        progress = get_user_progress("test_user")

        assert "error" in progress
        assert progress["error"] == "API Error"
        assert not progress["profile_public"]
        assert progress["active_languages"] == []


class TestDataStorage:
    """Test data saving and history management"""

    def test_save_daily_data(self):
        """Test saving daily progress data"""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = DataStorage(data_dir=tmpdir)

            test_results = {
                "TestUser": {"username": "test", "streak": 5, "total_xp": 1000}
            }

            storage.save_daily_data(test_results)

            # Check daily file was created
            daily_files = list(Path(tmpdir).glob("daily_*.json"))
            assert len(daily_files) == 1

            # Check history file was created
            history_file = Path(tmpdir) / "league_history.json"
            assert history_file.exists()

    def test_history_deduplication(self):
        """Test that duplicate daily entries are avoided"""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = DataStorage(data_dir=tmpdir)

            test_results = {"TestUser": {"username": "test", "streak": 5}}

            # Save twice on the same day
            storage.save_daily_data(test_results)
            test_results["TestUser"]["streak"] = 6
            storage.save_daily_data(test_results)

            # Check history has only one entry for today
            history_file = Path(tmpdir) / "league_history.json"
            with open(history_file) as f:
                history = json.load(f)

            from datetime import datetime

            today = datetime.now().strftime("%Y-%m-%d")
            today_entries = [h for h in history if h.get("date") == today]
            assert len(today_entries) == 1
            assert today_entries[0]["results"]["TestUser"]["streak"] == 6


class TestReportGeneration:
    """Test report generation functionality"""

    def test_generate_leaderboard(self):
        """Test leaderboard generation and sorting"""
        results = {
            "User1": {
                "streak": 5,
                "weekly_xp": 100,
                "total_xp": 1000,
                "total_languages_xp": 500,
            },
            "User2": {
                "streak": 10,
                "weekly_xp": 200,
                "total_xp": 2000,
                "total_languages_xp": 1000,
            },
            "User3": {
                "streak": 3,
                "weekly_xp": 50,
                "total_xp": 500,
                "total_languages_xp": 250,
            },
            "User4": {"error": "Profile private"},
        }

        leaderboard = generate_leaderboard(results)

        assert len(leaderboard) == 3  # User4 excluded due to error
        assert leaderboard[0]["name"] == "User2"  # Highest streak
        assert leaderboard[1]["name"] == "User1"
        assert leaderboard[2]["name"] == "User3"

    def test_generate_daily_report(self):
        """Test daily report generation"""
        results = {
            "User1": {
                "streak": 5,
                "weekly_xp": 100,
                "total_xp": 1000,
                "total_languages_xp": 500,
                "language_progress": {"Spanish": {"xp": 500, "level": 5}},
            },
            "User2": {
                "streak": 0,
                "weekly_xp": 0,
                "total_xp": 100,
                "total_languages_xp": 50,
                "language_progress": {"French": {"xp": 50, "level": 1}},
            },
        }

        report = generate_daily_report(results)

        assert "DAILY UPDATE" in report
        assert "User1" in report
        assert "needs to practice today" in report  # User2 has 0 streak

    def test_generate_weekly_report(self):
        """Test weekly report generation"""
        results = {
            "User1": {
                "username": "user1",
                "streak": 7,
                "weekly_xp": 600,
                "total_xp": 10000,
                "total_languages_xp": 5000,
                "language_progress": {
                    "Spanish": {"xp": 3000, "level": 10},
                    "French": {"xp": 2000, "level": 8},
                },
            }
        }

        goals = {"weekly_xp_goal": 500, "streak_goal": 7}
        report = generate_weekly_report(results, goals)

        assert "WEEKLY REPORT" in report
        assert "STREAK GOAL ACHIEVED" in report  # 7-day streak
        assert "WEEKLY XP GOAL ACHIEVED" in report  # 600 > 500
        assert "Spanish: Level 10" in report
        assert "French: Level 8" in report


class TestEmailFunctionality:
    """Test email sending functionality"""

    @patch("src.email_sender.smtplib.SMTP")
    def test_send_email_success(self, mock_smtp):
        """Test successful email sending"""
        mock_server = MagicMock()
        mock_smtp.return_value = mock_server

        email_config = {
            "smtp_server": "smtp.test.com",
            "smtp_port": 587,
            "sender_email": "sender@test.com",
            "sender_password": "test_password",
            "family_email_list": ["family@test.com"],
        }

        report = "Test Report Content"
        result = send_email(report, email_config, "Test - ")

        assert result
        mock_server.starttls.assert_called_once()
        mock_server.login.assert_called_once()
        mock_server.sendmail.assert_called_once()
        mock_server.quit.assert_called_once()

    @patch("src.email_sender.smtplib.SMTP")
    def test_send_email_failure(self, mock_smtp):
        """Test email sending with error"""
        mock_smtp.side_effect = Exception("SMTP Error")

        email_config = {
            "smtp_server": "smtp.test.com",
            "smtp_port": 587,
            "sender_email": "sender@test.com",
            "sender_password": "test_password",
            "family_email_list": ["family@test.com"],
        }

        report = "Test Report"
        result = send_email(report, email_config, "Test - ")

        assert not result

    def test_email_config_validation(self):
        """Test email configuration validation"""
        # Incomplete config
        email_config = {
            "smtp_server": "smtp.test.com",
            "smtp_port": 587,
            # Missing sender_email and sender_password
            "family_email_list": ["family@test.com"],
        }

        report = "Test Report"
        result = send_email(report, email_config)

        assert not result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

"""Tests for HTML report generation functionality"""

import pytest
import os
from unittest.mock import patch
from datetime import datetime
from src.html_report_generator import (
    generate_daily_html_report,
    generate_weekly_html_report,
)
from src.report_generator import generate_daily_report_html, generate_weekly_report_html
from src.i18n import I18n, get_language_from_env, set_global_language


class TestI18n:
    """Test internationalization functionality"""

    def test_i18n_initialization(self):
        """Test I18n class initialization"""
        i18n = I18n("en")
        assert i18n.language == "en"
        assert len(i18n._translations) == 2  # English and Hungarian

    def test_i18n_get_translation(self):
        """Test getting translations"""
        i18n = I18n("en")
        assert "DUOLINGO FAMILY LEAGUE" in i18n.get("daily_report_header")

        i18n = I18n("hu")
        assert "DUOLINGO CSALÁDI LIGA" in i18n.get("daily_report_header")

    def test_i18n_formatting(self):
        """Test translation string formatting"""
        i18n = I18n("en")
        result = i18n.get("day_streak", count=5)
        assert "5 day streak" in result

        result = i18n.get("days_streak", count=5)
        assert "5 days streak" in result

    def test_i18n_fallback_language(self):
        """Test fallback to English for unknown languages"""
        i18n = I18n("es")  # Spanish not implemented
        result = i18n.get("daily_report_header")
        assert "DUOLINGO FAMILY LEAGUE" in result  # Should fall back to English

    def test_i18n_missing_key(self):
        """Test behavior with missing translation keys"""
        i18n = I18n("en")
        result = i18n.get("nonexistent_key")
        assert result == "nonexistent_key"

    def test_i18n_set_language(self):
        """Test changing language"""
        i18n = I18n("en")
        i18n.set_language("hu")
        assert i18n.language == "hu"

        result = i18n.get("daily_report_header")
        assert "DUOLINGO CSALÁDI LIGA" in result

    def test_i18n_available_languages(self):
        """Test getting available languages"""
        i18n = I18n("en")
        languages = i18n.get_available_languages()
        assert "en" in languages
        assert "hu" in languages
        assert len(languages) == 2

    @patch.dict(os.environ, {"DUOLINGO_REPORT_LANGUAGE": "hu"})
    def test_get_language_from_env(self):
        """Test getting language from environment variable"""
        language = get_language_from_env()
        assert language == "hu"

    @patch.dict(os.environ, {}, clear=True)
    def test_get_language_from_env_default(self):
        """Test default language when env var not set"""
        language = get_language_from_env()
        assert language == "en"


class TestHtmlReportGeneration:
    """Test HTML report generation functionality"""

    @pytest.fixture
    def sample_results(self):
        """Sample results data for testing"""
        return {
            "Alice": {
                "username": "alice_duo",
                "streak": 15,
                "weekly_xp": 750,
                "total_xp": 12500,
                "weekly_xp_per_language": {"Spanish": 400, "French": 350},
                "language_progress": {
                    "Spanish": {"level": 8, "xp": 3200},
                    "French": {"level": 5, "xp": 1800},
                },
            },
            "Bob": {
                "username": "bob_duo",
                "streak": 8,
                "weekly_xp": 420,
                "total_xp": 8400,
                "weekly_xp_per_language": {"German": 420},
                "language_progress": {"German": {"level": 6, "xp": 2400}},
            },
            "Charlie": {"error": "Profile not found"},
        }

    @pytest.fixture
    def sample_goals(self):
        """Sample goals data for testing"""
        return {"streak_goal": 7, "weekly_xp_goal": 500}

    def test_generate_daily_html_report(self, sample_results):
        """Test daily HTML report generation"""
        with patch("src.html_report_generator.get_i18n") as mock_i18n:
            mock_i18n_instance = I18n("en")
            mock_i18n.return_value = mock_i18n_instance

            html_report = generate_daily_html_report(sample_results)

            # Check HTML structure
            assert "<!DOCTYPE html>" in html_report
            assert '<html lang="en">' in html_report
            assert "DUOLINGO FAMILY LEAGUE - DAILY UPDATE" in html_report
            assert "Alice" in html_report
            assert "Bob" in html_report
            assert "15 days streak" in html_report
            assert "750 weekly XP" in html_report
            assert "Spanish +400, French +350" in html_report

            # Should not include error user in leaderboard
            assert "Charlie" not in html_report

    def test_generate_daily_html_report_hungarian(self, sample_results):
        """Test daily HTML report generation in Hungarian"""
        with patch("src.html_report_generator.get_i18n") as mock_i18n:
            mock_i18n_instance = I18n("hu")
            mock_i18n.return_value = mock_i18n_instance

            html_report = generate_daily_html_report(sample_results)

            assert '<html lang="hu">' in html_report
            assert "DUOLINGO CSALÁDI LIGA" in html_report
            assert "napos sorozat" in html_report
            assert "heti XP" in html_report

    def test_generate_daily_html_report_with_broken_streaks(self):
        """Test daily report with broken streaks"""
        results_with_broken_streak = {
            "Alice": {
                "username": "alice_duo",
                "streak": 0,  # Broken streak
                "weekly_xp": 100,
                "total_xp": 5000,
                "weekly_xp_per_language": {},
            }
        }

        with patch("src.html_report_generator.get_i18n") as mock_i18n:
            mock_i18n_instance = I18n("en")
            mock_i18n.return_value = mock_i18n_instance

            html_report = generate_daily_html_report(results_with_broken_streak)

            assert "needs to practice today!" in html_report
            assert "alert warning" in html_report

    def test_generate_weekly_html_report(self, sample_results, sample_goals):
        """Test weekly HTML report generation"""
        with patch("src.html_report_generator.get_i18n") as mock_i18n:
            mock_i18n_instance = I18n("en")
            mock_i18n.return_value = mock_i18n_instance

            html_report = generate_weekly_html_report(sample_results, sample_goals)

            # Check HTML structure
            assert "<!DOCTYPE html>" in html_report
            assert '<html lang="en">' in html_report
            assert "DUOLINGO FAMILY LEAGUE - WEEKLY REPORT" in html_report
            assert "FAMILY LEADERBOARD" in html_report
            assert "DETAILED PROGRESS" in html_report
            assert "THIS WEEK'S FAMILY GOALS" in html_report

            # Check leaderboard order (Alice should be first with highest streak and XP)
            alice_pos = html_report.find("Alice")
            bob_pos = html_report.find("Bob")
            assert alice_pos < bob_pos  # Alice should appear before Bob

            # Check goal achievements
            assert "STREAK GOAL ACHIEVED" in html_report  # Alice has 15-day streak
            assert "WEEKLY XP GOAL ACHIEVED" in html_report  # Alice has 750 XP

            # Check error handling for Charlie
            assert "Unable to check progress: Profile not found" in html_report

    def test_generate_weekly_html_report_hungarian(self, sample_results, sample_goals):
        """Test weekly HTML report generation in Hungarian"""
        with patch("src.html_report_generator.get_i18n") as mock_i18n:
            mock_i18n_instance = I18n("hu")
            mock_i18n.return_value = mock_i18n_instance

            html_report = generate_weekly_html_report(sample_results, sample_goals)

            assert '<html lang="hu">' in html_report
            assert "DUOLINGO CSALÁDI LIGA" in html_report
            assert "CSALÁDI RANGLISTA" in html_report
            assert "RÉSZLETES ELŐREHALADÁS" in html_report
            assert "SOROZAT CÉL TELJESÍTVE" in html_report

    def test_report_generator_wrapper_functions(self, sample_results, sample_goals):
        """Test the wrapper functions in report_generator.py"""
        with patch(
            "src.html_report_generator.generate_daily_html_report"
        ) as mock_daily:
            mock_daily.return_value = "<html>daily</html>"

            result = generate_daily_report_html(sample_results)
            assert result == "<html>daily</html>"
            mock_daily.assert_called_once_with(sample_results)

        with patch(
            "src.html_report_generator.generate_weekly_html_report"
        ) as mock_weekly:
            mock_weekly.return_value = "<html>weekly</html>"

            result = generate_weekly_report_html(sample_results, sample_goals)
            assert result == "<html>weekly</html>"
            mock_weekly.assert_called_once_with(sample_results, sample_goals)


class TestHtmlTemplates:
    """Test HTML template functionality"""

    def test_daily_template_contains_required_elements(self):
        """Test that daily template contains all required placeholders"""
        from src.html_templates import DAILY_REPORT_TEMPLATE

        required_placeholders = [
            "{lang}",
            "{title}",
            "{header}",
            "{subtitle}",
            "{date}",
            "{standings_title}",
            "{leaderboard_items}",
            "{streak_alerts_title}",
            "{streak_alerts}",
            "{footer_message}",
        ]

        for placeholder in required_placeholders:
            assert placeholder in DAILY_REPORT_TEMPLATE

        # Check CSS is included
        assert "font-family:" in DAILY_REPORT_TEMPLATE
        assert ".container" in DAILY_REPORT_TEMPLATE
        assert ".leaderboard" in DAILY_REPORT_TEMPLATE

    def test_weekly_template_contains_required_elements(self):
        """Test that weekly template contains all required placeholders"""
        from src.html_templates import WEEKLY_REPORT_TEMPLATE

        required_placeholders = [
            "{lang}",
            "{title}",
            "{header}",
            "{subtitle}",
            "{week_ending}",
            "{generated_date}",
            "{family_leaderboard_title}",
            "{leaderboard_items}",
            "{detailed_progress_title}",
            "{member_details}",
            "{goals_title}",
            "{goals_list}",
            "{keep_up_message}",
            "{footer_message}",
        ]

        for placeholder in required_placeholders:
            assert placeholder in WEEKLY_REPORT_TEMPLATE

        # Check CSS classes for styling
        assert ".leaderboard-item.first" in WEEKLY_REPORT_TEMPLATE
        assert ".status-badge.achieved" in WEEKLY_REPORT_TEMPLATE
        assert ".goals-section" in WEEKLY_REPORT_TEMPLATE


class TestDateFormatting:
    """Test date formatting in different languages"""

    @patch("src.html_report_generator.datetime")
    def test_date_formatting_english(self, mock_datetime):
        """Test date formatting in English"""
        mock_datetime.now.return_value = datetime(2025, 8, 8, 14, 30, 0)
        mock_datetime.strftime = datetime.strftime

        with patch("src.html_report_generator.get_i18n") as mock_i18n:
            mock_i18n_instance = I18n("en")
            mock_i18n.return_value = mock_i18n_instance

            results = {
                "Alice": {
                    "username": "alice",
                    "streak": 5,
                    "weekly_xp": 100,
                    "total_xp": 1000,
                }
            }
            html_report = generate_daily_html_report(results)

            assert "2025-08-08" in html_report

    @patch("src.html_report_generator.datetime")
    def test_date_formatting_hungarian(self, mock_datetime):
        """Test date formatting in Hungarian"""
        mock_datetime.now.return_value = datetime(2025, 8, 8, 14, 30, 0)
        mock_datetime.strftime = datetime.strftime

        with patch("src.html_report_generator.get_i18n") as mock_i18n:
            mock_i18n_instance = I18n("hu")
            mock_i18n.return_value = mock_i18n_instance

            results = {
                "Alice": {
                    "username": "alice",
                    "streak": 5,
                    "weekly_xp": 100,
                    "total_xp": 1000,
                }
            }
            html_report = generate_daily_html_report(results)

            # Hungarian date format includes dots
            assert "2025. 08. 08." in html_report


class TestEdgeCases:
    """Test edge cases and error conditions"""

    def test_empty_results(self):
        """Test HTML generation with empty results"""
        with patch("src.html_report_generator.get_i18n") as mock_i18n:
            mock_i18n_instance = I18n("en")
            mock_i18n.return_value = mock_i18n_instance

            html_report = generate_daily_html_report({})

            assert "<!DOCTYPE html>" in html_report
            assert "Everyone is maintaining their streaks!" in html_report

    def test_single_day_streak_formatting(self):
        """Test singular vs plural streak formatting"""
        results = {
            "Alice": {
                "username": "alice",
                "streak": 1,  # Single day
                "weekly_xp": 100,
                "total_xp": 1000,
            }
        }

        with patch("src.html_report_generator.get_i18n") as mock_i18n:
            mock_i18n_instance = I18n("en")
            mock_i18n.return_value = mock_i18n_instance

            html_report = generate_daily_html_report(results)

            # Should use singular "day"
            assert "1 day streak" in html_report
            assert "1 days streak" not in html_report

    def test_formatting_error_handling(self):
        """Test that formatting errors don't crash the system"""
        i18n = I18n("en")

        # Test with missing format parameter
        result = i18n.get("day_streak")  # Missing count parameter
        assert result == "{count} day streak"  # Should return unformatted string

        # Test with extra parameters
        result = i18n.get("day_streak", count=5, extra_param="ignored")
        assert "5 day streak" in result

    def test_global_language_functions(self):
        """Test global i18n functions"""
        # Test setting global language
        set_global_language("hu")
        from src.i18n import get_i18n

        i18n = get_i18n()
        assert i18n.language == "hu"

        # Reset to English
        set_global_language("en")
        i18n = get_i18n()
        assert i18n.language == "en"

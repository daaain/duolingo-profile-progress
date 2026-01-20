"""Tests for weekly XP calculation functionality"""

from datetime import datetime, timedelta
from unittest.mock import patch

import pytest

from src.duolingo_api import calculate_weekly_xp, calculate_weekly_xp_per_language


class TestWeeklyXPCalculation:
    """Test weekly XP calculation logic"""

    @pytest.fixture
    def mock_storage(self):
        """Mock DataStorage for testing"""
        with patch("src.data_storage.DataStorage") as MockStorage:
            yield MockStorage.return_value

    def test_weekly_xp_no_history(self, mock_storage):
        """Test weekly XP when no history exists"""
        mock_storage.load_history.return_value = []

        result = calculate_weekly_xp("testuser", 1000)

        assert result == 0

    def test_weekly_xp_with_previous_week_data(self, mock_storage):
        """Test weekly XP calculation with data from previous week"""
        today = datetime.now()
        last_sunday = today - timedelta(days=today.weekday() + 1)

        mock_storage.load_history.return_value = [
            {
                "date": last_sunday.strftime("%Y-%m-%d"),
                "results": {"testuser": {"username": "testuser", "total_xp": 5000}},
            }
        ]

        result = calculate_weekly_xp("testuser", 5500)

        assert result == 500

    def test_weekly_xp_current_week_only(self, mock_storage):
        """Test weekly XP when only current week data exists"""
        today = datetime.now()
        monday = today - timedelta(days=today.weekday())

        mock_storage.load_history.return_value = [
            {
                "date": monday.strftime("%Y-%m-%d"),
                "results": {"testuser": {"username": "testuser", "total_xp": 3000}},
            },
            {
                "date": today.strftime("%Y-%m-%d"),
                "results": {"testuser": {"username": "testuser", "total_xp": 3200}},
            },
        ]

        result = calculate_weekly_xp("testuser", 3200)

        assert result == 200

    def test_weekly_xp_first_day_of_week(self, mock_storage):
        """Test weekly XP on first day with no prior data"""
        today = datetime.now()
        monday = today - timedelta(days=today.weekday())

        mock_storage.load_history.return_value = [
            {
                "date": monday.strftime("%Y-%m-%d"),
                "results": {"testuser": {"username": "testuser", "total_xp": 1000}},
            }
        ]

        # Same XP as recorded = no progress yet
        result = calculate_weekly_xp("testuser", 1000)

        assert result == 0

    def test_weekly_xp_case_insensitive_username(self, mock_storage):
        """Test that username matching is case-insensitive"""
        today = datetime.now()
        last_week = today - timedelta(days=7)

        mock_storage.load_history.return_value = [
            {
                "date": last_week.strftime("%Y-%m-%d"),
                "results": {"TestUser": {"username": "TestUser", "total_xp": 2000}},
            }
        ]

        result = calculate_weekly_xp("testuser", 2500)

        assert result == 500

    def test_weekly_xp_username_with_spaces(self, mock_storage):
        """Test username matching with spaces converted to underscores"""
        today = datetime.now()
        monday = today - timedelta(days=today.weekday())

        mock_storage.load_history.return_value = [
            {
                "date": monday.strftime("%Y-%m-%d"),
                "results": {"test user": {"username": "test_user", "total_xp": 1500}},
            }
        ]

        result = calculate_weekly_xp("test_user", 1700)

        assert result == 200

    def test_weekly_xp_mixed_week_data(self, mock_storage):
        """Test with data from both current and previous weeks"""
        today = datetime.now()
        monday = today - timedelta(days=today.weekday())
        last_week = monday - timedelta(days=3)
        yesterday = today - timedelta(days=1)

        mock_storage.load_history.return_value = [
            {
                "date": last_week.strftime("%Y-%m-%d"),
                "results": {"testuser": {"username": "testuser", "total_xp": 4000}},
            },
            {
                "date": monday.strftime("%Y-%m-%d"),
                "results": {"testuser": {"username": "testuser", "total_xp": 4100}},
            },
            {
                "date": yesterday.strftime("%Y-%m-%d"),
                "results": {"testuser": {"username": "testuser", "total_xp": 4300}},
            },
        ]

        # Should use last week's Sunday data as baseline
        result = calculate_weekly_xp("testuser", 4500)

        assert result == 500  # 4500 - 4000

    def test_weekly_xp_user_not_found(self, mock_storage):
        """Test when user is not in history"""
        today = datetime.now()

        mock_storage.load_history.return_value = [
            {
                "date": today.strftime("%Y-%m-%d"),
                "results": {"otheruser": {"username": "otheruser", "total_xp": 1000}},
            }
        ]

        result = calculate_weekly_xp("testuser", 5000)

        assert result == 0

    def test_weekly_xp_negative_protection(self, mock_storage):
        """Test that weekly XP never goes negative"""
        today = datetime.now()
        monday = today - timedelta(days=today.weekday())

        mock_storage.load_history.return_value = [
            {
                "date": monday.strftime("%Y-%m-%d"),
                "results": {"testuser": {"username": "testuser", "total_xp": 5000}},
            }
        ]

        # Current XP less than historical (shouldn't happen but test protection)
        result = calculate_weekly_xp("testuser", 4000)

        assert result == 0  # max(0, 4000 - 5000) = 0

    def test_weekly_xp_exception_handling(self, mock_storage):
        """Test exception handling in weekly XP calculation"""
        mock_storage.load_history.side_effect = Exception("Database error")

        result = calculate_weekly_xp("testuser", 1000)

        assert result == 0

    def test_weekly_xp_with_actual_data_structure(self, mock_storage):
        """Test with actual data structure from the application"""
        today = datetime.now()
        yesterday = today - timedelta(days=1)

        mock_storage.load_history.return_value = [
            {
                "date": yesterday.strftime("%Y-%m-%d"),
                "timestamp": yesterday.isoformat(),
                "results": {
                    "daaain": {
                        "username": "daaain",
                        "name": "Daniel",
                        "streak": 288,
                        "total_xp": 181289,
                        "weekly_xp": 0,
                        "active_languages": ["Spanish", "French"],
                        "language_progress": {
                            "Spanish": {
                                "xp": 180932,
                                "from_language": "en",
                                "learning_language": "es",
                            }
                        },
                    }
                },
            },
            {
                "date": today.strftime("%Y-%m-%d"),
                "timestamp": today.isoformat(),
                "results": {
                    "daaain": {
                        "username": "daaain",
                        "name": "Daniel",
                        "streak": 289,
                        "total_xp": 181946,
                        "weekly_xp": 0,
                        "active_languages": ["Spanish", "French"],
                        "language_progress": {
                            "Spanish": {
                                "xp": 181589,
                                "from_language": "en",
                                "learning_language": "es",
                            }
                        },
                    }
                },
            },
        ]

        result = calculate_weekly_xp("daaain", 181946)

        assert result == 657  # 181946 - 181289


class TestWeeklyXPPerLanguage:
    """Test per-language weekly XP calculation"""

    @pytest.fixture
    def mock_storage(self):
        """Mock DataStorage for testing"""
        with patch("src.data_storage.DataStorage") as MockStorage:
            yield MockStorage.return_value

    def test_weekly_xp_per_language_no_history(self, mock_storage):
        """Test weekly XP per language when no history exists"""
        mock_storage.load_history.return_value = []

        current_languages = {
            "Spanish": {"xp": 5000, "from_language": "en", "learning_language": "es"},
            "French": {"xp": 2000, "from_language": "en", "learning_language": "fr"},
        }

        result = calculate_weekly_xp_per_language("testuser", current_languages)

        assert result == {}

    def test_weekly_xp_per_language_with_baseline(self, mock_storage):
        """Test weekly XP per language with baseline data"""
        today = datetime.now()
        last_sunday = today - timedelta(days=today.weekday() + 1)

        mock_storage.load_history.return_value = [
            {
                "date": last_sunday.strftime("%Y-%m-%d"),
                "results": {
                    "testuser": {
                        "username": "testuser",
                        "language_progress": {
                            "Spanish": {
                                "xp": 4500,
                                "from_language": "en",
                                "learning_language": "es",
                            },
                            "French": {
                                "xp": 1800,
                                "from_language": "en",
                                "learning_language": "fr",
                            },
                        },
                    }
                },
            }
        ]

        current_languages = {
            "Spanish": {"xp": 5000, "from_language": "en", "learning_language": "es"},
            "French": {"xp": 2000, "from_language": "en", "learning_language": "fr"},
        }

        result = calculate_weekly_xp_per_language("testuser", current_languages)

        assert result["Spanish"] == 500  # 5000 - 4500
        assert result["French"] == 200  # 2000 - 1800

    def test_weekly_xp_per_language_new_language(self, mock_storage):
        """Test weekly XP when a new language is started this week"""
        today = datetime.now()
        monday = today - timedelta(days=today.weekday())

        mock_storage.load_history.return_value = [
            {
                "date": monday.strftime("%Y-%m-%d"),
                "results": {
                    "testuser": {
                        "username": "testuser",
                        "language_progress": {
                            "Spanish": {
                                "xp": 4500,
                                "from_language": "en",
                                "learning_language": "es",
                            }
                        },
                    }
                },
            }
        ]

        current_languages = {
            "Spanish": {"xp": 5000, "from_language": "en", "learning_language": "es"},
            "French": {"xp": 200},  # New language
            "German": {
                "xp": 150,
                "from_language": "en",
                "learning_language": "de",
            },  # Another new language
        }

        result = calculate_weekly_xp_per_language("testuser", current_languages)

        assert result["Spanish"] == 500  # 5000 - 4500
        assert result["French"] == 200  # All XP is new
        assert result["German"] == 150  # All XP is new

    def test_weekly_xp_per_language_no_progress(self, mock_storage):
        """Test when no progress was made in any language"""
        today = datetime.now()
        yesterday = today - timedelta(days=1)

        mock_storage.load_history.return_value = [
            {
                "date": yesterday.strftime("%Y-%m-%d"),
                "results": {
                    "testuser": {
                        "username": "testuser",
                        "language_progress": {
                            "Spanish": {
                                "xp": 5000,
                                "from_language": "en",
                                "learning_language": "es",
                            },
                            "French": {
                                "xp": 2000,
                                "from_language": "en",
                                "learning_language": "fr",
                            },
                        },
                    }
                },
            }
        ]

        current_languages = {
            "Spanish": {"xp": 5000, "from_language": "en", "learning_language": "es"},
            "French": {"xp": 2000, "from_language": "en", "learning_language": "fr"},
        }

        result = calculate_weekly_xp_per_language("testuser", current_languages)

        assert result["Spanish"] == 0
        assert result["French"] == 0

    def test_weekly_xp_per_language_with_actual_data(self, mock_storage):
        """Test with actual application data structure"""
        today = datetime.now()
        yesterday = today - timedelta(days=1)

        mock_storage.load_history.return_value = [
            {
                "date": yesterday.strftime("%Y-%m-%d"),
                "results": {
                    "daaain": {
                        "username": "daaain",
                        "language_progress": {
                            "Spanish": {
                                "xp": 180932,
                                "from_language": "en",
                                "learning_language": "es",
                            },
                            "French": {
                                "xp": 357,
                                "from_language": "en",
                                "learning_language": "fr",
                            },
                        },
                    }
                },
            }
        ]

        current_languages = {
            "Spanish": {
                "level": 9999,
                "xp": 181589,
                "from_language": "en",
                "learning_language": "es",
            },
            "French": {
                "level": 9999,
                "xp": 357,
                "from_language": "en",
                "learning_language": "fr",
            },
        }

        result = calculate_weekly_xp_per_language("daaain", current_languages)

        assert result["Spanish"] == 657  # 181589 - 180932
        assert result["French"] == 0  # 357 - 357


class TestReferenceDateParameter:
    """Test reference_date parameter for weekly XP calculations"""

    def test_calculate_weekly_xp_with_reference_date_shifts_week_boundary(self):
        """Test that reference_date shifts the week boundary correctly.

        When the weekly report runs on Monday morning (e.g., Jan 19),
        using reference_date = yesterday (Sunday Jan 18) should use
        the week starting Jan 12, not Jan 19.
        """
        # Simulate data collected during the previous week
        history = [
            {
                "date": "2026-01-11",  # Saturday before the week
                "results": {
                    "cheezegamer": {"username": "cheezegamer", "total_xp": 28272}
                },
            },
            {
                "date": "2026-01-13",  # Monday of the week
                "results": {
                    "cheezegamer": {"username": "cheezegamer", "total_xp": 28295}
                },
            },
            {
                "date": "2026-01-15",  # Wednesday
                "results": {
                    "cheezegamer": {"username": "cheezegamer", "total_xp": 28570}
                },
            },
            {
                "date": "2026-01-18",  # Sunday (end of week)
                "results": {
                    "cheezegamer": {"username": "cheezegamer", "total_xp": 28570}
                },
            },
        ]

        current_total_xp = 28570  # Same as Sunday's XP

        # Without reference_date on Monday Jan 19: week_start = Jan 19
        # Baseline would be Jan 18 (28570), result = 28570 - 28570 = 0
        monday_jan_19 = datetime(2026, 1, 19)
        result_without_ref = calculate_weekly_xp(
            "cheezegamer",
            current_total_xp,
            history,
            reference_date=monday_jan_19,
        )
        assert result_without_ref == 0  # BUG: Reports 0 because baseline is same day

        # With reference_date = Sunday Jan 18: week_start = Jan 12
        # Baseline should be Jan 11 (28272), result = 28570 - 28272 = 298
        sunday_jan_18 = datetime(2026, 1, 18)
        result_with_ref = calculate_weekly_xp(
            "cheezegamer",
            current_total_xp,
            history,
            reference_date=sunday_jan_18,
        )
        assert result_with_ref == 298  # CORRECT: Uses previous week's baseline

    def test_calculate_weekly_xp_per_language_with_reference_date(self):
        """Test that reference_date works correctly for per-language XP."""
        history = [
            {
                "date": "2026-01-11",  # Saturday before the week
                "results": {
                    "testuser": {
                        "username": "testuser",
                        "language_progress": {
                            "Spanish": {"xp": 5000},
                            "French": {"xp": 2000},
                        },
                    }
                },
            },
            {
                "date": "2026-01-15",  # Wednesday
                "results": {
                    "testuser": {
                        "username": "testuser",
                        "language_progress": {
                            "Spanish": {"xp": 5500},
                            "French": {"xp": 2200},
                        },
                    }
                },
            },
        ]

        current_languages = {
            "Spanish": {"xp": 5500, "from_language": "en", "learning_language": "es"},
            "French": {"xp": 2200, "from_language": "en", "learning_language": "fr"},
        }

        # With reference_date = Sunday Jan 18: week_start = Jan 12
        # Baseline should be Jan 11
        sunday_jan_18 = datetime(2026, 1, 18)
        result = calculate_weekly_xp_per_language(
            "testuser",
            current_languages,
            history,
            reference_date=sunday_jan_18,
        )

        assert result["Spanish"] == 500  # 5500 - 5000
        assert result["French"] == 200  # 2200 - 2000

    def test_reference_date_none_uses_current_datetime(self):
        """Test that reference_date=None uses current datetime (default behavior)."""
        today = datetime.now()
        monday = today - timedelta(days=today.weekday())
        last_sunday = monday - timedelta(days=1)

        history = [
            {
                "date": last_sunday.strftime("%Y-%m-%d"),
                "results": {"testuser": {"username": "testuser", "total_xp": 1000}},
            }
        ]

        # Both should give the same result when reference_date=None
        result_none = calculate_weekly_xp(
            "testuser", 1500, history, reference_date=None
        )
        result_now = calculate_weekly_xp(
            "testuser", 1500, history, reference_date=datetime.now()
        )

        # Allow for minor timing differences
        assert result_none == result_now

    def test_mid_week_reference_date(self):
        """Test reference_date in the middle of a week."""
        history = [
            {
                "date": "2026-01-05",  # Sunday before
                "results": {"testuser": {"username": "testuser", "total_xp": 1000}},
            },
            {
                "date": "2026-01-08",  # Wednesday
                "results": {"testuser": {"username": "testuser", "total_xp": 1200}},
            },
        ]

        # Reference date = Thursday Jan 9
        # Week start = Monday Jan 6
        # Baseline should be Jan 5 (1000)
        thursday_jan_9 = datetime(2026, 1, 9)
        result = calculate_weekly_xp(
            "testuser", 1300, history, reference_date=thursday_jan_9
        )

        assert result == 300  # 1300 - 1000

"""Tests for weekly XP calculation functionality"""

from datetime import datetime, timedelta
from unittest.mock import patch

import pytest

from src.duolingo_api import (
    calculate_daily_xp,
    calculate_weekly_xp,
    calculate_weekly_xp_per_language,
    get_language_xp,
)


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
        # Pinned to a Wednesday: on a Monday "yesterday" falls in the previous week
        today = datetime(2026, 1, 14)
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

        # Monday's snapshot (taken early morning) holds the XP at the end of
        # Sunday, so it's the baseline rather than last week's data
        result = calculate_weekly_xp("testuser", 4500, reference_date=today)

        assert result == 400  # 4500 - 4100

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
        today = datetime(2026, 1, 14)
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

        # Language XP is compared, not Duolingo's totalXp
        result = calculate_weekly_xp("daaain", 181589, reference_date=today)

        assert result == 657  # 181589 - 180932


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
                "date": "2026-01-11",  # Sunday before the week
                "results": {
                    "cheezegamer": {"username": "cheezegamer", "total_xp": 28272}
                },
            },
            {
                "date": "2026-01-12",  # Monday of the week
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
        # Baseline should be Jan 12 (28295), result = 28570 - 28295 = 275
        sunday_jan_18 = datetime(2026, 1, 18)
        result_with_ref = calculate_weekly_xp(
            "cheezegamer",
            current_total_xp,
            history,
            reference_date=sunday_jan_18,
        )
        assert result_with_ref == 275  # CORRECT: Uses previous week's baseline

    def test_calculate_weekly_xp_per_language_with_reference_date(self):
        """Test that reference_date works correctly for per-language XP."""
        history = [
            {
                "date": "2026-01-11",  # Sunday before the week
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
        # No Monday snapshot, so the nearest one is used: Jan 11 rather than Jan 15
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
                "date": "2026-01-04",  # Sunday before
                "results": {"testuser": {"username": "testuser", "total_xp": 1000}},
            },
            {
                "date": "2026-01-08",  # Wednesday
                "results": {"testuser": {"username": "testuser", "total_xp": 1200}},
            },
        ]

        # Reference date = Thursday Jan 9
        # Week start = Monday Jan 5
        # Baseline should be Jan 4 (1000), the only snapshot near the week start
        thursday_jan_9 = datetime(2026, 1, 9)
        result = calculate_weekly_xp(
            "testuser", 1300, history, reference_date=thursday_jan_9
        )

        assert result == 300  # 1300 - 1000


class TestWeekBaseline:
    """Snapshots are taken in the early morning (the GitHub Action runs around
    00:30-07:00 UTC), so the one dated Monday holds the XP at the end of Sunday
    and is the start of the week. Values below are from the family gist."""

    @staticmethod
    def snapshot(date, spanish_xp):
        return {
            "date": date,
            "results": {
                "dius": {
                    "username": "dius",
                    "total_xp": spanish_xp,
                    "language_progress": {"Spanish": {"xp": spanish_xp}},
                }
            },
        }

    def test_monday_snapshot_is_baseline_not_sunday(self):
        """Using Sunday morning's snapshot made each week cover 8 days and
        counted every Sunday in two weekly reports."""
        history = [
            self.snapshot("2026-09-20", 67594),  # Sunday morning
            self.snapshot("2026-09-21", 67640),  # Monday morning
            self.snapshot("2026-09-24", 67875),
        ]

        result = calculate_weekly_xp(
            "dius", 68073, history, reference_date=datetime(2026, 9, 27)
        )

        assert result == 433  # 68073 - 67640

    def test_per_language_monday_snapshot_is_baseline(self):
        history = [
            self.snapshot("2026-09-20", 67594),
            self.snapshot("2026-09-21", 67640),
        ]

        result = calculate_weekly_xp_per_language(
            "dius",
            {"Spanish": {"xp": 68073}},
            history,
            reference_date=datetime(2026, 9, 27),
        )

        assert result == {"Spanish": 433}

    def test_missing_monday_uses_nearest_snapshot_before(self):
        history = [
            self.snapshot("2026-09-20", 67594),  # Sunday: 1 day off
            self.snapshot("2026-09-24", 67875),  # Thursday: 3 days off
        ]

        result = calculate_weekly_xp(
            "dius", 68073, history, reference_date=datetime(2026, 9, 27)
        )

        assert result == 479  # 68073 - 67594

    def test_missing_monday_prefers_later_snapshot_when_equally_near(self):
        """Prefer under-counting a day over counting it in two weekly reports"""
        history = [
            self.snapshot("2026-09-20", 67594),  # Sunday: 1 day off
            self.snapshot("2026-09-22", 67689),  # Tuesday: 1 day off
        ]

        result = calculate_weekly_xp(
            "dius", 68073, history, reference_date=datetime(2026, 9, 27)
        )

        assert result == 384  # 68073 - 67689

    def test_error_snapshot_is_not_a_baseline(self):
        """A failed fetch has no XP data and must not count as zero XP"""
        history = [
            self.snapshot("2026-09-20", 67594),
            {
                "date": "2026-09-21",
                "results": {
                    "dius": {
                        "username": "dius",
                        "error": "API request failed",
                        "language_progress": {},
                    }
                },
            },
        ]

        result = calculate_weekly_xp(
            "dius", 68073, history, reference_date=datetime(2026, 9, 27)
        )

        assert result == 479  # 68073 - 67594


class TestLanguageXP:
    """League XP is based on language courses only, not Duolingo's totalXp"""

    def test_get_language_xp_sums_courses(self):
        user_data = {
            "total_xp": 428273,
            "language_progress": {"Spanish": {"xp": 355317}, "French": {"xp": 357}},
        }
        assert get_language_xp(user_data) == 355674

    def test_get_language_xp_falls_back_to_total_xp(self):
        assert get_language_xp({"total_xp": 1000}) == 1000

    def test_get_language_xp_is_zero_without_courses(self):
        assert get_language_xp({"total_xp": 1000, "language_progress": {}}) == 0

    def test_weekly_xp_counts_first_course_started_this_week(self):
        """A member with no course XP at the week start has a language XP
        baseline of 0, not their total_xp."""
        history = [
            {
                "date": "2026-09-28",
                "results": {
                    "kid": {
                        "username": "kid",
                        "total_xp": 1000,
                        "language_progress": {},
                    }
                },
            }
        ]

        result = calculate_weekly_xp(
            "kid", 150, history, reference_date=datetime(2026, 10, 4)
        )

        assert result == 150

    def test_weekly_xp_ignores_non_language_total_xp_jump(self):
        """Duolingo's totalXp jumped by ~90k in October 2026 without course XP
        changing accordingly; that must not count as weekly XP."""
        history = [
            {
                "date": "2026-09-27",
                "results": {
                    "daniel": {
                        "username": "daaain",
                        "total_xp": 334786,
                        "language_progress": {"Spanish": {"xp": 334786}},
                    }
                },
            },
            {
                "date": "2026-10-02",
                "results": {
                    "daniel": {
                        "username": "daaain",
                        "total_xp": 425000,
                        "language_progress": {"Spanish": {"xp": 335500}},
                    }
                },
            },
        ]

        result = calculate_weekly_xp(
            "daaain", 336000, history, reference_date=datetime(2026, 10, 4)
        )

        assert result == 1214  # 336000 - 334786, total_xp ignored

    def test_daily_xp_uses_language_xp(self):
        yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        history = [
            {
                "date": yesterday,
                "results": {
                    "daniel": {
                        "username": "daaain",
                        "total_xp": 425000,
                        "language_progress": {"Spanish": {"xp": 335500}},
                    }
                },
            }
        ]

        assert calculate_daily_xp("daaain", 336000, history) == 500

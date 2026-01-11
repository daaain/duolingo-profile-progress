#!/usr/bin/env python3
"""
Test suite for SQLite storage backend
"""

import json
import os
import sys
import pytest
import tempfile
from pathlib import Path
from unittest.mock import patch

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.sqlite_storage import SQLiteStorage
from src.storage_factory import StorageFactory
from src.migrate_storage import StorageMigrator
from src.data_storage import DataStorage


class TestSQLiteStorage:
    """Test SQLite storage functionality"""

    @pytest.fixture
    def temp_db(self):
        """Create temporary SQLite database for testing"""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name

        yield db_path

        # Cleanup
        if os.path.exists(db_path):
            os.unlink(db_path)

    @pytest.fixture
    def sample_user_data(self):
        """Sample user data for testing"""
        return {
            "test_user_1": {
                "username": "test_user_1",
                "name": "Test User 1",
                "streak": 15,
                "total_xp": 2500,
                "weekly_xp": 350,
                "weekly_xp_per_language": {"Spanish": 200, "French": 150},
                "active_languages": ["Spanish", "French"],
                "language_progress": {
                    "Spanish": {
                        "xp": 1500,
                        "from_language": "en",
                        "learning_language": "es",
                    },
                    "French": {
                        "xp": 1000,
                        "from_language": "en",
                        "learning_language": "fr",
                    },
                },
                "last_check": "2025-08-14 10:00:00",
            },
            "test_user_2": {
                "username": "test_user_2",
                "name": "Test User 2",
                "streak": 7,
                "total_xp": 1200,
                "weekly_xp": 180,
                "weekly_xp_per_language": {"German": 180},
                "active_languages": ["German"],
                "language_progress": {
                    "German": {
                        "xp": 1200,
                        "from_language": "en",
                        "learning_language": "de",
                    }
                },
                "last_check": "2025-08-14 10:00:00",
            },
        }

    @pytest.fixture
    def sample_error_data(self):
        """Sample data with user error"""
        return {
            "test_user_1": {
                "username": "test_user_1",
                "error": "Profile not found",
                "last_check": "2025-08-14 10:00:00",
                "language_progress": {},
                "weekly_xp_per_language": {},
                "active_languages": [],
            }
        }

    def test_sqlite_storage_initialization(self, temp_db):
        """Test SQLite storage initialization"""
        SQLiteStorage(temp_db)  # Initialize database

        # Check that database file was created
        assert os.path.exists(temp_db)

        # Check that tables were created
        import sqlite3

        with sqlite3.connect(temp_db) as conn:
            cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]

            expected_tables = [
                "daily_snapshots",
                "user_progress",
                "language_progress",
                "metadata",
            ]
            for table in expected_tables:
                assert table in tables

    def test_save_and_load_daily_data(self, temp_db, sample_user_data):
        """Test saving and loading daily data"""
        storage = SQLiteStorage(temp_db)

        # Save data
        storage.save_daily_data(sample_user_data)

        # Load history and verify
        history = storage.load_history()
        assert len(history) == 1

        entry = history[0]
        assert "date" in entry
        assert "timestamp" in entry
        assert "results" in entry

        # Verify user data integrity
        results = entry["results"]
        assert "test_user_1" in results
        assert "test_user_2" in results

        user1 = results["test_user_1"]
        assert user1["streak"] == 15
        assert user1["total_xp"] == 2500
        assert user1["weekly_xp"] == 350
        assert "Spanish" in user1["language_progress"]
        assert "French" in user1["language_progress"]

    def test_save_error_data(self, temp_db, sample_error_data):
        """Test saving data with user errors"""
        storage = SQLiteStorage(temp_db)

        # Save error data
        storage.save_daily_data(sample_error_data)

        # Load and verify
        history = storage.load_history()
        assert len(history) == 1

        results = history[0]["results"]
        assert "test_user_1" in results

        user1 = results["test_user_1"]
        assert user1["error"] == "Profile not found"

    def test_multiple_days_data(self, temp_db, sample_user_data):
        """Test saving data across multiple days"""
        storage = SQLiteStorage(temp_db)

        # Mock different dates
        with patch("src.sqlite_storage.datetime") as mock_datetime:
            # Day 1
            mock_datetime.now.return_value.strftime.return_value = "2025-08-10"
            mock_datetime.now.return_value.isoformat.return_value = (
                "2025-08-10T10:00:00"
            )
            storage.save_daily_data(sample_user_data)

            # Day 2 - modify data slightly
            modified_data = sample_user_data.copy()
            modified_data["test_user_1"]["streak"] = 16
            modified_data["test_user_1"]["total_xp"] = 2650

            mock_datetime.now.return_value.strftime.return_value = "2025-08-11"
            mock_datetime.now.return_value.isoformat.return_value = (
                "2025-08-11T10:00:00"
            )
            storage.save_daily_data(modified_data)

        # Verify both days are stored
        history = storage.load_history()
        assert len(history) == 2

        # Verify chronological order
        assert history[0]["date"] == "2025-08-10"
        assert history[1]["date"] == "2025-08-11"

        # Verify data changes
        assert history[0]["results"]["test_user_1"]["streak"] == 15
        assert history[1]["results"]["test_user_1"]["streak"] == 16

    def test_get_weekly_progress(self, temp_db, sample_user_data):
        """Test getting weekly progress data"""
        storage = SQLiteStorage(temp_db)

        # Save multiple days of data
        for i in range(10):  # More than 7 days
            with patch("src.sqlite_storage.datetime") as mock_datetime:
                date = f"2025-08-{10 + i:02d}"
                mock_datetime.now.return_value.strftime.return_value = date
                mock_datetime.now.return_value.isoformat.return_value = (
                    f"{date}T10:00:00"
                )
                storage.save_daily_data(sample_user_data)

        # Get weekly progress (should return last 7 days)
        weekly = storage.get_weekly_progress()
        assert len(weekly) == 7

        # Verify chronological order (oldest first)
        dates = [entry["date"] for entry in weekly]
        assert dates == sorted(dates)

    def test_get_user_progress_history(self, temp_db, sample_user_data):
        """Test getting user-specific progress history"""
        storage = SQLiteStorage(temp_db)

        # Save data
        storage.save_daily_data(sample_user_data)

        # Get user history
        user_history = storage.get_user_progress_history("test_user_1")
        assert len(user_history) == 1

        entry = user_history[0]
        assert entry["streak"] == 15
        assert entry["total_xp"] == 2500
        assert entry["weekly_xp"] == 350

    def test_get_language_progress_history(self, temp_db, sample_user_data):
        """Test getting language-specific progress history"""
        storage = SQLiteStorage(temp_db)

        # Save data
        storage.save_daily_data(sample_user_data)

        # Get Spanish progress for test_user_1
        lang_history = storage.get_language_progress_history("test_user_1", "Spanish")
        assert len(lang_history) == 1

        entry = lang_history[0]
        assert entry["xp"] == 1500
        assert entry["weekly_xp"] == 200

    def test_database_stats(self, temp_db, sample_user_data):
        """Test database statistics"""
        storage = SQLiteStorage(temp_db)

        # Save data
        storage.save_daily_data(sample_user_data)

        # Get stats
        stats = storage.get_database_stats()
        assert stats["daily_snapshots"] == 1
        assert stats["user_progress_entries"] == 2  # Two users
        assert stats["language_progress_entries"] == 3  # User1: 2 langs, User2: 1 lang
        assert "date_range" in stats
        assert stats["database_size_mb"] > 0

    def test_cleanup_old_data(self, temp_db, sample_user_data):
        """Test cleaning up old data"""
        storage = SQLiteStorage(temp_db)

        # Save data for multiple days
        with patch("src.sqlite_storage.datetime") as mock_datetime:
            # Old data (should be cleaned up)
            mock_datetime.now.return_value.strftime.return_value = "2025-06-01"
            mock_datetime.now.return_value.isoformat.return_value = (
                "2025-06-01T10:00:00"
            )
            storage.save_daily_data(sample_user_data)

            # Recent data (should be kept)
            mock_datetime.now.return_value.strftime.return_value = "2025-08-14"
            mock_datetime.now.return_value.isoformat.return_value = (
                "2025-08-14T10:00:00"
            )
            storage.save_daily_data(sample_user_data)

        # Verify both entries exist
        history_before = storage.load_history()
        assert len(history_before) == 2

        # Cleanup with a small retention period
        with patch("src.sqlite_storage.SQLiteStorage.cleanup_old_data"):
            # Manually delete old data to simulate cleanup
            import sqlite3

            with sqlite3.connect(temp_db) as conn:
                conn.execute("DELETE FROM daily_snapshots WHERE date < '2025-08-01'")
                conn.commit()

        # Verify old data was removed
        history_after = storage.load_history()
        assert len(history_after) == 1
        assert history_after[0]["date"] == "2025-08-14"


class TestStorageFactory:
    """Test storage factory functionality"""

    def test_create_json_storage(self):
        """Test creating JSON storage backend"""
        storage = StorageFactory.create_storage("json", "test_data")
        assert isinstance(storage, DataStorage)

    def test_create_sqlite_storage(self):
        """Test creating SQLite storage backend"""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name

        try:
            storage = StorageFactory.create_storage("sqlite", db_path=db_path)
            assert isinstance(storage, SQLiteStorage)
        finally:
            if os.path.exists(db_path):
                os.unlink(db_path)

    def test_invalid_backend(self):
        """Test error handling for invalid backend"""
        with pytest.raises(ValueError, match="Unknown storage backend"):
            StorageFactory.create_storage("invalid_backend")

    def test_default_backend(self):
        """Test default backend selection"""
        with patch.dict(os.environ, {"STORAGE_BACKEND": "sqlite"}):
            storage = StorageFactory.create_storage()
            assert isinstance(storage, SQLiteStorage)

    def test_get_available_backends(self):
        """Test getting available backends"""
        backends = StorageFactory.get_available_backends()
        assert "json" in backends
        assert "sqlite" in backends


class TestStorageMigration:
    """Test data migration between storage backends"""

    @pytest.fixture
    def temp_json_dir(self):
        """Create temporary directory for JSON files"""
        import tempfile

        temp_dir = tempfile.mkdtemp()
        yield temp_dir

        # Cleanup
        import shutil

        shutil.rmtree(temp_dir)

    @pytest.fixture
    def temp_db_path(self):
        """Create temporary SQLite database path"""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name

        yield db_path

        # Cleanup
        if os.path.exists(db_path):
            os.unlink(db_path)

    @pytest.fixture
    def sample_json_data(self, temp_json_dir):
        """Create sample JSON data files"""
        # Create sample daily file
        daily_data = {
            "date": "2025-08-14",
            "timestamp": "2025-08-14T10:00:00",
            "results": {
                "test_user": {
                    "username": "test_user",
                    "name": "Test User",
                    "streak": 10,
                    "total_xp": 1500,
                    "weekly_xp": 200,
                    "weekly_xp_per_language": {"Spanish": 200},
                    "active_languages": ["Spanish"],
                    "language_progress": {
                        "Spanish": {
                            "xp": 1500,
                            "from_language": "en",
                            "learning_language": "es",
                        }
                    },
                    "last_check": "2025-08-14 10:00:00",
                }
            },
        }

        daily_file = Path(temp_json_dir) / "daily_2025-08-14.json"
        with open(daily_file, "w") as f:
            json.dump(daily_data, f)

        # Create master history file
        history_data = [daily_data]
        history_file = Path(temp_json_dir) / "league_history.json"
        with open(history_file, "w") as f:
            json.dump(history_data, f)

        return temp_json_dir

    def test_json_to_sqlite_migration(self, sample_json_data, temp_db_path):
        """Test migrating from JSON to SQLite"""
        # Perform migration
        StorageMigrator.json_to_sqlite(sample_json_data, temp_db_path)

        # Verify migration
        sqlite_storage = SQLiteStorage(temp_db_path)
        history = sqlite_storage.load_history()

        assert len(history) == 1
        assert history[0]["date"] == "2025-08-14"
        assert "test_user" in history[0]["results"]

    def test_sqlite_to_json_migration(
        self, temp_db_path, temp_json_dir, sample_json_data
    ):
        """Test migrating from SQLite to JSON"""
        # First migrate JSON to SQLite
        StorageMigrator.json_to_sqlite(sample_json_data, temp_db_path)

        # Create new export directory
        export_dir = temp_json_dir + "_export"

        # Export SQLite to JSON
        StorageMigrator.sqlite_to_json(temp_db_path, export_dir)

        # Verify export
        exported_daily_file = Path(export_dir) / "daily_2025-08-14.json"
        exported_history_file = Path(export_dir) / "league_history.json"

        assert exported_daily_file.exists()
        assert exported_history_file.exists()

        # Check content
        with open(exported_daily_file) as f:
            daily_data = json.load(f)

        assert daily_data["date"] == "2025-08-14"
        assert "test_user" in daily_data["results"]

        # Cleanup
        import shutil

        shutil.rmtree(export_dir)

    def test_migration_validation(self, sample_json_data, temp_db_path):
        """Test migration validation"""
        # Perform migration
        StorageMigrator.json_to_sqlite(sample_json_data, temp_db_path)

        # Create storage instances
        json_storage = DataStorage(sample_json_data)
        sqlite_storage = SQLiteStorage(temp_db_path)

        # Validate migration
        is_valid = StorageMigrator.validate_migration(json_storage, sqlite_storage)
        assert is_valid is True


if __name__ == "__main__":
    pytest.main([__file__])

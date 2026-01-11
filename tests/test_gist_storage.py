#!/usr/bin/env python3
"""
Test suite for Gist storage backend
"""

import json
import os
import sys
import pytest
from unittest.mock import Mock, patch

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.gist_storage import GistStorage
from src.storage_factory import StorageFactory


class TestGistStorage:
    """Test Gist storage functionality"""

    @pytest.fixture
    def mock_gist_response(self) -> dict:
        """Mock Gist API response with empty history"""
        return {
            "id": "test_gist_id",
            "files": {
                "league_history.json": {
                    "content": "[]",
                }
            },
        }

    @pytest.fixture
    def mock_gist_with_history(self) -> dict:
        """Mock Gist API response with existing history"""
        history = [
            {
                "date": "2025-08-13",
                "timestamp": "2025-08-13T10:00:00",
                "results": {
                    "test_user": {
                        "username": "test_user",
                        "name": "Test User",
                        "streak": 10,
                        "total_xp": 1500,
                        "weekly_xp": 200,
                    }
                },
            }
        ]
        return {
            "id": "test_gist_id",
            "files": {
                "league_history.json": {
                    "content": json.dumps(history),
                }
            },
        }

    @pytest.fixture
    def sample_user_data(self) -> dict:
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
            }
        }

    def test_gist_storage_requires_gist_id(self):
        """Test that GistStorage requires GIST_ID"""
        with patch.dict(os.environ, {"GIST_ID": "", "GITHUB_TOKEN": "test_token"}):
            with pytest.raises(ValueError, match="GIST_ID"):
                GistStorage(gist_id=None, github_token="test_token")

    def test_gist_storage_requires_github_token(self):
        """Test that GistStorage requires GITHUB_TOKEN"""
        with patch.dict(os.environ, {"GIST_ID": "test_id", "GITHUB_TOKEN": ""}):
            with pytest.raises(ValueError, match="GITHUB_TOKEN"):
                GistStorage(gist_id="test_id", github_token=None)

    def test_gist_storage_initialization(self):
        """Test GistStorage initialization with valid credentials"""
        storage = GistStorage(gist_id="test_id", github_token="test_token")
        assert storage.gist_id == "test_id"
        assert storage.github_token == "test_token"

    @patch("src.gist_storage.requests.get")
    def test_load_empty_history(self, mock_get, mock_gist_response):
        """Test loading empty history from Gist"""
        mock_get.return_value = Mock(status_code=200)
        mock_get.return_value.json.return_value = mock_gist_response
        mock_get.return_value.raise_for_status = Mock()

        storage = GistStorage(gist_id="test_id", github_token="test_token")
        history = storage.load_history()

        assert history == []
        mock_get.assert_called_once()

    @patch("src.gist_storage.requests.get")
    def test_load_existing_history(self, mock_get, mock_gist_with_history):
        """Test loading existing history from Gist"""
        mock_get.return_value = Mock(status_code=200)
        mock_get.return_value.json.return_value = mock_gist_with_history
        mock_get.return_value.raise_for_status = Mock()

        storage = GistStorage(gist_id="test_id", github_token="test_token")
        history = storage.load_history()

        assert len(history) == 1
        assert history[0]["date"] == "2025-08-13"
        assert "test_user" in history[0]["results"]

    @patch("src.gist_storage.requests.patch")
    @patch("src.gist_storage.requests.get")
    def test_save_daily_data(
        self, mock_get, mock_patch, mock_gist_response, sample_user_data
    ):
        """Test saving daily data to Gist"""
        mock_get.return_value = Mock(status_code=200)
        mock_get.return_value.json.return_value = mock_gist_response
        mock_get.return_value.raise_for_status = Mock()

        mock_patch.return_value = Mock(status_code=200)
        mock_patch.return_value.raise_for_status = Mock()

        storage = GistStorage(gist_id="test_id", github_token="test_token")

        with patch("src.gist_storage.datetime") as mock_datetime:
            mock_datetime.now.return_value.strftime.return_value = "2025-08-14"
            mock_datetime.now.return_value.isoformat.return_value = (
                "2025-08-14T10:00:00"
            )
            storage.save_daily_data(sample_user_data)

        # Verify PATCH was called with correct data
        mock_patch.assert_called_once()
        call_args = mock_patch.call_args
        payload = call_args.kwargs["json"]

        assert "files" in payload
        assert "league_history.json" in payload["files"]

        # Parse the saved content
        saved_content = json.loads(payload["files"]["league_history.json"]["content"])
        assert len(saved_content) == 1
        assert saved_content[0]["date"] == "2025-08-14"
        assert "test_user_1" in saved_content[0]["results"]

    @patch("src.gist_storage.requests.patch")
    @patch("src.gist_storage.requests.get")
    def test_save_daily_data_replaces_same_day(
        self, mock_get, mock_patch, mock_gist_with_history, sample_user_data
    ):
        """Test that saving data for the same day replaces existing entry"""
        mock_get.return_value = Mock(status_code=200)
        mock_get.return_value.json.return_value = mock_gist_with_history
        mock_get.return_value.raise_for_status = Mock()

        mock_patch.return_value = Mock(status_code=200)
        mock_patch.return_value.raise_for_status = Mock()

        storage = GistStorage(gist_id="test_id", github_token="test_token")

        # Save data for the same date as existing history (2025-08-13)
        with patch("src.gist_storage.datetime") as mock_datetime:
            mock_datetime.now.return_value.strftime.return_value = "2025-08-13"
            mock_datetime.now.return_value.isoformat.return_value = (
                "2025-08-13T15:00:00"
            )
            storage.save_daily_data(sample_user_data)

        # Verify the saved content only has one entry (replaced, not appended)
        call_args = mock_patch.call_args
        payload = call_args.kwargs["json"]
        saved_content = json.loads(payload["files"]["league_history.json"]["content"])

        assert len(saved_content) == 1
        assert saved_content[0]["date"] == "2025-08-13"
        # Should have the new data, not the old
        assert "test_user_1" in saved_content[0]["results"]

    @patch("src.gist_storage.requests.get")
    def test_get_weekly_progress(self, mock_get):
        """Test getting weekly progress from Gist"""
        # Create history with 10 days of data
        history = []
        for i in range(10):
            history.append(
                {
                    "date": f"2025-08-{5 + i:02d}",
                    "timestamp": f"2025-08-{5 + i:02d}T10:00:00",
                    "results": {"test_user": {"streak": i}},
                }
            )

        mock_response = {
            "id": "test_gist_id",
            "files": {
                "league_history.json": {
                    "content": json.dumps(history),
                }
            },
        }
        mock_get.return_value = Mock(status_code=200)
        mock_get.return_value.json.return_value = mock_response
        mock_get.return_value.raise_for_status = Mock()

        storage = GistStorage(gist_id="test_id", github_token="test_token")
        weekly = storage.get_weekly_progress()

        # Should return last 7 entries
        assert len(weekly) == 7
        # Should be the most recent 7 days
        assert weekly[0]["date"] == "2025-08-08"
        assert weekly[-1]["date"] == "2025-08-14"

    @patch("src.gist_storage.requests.get")
    def test_cache_is_used(self, mock_get, mock_gist_with_history):
        """Test that history is cached and not re-fetched unnecessarily"""
        mock_get.return_value = Mock(status_code=200)
        mock_get.return_value.json.return_value = mock_gist_with_history
        mock_get.return_value.raise_for_status = Mock()

        storage = GistStorage(gist_id="test_id", github_token="test_token")

        # First call should fetch from API
        storage.load_history()
        assert mock_get.call_count == 1

        # Second call should use cache
        storage.load_history()
        assert mock_get.call_count == 1

        # Clear cache and call again
        storage.clear_cache()
        storage.load_history()
        assert mock_get.call_count == 2

    @patch("src.gist_storage.requests.get")
    def test_handles_missing_file(self, mock_get):
        """Test handling when the Gist file doesn't exist yet"""
        mock_response = {
            "id": "test_gist_id",
            "files": {},  # No files
        }
        mock_get.return_value = Mock(status_code=200)
        mock_get.return_value.json.return_value = mock_response
        mock_get.return_value.raise_for_status = Mock()

        storage = GistStorage(gist_id="test_id", github_token="test_token")
        history = storage.load_history()

        assert history == []

    @patch("src.gist_storage.requests.get")
    def test_handles_invalid_json(self, mock_get):
        """Test handling invalid JSON in Gist file"""
        mock_response = {
            "id": "test_gist_id",
            "files": {
                "league_history.json": {
                    "content": "not valid json",
                }
            },
        }
        mock_get.return_value = Mock(status_code=200)
        mock_get.return_value.json.return_value = mock_response
        mock_get.return_value.raise_for_status = Mock()

        storage = GistStorage(gist_id="test_id", github_token="test_token")
        history = storage.load_history()

        # Should return empty list on invalid JSON
        assert history == []

    def test_update_history_is_noop(self):
        """Test that update_history is a no-op for Gist storage"""
        storage = GistStorage(gist_id="test_id", github_token="test_token")
        # Should not raise any errors
        storage.update_history({"test": "data"})


class TestStorageFactoryGist:
    """Test storage factory with Gist backend"""

    def test_create_gist_storage(self):
        """Test creating Gist storage via factory"""
        storage = StorageFactory.create_storage(
            "gist", gist_id="test_id", github_token="test_token"
        )
        assert isinstance(storage, GistStorage)

    def test_create_gist_storage_from_env(self):
        """Test creating Gist storage from environment variables"""
        with patch.dict(
            os.environ,
            {
                "STORAGE_BACKEND": "gist",
                "GIST_ID": "env_gist_id",
                "GITHUB_TOKEN": "env_token",
            },
        ):
            storage = StorageFactory.create_storage()
            assert isinstance(storage, GistStorage)
            assert storage.gist_id == "env_gist_id"

    def test_gist_in_available_backends(self):
        """Test that gist is listed as available backend"""
        backends = StorageFactory.get_available_backends()
        assert "gist" in backends


if __name__ == "__main__":
    pytest.main([__file__])

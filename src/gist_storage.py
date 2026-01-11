"""Gist storage backend for Duolingo Family League data

Stores league history in a GitHub Gist for serverless deployments.
"""

import json
import os
from datetime import datetime
from typing import Any

import requests

from .storage_interface import StorageInterface


class GistStorage(StorageInterface):
    """GitHub Gist-based storage for serverless deployments"""

    GIST_FILENAME = "league_history.json"

    def __init__(
        self,
        gist_id: str | None = None,
        github_token: str | None = None,
    ) -> None:
        self.gist_id = gist_id or os.getenv("GIST_ID")
        self.github_token = github_token or os.getenv("GITHUB_TOKEN")

        if not self.gist_id:
            raise ValueError(
                "GIST_ID environment variable or gist_id parameter required"
            )
        if not self.github_token:
            raise ValueError(
                "GITHUB_TOKEN environment variable or github_token parameter required"
            )

        self._api_base = "https://api.github.com"
        self._history_cache: list[dict[str, Any]] | None = None

    def _get_headers(self) -> dict[str, str]:
        """Get headers for GitHub API requests"""
        return {
            "Authorization": f"Bearer {self.github_token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }

    def _fetch_gist(self) -> dict[str, Any]:
        """Fetch the gist content from GitHub"""
        url = f"{self._api_base}/gists/{self.gist_id}"
        response = requests.get(url, headers=self._get_headers(), timeout=30)
        response.raise_for_status()
        return response.json()

    def _update_gist(self, history: list[dict[str, Any]]) -> None:
        """Update the gist with new history data"""
        url = f"{self._api_base}/gists/{self.gist_id}"
        payload = {
            "files": {
                self.GIST_FILENAME: {
                    "content": json.dumps(history, indent=2),
                }
            }
        }
        response = requests.patch(
            url, headers=self._get_headers(), json=payload, timeout=30
        )
        response.raise_for_status()
        # Clear cache after update
        self._history_cache = None

    def _get_history_from_gist(self) -> list[dict[str, Any]]:
        """Get history data from the gist"""
        if self._history_cache is not None:
            return self._history_cache

        gist = self._fetch_gist()
        files = gist.get("files", {})
        history_file = files.get(self.GIST_FILENAME)

        if not history_file:
            # File doesn't exist yet, return empty history
            return []

        content = history_file.get("content", "[]")
        try:
            history: list[dict[str, Any]] = json.loads(content)
            self._history_cache = history
            return history
        except json.JSONDecodeError:
            # Invalid JSON, start fresh
            return []

    def save_daily_data(self, results: dict[str, Any]) -> None:
        """Save daily progress data to Gist"""
        today = datetime.now().strftime("%Y-%m-%d")
        timestamp = datetime.now().isoformat()

        # Load existing history
        history = self._get_history_from_gist()

        # Create new entry
        entry = {
            "date": today,
            "timestamp": timestamp,
            "results": results,
        }

        # Remove existing entry for today if present
        history = [h for h in history if h.get("date") != today]
        history.append(entry)

        # Sort by date
        history = sorted(history, key=lambda x: x.get("date", ""))

        # Update gist
        self._update_gist(history)
        print(f"Daily data saved to Gist: {self.gist_id}")

    def update_history(self, results: dict[str, Any]) -> None:
        """Update history - for Gist this is handled by save_daily_data"""
        # In Gist storage, history is automatically maintained through save_daily_data
        # This method exists for compatibility with the StorageInterface
        pass

    def load_history(self) -> list[dict[str, Any]]:
        """Load historical data from Gist"""
        return self._get_history_from_gist()

    def get_weekly_progress(self) -> list[dict[str, Any]]:
        """Get progress data for the current week"""
        history = self._get_history_from_gist()
        if not history:
            return []

        # Get last 7 days of data
        return history[-7:]

    def clear_cache(self) -> None:
        """Clear the history cache to force a fresh fetch"""
        self._history_cache = None

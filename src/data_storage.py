"""Data storage and history management for Duolingo Family League"""

import json
from datetime import datetime
from pathlib import Path


class DataStorage:
    def __init__(self, data_dir="league_data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)

    def save_daily_data(self, results):
        """Save daily progress data"""
        today = datetime.now().strftime("%Y-%m-%d")
        daily_file = self.data_dir / f"daily_{today}.json"

        daily_data = {
            "date": today,
            "timestamp": datetime.now().isoformat(),
            "results": results,
        }

        with open(daily_file, "w") as f:
            json.dump(daily_data, f, indent=2)

        print(f"Daily data saved to {daily_file}")

        # Also update the master history file
        self.update_history(results)

    def update_history(self, results):
        """Update the master history file with daily data"""
        history_file = self.data_dir / "league_history.json"

        if history_file.exists():
            with open(history_file, "r") as f:
                history = json.load(f)
        else:
            history = []

        entry = {
            "date": datetime.now().strftime("%Y-%m-%d"),
            "timestamp": datetime.now().isoformat(),
            "results": results,
        }

        # Avoid duplicate entries for the same day
        today = datetime.now().strftime("%Y-%m-%d")
        history = [h for h in history if h.get("date") != today]
        history.append(entry)

        # Keep only last 90 days of history
        history = sorted(history, key=lambda x: x["date"])[-90:]

        with open(history_file, "w") as f:
            json.dump(history, f, indent=2)

    def load_history(self):
        """Load historical data"""
        history_file = self.data_dir / "league_history.json"

        if history_file.exists():
            with open(history_file, "r") as f:
                return json.load(f)
        return []

    def get_weekly_progress(self):
        """Get progress data for the current week"""
        history = self.load_history()
        if not history:
            return []

        # Get last 7 days of data
        return history[-7:]

"""SQLite storage backend for Duolingo Family League data"""

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any

from .storage_interface import StorageInterface


class SQLiteStorage(StorageInterface):
    """SQLite-based storage for family league data with better scalability"""
    
    def __init__(self, db_path: str = "league_data/league_data.db") -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(exist_ok=True)
        self._init_database()
    
    def _init_database(self) -> None:
        """Initialize database schema"""
        with sqlite3.connect(self.db_path) as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS daily_snapshots (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    data TEXT NOT NULL,
                    UNIQUE(date)
                );
                
                CREATE TABLE IF NOT EXISTS user_progress (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    snapshot_id INTEGER NOT NULL,
                    username TEXT NOT NULL,
                    name TEXT NOT NULL,
                    streak INTEGER NOT NULL,
                    total_xp INTEGER NOT NULL,
                    weekly_xp INTEGER NOT NULL,
                    last_check TEXT NOT NULL,
                    error TEXT NULL,
                    FOREIGN KEY (snapshot_id) REFERENCES daily_snapshots(id)
                );
                
                CREATE TABLE IF NOT EXISTS language_progress (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_progress_id INTEGER NOT NULL,
                    language TEXT NOT NULL,
                    xp INTEGER NOT NULL,
                    from_language TEXT NOT NULL,
                    learning_language TEXT NOT NULL,
                    weekly_xp INTEGER DEFAULT 0,
                    FOREIGN KEY (user_progress_id) REFERENCES user_progress(id)
                );
                
                CREATE TABLE IF NOT EXISTS metadata (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                );
                
                -- Indexes for efficient queries
                CREATE INDEX IF NOT EXISTS idx_daily_snapshots_date 
                    ON daily_snapshots(date);
                CREATE INDEX IF NOT EXISTS idx_user_progress_username 
                    ON user_progress(username);
                CREATE INDEX IF NOT EXISTS idx_user_progress_snapshot 
                    ON user_progress(snapshot_id);
                CREATE INDEX IF NOT EXISTS idx_language_progress_user 
                    ON language_progress(user_progress_id);
                CREATE INDEX IF NOT EXISTS idx_language_progress_language 
                    ON language_progress(language);
            """)
            
            # Set schema version if not exists
            cursor = conn.execute("SELECT value FROM metadata WHERE key = 'schema_version'")
            if not cursor.fetchone():
                conn.execute("INSERT INTO metadata (key, value) VALUES ('schema_version', '1')")
            conn.commit()
    
    def save_daily_data(self, results: dict[str, Any]) -> None:
        """Save daily progress data to SQLite"""
        today = datetime.now().strftime("%Y-%m-%d")
        timestamp = datetime.now().isoformat()
        
        with sqlite3.connect(self.db_path) as conn:
            # Insert or replace daily snapshot
            cursor = conn.execute(
                "INSERT OR REPLACE INTO daily_snapshots (date, timestamp, data) VALUES (?, ?, ?)",
                (today, timestamp, json.dumps(results))
            )
            snapshot_id = cursor.lastrowid
            
            # Clear existing user progress for this snapshot
            conn.execute("DELETE FROM user_progress WHERE snapshot_id = ?", (snapshot_id,))
            
            # Insert user progress data
            for username, user_data in results.items():
                if isinstance(user_data, dict) and "error" in user_data:
                    # Handle error case
                    cursor = conn.execute("""
                        INSERT INTO user_progress 
                        (snapshot_id, username, name, streak, total_xp, weekly_xp, last_check, error)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        snapshot_id, username, username, 0, 0, 0, 
                        user_data.get("last_check", timestamp), user_data["error"]
                    ))
                else:
                    # Handle successful user data
                    cursor = conn.execute("""
                        INSERT INTO user_progress 
                        (snapshot_id, username, name, streak, total_xp, weekly_xp, last_check, error)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        snapshot_id, user_data["username"], user_data["name"],
                        user_data["streak"], user_data["total_xp"], user_data["weekly_xp"],
                        user_data["last_check"], None
                    ))
                    
                    user_progress_id = cursor.lastrowid
                    
                    # Insert language progress
                    for language, lang_data in user_data.get("language_progress", {}).items():
                        weekly_xp = user_data.get("weekly_xp_per_language", {}).get(language, 0)
                        conn.execute("""
                            INSERT INTO language_progress 
                            (user_progress_id, language, xp, from_language, learning_language, weekly_xp)
                            VALUES (?, ?, ?, ?, ?, ?)
                        """, (
                            user_progress_id, language, lang_data["xp"],
                            lang_data["from_language"], lang_data["learning_language"], weekly_xp
                        ))
            
            conn.commit()
        
        print(f"Daily data saved to SQLite database: {self.db_path}")
    
    def update_history(self, results: dict[str, Any]) -> None:
        """Update history - for SQLite this is handled by save_daily_data"""
        # In SQLite, history is automatically maintained through daily_snapshots
        # This method exists for compatibility with the DataStorage interface
        pass
    
    def load_history(self) -> list[dict[str, Any]]:
        """Load historical data from SQLite"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT date, timestamp, data 
                FROM daily_snapshots 
                ORDER BY date ASC
            """)
            
            history = []
            for date, timestamp, data_json in cursor.fetchall():
                results = json.loads(data_json)
                history.append({
                    "date": date,
                    "timestamp": timestamp,
                    "results": results
                })
            
            return history
    
    def get_weekly_progress(self) -> list[dict[str, Any]]:
        """Get progress data for the current week"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT date, timestamp, data 
                FROM daily_snapshots 
                ORDER BY date DESC 
                LIMIT 7
            """)
            
            weekly_data = []
            for date, timestamp, data_json in cursor.fetchall():
                results = json.loads(data_json)
                weekly_data.append({
                    "date": date,
                    "timestamp": timestamp,
                    "results": results
                })
            
            # Return in chronological order (oldest first)
            return list(reversed(weekly_data))
    
    def get_user_progress_history(self, username: str, days: int = 30) -> list[dict[str, Any]]:
        """Get progress history for a specific user"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT ds.date, ds.timestamp, up.streak, up.total_xp, up.weekly_xp, up.error
                FROM daily_snapshots ds
                JOIN user_progress up ON ds.id = up.snapshot_id
                WHERE up.username = ?
                ORDER BY ds.date DESC
                LIMIT ?
            """, (username, days))
            
            history = []
            for date, timestamp, streak, total_xp, weekly_xp, error in cursor.fetchall():
                entry = {
                    "date": date,
                    "timestamp": timestamp,
                    "streak": streak,
                    "total_xp": total_xp,
                    "weekly_xp": weekly_xp
                }
                if error:
                    entry["error"] = error
                history.append(entry)
            
            return list(reversed(history))  # Return chronological order
    
    def get_language_progress_history(self, username: str, language: str, days: int = 30) -> list[dict[str, Any]]:
        """Get language-specific progress history"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT ds.date, ds.timestamp, lp.xp, lp.weekly_xp
                FROM daily_snapshots ds
                JOIN user_progress up ON ds.id = up.snapshot_id
                JOIN language_progress lp ON up.id = lp.user_progress_id
                WHERE up.username = ? AND lp.language = ?
                ORDER BY ds.date DESC
                LIMIT ?
            """, (username, language, days))
            
            history = []
            for date, timestamp, xp, weekly_xp in cursor.fetchall():
                history.append({
                    "date": date,
                    "timestamp": timestamp,
                    "xp": xp,
                    "weekly_xp": weekly_xp
                })
            
            return list(reversed(history))  # Return chronological order
    
    def cleanup_old_data(self, keep_days: int = 90) -> None:
        """Remove old data beyond the specified number of days"""
        with sqlite3.connect(self.db_path) as conn:
            # Delete old snapshots and cascading data
            conn.execute("""
                DELETE FROM daily_snapshots 
                WHERE date < date('now', '-{} days')
            """.format(keep_days))
            conn.commit()
        
        print(f"Cleaned up data older than {keep_days} days")
    
    def get_database_stats(self) -> dict[str, Any]:
        """Get database statistics"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT COUNT(*) FROM daily_snapshots")
            daily_snapshots_count = cursor.fetchone()[0]
            
            cursor = conn.execute("SELECT COUNT(*) FROM user_progress")
            user_progress_count = cursor.fetchone()[0]
            
            cursor = conn.execute("SELECT COUNT(*) FROM language_progress")
            language_progress_count = cursor.fetchone()[0]
            
            cursor = conn.execute("SELECT MIN(date), MAX(date) FROM daily_snapshots")
            date_range = cursor.fetchone()
            
            return {
                "daily_snapshots": daily_snapshots_count,
                "user_progress_entries": user_progress_count,
                "language_progress_entries": language_progress_count,
                "date_range": {
                    "start": date_range[0],
                    "end": date_range[1]
                },
                "database_size_mb": self.db_path.stat().st_size / (1024 * 1024) if self.db_path.exists() else 0
            }
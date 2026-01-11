"""Data migration utilities for converting between JSON and SQLite storage backends"""

import json
from pathlib import Path

from .data_storage import DataStorage
from .sqlite_storage import SQLiteStorage
from .storage_interface import StorageInterface


class StorageMigrator:
    """Utility class for migrating data between storage backends"""
    
    @staticmethod
    def json_to_sqlite(
        json_data_dir: str = "league_data",
        sqlite_db_path: str = "league_data/league_data.db"
    ) -> None:
        """
        Migrate data from JSON files to SQLite database
        
        Args:
            json_data_dir: Directory containing JSON files
            sqlite_db_path: Path for the SQLite database
        """
        print(f"Starting migration from JSON ({json_data_dir}) to SQLite ({sqlite_db_path})")
        
        # Initialize storages
        json_storage = DataStorage(json_data_dir)
        sqlite_storage = SQLiteStorage(sqlite_db_path)
        
        # Load all historical data from JSON
        history = json_storage.load_history()
        
        if not history:
            print("No historical data found in JSON files")
            return
        
        print(f"Found {len(history)} historical entries to migrate")
        
        # Migrate each historical entry
        migrated_count = 0
        for entry in history:
            try:
                # For migration, we need to use the specific date from the entry
                # not the current date. We'll need to patch the datetime for each entry
                from unittest.mock import patch
                
                entry_date = entry["date"]
                entry_timestamp = entry.get("timestamp", f"{entry_date}T00:00:00")
                
                with patch('src.sqlite_storage.datetime') as mock_datetime:
                    mock_datetime.now.return_value.strftime.return_value = entry_date
                    mock_datetime.now.return_value.isoformat.return_value = entry_timestamp
                    sqlite_storage.save_daily_data(entry["results"])
                
                migrated_count += 1
                
                if migrated_count % 10 == 0:
                    print(f"Migrated {migrated_count}/{len(history)} entries...")
                    
            except Exception as e:
                print(f"Error migrating entry for {entry['date']}: {e}")
                continue
        
        print(f"Migration completed: {migrated_count}/{len(history)} entries migrated successfully")
        
        # Show database stats
        stats = sqlite_storage.get_database_stats()
        print(f"SQLite database stats: {stats}")
    
    @staticmethod
    def sqlite_to_json(
        sqlite_db_path: str = "league_data/league_data.db",
        json_data_dir: str = "league_data_exported"
    ) -> None:
        """
        Export data from SQLite database to JSON files
        
        Args:
            sqlite_db_path: Path to the SQLite database
            json_data_dir: Directory to export JSON files to
        """
        print(f"Starting export from SQLite ({sqlite_db_path}) to JSON ({json_data_dir})")
        
        # Initialize storages
        sqlite_storage = SQLiteStorage(sqlite_db_path)
        
        # Load all historical data from SQLite
        history = sqlite_storage.load_history()
        
        if not history:
            print("No historical data found in SQLite database")
            return
        
        print(f"Found {len(history)} historical entries to export")
        
        # Create JSON data directory
        Path(json_data_dir).mkdir(exist_ok=True)
        
        # Export each historical entry
        exported_count = 0
        for entry in history:
            try:
                # Create daily JSON file
                date = entry["date"]
                daily_file = Path(json_data_dir) / f"daily_{date}.json"
                
                daily_data = {
                    "date": entry["date"],
                    "timestamp": entry["timestamp"],
                    "results": entry["results"],
                }
                
                with open(daily_file, "w") as f:
                    json.dump(daily_data, f, indent=2)
                
                exported_count += 1
                
                if exported_count % 10 == 0:
                    print(f"Exported {exported_count}/{len(history)} entries...")
                    
            except Exception as e:
                print(f"Error exporting entry for {entry['date']}: {e}")
                continue
        
        # Create master history file
        try:
            history_file = Path(json_data_dir) / "league_history.json"
            with open(history_file, "w") as f:
                json.dump(history, f, indent=2)
            print(f"Created master history file: {history_file}")
        except Exception as e:
            print(f"Error creating master history file: {e}")
        
        print(f"Export completed: {exported_count}/{len(history)} entries exported successfully")
    
    @staticmethod
    def validate_migration(
        source_storage: StorageInterface,
        target_storage: StorageInterface,
        check_last_n_days: int = 30
    ) -> bool:
        """
        Validate that data migration was successful by comparing data
        
        Args:
            source_storage: Source storage backend
            target_storage: Target storage backend
            check_last_n_days: Number of recent days to validate
        
        Returns:
            True if validation passes, False otherwise
        """
        print(f"Validating migration by comparing last {check_last_n_days} days of data...")
        
        try:
            source_history = source_storage.load_history()[-check_last_n_days:]
            target_history = target_storage.load_history()[-check_last_n_days:]
            
            if len(source_history) != len(target_history):
                print(f"❌ History length mismatch: source={len(source_history)}, target={len(target_history)}")
                return False
            
            # Compare each day's data
            mismatches = 0
            for source_entry, target_entry in zip(source_history, target_history):
                if source_entry["date"] != target_entry["date"]:
                    print(f"❌ Date mismatch: {source_entry['date']} != {target_entry['date']}")
                    mismatches += 1
                    continue
                
                # Compare user data
                source_results = source_entry["results"]
                target_results = target_entry["results"]
                
                if set(source_results.keys()) != set(target_results.keys()):
                    print(f"❌ User set mismatch for {source_entry['date']}")
                    mismatches += 1
                    continue
                
                # Check core fields for each user
                for username in source_results:
                    source_user = source_results[username]
                    target_user = target_results[username]
                    
                    if isinstance(source_user, dict) and "error" in source_user:
                        continue  # Skip error entries
                    
                    core_fields = ["streak", "total_xp", "weekly_xp"]
                    for field in core_fields:
                        if source_user.get(field) != target_user.get(field):
                            print(f"❌ Field mismatch for {username} on {source_entry['date']}: {field}")
                            mismatches += 1
            
            if mismatches == 0:
                print("✅ Migration validation passed - data matches between source and target")
                return True
            else:
                print(f"❌ Migration validation failed - found {mismatches} mismatches")
                return False
                
        except Exception as e:
            print(f"❌ Validation error: {e}")
            return False


def main():
    """CLI interface for data migration"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Migrate data between JSON and SQLite storage backends")
    parser.add_argument("command", choices=["json-to-sqlite", "sqlite-to-json"], 
                       help="Migration direction")
    parser.add_argument("--json-dir", default="league_data",
                       help="Directory containing JSON files")
    parser.add_argument("--sqlite-path", default="league_data/league_data.db",
                       help="Path to SQLite database")
    parser.add_argument("--validate", action="store_true",
                       help="Validate migration after completion")
    
    args = parser.parse_args()
    
    if args.command == "json-to-sqlite":
        StorageMigrator.json_to_sqlite(args.json_dir, args.sqlite_path)
        
        if args.validate:
            json_storage = DataStorage(args.json_dir)
            sqlite_storage = SQLiteStorage(args.sqlite_path)
            StorageMigrator.validate_migration(json_storage, sqlite_storage)
            
    elif args.command == "sqlite-to-json":
        StorageMigrator.sqlite_to_json(args.sqlite_path, args.json_dir)
        
        if args.validate:
            sqlite_storage = SQLiteStorage(args.sqlite_path)
            json_storage = DataStorage(args.json_dir)
            StorageMigrator.validate_migration(sqlite_storage, json_storage)


if __name__ == "__main__":
    main()
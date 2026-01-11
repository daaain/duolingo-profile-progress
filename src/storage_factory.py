"""Storage factory for creating appropriate storage backends"""

import os

from .storage_interface import StorageInterface
from .data_storage import DataStorage
from .sqlite_storage import SQLiteStorage


class StorageFactory:
    """Factory class for creating storage backends"""

    @staticmethod
    def create_storage(
        backend: str | None = None,
        data_dir: str = "league_data",
        db_path: str | None = None,
        gist_id: str | None = None,
        github_token: str | None = None,
    ) -> StorageInterface:
        """
        Create a storage backend based on configuration

        Args:
            backend: Storage backend type ('json', 'sqlite', or 'gist')
            data_dir: Directory for JSON files (used for JSON backend)
            db_path: Path to SQLite database file (used for SQLite backend)
            gist_id: GitHub Gist ID (used for Gist backend)
            github_token: GitHub token with gist scope (used for Gist backend)

        Returns:
            Storage backend instance
        """
        # Default backend from environment or fallback to JSON
        if backend is None:
            backend = os.getenv("STORAGE_BACKEND", "json").lower()

        if backend == "sqlite":
            if db_path is None:
                db_path = os.getenv("SQLITE_DB_PATH", f"{data_dir}/league_data.db")
            return SQLiteStorage(db_path)
        elif backend == "json":
            return DataStorage(data_dir)
        elif backend == "gist":
            from .gist_storage import GistStorage

            return GistStorage(gist_id=gist_id, github_token=github_token)
        else:
            raise ValueError(
                f"Unknown storage backend: {backend}. Supported: 'json', 'sqlite', 'gist'"
            )

    @staticmethod
    def get_available_backends() -> list[str]:
        """Get list of available storage backends"""
        return ["json", "sqlite", "gist"]

    @staticmethod
    def get_default_backend() -> str:
        """Get the default storage backend"""
        return os.getenv("STORAGE_BACKEND", "json").lower()


def create_default_storage() -> StorageInterface:
    """Create storage using default configuration"""
    return StorageFactory.create_storage()

"""Storage interface and abstract base class for data storage backends"""

from abc import ABC, abstractmethod
from typing import Any


class StorageInterface(ABC):
    """Abstract interface for storage backends"""
    
    @abstractmethod
    def save_daily_data(self, results: dict[str, Any]) -> None:
        """Save daily progress data"""
        pass
    
    @abstractmethod
    def update_history(self, results: dict[str, Any]) -> None:
        """Update the master history with daily data"""
        pass
    
    @abstractmethod
    def load_history(self) -> list[dict[str, Any]]:
        """Load historical data"""
        pass
    
    @abstractmethod
    def get_weekly_progress(self) -> list[dict[str, Any]]:
        """Get progress data for the current week"""
        pass
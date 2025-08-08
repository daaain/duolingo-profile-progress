"""Internationalization support for Duolingo Family League reports"""

import os
from typing import Any, Dict


class I18n:
    """Simple internationalization class for managing translations"""
    
    def __init__(self, language: str = "en"):
        """Initialize with specified language"""
        self.language = language
        self._translations: Dict[str, Dict[str, str]] = {}
        self._load_translations()
    
    def _load_translations(self) -> None:
        """Load translation strings for all languages"""
        self._translations = {
            "en": {
                # Daily report translations
                "daily_report_title": "Duolingo Family League - Daily Update",
                "daily_report_header": "DUOLINGO FAMILY LEAGUE - DAILY UPDATE",
                "daily_report_subtitle": "Track your family's language learning progress",
                "standings_title": "Today's Standings",
                "streak_alerts_title": "Streak Alerts",
                "everyone_maintaining_streaks": "Everyone is maintaining their streaks!",
                "needs_to_practice": "needs to practice today!",
                "keep_learning": "Keep learning! 🌟",
                
                # Weekly report translations
                "weekly_report_title": "Duolingo Family League - Weekly Report",
                "weekly_report_header": "DUOLINGO FAMILY LEAGUE - WEEKLY REPORT",
                "weekly_report_subtitle": "Comprehensive weekly family progress report",
                "week_ending": "Week ending: {date}",
                "generated_date": "Generated: {date}",
                "family_leaderboard_title": "FAMILY LEADERBOARD",
                "detailed_progress_title": "DETAILED PROGRESS",
                "goals_title": "THIS WEEK'S FAMILY GOALS",
                "keep_up_message": "Keep up the great work, everyone! 🌟",
                
                # General translations
                "day_streak": "{count} day streak",
                "days_streak": "{count} days streak",
                "weekly_xp": "{count} weekly XP",
                "total_xp": "{count:,} total XP",
                "current_streak": "Current streak: {count} days",
                "streak_goal_achieved": "STREAK GOAL ACHIEVED!",
                "weekly_xp_goal_achieved": "WEEKLY XP GOAL ACHIEVED! ({current}/{goal})",
                "good_progress_streak": "Good progress towards {goal}-day goal",
                "work_needed_streak": "Work needed for {goal}-day streak goal",
                "weekly_xp_progress": "Weekly XP progress: {current}/{goal}",
                "language_progress": "Language Progress:",
                "active_languages": "Active Languages: {languages}",
                "not_started_yet": "Not started yet",
                "maintain_streak_goal": "Maintain a {goal}-day streak",
                "earn_xp_goal": "Earn {goal} XP this week",
                "beat_personal_best": "Try to beat your personal best!",
                "unable_to_check": "Unable to check progress: {error}",
                "level": "Level {level}",
                "xp": "{xp:,} XP",
                "weekly_gain": "+{xp} this week",
                "date_format": "%Y-%m-%d",
                "datetime_format": "%Y-%m-%d %H:%M:%S",
            },
            "hu": {
                # Daily report translations
                "daily_report_title": "Duolingo Családi Liga - Napi Frissítés",
                "daily_report_header": "DUOLINGO CSALÁDI LIGA - NAPI FRISSÍTÉS",
                "daily_report_subtitle": "Kövesse nyomon családja nyelvtanulási előrehaladását",
                "standings_title": "Mai Eredmények",
                "streak_alerts_title": "Sorozat Figyelmeztetések",
                "everyone_maintaining_streaks": "Mindenki tartja a sorozatát!",
                "needs_to_practice": "ma gyakorolnia kell!",
                "keep_learning": "Folytassátok a tanulást! 🌟",
                
                # Weekly report translations
                "weekly_report_title": "Duolingo Családi Liga - Heti Jelentés",
                "weekly_report_header": "DUOLINGO CSALÁDI LIGA - HETI JELENTÉS",
                "weekly_report_subtitle": "Átfogó heti családi előrehaladási jelentés",
                "week_ending": "Hét vége: {date}",
                "generated_date": "Létrehozva: {date}",
                "family_leaderboard_title": "CSALÁDI RANGLISTA",
                "detailed_progress_title": "RÉSZLETES ELŐREHALADÁS",
                "goals_title": "E HETI CSALÁDI CÉLOK",
                "keep_up_message": "Csak így tovább, mindenki! 🌟",
                
                # General translations
                "day_streak": "{count} napos sorozat",
                "days_streak": "{count} napos sorozat",
                "weekly_xp": "{count} heti XP",
                "total_xp": "{count:,} összes XP",
                "current_streak": "Jelenlegi sorozat: {count} nap",
                "streak_goal_achieved": "SOROZAT CÉL TELJESÍTVE!",
                "weekly_xp_goal_achieved": "HETI XP CÉL TELJESÍTVE! ({current}/{goal})",
                "good_progress_streak": "Jó előrehaladás a {goal}-napos cél felé",
                "work_needed_streak": "További munka szükséges a {goal}-napos sorozat céljához",
                "weekly_xp_progress": "Heti XP előrehaladás: {current}/{goal}",
                "language_progress": "Nyelvi Előrehaladás:",
                "active_languages": "Aktív Nyelvek: {languages}",
                "not_started_yet": "Még nem kezdte el",
                "maintain_streak_goal": "Tartsa fenn a {goal}-napos sorozatot",
                "earn_xp_goal": "Szerezzen {goal} XP-t ezen a héten",
                "beat_personal_best": "Próbálja megdönteni a személyes rekordját!",
                "unable_to_check": "Nem sikerült ellenőrizni az előrehaladást: {error}",
                "level": "{level}. szint",
                "xp": "{xp:,} XP",
                "weekly_gain": "+{xp} ezen a héten",
                "date_format": "%Y. %m. %d.",
                "datetime_format": "%Y. %m. %d. %H:%M:%S",
            }
        }
    
    def get(self, key: str, **kwargs: Any) -> str:
        """Get translated string with optional formatting parameters"""
        if self.language not in self._translations:
            # Fallback to English if language not found
            translation = self._translations.get("en", {}).get(key, key)
        else:
            translation = self._translations[self.language].get(key, key)
        
        if kwargs:
            try:
                return translation.format(**kwargs)
            except (KeyError, ValueError):
                # If formatting fails, return the unformatted string
                return translation
        
        return translation
    
    def set_language(self, language: str) -> None:
        """Change the current language"""
        self.language = language
    
    def get_available_languages(self) -> list[str]:
        """Get list of available language codes"""
        return list(self._translations.keys())


def get_language_from_env() -> str:
    """Get language setting from environment variable, defaulting to English"""
    return os.getenv("DUOLINGO_REPORT_LANGUAGE", "en").lower()


# Global instance for easy access
_i18n = I18n(get_language_from_env())

def get_i18n() -> I18n:
    """Get the global i18n instance"""
    return _i18n

def set_global_language(language: str) -> None:
    """Set the global language"""
    _i18n.set_language(language)
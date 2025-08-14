"""Internationalization support for Duolingo Family League reports"""

import json
import os
from pathlib import Path
from typing import Any, Dict


class I18n:
    """Simple internationalization class for managing translations"""

    def __init__(self, language: str = "en"):
        """Initialize with specified language"""
        self.language = language
        self._translations: Dict[str, Dict[str, str]] = {}
        self._load_translations()

    def _load_translations(self) -> None:
        """Load translation strings from JSON files"""
        # Get the project root directory (parent of src)
        project_root = Path(__file__).parent.parent
        translations_dir = project_root / "translations"

        self._translations = {}

        # Load all JSON files in the translations directory
        if translations_dir.exists():
            for json_file in translations_dir.glob("*.json"):
                language_code = json_file.stem
                try:
                    with open(json_file, "r", encoding="utf-8") as f:
                        self._translations[language_code] = json.load(f)
                except (json.JSONDecodeError, IOError) as e:
                    print(
                        f"Warning: Could not load translations for {language_code}: {e}"
                    )

        # Fallback to English if no translations were loaded
        if not self._translations:
            print(
                "Warning: No translation files found, using fallback English translations"
            )
            self._translations = {
                "en": {
                    "daily_report_title": "Duolingo Family League - Daily Update",
                    "daily_report_header": "DUOLINGO FAMILY LEAGUE - DAILY UPDATE",
                    "keep_learning": "Keep learning! 🌟",
                }
            }

    def get(self, key: str, default: str | None = None, **kwargs: Any) -> str:
        """Get translated string with optional formatting parameters"""
        # Handle nested keys like "languages.Spanish"
        keys = key.split(".")

        if self.language not in self._translations:
            # Fallback to English if language not found
            translation_dict = self._translations.get("en", {})
        else:
            translation_dict = self._translations[self.language]

        # Navigate through nested keys
        translation = translation_dict
        for k in keys:
            if isinstance(translation, dict) and k in translation:
                translation = translation[k]
            else:
                translation = default if default is not None else key
                break

        # If we ended up with a dict, return the default/key
        if isinstance(translation, dict):
            translation = default if default is not None else key

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


def translate_language_name(language_name: str) -> str:
    """Translate a language name using the current i18n settings"""
    return _i18n.get(f"languages.{language_name}", default=language_name)

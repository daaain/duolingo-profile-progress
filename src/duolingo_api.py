"""Duolingo API integration for fetching user progress"""

import requests
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta
from typing import Any, Union

try:
    from .types import (
        DuolingoApiResponse,
        DuolingoUser,
        UserProgress,
        UserProgressError,
        LanguageProgress,
    )
except ImportError:
    from src.types import (
        DuolingoApiResponse,
        DuolingoUser,
        UserProgress,
        UserProgressError,
        LanguageProgress,
    )


def make_api_request_with_retry(
    url: str, headers: dict[str, str], max_retries: int = 3, base_delay: int = 1
) -> requests.Response:
    """Make API request with exponential backoff retry logic"""
    for attempt in range(max_retries):
        try:
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            return response

        except requests.RequestException as e:
            if attempt == max_retries - 1:
                # Last attempt failed, re-raise the exception
                raise e

            # Calculate delay with exponential backoff
            delay = base_delay * (2**attempt)
            print(
                f"⚠️ API request failed (attempt {attempt + 1}/{max_retries}): {str(e)}"
            )
            print(f"   Retrying in {delay} seconds...")
            time.sleep(delay)

    # This should never be reached, but just in case
    raise requests.RequestException("Max retries exceeded")


def calculate_weekly_xp(
    username: str, current_total_xp: int, history: list[dict[str, Any]] | None = None
) -> int:
    """Calculate weekly XP from historical data (total across all languages)

    Args:
        username: The Duolingo username
        current_total_xp: Current total XP for the user
        history: Optional pre-loaded history data. If None, loads from default JSON storage.
    """
    try:
        if history is None:
            from .data_storage import DataStorage

            storage = DataStorage()
            history = storage.load_history()

        if not history:
            return 0

        # Get start of current week (Monday)
        today = datetime.now()
        days_since_monday = today.weekday()
        week_start = (today - timedelta(days=days_since_monday)).strftime("%Y-%m-%d")

        # Find XP at start of week or earliest available data this week
        week_start_xp = None
        earliest_this_week_xp = None

        for entry in history:
            entry_date = entry.get("date")
            if entry_date and entry_date >= week_start:
                # This entry is from current week
                user_results = entry.get("results", {})
                for user_key, user_data in user_results.items():
                    if (
                        user_data.get("username", "").lower() == username.lower()
                        or user_key.lower().replace(" ", "_") == username.lower()
                    ):
                        if earliest_this_week_xp is None or (
                            entry_date and entry_date < earliest_this_week_xp[0]
                        ):
                            earliest_this_week_xp = (
                                entry_date,
                                user_data.get("total_xp", 0),
                            )
                        break
            elif entry_date and entry_date < week_start:
                # This is from before the week - use as baseline if it's the most recent
                user_results = entry.get("results", {})
                for user_key, user_data in user_results.items():
                    if (
                        user_data.get("username", "").lower() == username.lower()
                        or user_key.lower().replace(" ", "_") == username.lower()
                    ):
                        if week_start_xp is None or (
                            entry_date and entry_date > week_start_xp[0]
                        ):
                            week_start_xp = (entry_date, user_data.get("total_xp", 0))
                        break

        # Calculate weekly XP
        if week_start_xp is not None:
            # We have data from before this week - use it as baseline
            return max(0, current_total_xp - week_start_xp[1])
        elif earliest_this_week_xp is not None:
            # No data from before this week, use earliest data from this week
            # If it's the first day, return 0 (no progress yet)
            if earliest_this_week_xp[1] == current_total_xp:
                return 0
            return max(0, current_total_xp - earliest_this_week_xp[1])

        return 0

    except Exception:
        # If we can't calculate weekly XP (e.g., no history), return 0
        return 0


def calculate_weekly_xp_per_language(
    username: str,
    current_language_progress: dict[str, LanguageProgress],
    history: list[dict[str, Any]] | None = None,
) -> dict[str, int]:
    """Calculate weekly XP per language from historical data

    Args:
        username: The Duolingo username
        current_language_progress: Current language progress data
        history: Optional pre-loaded history data. If None, loads from default JSON storage.
    """
    try:
        if history is None:
            from .data_storage import DataStorage

            storage = DataStorage()
            history = storage.load_history()

        if not history:
            return {}

        # Get start of current week (Monday)
        today = datetime.now()
        days_since_monday = today.weekday()
        week_start = (today - timedelta(days=days_since_monday)).strftime("%Y-%m-%d")

        # Find language XP at start of week or earliest available data this week
        week_start_languages = None
        earliest_this_week_languages = None

        for entry in history:
            entry_date = entry.get("date")
            if entry_date and entry_date >= week_start:
                # This entry is from current week
                user_results = entry.get("results", {})
                for user_key, user_data in user_results.items():
                    if (
                        user_data.get("username", "").lower() == username.lower()
                        or user_key.lower().replace(" ", "_") == username.lower()
                    ):
                        if earliest_this_week_languages is None or (
                            entry_date and entry_date < earliest_this_week_languages[0]
                        ):
                            earliest_this_week_languages = (
                                entry_date,
                                user_data.get("language_progress", {}),
                            )
                        break
            elif entry_date and entry_date < week_start:
                # This is from before the week - use as baseline if it's the most recent
                user_results = entry.get("results", {})
                for user_key, user_data in user_results.items():
                    if (
                        user_data.get("username", "").lower() == username.lower()
                        or user_key.lower().replace(" ", "_") == username.lower()
                    ):
                        if week_start_languages is None or (
                            entry_date and entry_date > week_start_languages[0]
                        ):
                            week_start_languages = (
                                entry_date,
                                user_data.get("language_progress", {}),
                            )
                        break

        # Calculate weekly XP per language
        weekly_xp_per_language: dict[str, int] = {}
        baseline_languages = None

        if week_start_languages is not None:
            # We have data from before this week - use it as baseline
            baseline_languages = week_start_languages[1]
        elif earliest_this_week_languages is not None:
            # No data from before this week, use earliest data from this week
            baseline_languages = earliest_this_week_languages[1]

        if baseline_languages:
            for lang, lang_data in current_language_progress.items():
                current_xp = lang_data.get("xp", 0)
                baseline_xp = baseline_languages.get(lang, {}).get("xp", 0)
                weekly_xp = max(0, current_xp - baseline_xp)
                weekly_xp_per_language[lang] = weekly_xp

        # Add any new languages that weren't in the baseline
        for lang, lang_data in current_language_progress.items():
            if lang not in weekly_xp_per_language:
                # This is a new language started this week
                weekly_xp_per_language[lang] = lang_data.get("xp", 0)

        return weekly_xp_per_language

    except Exception:
        # If we can't calculate weekly XP, return empty dict
        return {}


def calculate_daily_xp(
    username: str, current_total_xp: int, history: list[dict[str, Any]] | None = None
) -> int:
    """Calculate daily XP from historical data (XP earned since yesterday)

    Args:
        username: The Duolingo username
        current_total_xp: Current total XP for the user
        history: Optional pre-loaded history data. If None, loads from default JSON storage.
    """
    try:
        if history is None:
            from .data_storage import DataStorage

            storage = DataStorage()
            history = storage.load_history()

        if not history:
            return 0

        # Get yesterday's date
        today = datetime.now()
        yesterday = (today - timedelta(days=1)).strftime("%Y-%m-%d")

        # Find yesterday's XP
        yesterday_xp = None
        for entry in reversed(history):  # Start from most recent
            entry_date = entry.get("date")
            if entry_date and entry_date <= yesterday:
                user_results = entry.get("results", {})
                for user_key, user_data in user_results.items():
                    if (
                        user_data.get("username", "").lower() == username.lower()
                        or user_key.lower().replace(" ", "_") == username.lower()
                    ):
                        yesterday_xp = user_data.get("total_xp", 0)
                        break
                if yesterday_xp is not None:
                    break

        if yesterday_xp is not None:
            return max(0, current_total_xp - yesterday_xp)

        return 0

    except Exception:
        return 0


def calculate_daily_xp_per_language(
    username: str,
    current_language_progress: dict[str, LanguageProgress],
    history: list[dict[str, Any]] | None = None,
) -> dict[str, int]:
    """Calculate daily XP per language from historical data

    Args:
        username: The Duolingo username
        current_language_progress: Current language progress data
        history: Optional pre-loaded history data. If None, loads from default JSON storage.
    """
    try:
        if history is None:
            from .data_storage import DataStorage

            storage = DataStorage()
            history = storage.load_history()

        if not history:
            return {}

        # Get yesterday's date
        today = datetime.now()
        yesterday = (today - timedelta(days=1)).strftime("%Y-%m-%d")

        # Find yesterday's language XP
        yesterday_languages = None
        for entry in reversed(history):  # Start from most recent
            entry_date = entry.get("date")
            if entry_date and entry_date <= yesterday:
                user_results = entry.get("results", {})
                for user_key, user_data in user_results.items():
                    if (
                        user_data.get("username", "").lower() == username.lower()
                        or user_key.lower().replace(" ", "_") == username.lower()
                    ):
                        yesterday_languages = user_data.get("language_progress", {})
                        break
                if yesterday_languages is not None:
                    break

        # Calculate daily XP per language
        daily_xp_per_language: dict[str, int] = {}

        if yesterday_languages:
            for lang, lang_data in current_language_progress.items():
                current_xp = lang_data.get("xp", 0)
                yesterday_lang_xp = yesterday_languages.get(lang, {}).get("xp", 0)
                daily_xp = max(0, current_xp - yesterday_lang_xp)
                daily_xp_per_language[lang] = daily_xp
        else:
            # No history, can't calculate daily XP
            for lang in current_language_progress:
                daily_xp_per_language[lang] = 0

        return daily_xp_per_language

    except Exception:
        return {}


def get_user_progress(
    username: str, history: list[dict[str, Any]] | None = None
) -> Union[UserProgress, UserProgressError]:
    """Get progress data for a specific user using the unauthenticated API

    Args:
        username: The Duolingo username
        history: Optional pre-loaded history data for XP calculations
    """
    try:
        # Use the unauthenticated API endpoint
        url = f"https://www.duolingo.com/2017-06-30/users?username={username}"

        # Add headers to make the request look like it's coming from a browser
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "application/json",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin",
        }

        response = make_api_request_with_retry(url, headers)

        data: DuolingoApiResponse = response.json()
        users = data.get("users", [])

        if not users:
            return UserProgressError(
                username=username,
                error="User not found",
                last_check=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                language_progress={},
                weekly_xp_per_language={},
                daily_xp_per_language={},
                active_languages=[],
            )

        user: DuolingoUser = users[0]

        # Extract language progress from courses
        language_progress: dict[str, LanguageProgress] = {}
        active_languages: list[str] = []

        courses = user.get("courses", [])
        for course in courses:
            lang_xp = course.get("xp", 0)
            if lang_xp > 0:
                lang_title = course.get("title", "")
                if lang_title:
                    active_languages.append(lang_title)
                    language_progress[lang_title] = LanguageProgress(
                        xp=lang_xp,
                        from_language=course.get("fromLanguage", "en"),
                        learning_language=course.get("learningLanguage", ""),
                    )

        # Get streak data
        streak_data = user.get("streakData", {})
        current_streak = streak_data.get("currentStreak", {})
        streak = (
            current_streak.get("length", 0) if current_streak else user.get("streak", 0)
        )

        # Calculate weekly XP per language
        weekly_xp_per_language = calculate_weekly_xp_per_language(
            username, language_progress, history
        )

        # Calculate daily XP per language
        daily_xp_per_language = calculate_daily_xp_per_language(
            username, language_progress, history
        )

        total_xp = user.get("totalXp", 0)

        return UserProgress(
            username=username,
            name=user.get("name", username),
            streak=streak,
            total_xp=total_xp,
            weekly_xp=calculate_weekly_xp(username, total_xp, history),
            weekly_xp_per_language=weekly_xp_per_language,
            daily_xp=calculate_daily_xp(username, total_xp, history),
            daily_xp_per_language=daily_xp_per_language,
            active_languages=active_languages,
            language_progress=language_progress,
            last_check=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        )

    except requests.RequestException as e:
        return UserProgressError(
            username=username,
            error=f"API request failed: {str(e)}",
            last_check=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            language_progress={},
            weekly_xp_per_language={},
            daily_xp_per_language={},
            active_languages=[],
        )
    except Exception as e:
        return UserProgressError(
            username=username,
            error=str(e),
            last_check=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            language_progress={},
            weekly_xp_per_language={},
            daily_xp_per_language={},
            active_languages=[],
        )


def check_all_family(
    config: dict[str, Any] | None,
    history: list[dict[str, Any]] | None = None,
) -> dict[str, Union[UserProgress, UserProgressError]]:
    """Check progress for all family members

    Args:
        config: Configuration dictionary
        history: Optional pre-loaded history data for XP calculations.
                 If None, XP calculations will load from default JSON storage.
    """
    results: dict[str, Union[UserProgress, UserProgressError]] = {}

    if not config:
        print("❌ No configuration found")
        return results

    print("Checking Duolingo progress for the family league...\n")
    print("=" * 60)

    # Get users to check from config
    users_to_check: dict[str, str] = {}

    if config["family_members"]:
        # Use specified usernames
        for member_name, member_data in config["family_members"].items():
            username = member_data["username"]
            users_to_check[member_name] = username
    else:
        print("⚠️ No users specified in DUOLINGO_USERNAMES")
        return results

    # Process all users in parallel
    with ThreadPoolExecutor(max_workers=5) as executor:
        # Submit all requests
        future_to_member = {
            executor.submit(get_user_progress, username, history): member_name
            for member_name, username in users_to_check.items()
        }

        # Process completed requests as they finish
        for future in as_completed(future_to_member):
            member_name = future_to_member[future]
            print(f"\nChecking {member_name}...")

            try:
                progress = future.result()
                results[member_name] = progress

                if "error" in progress:
                    print(f"❌ Error: {progress['error']}")
                else:
                    active_langs = progress.get("active_languages", [])
                    print(f"✅ Current streak: {progress['streak']} days")
                    print(f"   Name: {progress.get('name', 'Unknown')}")
                    print(
                        f"   Active languages: {', '.join(active_langs) if active_langs else 'None'}"
                    )
                    print(f"   Total XP: {progress['total_xp']}")
            except Exception as e:
                print(f"❌ Error processing {member_name}: {str(e)}")
                results[member_name] = UserProgressError(
                    username=users_to_check[member_name],
                    error=f"Processing failed: {str(e)}",
                    last_check=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    language_progress={},
                    weekly_xp_per_language={},
                    daily_xp_per_language={},
                    active_languages=[],
                )

    return results

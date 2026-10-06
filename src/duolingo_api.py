"""Duolingo API integration for fetching user progress"""

import requests
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date, datetime, timedelta
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


def get_language_xp(user_data: dict[str, Any]) -> int:
    """Sum of XP across language courses for a user progress entry

    Duolingo's totalXp also includes non-language XP (and was recalculated in
    October 2026), so only course XP is used for league calculations. Falls back
    to total_xp for entries without per-language data.
    """
    language_progress = user_data.get("language_progress")
    if language_progress is not None:
        return sum(lang.get("xp", 0) for lang in language_progress.values())
    return user_data.get("total_xp", 0)


def find_user_data(entry: dict[str, Any], username: str) -> dict[str, Any] | None:
    """User's progress in a history entry, or None if missing or failed to fetch"""
    for user_key, user_data in entry.get("results", {}).items():
        if (
            user_data.get("username", "").lower() == username.lower()
            or user_key.lower().replace(" ", "_") == username.lower()
        ):
            return None if "error" in user_data else user_data
    return None


def find_week_baseline(
    username: str,
    history: list[dict[str, Any]],
    reference_date: datetime | None = None,
) -> dict[str, Any] | None:
    """User's progress at the start of the week (Monday) containing reference_date

    Snapshots are taken in the early morning, so the one dated Monday holds the
    XP at the end of Sunday. If Monday's is missing, the snapshot dated nearest
    to Monday is used, preferring the later one when equally near so that no
    day is counted in two weekly reports.
    """
    today = reference_date or datetime.now()
    week_start = (today - timedelta(days=today.weekday())).date()

    before: tuple[date, dict[str, Any]] | None = None
    on_or_after: tuple[date, dict[str, Any]] | None = None

    for entry in history:
        user_data = find_user_data(entry, username)
        if user_data is None or not entry.get("date"):
            continue
        entry_date = date.fromisoformat(entry["date"])
        if entry_date < week_start:
            if before is None or entry_date > before[0]:
                before = (entry_date, user_data)
        elif on_or_after is None or entry_date < on_or_after[0]:
            on_or_after = (entry_date, user_data)

    if before is None or on_or_after is None:
        nearest = on_or_after or before
        return nearest[1] if nearest else None
    if on_or_after[0] - week_start <= week_start - before[0]:
        return on_or_after[1]
    return before[1]


def calculate_weekly_xp(
    username: str,
    current_language_xp: int,
    history: list[dict[str, Any]] | None = None,
    reference_date: datetime | None = None,
) -> int:
    """Calculate weekly XP from historical data (total across all languages)

    Args:
        username: The Duolingo username
        current_language_xp: Current XP summed across the user's language courses
        history: Optional pre-loaded history data. If None, loads from default JSON storage.
        reference_date: Optional date to use for week boundary calculations.
                       If None, uses datetime.now(). Use yesterday's date when
                       generating weekly reports on Monday morning to report on
                       the previous week (Mon-Sun) instead of the new week.
    """
    try:
        if history is None:
            from .data_storage import DataStorage

            storage = DataStorage()
            history = storage.load_history()

        baseline = find_week_baseline(username, history or [], reference_date)
        if baseline is None:
            return 0

        return max(0, current_language_xp - get_language_xp(baseline))

    except Exception:
        # If we can't calculate weekly XP (e.g., no history), return 0
        return 0


def calculate_weekly_xp_per_language(
    username: str,
    current_language_progress: dict[str, LanguageProgress],
    history: list[dict[str, Any]] | None = None,
    reference_date: datetime | None = None,
) -> dict[str, int]:
    """Calculate weekly XP per language from historical data

    Args:
        username: The Duolingo username
        current_language_progress: Current language progress data
        history: Optional pre-loaded history data. If None, loads from default JSON storage.
        reference_date: Optional date to use for week boundary calculations.
                       If None, uses datetime.now(). Use yesterday's date when
                       generating weekly reports on Monday morning to report on
                       the previous week (Mon-Sun) instead of the new week.
    """
    try:
        if history is None:
            from .data_storage import DataStorage

            storage = DataStorage()
            history = storage.load_history()

        if not history:
            return {}

        baseline = find_week_baseline(username, history, reference_date) or {}
        baseline_languages = baseline.get("language_progress", {})

        # Languages missing from the baseline were started this week
        return {
            lang: max(
                0,
                lang_data.get("xp", 0) - baseline_languages.get(lang, {}).get("xp", 0),
            )
            for lang, lang_data in current_language_progress.items()
        }

    except Exception:
        # If we can't calculate weekly XP, return empty dict
        return {}


def calculate_daily_xp(
    username: str,
    current_language_xp: int,
    history: list[dict[str, Any]] | None = None,
) -> int:
    """Calculate daily XP from historical data (XP earned since yesterday)

    Args:
        username: The Duolingo username
        current_language_xp: Current XP summed across the user's language courses
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
                user_data = find_user_data(entry, username)
                if user_data is not None:
                    yesterday_xp = get_language_xp(user_data)
                    break

        if yesterday_xp is not None:
            return max(0, current_language_xp - yesterday_xp)

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
                user_data = find_user_data(entry, username)
                if user_data is not None:
                    yesterday_languages = user_data.get("language_progress", {})
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
        language_xp = sum(lang["xp"] for lang in language_progress.values())

        return UserProgress(
            username=username,
            name=user.get("name", username),
            streak=streak,
            total_xp=total_xp,
            language_xp=language_xp,
            other_xp=max(0, total_xp - language_xp),
            weekly_xp=calculate_weekly_xp(username, language_xp, history),
            weekly_xp_per_language=weekly_xp_per_language,
            daily_xp=calculate_daily_xp(username, language_xp, history),
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
                    print(f"   Language XP: {progress['language_xp']}")
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

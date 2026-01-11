"""HTML report generation for Duolingo Family League"""

import html
from datetime import datetime
from typing import Any
from .html_templates import DAILY_REPORT_TEMPLATE, WEEKLY_REPORT_TEMPLATE
from .i18n import get_i18n, translate_language_name
from .report_generator import generate_leaderboard

# Constants
TOP_POSITIONS_COUNT = 3
POSITION_EMOJIS = ["🥇", "🥈", "🥉"]


# Removed duplicate leaderboard function - now using the one from report_generator.py


def generate_daily_html_report(results: dict[str, Any]) -> str:
    """Generate a daily progress report in HTML format"""

    i18n = get_i18n()
    leaderboard = generate_leaderboard(results, sort_by="daily")

    # Generate leaderboard items HTML
    leaderboard_items: list[str] = []

    for i, member in enumerate(leaderboard, 1):
        emoji = POSITION_EMOJIS[i - 1] if i <= len(POSITION_EMOJIS) else f"{i}."

        # Format language progress (using daily XP for daily report)
        daily_xp_per_lang = member["data"].get("daily_xp_per_language", {})
        active_langs = [
            f"{html.escape(translate_language_name(lang))} +{xp}"
            for lang, xp in daily_xp_per_lang.items()
            if xp > 0
        ]
        lang_info = f" ({', '.join(active_langs)})" if active_langs else ""

        # Format streak text
        streak_count = member["streak"]
        streak_text = i18n.get(
            "day_streak" if streak_count == 1 else "days_streak", count=streak_count
        )

        # Use daily XP for daily report
        daily_xp = member["data"].get("daily_xp", 0)

        leaderboard_items.append(
            f"""
            <li>
                <div class="position">{emoji}</div>
                <div class="member-info">
                    <div class="member-name">{html.escape(member["name"])}</div>
                    <div class="member-stats">
                        {streak_text} | {i18n.get("daily_xp", count=daily_xp)}
                    </div>
                    {f'<div class="language-progress">{lang_info}</div>' if lang_info else ""}
                </div>
            </li>
        """.strip()
        )

    # Generate streak alerts HTML
    alerts: list[str] = []
    for member_name, data in results.items():
        if "error" not in data and data["streak"] == 0:
            alerts.append(
                f"<li>{html.escape(data.get('name', member_name))} {i18n.get('needs_to_practice')}</li>"
            )

    if alerts:
        streak_alerts_html = (
            f'<div class="alert warning"><ul>{"".join(alerts)}</ul></div>'
        )
    else:
        streak_alerts_html = f'<div class="alert success">✅ {i18n.get("everyone_maintaining_streaks")}</div>'

    # Format current date
    current_date = datetime.now().strftime(i18n.get("date_format"))

    return DAILY_REPORT_TEMPLATE.format(
        lang=i18n.language,
        title=i18n.get("daily_report_title"),
        header=i18n.get("daily_report_header"),
        subtitle=i18n.get("daily_report_subtitle"),
        date=current_date,
        standings_title=i18n.get("standings_title"),
        leaderboard_items="".join(leaderboard_items),
        streak_alerts_title=i18n.get("streak_alerts_title"),
        streak_alerts=streak_alerts_html,
        footer_message=i18n.get("keep_learning"),
    )


def generate_weekly_html_report(results: dict[str, Any], goals: dict[str, Any]) -> str:
    """Generate comprehensive weekly family report in HTML format"""

    i18n = get_i18n()
    leaderboard = generate_leaderboard(results)

    # Generate leaderboard items HTML
    leaderboard_items: list[str] = []
    css_classes = ["first", "second", "third"]

    for i, member in enumerate(leaderboard, 1):
        if i <= TOP_POSITIONS_COUNT:
            emoji = POSITION_EMOJIS[i - 1]
            css_class = css_classes[i - 1]
        else:
            emoji = f"{i}."
            css_class = ""

        # Format streak text
        streak_count = member["streak"]
        streak_text = i18n.get(
            "day_streak" if streak_count == 1 else "days_streak", count=streak_count
        )

        leaderboard_items.append(
            f"""
            <div class="leaderboard-item {css_class}">
                <div class="position">{emoji}</div>
                <div class="member-name">{html.escape(member["name"])}</div>
                <div class="member-stats">
                    {streak_text} | {i18n.get("weekly_xp", count=member["weekly_xp"])} | {i18n.get("total_xp", count=member["total_xp"])}
                </div>
            </div>
        """.strip()
        )

    # Generate detailed member progress HTML
    member_details: list[str] = []
    for member_name, data in results.items():
        if "error" in data:
            member_details.append(
                f"""
                <div class="member-detail">
                    <div class="member-header">
                        <div class="member-avatar">👤</div>
                        <div>
                            <div class="member-title">{html.escape(data.get("name", member_name))}</div>
                        </div>
                    </div>
                    <div class="progress-item">
                        ❌ {i18n.get("unable_to_check", error=html.escape(str(data["error"])))}
                    </div>
                </div>
            """.strip()
            )
            continue

        # Format streak text
        streak_count = data["streak"]
        streak_text = i18n.get("current_streak", count=streak_count)

        # Generate streak status badge
        streak_goal = goals.get("streak_goal", 7)
        if data["streak"] >= streak_goal:
            streak_status = f'<span class="status-badge achieved">🔥 {i18n.get("streak_goal_achieved")}</span>'
        elif data["streak"] >= streak_goal // 2:
            streak_status = f'<span class="status-badge progress">⚡ {i18n.get("good_progress_streak", goal=streak_goal)}</span>'
        else:
            streak_status = f'<span class="status-badge warning">⚠️ {i18n.get("work_needed_streak", goal=streak_goal)}</span>'

        # Generate weekly XP status badge
        weekly_goal = goals.get("weekly_xp_goal", 500)
        if data["weekly_xp"] >= weekly_goal:
            xp_status = f'<span class="status-badge achieved">🎯 {i18n.get("weekly_xp_goal_achieved", current=data["weekly_xp"], goal=weekly_goal)}</span>'
        else:
            xp_status = f'<span class="status-badge progress">📈 {i18n.get("weekly_xp_progress", current=data["weekly_xp"], goal=weekly_goal)}</span>'

        # Generate language progress HTML
        language_progress_html = ""
        if data.get("language_progress"):
            language_items: list[str] = []
            weekly_xp_per_lang = data.get("weekly_xp_per_language", {})
            for lang, progress in data["language_progress"].items():
                if progress["xp"] > 0:
                    weekly_lang_xp = weekly_xp_per_lang.get(lang, 0)
                    if weekly_lang_xp > 0:
                        language_items.append(
                            f"""
                            <div class="language-item">
                                <span class="language-name">{html.escape(translate_language_name(lang))}:</span> 
                                {i18n.get("xp", xp=progress["xp"])} 
                                ({i18n.get("weekly_gain", xp=weekly_lang_xp)})
                            </div>
                        """.strip()
                        )
                    else:
                        language_items.append(
                            f"""
                            <div class="language-item">
                                <span class="language-name">{html.escape(translate_language_name(lang))}:</span> 
                                {i18n.get("xp", xp=progress["xp"])}
                            </div>
                        """.strip()
                        )
                else:
                    language_items.append(
                        f"""
                        <div class="language-item">
                            <span class="language-name">{html.escape(translate_language_name(lang))}:</span> {i18n.get("not_started_yet")}
                        </div>
                    """.strip()
                    )

            if language_items:
                language_progress_html = f"""
                    <div class="progress-item">
                        📚 {i18n.get("language_progress")}
                        <div class="language-list">
                            {"".join(language_items)}
                        </div>
                    </div>
                """
        elif data.get("active_languages"):
            translated_languages = [
                translate_language_name(lang) for lang in data["active_languages"]
            ]
            language_progress_html = f"""
                <div class="progress-item">
                    📚 {i18n.get("active_languages", languages=", ".join(translated_languages))}
                </div>
            """

        member_details.append(
            f"""
            <div class="member-detail">
                    <div class="member-header">
                        <div class="member-avatar">👤</div>
                        <div>
                            <div class="member-title">{html.escape(data.get("name", member_name))}</div>
                            <div class="member-username">({html.escape(data["username"])})</div>
                        </div>
                    </div>                <div class="progress-item">{streak_text}</div>
                <div class="progress-item">{streak_status}</div>
                <div class="progress-item">{xp_status}</div>
                {language_progress_html}
            </div>
        """.strip()
        )

    # Generate goals list HTML
    streak_goal = goals.get("streak_goal", 7)
    weekly_xp_goal = goals.get("weekly_xp_goal", 500)
    goals_list: list[str] = [
        f"<li>{i18n.get('maintain_streak_goal', goal=streak_goal)}</li>",
        f"<li>{i18n.get('earn_xp_goal', goal=weekly_xp_goal)}</li>",
        f"<li>{i18n.get('beat_personal_best')}</li>",
    ]

    # Format dates
    current_date = datetime.now()
    week_ending = current_date.strftime(i18n.get("date_format"))
    generated_date = current_date.strftime(i18n.get("datetime_format"))

    return WEEKLY_REPORT_TEMPLATE.format(
        lang=i18n.language,
        title=i18n.get("weekly_report_title"),
        header=i18n.get("weekly_report_header"),
        subtitle=i18n.get("weekly_report_subtitle"),
        week_ending=i18n.get("week_ending", date=week_ending),
        generated_date=i18n.get("generated_date", date=generated_date),
        family_leaderboard_title=i18n.get("family_leaderboard_title"),
        leaderboard_items="".join(leaderboard_items),
        detailed_progress_title=i18n.get("detailed_progress_title"),
        member_details="".join(member_details),
        goals_title=i18n.get("goals_title"),
        goals_list="".join(goals_list),
        keep_up_message=i18n.get("keep_up_message"),
        footer_message=i18n.get("keep_learning"),
    )

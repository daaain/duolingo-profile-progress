"""Report generation for Duolingo Family League"""

from datetime import datetime
from typing import Any


def generate_leaderboard(results: dict[str, Any]) -> list[dict[str, Any]]:
    """Generate family leaderboard"""
    leaderboard_data: list[dict[str, Any]] = []

    for member_name, data in results.items():
        if "error" not in data:
            leaderboard_data.append(
                {
                    "name": member_name,
                    "streak": data["streak"],
                    "weekly_xp": data["weekly_xp"],
                    "total_xp": data["total_xp"],
                    "target_xp": data.get(
                        "total_languages_xp", data.get("target_languages_xp", 0)
                    ),
                    "data": data,
                }
            )

    # Sort by multiple criteria
    leaderboard_data.sort(
        key=lambda x: (x["streak"], x["weekly_xp"], x["total_xp"]), reverse=True
    )

    return leaderboard_data


def generate_daily_report(results: dict[str, Any]) -> str:
    """Generate a concise daily progress report"""
    leaderboard = generate_leaderboard(results)

    report: list[str] = []
    report.append("📊 DUOLINGO FAMILY LEAGUE - DAILY UPDATE")
    report.append("=" * 45)
    report.append(f"Date: {datetime.now().strftime('%Y-%m-%d')}")
    report.append("")

    # Quick leaderboard
    report.append("🏆 Today's Standings:")
    for i, member in enumerate(leaderboard[:3], 1):
        emoji = ["🥇", "🥈", "🥉"][i - 1] if i <= 3 else f"{i}."
        weekly_xp_per_lang = member["data"].get("weekly_xp_per_language", {})
        active_langs = [
            f"{lang} +{xp}" for lang, xp in weekly_xp_per_lang.items() if xp > 0
        ]
        lang_info = f" ({', '.join(active_langs)})" if active_langs else ""
        report.append(
            f"{emoji} {member['name']}: {member['streak']} day streak | {member['weekly_xp']} weekly XP{lang_info}"
        )

    report.append("")

    # Streak warnings
    report.append("⚠️ Streak Alerts:")
    alerts: list[str] = []
    for member_name, data in results.items():
        if "error" not in data and data["streak"] == 0:
            alerts.append(f"  • {member_name} needs to practice today!")

    if alerts:
        report.extend(alerts)
    else:
        report.append("  ✅ Everyone is maintaining their streaks!")

    report.append("\nKeep learning! 🌟")

    return "\n".join(report)


def generate_weekly_report(results: dict[str, Any], goals: dict[str, Any]) -> str:
    """Generate comprehensive weekly family report"""
    leaderboard = generate_leaderboard(results)

    report: list[str] = []
    report.append("🏆 DUOLINGO FAMILY LEAGUE - WEEKLY REPORT")
    report.append("=" * 55)
    report.append(f"Week ending: {datetime.now().strftime('%Y-%m-%d')}")
    report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    # Overall leaderboard
    report.append("🥇 FAMILY LEADERBOARD")
    report.append("-" * 25)

    for i, member in enumerate(leaderboard, 1):
        if i == 1:
            trophy = "🥇"
        elif i == 2:
            trophy = "🥈"
        elif i == 3:
            trophy = "🥉"
        else:
            trophy = f"{i}."

        report.append(f"{trophy} {member['name']}")
        report.append(
            f"    Streak: {member['streak']} days | Weekly XP: {member['weekly_xp']} | Total XP: {member['total_xp']:,}"
        )

    report.append("")

    # Detailed individual progress
    report.append("📊 DETAILED PROGRESS")
    report.append("-" * 22)

    for member_name, data in results.items():
        if "error" in data:
            report.append(f"\n👤 {member_name}")
            report.append(f"   ❌ Unable to check progress: {data['error']}")
            continue

        report.append(f"\n👤 {member_name} ({data['username']})")
        report.append(f"   Current streak: {data['streak']} days")

        # Streak status
        streak_goal = goals.get("streak_goal", 7)
        if data["streak"] >= streak_goal:
            report.append("   🔥 STREAK GOAL ACHIEVED!")
        elif data["streak"] >= streak_goal // 2:
            report.append(f"   ⚡ Good progress towards {streak_goal}-day goal")
        else:
            report.append(f"   ⚠️  Work needed for {streak_goal}-day streak goal")

        # Weekly XP status
        weekly_goal = goals.get("weekly_xp_goal", 500)
        if data["weekly_xp"] >= weekly_goal:
            report.append(
                f"   🎯 WEEKLY XP GOAL ACHIEVED! ({data['weekly_xp']}/{weekly_goal})"
            )
        else:
            report.append(
                f"   📈 Weekly XP progress: {data['weekly_xp']}/{weekly_goal}"
            )

        # Language-specific progress
        if data.get("language_progress"):
            report.append("   📚 Language Progress:")
            weekly_xp_per_lang = data.get("weekly_xp_per_language", {})
            for lang, progress in data["language_progress"].items():
                if progress["xp"] > 0:
                    weekly_lang_xp = weekly_xp_per_lang.get(lang, 0)
                    if weekly_lang_xp > 0:
                        report.append(
                            f"      {lang}: Level {progress['level']} | {progress['xp']:,} XP (+{weekly_lang_xp} this week)"
                        )
                    else:
                        report.append(
                            f"      {lang}: Level {progress['level']} | {progress['xp']:,} XP"
                        )
                else:
                    report.append(f"      {lang}: Not started yet")
        elif data.get("active_languages"):
            report.append(
                f"   📚 Active Languages: {', '.join(data['active_languages'])}"
            )

        report.append("")

    # Weekly challenges and goals
    report.append("🎯 THIS WEEK'S FAMILY GOALS")
    report.append("-" * 30)
    report.append(f"• Maintain a {goals.get('streak_goal', 7)}-day streak")
    report.append(f"• Earn {goals.get('weekly_xp_goal', 500)} XP this week")
    report.append("• Try to beat your personal best!")
    report.append("\nKeep up the great work, everyone! 🌟")

    return "\n".join(report)


def generate_daily_report_html(results: dict[str, Any]) -> str:
    """Generate a daily progress report in HTML format"""
    from .html_report_generator import generate_daily_html_report

    return generate_daily_html_report(results)


def generate_weekly_report_html(results: dict[str, Any], goals: dict[str, Any]) -> str:
    """Generate comprehensive weekly family report in HTML format"""
    from .html_report_generator import generate_weekly_html_report

    return generate_weekly_html_report(results, goals)

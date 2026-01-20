#!/usr/bin/env python3
"""
Duolingo Family League Monitor
Tracks family members' language learning progress across multiple languages
Generates daily/weekly leaderboards and progress reports
"""

import argparse
from datetime import datetime, timedelta
from pathlib import Path
from typing import cast

from src.config import load_config, get_email_config, get_storage_config
from src.duolingo_api import (
    check_all_family,
    calculate_weekly_xp,
    calculate_weekly_xp_per_language,
)
from src.storage_factory import StorageFactory
from src.report_generator import generate_daily_report, generate_weekly_report
from src.html_report_generator import (
    generate_daily_html_report,
    generate_weekly_html_report,
)
from src.email_sender import send_email, should_send_daily, should_send_weekly
from src.i18n import set_global_language, get_language_from_env, get_i18n
from src.types import UserProgress


def generate_index_html(reports_dir: Path) -> str:
    """Generate an index.html that links to the latest daily and weekly reports"""
    daily_dir = reports_dir / "daily"
    weekly_dir = reports_dir / "weekly"

    # Find the latest reports
    latest_daily = None
    latest_weekly = None

    if daily_dir.exists():
        daily_files = sorted(daily_dir.glob("*.html"), reverse=True)
        if daily_files:
            latest_daily = daily_files[0].name

    if weekly_dir.exists():
        weekly_files = sorted(weekly_dir.glob("*.html"), reverse=True)
        if weekly_files:
            latest_weekly = weekly_files[0].name

    # Generate simple index page
    daily_link = (
        f'<a href="daily/{latest_daily}">Latest Daily Report</a>'
        if latest_daily
        else "<span>No daily reports yet</span>"
    )
    weekly_link = (
        f'<a href="weekly/{latest_weekly}">Latest Weekly Report</a>'
        if latest_weekly
        else "<span>No weekly reports yet</span>"
    )

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Duolingo Family League</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            max-width: 600px;
            margin: 50px auto;
            padding: 20px;
            text-align: center;
        }}
        h1 {{ color: #58CC02; }}
        .links {{ margin-top: 30px; }}
        .links a {{
            display: block;
            margin: 15px 0;
            padding: 15px 30px;
            background: #58CC02;
            color: white;
            text-decoration: none;
            border-radius: 12px;
            font-weight: bold;
        }}
        .links a:hover {{ background: #4CAF00; }}
        .links span {{ color: #999; }}
    </style>
</head>
<body>
    <h1>🦉 Duolingo Family League</h1>
    <div class="links">
        {daily_link}
        {weekly_link}
    </div>
</body>
</html>
"""


def save_html_report(
    html_content: str,
    report_type: str,
    date_str: str,
    output_dir: str = "reports",
) -> str:
    """Save HTML report to the reports directory for GitHub Pages

    Args:
        html_content: The HTML content to save
        report_type: Type of report ('daily', 'weekly', or 'status')
        date_str: Date string in YYYYMMDD format
        output_dir: Output directory (default: reports)

    Returns:
        Path to the saved file
    """
    reports_dir = Path(output_dir)
    reports_dir.mkdir(exist_ok=True)

    # Create subdirectory for report type
    type_dir = reports_dir / report_type
    type_dir.mkdir(exist_ok=True)

    # Save dated report
    dated_filename = f"{date_str}.html"
    dated_path = type_dir / dated_filename
    with open(dated_path, "w") as f:
        f.write(html_content)

    # Generate index page that links to latest reports
    index_html = generate_index_html(reports_dir)
    index_path = reports_dir / "index.html"
    with open(index_path, "w") as f:
        f.write(index_html)

    return str(dated_path)


def main():
    """Main execution function"""
    # Ensure report language is set from environment variable
    # (must be done before generating reports as i18n module may have loaded earlier)
    set_global_language(get_language_from_env())

    parser = argparse.ArgumentParser(description="Duolingo Family League Tracker")
    parser.add_argument(
        "--daily", action="store_true", help="Run daily check and save data"
    )
    parser.add_argument(
        "--weekly", action="store_true", help="Generate and send weekly report"
    )
    parser.add_argument(
        "--send-email", action="store_true", help="Send report via email"
    )
    parser.add_argument(
        "--check-only",
        action="store_true",
        help="Just check and display current status",
    )
    parser.add_argument(
        "--html",
        action="store_true",
        help="Generate HTML reports in addition to text reports",
    )

    args = parser.parse_args()

    # Load configuration from environment variables
    config = load_config()
    if not config:
        print("\nPlease configure your .env file with DUOLINGO_USERNAMES")
        return

    email_config = get_email_config(config)
    storage_config = get_storage_config(config)

    # Initialize data storage using factory
    storage = StorageFactory.create_storage(
        backend=storage_config["backend"],
        data_dir=storage_config["data_dir"],
        db_path=storage_config["sqlite_db_path"],
        gist_id=storage_config.get("gist_id"),
    )

    # Load history once for XP calculations
    history = storage.load_history()

    # Check all family members
    results = check_all_family(config, history)

    if args.daily:
        # Daily mode: save data and optionally send daily report
        storage.save_daily_data(results)
        report = generate_daily_report(results)
        print("\n" + report)

        # Generate HTML report (always needed for emails with i18n support)
        html_report = generate_daily_html_report(results)

        if args.send_email or should_send_daily(email_config):
            i18n = get_i18n()
            current_date = datetime.now().strftime(i18n.get("date_format"))
            subject = i18n.get("email_subject_daily", date=current_date)
            send_email(
                report,
                email_config,
                subject=subject,
                recipient_list=email_config.get("daily_email_list"),
                html_content=html_report,
            )

        # Save report to file
        report_filename = f"daily_report_{datetime.now().strftime('%Y%m%d')}.txt"
        with open(report_filename, "w") as f:
            f.write(report)
        print(f"\nDaily report saved to {report_filename}")

        # Save HTML report if requested
        if args.html:
            date_str = datetime.now().strftime("%Y%m%d")
            html_path = save_html_report(html_report, "daily", date_str)
            print(f"Daily HTML report saved to {html_path}")
            print("Latest report available at reports/index.html")

    elif args.weekly:
        # Weekly mode: generate comprehensive report
        # First save the data with current week's XP (for history tracking)
        storage.save_daily_data(results)

        # Recalculate weekly XP for the PREVIOUS week (for the report)
        # Use yesterday as reference so week boundary is last Mon-Sun
        # This fixes the bug where Monday morning reports show 0 XP because
        # the calculation uses the new week starting today instead of the
        # completed week that the report should cover.
        reference_date = datetime.now() - timedelta(days=1)
        for member_name, user_data in results.items():
            if "error" not in user_data:
                # Recalculate weekly XP using previous week reference
                # Cast to UserProgress since we've checked there's no error
                progress = cast(UserProgress, user_data)
                progress["weekly_xp"] = calculate_weekly_xp(
                    progress["username"],
                    progress["total_xp"],
                    history,
                    reference_date=reference_date,
                )
                progress["weekly_xp_per_language"] = calculate_weekly_xp_per_language(
                    progress["username"],
                    progress["language_progress"],
                    history,
                    reference_date=reference_date,
                )

        goals = config.get("goals", {})
        report = generate_weekly_report(results, goals)
        print("\n" + report)

        # Generate HTML report (always needed for emails with i18n support)
        html_report = generate_weekly_html_report(results, goals)

        if args.send_email or should_send_weekly(email_config):
            i18n = get_i18n()
            current_date = datetime.now().strftime(i18n.get("date_format"))
            subject = i18n.get("email_subject_weekly", date=current_date)
            send_email(
                report,
                email_config,
                subject=subject,
                html_content=html_report,
            )

        # Save report to file
        report_filename = f"weekly_report_{datetime.now().strftime('%Y%m%d')}.txt"
        with open(report_filename, "w") as f:
            f.write(report)
        print(f"\nWeekly report saved to {report_filename}")

        # Save HTML report if requested
        if args.html:
            date_str = datetime.now().strftime("%Y%m%d")
            html_path = save_html_report(html_report, "weekly", date_str)
            print(f"Weekly HTML report saved to {html_path}")
            print("Latest report available at reports/index.html")

    else:
        # Default: just check and display
        report = generate_daily_report(results)
        print("\n" + report)

        if args.send_email:
            html_report = generate_daily_html_report(results)
            i18n = get_i18n()
            current_date = datetime.now().strftime(i18n.get("date_format"))
            subject = i18n.get("email_subject_daily", date=current_date)
            send_email(
                report,
                email_config,
                subject=subject,
                html_content=html_report,
            )

        # Generate HTML report if requested
        if args.html:
            html_report = generate_daily_html_report(results)
            date_str = datetime.now().strftime("%Y%m%d")
            html_path = save_html_report(html_report, "status", date_str)
            print(f"\nStatus HTML report saved to {html_path}")
            print("Latest report available at reports/index.html")


if __name__ == "__main__":
    main()

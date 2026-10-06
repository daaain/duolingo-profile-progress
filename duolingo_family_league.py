#!/usr/bin/env python3
"""
Duolingo Family League Monitor
Tracks family members' language learning progress across multiple languages
Generates daily/weekly leaderboards and progress reports
"""

import argparse
from datetime import datetime, timedelta
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
                    progress["language_xp"],
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
        report = generate_weekly_report(results, goals, week_ending=reference_date)
        print("\n" + report)

        # Generate HTML report (always needed for emails with i18n support)
        html_report = generate_weekly_html_report(
            results, goals, week_ending=reference_date
        )

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


if __name__ == "__main__":
    main()

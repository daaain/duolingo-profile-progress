#!/usr/bin/env python3
"""
Duolingo Family League Monitor
Tracks family members' language learning progress across multiple languages
Generates daily/weekly leaderboards and progress reports
"""

import argparse
from datetime import datetime
from pathlib import Path

from src.config import load_config, get_email_config, get_storage_config
from src.duolingo_api import check_all_family
from src.storage_factory import StorageFactory
from src.report_generator import generate_daily_report, generate_weekly_report
from src.html_report_generator import (
    generate_daily_html_report,
    generate_weekly_html_report,
)
from src.email_sender import send_email, should_send_daily, should_send_weekly


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

    # Also save as index.html (latest report)
    index_path = reports_dir / "index.html"
    with open(index_path, "w") as f:
        f.write(html_content)

    return str(dated_path)


def main():
    """Main execution function"""
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

    # Check all family members
    results = check_all_family(config)

    if args.daily:
        # Daily mode: save data and optionally send daily report
        storage.save_daily_data(results)
        report = generate_daily_report(results)
        print("\n" + report)

        if args.send_email or should_send_daily(email_config):
            send_email(report, email_config, "Daily Update - ")

        # Save report to file
        report_filename = f"daily_report_{datetime.now().strftime('%Y%m%d')}.txt"
        with open(report_filename, "w") as f:
            f.write(report)
        print(f"\nDaily report saved to {report_filename}")

        # Generate HTML report if requested
        if args.html:
            html_report = generate_daily_html_report(results)
            date_str = datetime.now().strftime("%Y%m%d")
            html_path = save_html_report(html_report, "daily", date_str)
            print(f"Daily HTML report saved to {html_path}")
            print("Latest report available at reports/index.html")

    elif args.weekly:
        # Weekly mode: generate comprehensive report
        goals = config.get("goals", {})
        report = generate_weekly_report(results, goals)
        print("\n" + report)

        if args.send_email or should_send_weekly(email_config):
            send_email(report, email_config, "Weekly Report - ")

        # Save report to file
        report_filename = f"weekly_report_{datetime.now().strftime('%Y%m%d')}.txt"
        with open(report_filename, "w") as f:
            f.write(report)
        print(f"\nWeekly report saved to {report_filename}")

        # Generate HTML report if requested
        if args.html:
            html_report = generate_weekly_html_report(results, goals)
            date_str = datetime.now().strftime("%Y%m%d")
            html_path = save_html_report(html_report, "weekly", date_str)
            print(f"Weekly HTML report saved to {html_path}")
            print("Latest report available at reports/index.html")

        # Also save the data
        storage.save_daily_data(results)

    else:
        # Default: just check and display
        report = generate_daily_report(results)
        print("\n" + report)

        if args.send_email:
            send_email(report, email_config, "Status Update - ")

        # Generate HTML report if requested
        if args.html:
            html_report = generate_daily_html_report(results)
            date_str = datetime.now().strftime("%Y%m%d")
            html_path = save_html_report(html_report, "status", date_str)
            print(f"\nStatus HTML report saved to {html_path}")
            print("Latest report available at reports/index.html")


if __name__ == "__main__":
    main()

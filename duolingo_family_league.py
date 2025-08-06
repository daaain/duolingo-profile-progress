#!/usr/bin/env python3
"""
Duolingo Family League Monitor
Tracks family members' language learning progress across multiple languages
Generates daily/weekly leaderboards and progress reports
"""

import argparse
from datetime import datetime

from src.config import load_config, get_email_config
from src.duolingo_api import check_all_family
from src.data_storage import DataStorage
from src.report_generator import generate_daily_report, generate_weekly_report
from src.email_sender import send_email, should_send_daily, should_send_weekly


def main():
    """Main execution function"""
    parser = argparse.ArgumentParser(description='Duolingo Family League Tracker')
    parser.add_argument('--daily', action='store_true', help='Run daily check and save data')
    parser.add_argument('--weekly', action='store_true', help='Generate and send weekly report')
    parser.add_argument('--send-email', action='store_true', help='Send report via email')
    parser.add_argument('--check-only', action='store_true', help='Just check and display current status')
    
    args = parser.parse_args()
    
    # Load configuration from environment variables
    config = load_config()
    if not config:
        print("\nPlease configure your .env file with DUOLINGO_USERNAMES")
        return
    
    email_config = get_email_config(config)
    
    # Initialize data storage
    storage = DataStorage()
    
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
        with open(report_filename, 'w') as f:
            f.write(report)
        print(f"\nDaily report saved to {report_filename}")
        
    elif args.weekly:
        # Weekly mode: generate comprehensive report
        goals = config.get('goals', {})
        report = generate_weekly_report(results, goals)
        print("\n" + report)
        
        if args.send_email or should_send_weekly(email_config):
            send_email(report, email_config, "Weekly Report - ")
        
        # Save report to file
        report_filename = f"weekly_report_{datetime.now().strftime('%Y%m%d')}.txt"
        with open(report_filename, 'w') as f:
            f.write(report)
        print(f"\nWeekly report saved to {report_filename}")
        
        # Also save the data
        storage.save_daily_data(results)
        
    else:
        # Default: just check and display
        report = generate_daily_report(results)
        print("\n" + report)
        
        if args.send_email:
            send_email(report, email_config, "Status Update - ")


if __name__ == "__main__":
    main()
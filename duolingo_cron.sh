#!/bin/bash

# Enhanced Cron Script with Catch-up Functionality
# This script ensures weekly reports are sent even if your Mac was off during scheduled time

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCRIPT_PATH="$SCRIPT_DIR/duolingo_family_league.py"
LOCK_FILE="$SCRIPT_DIR/.duolingo_weekly_lock"
LOG_FILE="$SCRIPT_DIR/duolingo_cron.log"

# Function to log messages
log_message() {
    echo "$(date '+%Y-%m-%d %H:%M:%S'): $1" >> "$LOG_FILE"
}

# Get current week number (year + week)
CURRENT_WEEK=$(date +%Y%U)

# Check if we've already run this week
if [ -f "$LOCK_FILE" ]; then
    LAST_RUN_WEEK=$(cat "$LOCK_FILE")
    if [ "$CURRENT_WEEK" = "$LAST_RUN_WEEK" ]; then
        log_message "Already ran this week ($CURRENT_WEEK)"
        exit 0
    fi
fi

# Run the script
log_message "Running Duolingo Family League report for week $CURRENT_WEEK"
cd "$SCRIPT_DIR"

if /usr/bin/python3 "$SCRIPT_PATH" --weekly-email >> "$LOG_FILE" 2>&1; then
    # Mark this week as completed
    echo "$CURRENT_WEEK" > "$LOCK_FILE"
    log_message "SUCCESS - Completed weekly report for week $CURRENT_WEEK"
else
    log_message "ERROR - Failed to complete weekly report for week $CURRENT_WEEK"
    exit 1
fi

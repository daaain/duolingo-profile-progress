#!/bin/bash

# Duolingo Family League - Robust Wrapper Script
# This script ensures the weekly report runs even if your Mac was asleep

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCRIPT_PATH="$SCRIPT_DIR/duolingo_family_league.py"
LOG_FILE="$SCRIPT_DIR/duolingo_last_run.log"
ERROR_LOG="$SCRIPT_DIR/duolingo_error.log"

# Function to log messages
log_message() {
    echo "$(date '+%Y-%m-%d %H:%M:%S'): $1" | tee -a "$LOG_FILE"
}

# Get today's date and last Monday
TODAY=$(date +%Y-%m-%d)
LAST_MONDAY=$(date -v-monday +%Y-%m-%d)

# Check if we've run this week
if [ ! -f "$LOG_FILE" ] || ! grep -q "$LAST_MONDAY" "$LOG_FILE"; then
    log_message "Running weekly Duolingo report for week of $LAST_MONDAY"
    
    # Change to script directory
    cd "$SCRIPT_DIR"
    
    # Run the Python script
    if /usr/bin/python3 "$SCRIPT_PATH" --weekly-email 2>> "$ERROR_LOG"; then
        log_message "SUCCESS - Report sent for week of $LAST_MONDAY"
    else
        log_message "ERROR - Failed to send report for week of $LAST_MONDAY"
        exit 1
    fi
else
    log_message "Report already sent this week (week of $LAST_MONDAY)"
fi

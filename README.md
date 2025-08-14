# Duolingo Family League Tracker

Track your family's Duolingo language learning progress with automated daily and weekly reports.

## Features

- **Multi-language tracking**: Monitor progress across multiple languages for each family member
- **Daily & Weekly Reports**: Get automated email reports with leaderboards and progress updates
- **HTML Export**: Generate beautiful HTML reports with responsive design and styling
- **Multi-language Support**: Reports available in English and Hungarian (more languages can be added)
- **Streak tracking**: Monitor and celebrate streak achievements
- **Goal setting**: Set weekly XP and streak goals for motivation
- **Data persistence**: Automatically saves daily progress data for historical tracking
- **Secure configuration**: Use environment variables for sensitive credentials
- **Modular architecture**: Clean separation of concerns for easy maintenance

## Installation

### 1. Environment Variables

Copy the example environment file:

```bash
cp .env.example .env
```

Edit `.env` with your configuration:

```bash
# Duolingo Usernames (comma-separated list)
# Note: Profiles must be public for the API to access them
DUOLINGO_USERNAMES=dad_username,mom_username,alice_username

# Goals Configuration
WEEKLY_XP_GOAL=500
STREAK_GOAL=7

# Report Language (optional - defaults to English)
# Supported: en (English), hu (Hungarian)
DUOLINGO_REPORT_LANGUAGE=en

# Email Configuration
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SENDER_EMAIL=your_email@gmail.com
SENDER_PASSWORD=your_app_password
FAMILY_EMAIL_LIST=family1@example.com,family2@example.com
SEND_DAILY=false
SEND_WEEKLY=true
```

**Note**: For Gmail, you'll need to generate an [App Password](https://support.google.com/accounts/answer/185833).

## Usage

### Check Current Status

```bash
python duolingo_family_league.py
```

### Daily Report

Save daily data and optionally send email:

```bash
# Save data only
python duolingo_family_league.py --daily

# Save data and send email
python duolingo_family_league.py --daily --send-email

# Generate HTML report in addition to text
python duolingo_family_league.py --daily --html
```

### Weekly Report

Generate comprehensive weekly report:

```bash
# Display and save report
python duolingo_family_league.py --weekly

# Also send via email
python duolingo_family_league.py --weekly --send-email

# Generate HTML report in addition to text
python duolingo_family_league.py --weekly --html
```

### HTML Reports

Generate beautiful HTML reports with responsive design:

```bash
# Generate HTML for current status
python duolingo_family_league.py --html

# Generate HTML daily report
python duolingo_family_league.py --daily --html

# Generate HTML weekly report
python duolingo_family_league.py --weekly --html
```

HTML reports include professional styling, responsive design, and rich formatting with progress badges and visual indicators.

### Automation with Cron

Add to your crontab for automatic daily and weekly reports:

```bash
# Daily check at 8 PM
0 20 * * * cd /path/to/duolingo-family-league && python duolingo_family_league.py --daily

# Weekly report on Sundays at 9 PM
0 21 * * 0 cd /path/to/duolingo-family-league && python duolingo_family_league.py --weekly --send-email
```

### macOS LaunchAgent (Recommended for Mac users)

The project includes a LaunchAgent configuration for reliable scheduling:

1. Update the username in the plist file:

   ```bash
   sed -i '' 's/YOUR_USERNAME/'"$USER"'/g' com.duolingo.familyleague.plist
   ```

2. Install the LaunchAgent:

   ```bash
   cp com.duolingo.familyleague.plist ~/Library/LaunchAgents/
   launchctl load ~/Library/LaunchAgents/com.duolingo.familyleague.plist
   ```

## HTML Reports

The application can generate beautiful HTML reports with responsive design and professional styling. HTML reports include:

- **Responsive Design**: Optimized for both desktop and mobile viewing
- **Professional Styling**: Clean, modern interface with Duolingo-inspired colors
- **Rich Formatting**: Progress badges, status indicators, and visual hierarchy
- **Multi-language Support**: Available in English and Hungarian

### Generating HTML Reports

HTML reports are generated automatically when using the email functionality. The HTML versions are embedded in email reports for better presentation.

To programmatically generate HTML reports:

```python
from src.report_generator import generate_daily_report_html, generate_weekly_report_html
from src.duolingo_api import check_all_family
from src.config import load_config

# Load configuration and check family progress
config = load_config()
results = check_all_family(config)
goals = config.get("goals", {})

# Generate HTML reports
daily_html = generate_daily_report_html(results)
weekly_html = generate_weekly_report_html(results, goals)

# Save to files
with open("daily_report.html", "w") as f:
    f.write(daily_html)
    
with open("weekly_report.html", "w") as f:
    f.write(weekly_html)
```

### Language Selection

Set your preferred report language using the `DUOLINGO_REPORT_LANGUAGE` environment variable:

- `en` - English (default)
- `hu` - Hungarian

The language setting affects both text and HTML reports. Additional languages can be easily added by creating new JSON files in the `translations/` directory.

### Adding New Languages

To add support for a new language:

1. Create a new JSON file in the `translations/` directory (e.g., `translations/es.json` for Spanish)
2. Copy the structure from `translations/en.json` and translate all the values
3. Set `DUOLINGO_REPORT_LANGUAGE=es` in your environment variables

Example for Spanish (`translations/es.json`):

```json
{
  "daily_report_title": "Liga Familiar de Duolingo - Actualización Diaria",
  "daily_report_header": "LIGA FAMILIAR DE DUOLINGO - ACTUALIZACIÓN DIARIA",
  "keep_learning": "¡Sigue aprendiendo! 🌟",
  ...
}
```

## Data Storage

- Daily snapshots are saved in `league_data/daily_YYYY-MM-DD.json`
- Master history file at `league_data/league_history.json` (last 90 days)
- Reports are saved as `daily_report_YYYYMMDD.txt` and `weekly_report_YYYYMMDD.txt`

## Report Examples

### Daily Report

```sh
📊 DUOLINGO FAMILY LEAGUE - DAILY UPDATE
=============================================
Date: 2025-08-05

🏆 Today's Standings:
🥇 Alice: 12 day streak | 650 weekly XP
🥈 Bob: 8 day streak | 420 weekly XP

⚠️ Streak Alerts:
  ✅ Everyone is maintaining their streaks!

Keep learning! 🌟
```

### Weekly Report

```sh
🏆 DUOLINGO FAMILY LEAGUE - WEEKLY REPORT
=======================================================
Week ending: 2025-08-05

🥇 FAMILY LEADERBOARD
-------------------------
🥇 Alice
    Streak: 12 days | Weekly XP: 650 | Total XP: 15,420
🥈 Bob
    Streak: 8 days | Weekly XP: 420 | Total XP: 8,240

📊 DETAILED PROGRESS
----------------------
👤 Alice (alice_duolingo)
   Current streak: 12 days
   🔥 STREAK GOAL ACHIEVED!
   🎯 WEEKLY XP GOAL ACHIEVED! (650/500)
   📚 Language Progress:
      German: Level 8 | 3,240 XP
      Japanese: Level 5 | 1,180 XP
```

## Requirements

- Python 3.8+
- Public Duolingo profiles for all family members (required for API access)
- SMTP email server access (Gmail, Outlook, etc.) for email reports

## Troubleshooting

### Profile Not Found

Ensure the Duolingo profile is public and the username is correct.

### Email Not Sending

1. Check SMTP credentials in environment variables
2. For Gmail, ensure you're using an App Password, not your regular password
3. Check firewall/network settings for SMTP port access

### Missing Data

- The public API doesn't provide exact weekly XP. The tool calculates this from stored daily snapshots.
- For accurate weekly XP tracking, ensure the script runs daily to capture progress changes.
- Historical data is stored in `league_data/` for trend analysis.

## Development

### Dependencies

```bash
# Install uv if you haven't already
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install dependencies
uv sync --all-extras
```

## Project Structure

```text
.
├── duolingo_family_league.py   # Main entry point
├── src/
│   ├── config.py               # Configuration management
│   ├── duolingo_api.py         # Duolingo API integration
│   ├── data_storage.py         # Data persistence
│   ├── email_sender.py         # Email functionality
│   ├── report_generator.py     # Report generation
│   ├── html_report_generator.py # HTML report generation
│   ├── html_templates.py       # HTML templates and styling
│   ├── i18n.py                 # Internationalization support
│   └── types.py                # Type definitions
├── translations/               # Translation files
│   ├── en.json                 # English translations
│   └── hu.json                 # Hungarian translations
├── tests/
│   └── test_family_league.py   # Pytest test suite
├── league_data/                # Historical data (created automatically)
└── pyproject.toml              # Project dependencies
```

## Testing

Run the test suite:

```sh
pytest tests/ -v
```

### Linting

```sh
ruff check --fix
ty check
pyright
```

## License

MIT

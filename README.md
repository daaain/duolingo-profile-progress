# Duolingo Family League Progress Tracker

A comprehensive Python-based system to monitor your family's Duolingo language learning progress, generate weekly leaderboards, and send automated email reports with pocket money tracking.

## 🌟 Features

- **Multi-language tracking** - Monitor progress across any Duolingo language
- **Family leaderboard** - Weekly rankings based on streaks and XP
- **Automated email reports** - Weekly progress summaries sent every Monday
- **Pocket money tracking** - Automatic eligibility calculation for specified languages
- **Robust scheduling** - Works even if your Mac was asleep during scheduled time
- **Historical data** - Track progress trends over time
- **Public profile support** - No authentication required, uses public Duolingo data

## 📋 Requirements

- Python 3.6+
- macOS (for automation setup)
- Public Duolingo profiles for all family members
- Gmail account (for email reports)

## 🚀 Quick Start

### 1. Install Dependencies

```bash
cd ~/workspace/duolingo-profile-progress
pip3 install -r requirements.txt
```

### 2. Configure Your Family

Copy the example config and customize it:

```bash
cp family_league_config.json.example family_league_config.json
```

Edit `family_league_config.json` with your family's information:

```json
{
  "family_members": {
    "Alice": {
      "username": "alice_duolingo_username",
      "languages": ["Hungarian", "German"],
      "email": "alice@example.com"
    },
    "Bob": {
      "username": "bob_duolingo_username", 
      "languages": ["Hungarian"],
      "email": "bob@example.com"
    }
  },
  "email_settings": {
    "smtp_server": "smtp.gmail.com",
    "smtp_port": 587,
    "sender_email": "your_email@gmail.com",
    "sender_password": "your_gmail_app_password",
    "family_email_list": ["family@example.com"]
  },
  "league_settings": {
    "weekly_xp_goal": 500,
    "streak_goal": 7,
    "pocket_money_languages": ["Hungarian"],
    "pocket_money_amount": 5
  }
}
```

### 3. Set Up Gmail App Password

1. Enable 2-factor authentication on your Gmail account
2. Go to Google Account → Security → App passwords
3. Generate an app password for "Mail"
4. Use this password in your config file (not your regular Gmail password)

### 4. Test the System

```bash
# Test basic functionality
python3 duolingo_family_league.py

# Test email sending
python3 duolingo_family_league.py --weekly-email
```

## 🤖 Automation Setup

Choose one of these methods to automatically send weekly reports every Monday:

### Option 1: LaunchAgent (Recommended)

This method is most reliable and works even if your Mac was sleeping:

1. **Install the LaunchAgent:**

   ```bash
   # First, update the username in the plist file
   sed -i '' 's/YOUR_USERNAME/'"$USER"'/g' com.duolingo.familyleague.plist
   
   # Make scripts executable
   chmod +x duolingo_wrapper.sh duolingo_cron.sh
   
   # Copy to LaunchAgents directory
   cp com.duolingo.familyleague.plist ~/Library/LaunchAgents/
   
   # Load the agent
   launchctl load ~/Library/LaunchAgents/com.duolingo.familyleague.plist
   ```

2. **Verify it's loaded:**

   ```bash
   launchctl list | grep duolingo
   ```

### Option 2: Cron with Catch-up

```bash
# Make script executable
chmod +x duolingo_cron.sh

# Edit crontab
crontab -e

# Add this line (runs Monday 9 AM and every hour until 6 PM as catch-up)
0 9-18 * * 1 /Users/$USER/workspace/duolingo-profile-progress/duolingo_cron.sh
```

### Option 3: Automator + Calendar

1. Open **Automator** → New → **Application**
2. Add **Run Shell Script** action
3. Set script to:

   ```bash
   cd /Users/$USER/workspace/duolingo-profile-progress
   /usr/bin/python3 duolingo_family_league.py --weekly-email
   ```

4. Save as "Duolingo Family League.app"
5. In **Calendar**, create weekly Monday event with alert to open this app

## 📊 Output Examples

### Weekly Report Email

```
🏆 DUOLINGO FAMILY LEAGUE - WEEKLY REPORT
========================================================
Week ending: 2025-08-08
Generated: 2025-08-08 09:00:15

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
      Hungarian: Level 8 | 3,240 XP
      German: Level 5 | 1,180 XP
   💰 POCKET MONEY ELIGIBLE: $5 (Hungarian)
```

## 🔧 Configuration Options

### Family Members

- `username`: Duolingo username (must be public profile)
- `languages`: List of languages to track
- `email`: Individual email address

### Email Settings

- Gmail SMTP configuration
- Family distribution list
- App password authentication

### League Settings

- `weekly_xp_goal`: Target XP per week
- `streak_goal`: Target daily streak
- `pocket_money_languages`: Languages eligible for rewards
- `pocket_money_amount`: Reward amount per eligible language

## 📁 Generated Files

- `family_league_history.json` - Historical progress data
- `family_league_report_YYYYMMDD.txt` - Daily report files
- `duolingo_last_run.log` - Execution logs
- `duolingo_error.log` - Error logs

## 🛠️ Troubleshooting

### Email Issues

- Verify Gmail App Password is correct
- Check SMTP settings match your email provider
- Ensure 2FA is enabled on Gmail

### Profile Access Issues

- Confirm Duolingo usernames are correct
- Verify profiles are set to public
- Check if users have started the specified languages

### Automation Issues

```bash
# Check LaunchAgent status
launchctl list | grep duolingo

# View logs
tail -f duolingo_league.log
tail -f duolingo_league_error.log

# Reload LaunchAgent if needed
launchctl unload ~/Library/LaunchAgents/com.duolingo.familyleague.plist
launchctl load ~/Library/LaunchAgents/com.duolingo.familyleague.plist
```

### macOS Permissions

You may need to grant permissions in:
**System Preferences → Privacy & Security → Full Disk Access**

## 🎯 Supported Languages

The system supports all major Duolingo languages:

- European: Spanish, French, German, Italian, Portuguese, Dutch, Russian, Polish, Norwegian, Swedish, Danish, Finnish, Czech, Hungarian, Romanian, Ukrainian, Greek
- Asian: Japanese, Korean, Chinese, Hindi, Vietnamese, Thai, Indonesian
- Others: Arabic, Hebrew, Turkish, Swahili

## 🤝 Contributing

Feel free to submit issues and enhancement requests!

## 📄 License

This project is open source and available under the [MIT License](LICENSE).

## 🔗 Related

- [Duolingo Python Library](https://github.com/KartikTalwar/Duolingo) - Unofficial API wrapper
- [Duolingo](https://www.duolingo.com/) - Language learning platform

---

**Happy learning!** 🦉📚

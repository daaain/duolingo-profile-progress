#!/usr/bin/env python3
"""
Duolingo Family League Monitor
Tracks family members' language learning progress across multiple languages
Generates weekly leaderboards and progress reports
"""

import duolingo
import json
import smtplib
from email.mime.text import MimeText
from email.mime.multipart import MimeMultipart
from datetime import datetime, timedelta
import os
import sys
from collections import defaultdict

class DuolingoFamilyLeague:
    def __init__(self, config_file="family_league_config.json"):
        self.config_file = config_file
        self.config = self.load_config()
        
    def load_config(self):
        """Load family league configuration"""
        if os.path.exists(self.config_file):
            with open(self.config_file, 'r') as f:
                return json.load(f)
        else:
            # Create example config file
            example_config = {
                "family_members": {
                    "Dad": {
                        "username": "dad_username",
                        "languages": ["Spanish", "French"],
                        "email": "dad@example.com"
                    },
                    "Mom": {
                        "username": "mom_username", 
                        "languages": ["Italian"],
                        "email": "mom@example.com"
                    },
                    "Alice": {
                        "username": "alice_username",
                        "languages": ["Hungarian", "German"],
                        "email": "alice@example.com"
                    },
                    "Bob": {
                        "username": "bob_username",
                        "languages": ["Hungarian"],
                        "email": "bob@example.com"
                    }
                },
                "email_settings": {
                    "smtp_server": "smtp.gmail.com",
                    "smtp_port": 587,
                    "sender_email": "your_email@gmail.com",
                    "sender_password": "your_app_password",
                    "family_email_list": ["family@example.com"]
                },
                "league_settings": {
                    "weekly_xp_goal": 500,
                    "streak_goal": 7,
                    "pocket_money_languages": ["Hungarian"],
                    "pocket_money_amount": 5
                }
            }
            with open(self.config_file, 'w') as f:
                json.dump(example_config, f, indent=2)
            print(f"Created example config file: {self.config_file}")
            print("Please edit it with your family's actual information")
            return example_config
    
    def get_language_code(self, language_name):
        """Convert language name to Duolingo language code"""
        language_codes = {
            'Spanish': 'es', 'French': 'fr', 'German': 'de', 'Italian': 'it',
            'Portuguese': 'pt', 'Dutch': 'nl', 'Russian': 'ru', 'Japanese': 'ja',
            'Korean': 'ko', 'Chinese': 'zh', 'Arabic': 'ar', 'Hindi': 'hi',
            'Turkish': 'tr', 'Polish': 'pl', 'Norwegian': 'no', 'Swedish': 'sv',
            'Danish': 'da', 'Finnish': 'fi', 'Czech': 'cs', 'Hungarian': 'hu',
            'Romanian': 'ro', 'Ukrainian': 'uk', 'Greek': 'el', 'Hebrew': 'he',
            'Vietnamese': 'vi', 'Thai': 'th', 'Indonesian': 'id', 'Swahili': 'sw'
        }
        return language_codes.get(language_name, language_name.lower())
    
    def get_user_progress(self, username, target_languages):
        """Get progress data for a specific user across multiple languages"""
        try:
            lingo = duolingo.Duolingo(username)
            user_info = lingo.get_user_info()
            languages = lingo.get_languages(abbreviations=True)
            
            # Calculate weekly XP (approximation based on recent activity)
            weekly_xp = self.estimate_weekly_xp(lingo)
            
            language_progress = {}
            total_target_xp = 0
            
            for target_lang in target_languages:
                lang_code = self.get_language_code(target_lang)
                lang_data = None
                
                for lang in languages:
                    if (lang.get('language') == lang_code or 
                        lang.get('language_string', '').lower() == target_lang.lower()):
                        lang_data = lang
                        break
                
                if lang_data:
                    lang_xp = lang_data.get('points', 0)
                    total_target_xp += lang_xp
                    language_progress[target_lang] = {
                        'level': lang_data.get('level', 0),
                        'xp': lang_xp,
                        'fluency': lang_data.get('fluency_score', 0)
                    }
                else:
                    language_progress[target_lang] = {
                        'level': 0,
                        'xp': 0,
                        'fluency': 0
                    }
            
            return {
                'username': username,
                'streak': user_info.get('site_streak', 0),
                'total_xp': user_info.get('total_xp', 0),
                'weekly_xp': weekly_xp,
                'target_languages_xp': total_target_xp,
                'language_progress': language_progress,
                'last_check': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'profile_public': True
            }
            
        except Exception as e:
            return {
                'username': username,
                'error': str(e),
                'last_check': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'profile_public': False,
                'language_progress': {}
            }
    
    def estimate_weekly_xp(self, lingo_obj):
        """Estimate weekly XP based on available data"""
        try:
            # This is a rough estimation - the API doesn't provide exact weekly data
            # You might need to implement your own tracking for more accuracy
            user_info = lingo_obj.get_user_info()
            # For now, we'll use a placeholder calculation
            # In practice, you'd want to store daily XP and calculate the difference
            return user_info.get('total_xp', 0) // 52  # Rough weekly average
        except:
            return 0
    
    def check_all_family(self):
        """Check progress for all family members"""
        results = {}
        
        print("Checking Duolingo progress for the family league...\n")
        print("="*60)
        
        for member_name, member_data in self.config['family_members'].items():
            username = member_data['username']
            languages = member_data['languages']
            
            print(f"\nChecking {member_name} ({username})...")
            print(f"Target languages: {', '.join(languages)}")
            
            progress = self.get_user_progress(username, languages)
            results[member_name] = progress
            
            if 'error' in progress:
                print(f"❌ Error: {progress['error']}")
            else:
                print(f"✅ Current streak: {progress['streak']} days")
                print(f"   Weekly XP (est.): {progress['weekly_xp']}")
                print(f"   Target languages XP: {progress['target_languages_xp']}")
        
        return results
    
    def generate_leaderboard(self, results):
        """Generate family leaderboard"""
        leaderboard_data = []
        
        for member_name, data in results.items():
            if 'error' not in data:
                leaderboard_data.append({
                    'name': member_name,
                    'streak': data['streak'],
                    'weekly_xp': data['weekly_xp'],
                    'total_xp': data['total_xp'],
                    'target_xp': data['target_languages_xp'],
                    'data': data
                })
        
        # Sort by multiple criteria
        leaderboard_data.sort(key=lambda x: (x['streak'], x['weekly_xp'], x['total_xp']), reverse=True)
        
        return leaderboard_data
    
    def generate_weekly_report(self, results):
        """Generate comprehensive weekly family report"""
        leaderboard = self.generate_leaderboard(results)
        
        report = []
        report.append("🏆 DUOLINGO FAMILY LEAGUE - WEEKLY REPORT")
        report.append("="*55)
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
            report.append(f"    Streak: {member['streak']} days | Weekly XP: {member['weekly_xp']} | Total XP: {member['total_xp']:,}")
        
        report.append("")
        
        # Detailed individual progress
        report.append("📊 DETAILED PROGRESS")
        report.append("-" * 22)
        
        for member_name, data in results.items():
            if 'error' in data:
                report.append(f"\n👤 {member_name}")
                report.append(f"   ❌ Unable to check progress: {data['error']}")
                continue
            
            member_config = self.config['family_members'][member_name]
            
            report.append(f"\n👤 {member_name} ({data['username']})")
            report.append(f"   Current streak: {data['streak']} days")
            
            # Streak status
            streak_goal = self.config['league_settings']['streak_goal']
            if data['streak'] >= streak_goal:
                report.append("   🔥 STREAK GOAL ACHIEVED!")
            elif data['streak'] >= streak_goal // 2:
                report.append(f"   ⚡ Good progress towards {streak_goal}-day goal")
            else:
                report.append(f"   ⚠️  Work needed for {streak_goal}-day streak goal")
            
            # Weekly XP status
            weekly_goal = self.config['league_settings']['weekly_xp_goal']
            if data['weekly_xp'] >= weekly_goal:
                report.append(f"   🎯 WEEKLY XP GOAL ACHIEVED! ({data['weekly_xp']}/{weekly_goal})")
            else:
                report.append(f"   📈 Weekly XP progress: {data['weekly_xp']}/{weekly_goal}")
            
            # Language-specific progress
            report.append("   📚 Language Progress:")
            for lang, progress in data['language_progress'].items():
                if progress['xp'] > 0:
                    report.append(f"      {lang}: Level {progress['level']} | {progress['xp']:,} XP")
                else:
                    report.append(f"      {lang}: Not started yet")
            
            # Pocket money eligibility (for specified languages)
            pocket_money_langs = self.config['league_settings']['pocket_money_languages']
            eligible_langs = []
            for lang in pocket_money_langs:
                if lang in member_config['languages'] and data['streak'] >= 1:
                    eligible_langs.append(lang)
            
            if eligible_langs:
                amount = self.config['league_settings']['pocket_money_amount']
                total_amount = len(eligible_langs) * amount
                report.append(f"   💰 POCKET MONEY ELIGIBLE: ${total_amount} ({', '.join(eligible_langs)})")
            
            report.append("")
        
        # Weekly challenges and goals
        report.append("🎯 THIS WEEK'S FAMILY CHALLENGES")
        report.append("-" * 35)
        report.append(f"• Maintain a {self.config['league_settings']['streak_goal']}-day streak")
        report.append(f"• Earn {self.config['league_settings']['weekly_xp_goal']} XP this week")
        report.append("• Try to beat your personal best!")
        report.append("\nKeep up the great work, everyone! 🌟")
        
        return "\n".join(report)
    
    def send_weekly_email(self, report):
        """Send weekly report via email"""
        try:
            email_config = self.config['email_settings']
            
            msg = MimeMultipart()
            msg['From'] = email_config['sender_email']
            msg['To'] = ', '.join(email_config['family_email_list'])
            msg['Subject'] = f"Duolingo Family League - Week of {datetime.now().strftime('%B %d, %Y')}"
            
            msg.attach(MimeText(report, 'plain'))
            
            server = smtplib.SMTP(email_config['smtp_server'], email_config['smtp_port'])
            server.starttls()
            server.login(email_config['sender_email'], email_config['sender_password'])
            text = msg.as_string()
            server.sendmail(email_config['sender_email'], email_config['family_email_list'], text)
            server.quit()
            
            print("✅ Weekly report email sent successfully!")
            return True
            
        except Exception as e:
            print(f"❌ Failed to send email: {e}")
            return False
    
    def save_weekly_data(self, results):
        """Save weekly progress data"""
        log_file = "family_league_history.json"
        
        if os.path.exists(log_file):
            with open(log_file, 'r') as f:
                history = json.load(f)
        else:
            history = []
        
        week_entry = {
            'week_ending': datetime.now().strftime('%Y-%m-%d'),
            'results': results
        }
        history.append(week_entry)
        
        with open(log_file, 'w') as f:
            json.dump(history, f, indent=2)
        
        print(f"Weekly data saved to {log_file}")

def main():
    """Main execution function"""
    if len(sys.argv) > 1 and sys.argv[1] == '--weekly-email':
        # Weekly email mode
        league = DuolingoFamilyLeague()
        results = league.check_all_family()
        report = league.generate_weekly_report(results)
        
        # Save report to file
        report_filename = f"family_league_report_{datetime.now().strftime('%Y%m%d')}.txt"
        with open(report_filename, 'w') as f:
            f.write(report)
        
        # Send email
        league.send_weekly_email(report)
        league.save_weekly_data(results)
        
    else:
        # Regular check mode
        league = DuolingoFamilyLeague()
        results = league.check_all_family()
        report = league.generate_weekly_report(results)
        
        print("\n" + report)
        
        # Save report
        report_filename = f"family_league_report_{datetime.now().strftime('%Y%m%d')}.txt"
        with open(report_filename, 'w') as f:
            f.write(report)
        print(f"\nReport saved to {report_filename}")

if __name__ == "__main__":
    main()

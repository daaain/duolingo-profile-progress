"""Duolingo API integration for fetching user progress"""

import requests
from datetime import datetime


def get_user_progress(username):
    """Get progress data for a specific user using the unauthenticated API"""
    try:
        # Use the unauthenticated API endpoint
        url = f"https://www.duolingo.com/2017-06-30/users?username={username}"
        
        # Add headers to make the request look like it's coming from a browser
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        users = data.get('users', [])
        
        if not users:
            return {
                'username': username,
                'error': 'User not found',
                'last_check': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'profile_public': False,
                'language_progress': {},
                'active_languages': []
            }
        
        user = users[0]
        
        # Extract language progress from courses
        language_progress = {}
        total_languages_xp = 0
        active_languages = []
        
        courses = user.get('courses', [])
        for course in courses:
            lang_xp = course.get('xp', 0)
            if lang_xp > 0:
                lang_title = course.get('title', '')
                if lang_title:
                    total_languages_xp += lang_xp
                    active_languages.append(lang_title)
                    language_progress[lang_title] = {
                        'level': course.get('crowns', 0),  # Using crowns as level
                        'xp': lang_xp,
                        'from_language': course.get('fromLanguage', 'en'),
                        'learning_language': course.get('learningLanguage', '')
                    }
        
        # Get streak data
        streak_data = user.get('streakData', {})
        current_streak = streak_data.get('currentStreak', {})
        streak = current_streak.get('length', 0) if current_streak else user.get('streak', 0)
        
        return {
            'username': username,
            'name': user.get('name', username),
            'streak': streak,
            'total_xp': user.get('totalXp', 0),
            'weekly_xp': 0,  # Will need to be calculated from stored data
            'total_languages_xp': total_languages_xp,
            'active_languages': active_languages,
            'language_progress': language_progress,
            'last_check': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'profile_public': True,
            'has_plus': user.get('hasPlus', False)
        }
        
    except requests.RequestException as e:
        return {
            'username': username,
            'error': f'API request failed: {str(e)}',
            'last_check': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'profile_public': False,
            'language_progress': {},
            'active_languages': []
        }
    except Exception as e:
        return {
            'username': username,
            'error': str(e),
            'last_check': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'profile_public': False,
            'language_progress': {},
            'active_languages': []
        }


def check_all_family(config):
    """Check progress for all family members"""
    results = {}
    
    if not config:
        print("❌ No configuration found")
        return results
    
    print("Checking Duolingo progress for the family league...\n")
    print("="*60)
    
    # Get users to check from config
    users_to_check = {}
    
    if config['family_members']:
        # Use specified usernames
        for member_name, member_data in config['family_members'].items():
            username = member_data['username']
            users_to_check[member_name] = username
    else:
        print("⚠️ No users specified in DUOLINGO_USERNAMES")
        return results
    
    # Process each user
    for member_name, username in users_to_check.items():
        print(f"\nChecking {member_name}...")
        
        progress = get_user_progress(username)
        results[member_name] = progress
        
        if 'error' in progress:
            print(f"❌ Error: {progress['error']}")
        else:
            active_langs = progress.get('active_languages', [])
            print(f"✅ Current streak: {progress['streak']} days")
            print(f"   Name: {progress.get('name', 'Unknown')}")
            print(f"   Active languages: {', '.join(active_langs) if active_langs else 'None'}")
            print(f"   Total XP: {progress['total_xp']}")
            print(f"   Total languages XP: {progress['total_languages_xp']}")
            if progress.get('has_plus'):
                print("   Has Duolingo Plus: Yes")
    
    return results
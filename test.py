#!/usr/bin/env python3
"""
Test script for Duolingo Family League
Validates configuration and tests basic functionality
"""

import json
import os
import sys
from duolingo_family_league import DuolingoFamilyLeague

def test_config():
    """Test configuration file"""
    print("🔧 Testing configuration...")
    
    if not os.path.exists('family_league_config.json'):
        print("❌ Configuration file not found!")
        print("   Please copy family_league_config.json.example to family_league_config.json")
        print("   and update it with your family's information.")
        return False
    
    try:
        with open('family_league_config.json', 'r') as f:
            config = json.load(f)
        
        # Check required sections
        required_sections = ['family_members', 'email_settings', 'league_settings']
        for section in required_sections:
            if section not in config:
                print(f"❌ Missing section: {section}")
                return False
        
        # Check if using example data
        if any('example.com' in str(config).lower() for key in config.values()):
            print("⚠️  Configuration still contains example data")
            print("   Please update with your actual information")
            return False
        
        print("✅ Configuration file looks good!")
        return True
        
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON in configuration file: {e}")
        return False

def test_duolingo_connection():
    """Test connection to Duolingo API"""
    print("\n🔗 Testing Duolingo API connection...")
    
    try:
        league = DuolingoFamilyLeague()
        
        # Test with first family member
        first_member = next(iter(league.config['family_members'].items()))
        member_name, member_data = first_member
        
        print(f"   Testing with {member_name} ({member_data['username']})...")
        
        progress = league.get_user_progress(member_data['username'], member_data['languages'])
        
        if 'error' in progress:
            print(f"❌ Error accessing {member_name}'s profile: {progress['error']}")
            print("   Check that:")
            print("   - Username is correct")
            print("   - Profile is public")
            print("   - User has started the specified languages")
            return False
        else:
            print(f"✅ Successfully retrieved data for {member_name}")
            print(f"   Streak: {progress['streak']} days")
            print(f"   Total XP: {progress['total_xp']}")
            return True
            
    except Exception as e:
        print(f"❌ Error testing Duolingo connection: {e}")
        return False

def test_email_config():
    """Test email configuration"""
    print("\n📧 Testing email configuration...")
    
    try:
        league = DuolingoFamilyLeague()
        email_config = league.config['email_settings']
        
        # Check required email fields
        required_fields = ['smtp_server', 'smtp_port', 'sender_email', 'sender_password', 'family_email_list']
        for field in required_fields:
            if field not in email_config:
                print(f"❌ Missing email field: {field}")
                return False
        
        # Check if using example data
        if 'example.com' in email_config['sender_email']:
            print("⚠️  Email configuration still contains example data")
            print("   Please update with your actual Gmail information")
            return False
        
        print("✅ Email configuration looks good!")
        print("   Note: Email sending will be tested when you run --weekly-email")
        return True
        
    except Exception as e:
        print(f"❌ Error checking email configuration: {e}")
        return False

def main():
    """Run all tests"""
    print("🧪 Duolingo Family League - Test Suite")
    print("=" * 45)
    
    # Change to script directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    
    tests = [
        test_config,
        test_duolingo_connection,
        test_email_config
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
    
    print(f"\n📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Your setup looks good.")
        print("\n🚀 Ready to run:")
        print("   python3 duolingo_family_league.py")
        print("   python3 duolingo_family_league.py --weekly-email")
    else:
        print("❌ Some tests failed. Please fix the issues above.")
        sys.exit(1)

if __name__ == "__main__":
    main()

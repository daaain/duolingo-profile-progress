"""HTML template definitions for Duolingo Family League reports"""

DAILY_REPORT_TEMPLATE = """
<!DOCTYPE html>
<html lang="{lang}">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 600px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f8f9fa;
        }}
        .container {{
            background: white;
            border-radius: 12px;
            padding: 30px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #58CC02;
            text-align: center;
            margin-bottom: 10px;
            font-size: 24px;
        }}
        .subtitle {{
            text-align: center;
            color: #777;
            margin-bottom: 30px;
            font-size: 16px;
        }}
        .date {{
            text-align: center;
            color: #58CC02;
            font-weight: bold;
            margin-bottom: 30px;
            font-size: 18px;
        }}
        .section {{
            margin-bottom: 30px;
        }}
        .section h2 {{
            color: #58CC02;
            border-bottom: 2px solid #58CC02;
            padding-bottom: 5px;
            font-size: 18px;
        }}
        .leaderboard {{
            list-style: none;
            padding: 0;
        }}
        .leaderboard li {{
            background: #f8f9fa;
            margin: 10px 0;
            padding: 15px;
            border-radius: 8px;
            display: flex;
            align-items: center;
            font-weight: bold;
        }}
        .position {{
            font-size: 24px;
            margin-right: 15px;
            min-width: 40px;
        }}
        .member-info {{
            flex: 1;
        }}
        .member-name {{
            color: #333;
            font-size: 16px;
        }}
        .member-stats {{
            color: #666;
            font-size: 14px;
            font-weight: normal;
        }}
        .language-progress {{
            color: #58CC02;
            font-size: 12px;
            font-weight: normal;
            margin-top: 5px;
        }}
        .alert {{
            padding: 15px;
            border-radius: 8px;
            margin: 10px 0;
        }}
        .alert.success {{
            background: #d4edda;
            border: 1px solid #c3e6cb;
            color: #155724;
        }}
        .alert.warning {{
            background: #fff3cd;
            border: 1px solid #ffeaa7;
            color: #856404;
        }}
        .footer {{
            text-align: center;
            margin-top: 30px;
            color: #777;
            font-size: 14px;
        }}
        .emoji {{
            font-size: 20px;
            margin-right: 8px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>📊 {header}</h1>
        <div class="subtitle">{subtitle}</div>
        <div class="date">{date}</div>
        
        <div class="section">
            <h2>🏆 {standings_title}</h2>
            <ul class="leaderboard">
                {leaderboard_items}
            </ul>
        </div>
        
        <div class="section">
            <h2>⚠️ {streak_alerts_title}</h2>
            {streak_alerts}
        </div>
        
        <div class="footer">
            {footer_message}
        </div>
    </div>
</body>
</html>
"""

WEEKLY_REPORT_TEMPLATE = """
<!DOCTYPE html>
<html lang="{lang}">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f8f9fa;
        }}
        .container {{
            background: white;
            border-radius: 12px;
            padding: 30px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #58CC02;
            text-align: center;
            margin-bottom: 10px;
            font-size: 28px;
        }}
        .subtitle {{
            text-align: center;
            color: #777;
            margin-bottom: 20px;
            font-size: 16px;
        }}
        .date-info {{
            text-align: center;
            color: #58CC02;
            font-weight: bold;
            margin-bottom: 30px;
            font-size: 16px;
        }}
        .section {{
            margin-bottom: 40px;
        }}
        .section h2 {{
            color: #58CC02;
            border-bottom: 3px solid #58CC02;
            padding-bottom: 8px;
            font-size: 20px;
            margin-bottom: 20px;
        }}
        .leaderboard {{
            display: grid;
            gap: 15px;
        }}
        .leaderboard-item {{
            background: #f8f9fa;
            padding: 20px;
            border-radius: 12px;
            border-left: 5px solid #58CC02;
        }}
        .leaderboard-item.first {{
            border-left-color: #FFD700;
            background: linear-gradient(135deg, #fff9e6 0%, #f8f9fa 100%);
        }}
        .leaderboard-item.second {{
            border-left-color: #C0C0C0;
        }}
        .leaderboard-item.third {{
            border-left-color: #CD7F32;
        }}
        .position {{
            font-size: 24px;
            float: left;
            margin-right: 15px;
            line-height: 1;
        }}
        .member-name {{
            font-size: 18px;
            font-weight: bold;
            color: #333;
            margin-bottom: 8px;
        }}
        .member-stats {{
            color: #666;
            font-size: 14px;
        }}
        .detailed-progress {{
            display: grid;
            gap: 25px;
        }}
        .member-detail {{
            background: #f8f9fa;
            padding: 20px;
            border-radius: 12px;
            border: 1px solid #e9ecef;
        }}
        .member-header {{
            display: flex;
            align-items: center;
            margin-bottom: 15px;
        }}
        .member-avatar {{
            font-size: 24px;
            margin-right: 12px;
        }}
        .member-title {{
            font-size: 16px;
            font-weight: bold;
            color: #333;
        }}
        .member-username {{
            font-size: 14px;
            color: #666;
        }}
        .progress-item {{
            margin: 8px 0;
            padding: 8px 0;
        }}
        .status-badge {{
            display: inline-block;
            padding: 4px 8px;
            border-radius: 12px;
            font-size: 12px;
            font-weight: bold;
            margin: 2px 0;
        }}
        .status-badge.achieved {{
            background: #d4edda;
            color: #155724;
        }}
        .status-badge.progress {{
            background: #fff3cd;
            color: #856404;
        }}
        .status-badge.warning {{
            background: #f8d7da;
            color: #721c24;
        }}
        .language-list {{
            margin-left: 20px;
            margin-top: 10px;
        }}
        .language-item {{
            margin: 5px 0;
            color: #666;
            font-size: 14px;
        }}
        .language-name {{
            font-weight: bold;
            color: #58CC02;
        }}
        .goals-section {{
            background: linear-gradient(135deg, #e8f5e8 0%, #f8f9fa 100%);
            padding: 20px;
            border-radius: 12px;
            border: 2px solid #58CC02;
        }}
        .goals-list {{
            list-style: none;
            padding: 0;
        }}
        .goals-list li {{
            margin: 10px 0;
            padding-left: 25px;
            position: relative;
        }}
        .goals-list li::before {{
            content: "🎯";
            position: absolute;
            left: 0;
        }}
        .footer {{
            text-align: center;
            margin-top: 40px;
            color: #777;
            font-size: 14px;
            border-top: 1px solid #e9ecef;
            padding-top: 20px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🏆 {header}</h1>
        <div class="subtitle">{subtitle}</div>
        <div class="date-info">
            {week_ending}<br>
            {generated_date}
        </div>
        
        <div class="section">
            <h2>🥇 {family_leaderboard_title}</h2>
            <div class="leaderboard">
                {leaderboard_items}
            </div>
        </div>
        
        <div class="section">
            <h2>📊 {detailed_progress_title}</h2>
            <div class="detailed-progress">
                {member_details}
            </div>
        </div>
        
        <div class="section">
            <div class="goals-section">
                <h2>🎯 {goals_title}</h2>
                <ul class="goals-list">
                    {goals_list}
                </ul>
                <div style="text-align: center; margin-top: 20px; font-weight: bold; color: #58CC02;">
                    {keep_up_message}
                </div>
            </div>
        </div>
        
        <div class="footer">
            {footer_message}
        </div>
    </div>
</body>
</html>
"""
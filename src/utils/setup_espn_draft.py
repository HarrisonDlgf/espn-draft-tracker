
import os
import re

def get_league_id_from_url():
    """Helper to extract league ID from ESPN URL"""
    print("📋 To find your League ID:")
    print("1. Go to your ESPN league")
    print("2. Copy the URL from your browser")
    print("3. Look for a number in the URL like: fantasy.espn.com/football/league?leagueId=123456")
    print("4. The number after 'leagueId=' is your League ID")
    print()
    
    url = input("Paste your ESPN league URL (or just the league ID): ").strip()
    
    # Extract league ID from URL or use direct input
    if 'leagueId=' in url:
        match = re.search(r'leagueId=(\d+)', url)
        if match:
            return match.group(1)
    elif url.isdigit():
        return url
    else:
        print("❌ Could not extract league ID. Please enter it manually.")
        return input("Enter your League ID: ").strip()

def get_credentials():
    """Interactive setup for ESPN credentials"""
    print("🔐 ESPN Credentials Setup")
    print("=" * 50)
    print()
    
    # Get league ID
    league_id = get_league_id_from_url()
    
    # Get credentials
    print("\n📋 ESPN Credentials:")
    print("1. Go to ESPN Fantasy Football")
    print("2. Log into your account")
    print("3. Open Developer Tools (F12)")
    print("4. Go to Application/Storage → Cookies → fantasy.espn.com")
    print("5. Find 'espn_s2' and 'SWID' cookies")
    print()
    
    espn_s2 = input("Enter your espn_s2 value: ").strip()
    swid = input("Enter your SWID value: ").strip()
    
    # Get draft slot
    print("\n📋 Draft Position:")
    print("Enter your draft position (1-12):")
    draft_slot = int(input("Draft slot: ").strip()) - 1  # Convert to 0-based
    
    return {
        'league_id': league_id,
        'espn_s2': espn_s2,
        'swid': swid,
        'draft_slot': draft_slot
    }

def update_config(credentials):
    """Update config.py with the provided credentials"""
    config_path = 'src/config.py'
    
    # Read current config
    with open(config_path, 'r') as f:
        content = f.read()
    
    # Update values
    content = re.sub(r'LEAGUE_ID = \d+', f'LEAGUE_ID = {credentials["league_id"]}', content)
    content = re.sub(r'ESPN_S2 = "[^"]*"', f'ESPN_S2 = "{credentials["espn_s2"]}"', content)
    content = re.sub(r'SWID = "[^"]*"', f'SWID = "{credentials["swid"]}"', content)
    content = re.sub(r'YOUR_DRAFT_SLOT = \d+', f'YOUR_DRAFT_SLOT = {credentials["draft_slot"]}', content)
    
    # Write updated config
    with open(config_path, 'w') as f:
        f.write(content)
    
    print("✅ config.py updated successfully!")

def main():
    print("🎯 ESPN Draft Assistant Setup")
    print("=" * 50)
    print()
    
    try:
        # Get credentials
        credentials = get_credentials()
        
        # Update config
        update_config(credentials)
        
        print("\n✅ Setup complete!")
        print("\nNext steps:")
        print("1. Test connection: python src/tests/test_espn_connection.py")
        print("2. Join ESPN mock draft")
        print("3. Run draft assistant: python src/main_gui.py")
        
    except KeyboardInterrupt:
        print("\n\n❌ Setup cancelled.")
    except Exception as e:
        print(f"\n❌ Error during setup: {e}")

if __name__ == "__main__":
    main()

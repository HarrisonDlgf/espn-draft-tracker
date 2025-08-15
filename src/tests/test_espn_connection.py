import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
from espn_api.football import League
from config import *

def test_espn_connection():
    """Test ESPN API connection and get basic league info"""
    try:
        print("🔗 Testing ESPN API Connection...")
        print(f"League ID: {LEAGUE_ID}")
        print(f"Year: {YEAR}")
        print(f"Draft Slot: {YOUR_DRAFT_SLOT + 1}")
        print(f"Total Teams: {TOTAL_TEAMS}")
        print()
        
        # Connect to league
        league = League(league_id=LEAGUE_ID, year=YEAR, espn_s2=ESPN_S2, swid=SWID)
        
        print("✅ Successfully connected to ESPN!")
        print(f"League Name: {league.settings.name}")
        print(f"Teams: {len(league.teams)}")
        print(f"Your Team: {league.teams[YOUR_DRAFT_SLOT].team_name}")
        print()
        
        # Check draft status
        if hasattr(league, 'draft') and league.draft:
            print("📋 Draft Information:")
            print(f"Total Picks: {len(league.draft)}")
            # Handle different ESPN API versions
            try:
                your_picks = [pick.playerName for pick in league.draft if hasattr(pick, 'teamId') and pick.teamId == league.teams[YOUR_DRAFT_SLOT].team_id]
            except AttributeError:
                try:
                    your_picks = [pick.playerName for pick in league.draft if hasattr(pick, 'team') and pick.team == league.teams[YOUR_DRAFT_SLOT].team_id]
                except:
                    your_picks = [pick.playerName for pick in league.draft if hasattr(pick, 'team') and pick.team == YOUR_DRAFT_SLOT]
            print(f"Your Picks: {your_picks}")
        else:
            print("📋 Draft not started yet or no draft data available")
        
        # Check scoring settings
        print(f"\n⚙️ Scoring Settings:")
        try:
            print(f"PPR: {league.settings.points_per_reception}")
        except AttributeError:
            print("PPR: Not available")
        try:
            print(f"Passing TD: {league.settings.pass_td}")
        except AttributeError:
            print("Passing TD: Not available")
        try:
            print(f"Rushing TD: {league.settings.rush_td}")
        except AttributeError:
            print("Rushing TD: Not available")
        try:
            print(f"Receiving TD: {league.settings.rec_td}")
        except AttributeError:
            print("Receiving TD: Not available")
        
        return True
        
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        print("\n🔧 Troubleshooting:")
        print("1. Check your ESPN_S2 and SWID values in config.py")
        print("2. Verify your League ID is correct")
        print("3. Make sure you're logged into ESPN in your browser")
        print("4. Check if the league exists and you have access")
        return False

def get_espn_credentials_help():
    """Provide instructions for getting ESPN credentials"""
    print("\n📖 How to Get ESPN Credentials:")
    print("1. Go to ESPN Fantasy Football")
    print("2. Log into your account")
    print("3. Open Developer Tools (F12)")
    print("4. Go to Application/Storage tab")
    print("5. Look for 'espn_s2' and 'SWID' cookies")
    print("6. Copy their values to config.py")
    print("\nExample:")
    print("ESPN_S2 = \"AEB%2B...\"")
    print("SWID = \"{12345678-1234-1234-1234-123456789012}\"")

if __name__ == "__main__":
    print("=== ESPN Connection Test ===")
    
    if test_espn_connection():
        print("\n✅ Ready to test with ESPN mock draft!")
        print("\nNext steps:")
        print("1. Join an ESPN mock draft")
        print("2. Update config.py with your draft slot")
        print("3. Run main.py to start the draft assistant")
    else:
        get_espn_credentials_help()

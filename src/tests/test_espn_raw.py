#!/usr/bin/env python3

import requests
import json
from config import *

def test_raw_espn_api():
    """Test accessing ESPN API directly to get draft data"""
    
    print("🔍 Testing Raw ESPN API Access...")
    
    # ESPN API endpoints
    base_url = "https://fantasy.espn.com/apis/v3/games/ffl"
    
    # Headers with your credentials
    headers = {
        'Cookie': f'espn_s2={ESPN_S2}; SWID={SWID}',
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
    }
    
    # Try to get league info
    league_url = f"{base_url}/seasons/{YEAR}/segments/0/leagues/{LEAGUE_ID}"
    
    try:
        print(f"Fetching: {league_url}")
        response = requests.get(league_url, headers=headers)
        
        print(f"Response status: {response.status_code}")
        print(f"Response headers: {dict(response.headers)}")
        print(f"Response text (first 500 chars): {response.text[:500]}")
        
        if response.status_code == 200:
            try:
                data = response.json()
                print("✅ Successfully got league data!")
            except json.JSONDecodeError as e:
                print(f"❌ JSON decode error: {e}")
                print(f"Response text: {response.text}")
                return
            
            # Check for draft info
            if 'draft' in data:
                draft_data = data['draft']
                print(f"Draft data found: {draft_data}")
                
                if 'picks' in draft_data:
                    picks = draft_data['picks']
                    print(f"Found {len(picks)} draft picks!")
                    for pick in picks:
                        print(f"Pick: {pick}")
                else:
                    print("No picks in draft data")
            else:
                print("No draft data in response")
            
            # Check for teams
            if 'teams' in data:
                teams = data['teams']
                print(f"Found {len(teams)} teams")
                
                for team in teams:
                    team_name = team.get('name', 'Unknown')
                    roster = team.get('roster', {})
                    players = roster.get('entries', [])
                    print(f"Team {team_name}: {len(players)} players")
                    
                    if len(players) > 0:
                        print(f"  Players: {[p.get('playerPoolEntry', {}).get('player', {}).get('fullName', 'Unknown') for p in players[:3]]}")
            
        else:
            print(f"❌ Failed to get data: {response.status_code}")
            print(f"Response: {response.text[:200]}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_raw_espn_api()

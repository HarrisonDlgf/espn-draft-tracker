import pandas as pd
import time
import warnings
import os
import sys
import requests
import json

# Suppress PySimpleGUI warnings by redirecting stderr
original_stderr = sys.stderr
sys.stderr = open(os.devnull, 'w')

# Suppress warnings
os.environ['PYTHONWARNINGS'] = 'ignore'
warnings.filterwarnings('ignore')

import PySimpleGUI as sg

# Restore stderr
sys.stderr = original_stderr

from espn_api.football import League
from config import *
from data_loader import load_and_clean_data
from draft_analyzer import print_draft_insights, is_my_pick

# Load data
df = load_and_clean_data()
if df is None:
    print("Failed to load data. Exiting.")
    exit(1)

df["Drafted"] = False

# Set to False for live ESPN draft, True for testing
TEST_MODE = False

if TEST_MODE:
    mock_drafted_players = set()
    mock_draft_slot = YOUR_DRAFT_SLOT
    mock_total_teams = TOTAL_TEAMS

    def get_drafted_players():
        return mock_drafted_players

    def add_mock_pick(player_name):
        mock_drafted_players.add(player_name)
        print(f"Mock pick added: {player_name}")

    print("Running in TEST MODE - using mock draft data")
    print("To test picks, you can manually add them in the console")
    print("Example: add_mock_pick('Bijan Robinson')")
else:
    league = League(
        league_id=LEAGUE_ID,
        year=YEAR,
        espn_s2=ESPN_S2,
        swid=SWID
    )

    def get_drafted_players():
        try:
            drafted_players = set()
            
            # Method 1: Direct draft picks (espn-api)
            try:
                picks = league.draft
                if picks and len(picks) > 0:
                    for pick in picks:
                        if hasattr(pick, 'playerName'):
                            drafted_players.add(pick.playerName)
                        elif hasattr(pick, 'name'):
                            drafted_players.add(pick.name)
            except Exception as e:
                pass
            
            # Method 2: Check all team rosters (most reliable during live draft)
            try:
                for team in league.teams:
                    for player in team.roster:
                        if hasattr(player, 'name'):
                            drafted_players.add(player.name)
                        elif hasattr(player, 'playerName'):
                            drafted_players.add(player.playerName)
                        elif hasattr(player, 'full_name'):
                            drafted_players.add(player.full_name)
            except Exception as e:
                pass
            
            # Method 3: Draft recap endpoint (most reliable for mock drafts)
            try:
                recap_picks = fetch_draft_recap(LEAGUE_ID, YEAR)
                drafted_players.update(recap_picks)
            except Exception as e:
                pass
            
            # Method 4: Try to get draft from league settings
            try:
                if hasattr(league, 'settings') and hasattr(league.settings, 'draft'):
                    draft_settings = league.settings.draft
                    if hasattr(draft_settings, 'picks'):
                        for pick in draft_settings.picks:
                            if hasattr(pick, 'playerName'):
                                drafted_players.add(pick.playerName)
            except Exception as e:
                pass
            
            return drafted_players
            
        except Exception as e:
            return set()


def fetch_draft_recap(league_id, year):
    """Fetch draft picks using ESPN's draft recap endpoint"""
    try:
        url = (
            f"https://fantasy.espn.com/apis/v3/games/ffl/seasons/{year}/segments/0/"
            f"leagues/{league_id}?view=mDraftDetail&view=mTeam"
        )
        
        headers = {
            'Cookie': f'espn_s2={ESPN_S2}; SWID={SWID}',
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        }
        
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            return set()
            
        data = response.json()
        picks = data.get('draftDetail', {}).get('picks', [])
        return {p['player']['fullName'] for p in picks if 'player' in p}
        
    except Exception as e:
        return set()


def get_best_available(df, drafted, drafted_positions, current_pick_number):
    df["Drafted"] = df["Player"].isin(drafted)
    available = df[~df["Drafted"]]

    for pos in ["QB", "TE", "K", "DST", "RB", "WR"]:
        limit = POSITION_LIMITS.get(pos, None)
        if limit is not None and drafted_positions.get(pos, 0) >= limit:
            available = available[available["Position"] != pos]

    def is_reasonable_pick(row):
        adp = row["ADP"]
        vor = row["VOR"]
        tier = row["Tier"]

        if pd.isna(adp) or adp == "NA":
            return True

        adp = float(adp)
        current_round = (current_pick_number - 1) // TOTAL_TEAMS + 1
        next_picks = []
        for i in range(3):
            round_num = current_round + i
            if round_num % 2 == 1:
                pick_num = (round_num - 1) * TOTAL_TEAMS + YOUR_DRAFT_SLOT + 1
            else:
                pick_num = round_num * TOTAL_TEAMS - YOUR_DRAFT_SLOT
            next_picks.append(pick_num)

        max_reasonable_adp = max(next_picks) + (TOTAL_TEAMS * 1)
        if vor > 50:
            max_reasonable_adp = max(next_picks) + (TOTAL_TEAMS * 2)
        elif str(tier) == "1":
            max_reasonable_adp = max(next_picks) + (TOTAL_TEAMS * 3)

        return adp <= max_reasonable_adp

    available = available[available.apply(is_reasonable_pick, axis=1)]
    return available.sort_values(by=["Tier", "VOR"], ascending=[True, False]).head(10)


def show_position_analysis(df, drafted, position):
    
    available_df = df[~df['Player'].isin(drafted)]
    pos_data = available_df[available_df['Position'] == position].copy()
    pos_data = pos_data.sort_values('VOR', ascending=False).head(10)
    
    print(f"\n=== {position} ANALYSIS ===")
    print(f"Available players: {len(pos_data)}")
    
    if len(pos_data) == 0:
        print(f"No {position} players available")
        return
    
    print(f"\nTop {position} players:")
    for i, (_, player) in enumerate(pos_data.iterrows(), 1):
        adp_str = f"ADP: {player['ADP']}" if not pd.isna(player['ADP']) and player['ADP'] != 'NA' else "ADP: N/A"
        print(f"  {i}. {player['Player']} | VOR: {player['VOR']:.1f} | Tier {player['Tier']} | {adp_str}")


def show_roster_summary(drafted_positions):
   
    print("\n=== ROSTER SUMMARY ===")
    total_players = sum(drafted_positions.values())
    
    for pos, count in drafted_positions.items():
        limit = POSITION_LIMITS.get(pos, "∞")
        status = "✅" if count >= STARTING_LINEUP.get(pos, 0) else "⚠️"
        print(f"  {status} {pos}: {count}/{limit}")
    
    print(f"\nTotal players: {total_players}/{TOTAL_ROSTER_SIZE}")


def show_quick_recommendations(df, drafted, drafted_positions, current_pick):
    available_df = df[~df['Player'].isin(drafted)]
    available_df = available_df.sort_values('VOR', ascending=False).head(5)
    
    print(f"\n=== TOP RECOMMENDATIONS (Filtered from {len(drafted)} drafted players) ===")
    for i, (_, player) in enumerate(available_df.iterrows(), 1):
        adp_str = f"ADP: {player['ADP']}" if not pd.isna(player['ADP']) and player['ADP'] != 'NA' else "ADP: N/A"
        print(f"  {i}. {player['Player']} ({player['Position']}) | VOR: {player['VOR']:.1f} | Tier {player['Tier']} | {adp_str}")


def show_draft_status(current_pick, drafted, is_my_turn):
    print(f"\n=== DRAFT STATUS ===")
    print(f"Current pick: #{current_pick}")
    print(f"Round: {(current_pick - 1) // TOTAL_TEAMS + 1}")
    print(f"Players drafted: {len(drafted)}")
    print(f"Your turn: {'YES' if is_my_turn else 'NO'}")
    
    if len(drafted) > 0:
        print(f"Recent picks: {list(drafted)[-5:]}")  # Show last 5 picks
    
    if is_my_turn:
        print("🎯 IT'S YOUR PICK!")
    else:
        current_round = (current_pick - 1) // TOTAL_TEAMS + 1
        picks_until_my_turn = 0
        
        # Calculate picks until my turn
        for pick in range(current_pick, current_pick + TOTAL_TEAMS * 2):
            if is_my_pick(pick):
                picks_until_my_turn = pick - current_pick
                break
        
        if picks_until_my_turn > 0:
            print(f"Picks until your turn: {picks_until_my_turn}")
    
    print(f"API Status: {'Connected' if len(drafted) > 0 else 'No picks detected - use manual mode'}")


def debug_connection(league, drafted):
    """Debug ESPN connection and drafted players"""
    print("\n=== DEBUG CONNECTION ===")
    
    try:
        print(f"League ID: {LEAGUE_ID}")
        print(f"Year: {YEAR}")
        print(f"Total teams: {TOTAL_TEAMS}")
        print(f"Your draft slot: {YOUR_DRAFT_SLOT + 1}")
        
        # Test league connection
        print(f"\nLeague connection test:")
        teams = league.teams
        print(f"Found {len(teams)} teams")
        
        # Show your team
        your_team = league.teams[YOUR_DRAFT_SLOT]
        print(f"Your team: {your_team.team_name}")
        print(f"Your roster: {len(your_team.roster)} players")
        
        # Show detailed draft info
        print(f"\nDraft info:")
        print(f"Drafted players found: {len(drafted)}")
        
        # Try to get more detailed draft information
        try:
            draft_picks = league.draft
            print(f"Raw draft picks object: {type(draft_picks)}")
            print(f"Number of draft picks: {len(draft_picks)}")
            
            if len(draft_picks) > 0:
                print(f"First pick details: {draft_picks[0]}")
                print(f"First pick player name: {draft_picks[0].playerName}")
                print(f"First pick team: {draft_picks[0].team}")
                print(f"First pick round: {draft_picks[0].round_num}")
                print(f"First pick pick_num: {draft_picks[0].pick_num}")
        except Exception as draft_error:
            print(f"Error getting detailed draft info: {draft_error}")
        
        # Check league object attributes
        print(f"\nLeague object attributes:")
        league_attrs = [attr for attr in dir(league) if not attr.startswith('_')]
        print(f"Available attributes: {league_attrs[:10]}...")
        
        # Check if there's a draft status
        try:
            if hasattr(league, 'settings'):
                print(f"League settings attributes: {[attr for attr in dir(league.settings) if not attr.startswith('_')][:10]}")
        except:
            pass
        
        # Check all team rosters for players
        print(f"\nChecking all team rosters:")
        total_rostered_players = 0
        for i, team in enumerate(league.teams):
            roster_count = len(team.roster)
            total_rostered_players += roster_count
            print(f"  Team {i+1} ({team.team_name}): {roster_count} players")
            if roster_count > 0:
                print(f"    Sample players: {[p.name if hasattr(p, 'name') else p.playerName if hasattr(p, 'playerName') else str(p) for p in team.roster[:3]]}")
        
        print(f"Total rostered players across all teams: {total_rostered_players}")
        
        # Check draft recap endpoint
        print(f"\nChecking draft recap endpoint:")
        try:
            recap_picks = fetch_draft_recap(LEAGUE_ID, YEAR)
            print(f"Draft recap picks found: {len(recap_picks)}")
            if len(recap_picks) > 0:
                print(f"Sample recap picks: {list(recap_picks)[:5]}")
        except Exception as e:
            print(f"Error checking draft recap: {e}")
        
        if len(drafted) > 0:
            print(f"Sample drafted players: {list(drafted)[:10]}")
        
        # Show all available players for comparison
        all_players = set(df['Player'].tolist())
        print(f"\nTotal players in dataset: {len(all_players)}")
        print(f"Sample available players: {list(all_players)[:10]}")
        
    except Exception as e:
        print(f"Error during debug: {e}")


def get_user_choice():
    """Get user input for what to view"""
    print("\n" + "="*50)
    print("DRAFT ASSISTANT MENU")
    print("="*50)
    print("1. Show draft status")
    print("2. Show roster summary")
    print("3. Show top recommendations")
    print("4. Analyze QB position")
    print("5. Analyze RB position")
    print("6. Analyze WR position")
    print("7. Analyze TE position")
    print("8. Refresh draft data")
    print("9. Debug connection")
    print("A. Add manual pick")
    print("B. Show manual picks")
    print("C. Clear manual picks")
    print("0. Exit")
    print("="*50)
    
    while True:
        try:
            choice = input("Enter your choice (0-9, A-C): ").strip().upper()
            if choice in ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', 'A', 'B', 'C']:
                return choice
            else:
                print("Please enter a number between 0-9 or A-C")
        except KeyboardInterrupt:
            return '0'


def popup_recommendations(picks):
    layout = [[sg.Text("Recommended Picks at My Turn", font=("Helvetica", 14))]]
    for _, row in picks.iterrows():
        text = (
            f"{row['Player']} ({row['Position']}) | VOR: {row['VOR']:.1f} "
            f"| Tier {row['Tier']} | ADP: {row['ADP']}"
        )
        layout.append([sg.Text(text)])
    layout.append([sg.Button("Refresh")])
    layout.append([sg.Button("Add Mock Pick")])
    window = sg.Window("Draft Assistant", layout)
    return window


drafted_positions = {}
seen_picks = set()
manual_drafted_players = set()  # For manual picks when API fails
last_known_pick_count = 0  # Track changes in pick count

print("Draft Assistant Started!")
print(f"Your draft slot: {YOUR_DRAFT_SLOT + 1}")
print(f"Position limits: {POSITION_LIMITS}")

while True:
    drafted = get_drafted_players()
    # Combine API detected picks with manual picks
    drafted.update(manual_drafted_players)
    
    # Check if we detected new picks
    current_pick_count = len(drafted)
    if current_pick_count > last_known_pick_count:
        print(f"🎉 Detected {current_pick_count - last_known_pick_count} new picks! Total: {current_pick_count}")
        last_known_pick_count = current_pick_count

    if TEST_MODE:
        drafted_positions = {"QB": 0, "RB": 0, "WR": 0, "TE": 0, "FLEX": 0, "K": 0, "DST": 0}
    else:
        your_team = league.teams[YOUR_DRAFT_SLOT]
        drafted_positions = {}
        for player in your_team.roster:
            pos = player.position
            drafted_positions[pos] = drafted_positions.get(pos, 0) + 1

    current_pick_number = len(drafted) + 1
    my_pick = is_my_pick(current_pick_number)

    if my_pick:
        print(f"\n🎯 IT'S YOUR PICK (#{current_pick_number})")
        print("=" * 50)
        
        top_recs = get_best_available(
            df.copy(), drafted, drafted_positions, current_pick_number
        )
        
        print("\nTOP RECOMMENDATIONS FOR YOUR PICK:")
        for i, (_, player) in enumerate(top_recs.iterrows(), 1):
            adp_str = f"ADP: {player['ADP']}" if not pd.isna(player['ADP']) and player['ADP'] != 'NA' else "ADP: N/A"
            print(f"  {i}. {player['Player']} ({player['Position']}) | VOR: {player['VOR']:.1f} | Tier {player['Tier']} | {adp_str}")
        
        # No GUI popup - everything handled through main menu
        pass
    
    # Get user choice for what to view
    choice = get_user_choice()
    
    if choice == '1':
        show_draft_status(current_pick_number, drafted, my_pick)
    elif choice == '2':
        show_roster_summary(drafted_positions)
    elif choice == '3':
        show_quick_recommendations(df, drafted, drafted_positions, current_pick_number)
    elif choice == '4':
        show_position_analysis(df, drafted, 'QB')
    elif choice == '5':
        show_position_analysis(df, drafted, 'RB')
    elif choice == '6':
        show_position_analysis(df, drafted, 'WR')
    elif choice == '7':
        show_position_analysis(df, drafted, 'TE')
    elif choice == '8':
        print("Refreshing draft data...")
        # Force a fresh connection to get latest data
        try:
            league = League(
                league_id=LEAGUE_ID,
                year=YEAR,
                espn_s2=ESPN_S2,
                swid=SWID
            )
            print("Successfully refreshed league connection")
            
            # Try to detect any new picks
            new_drafted = get_drafted_players()
            new_pick_count = len(new_drafted)
            if new_pick_count > current_pick_count:
                print(f"🎉 Found {new_pick_count - current_pick_count} new picks after refresh!")
                drafted.update(new_drafted)
                last_known_pick_count = new_pick_count
            else:
                print("No new picks detected")
                
        except Exception as e:
            print(f"Error refreshing connection: {e}")
        continue
    elif choice == '9':
        debug_connection(league, drafted)
    elif choice == 'A':
        print(f"\n=== ADD MANUAL PICK (Pick #{current_pick_number}) ===")
        
        # Get available players sorted by ADP
        available_df = df[~df['Player'].isin(drafted)]
        available_df = available_df.sort_values('ADP', ascending=True)
        
        # Show top 20 players by ADP
        print("Top 20 available players by ADP:")
        print("=" * 60)
        
        for i, (_, player) in enumerate(available_df.head(20).iterrows(), 1):
            adp_str = f"ADP: {player['ADP']}" if not pd.isna(player['ADP']) and player['ADP'] != 'NA' else "ADP: N/A"
            checkbox = "[ ]" if player['Player'] not in manual_drafted_players else "[✓]"
            print(f"{checkbox} {i:2d}. {player['Player']} ({player['Position']}) | {adp_str} | VOR: {player['VOR']:.1f}")
        
        print("=" * 60)
        print("Enter the number(s) of the player(s) to mark as drafted (comma-separated):")
        print("Example: '1,3,5' or just '1' for a single player")
        
        try:
            choice_input = input("Enter choice(s): ").strip()
            if choice_input:
                # Parse the choices
                choices = [int(x.strip()) for x in choice_input.split(',') if x.strip().isdigit()]
                
                # Validate choices and add players
                added_count = 0
                for choice in choices:
                    if 1 <= choice <= 20:
                        player_row = available_df.iloc[choice - 1]
                        player_name = player_row['Player']
                        if player_name not in manual_drafted_players:
                            manual_drafted_players.add(player_name)
                            print(f"✅ Added {player_name} ({player_row['Position']}) - ADP: {player_row['ADP']}")
                            added_count += 1
                        else:
                            print(f"⚠️  {player_name} already marked as drafted")
                    else:
                        print(f"❌ Invalid choice: {choice} (must be 1-20)")
                
                if added_count > 0:
                    print(f"Total manual picks: {len(manual_drafted_players)}")
                    current_pick_number += added_count
        except ValueError:
            print("❌ Invalid input. Please enter numbers only.")
        except Exception as e:
            print(f"❌ Error: {e}")
    elif choice == 'B':
        print(f"\n=== MANUAL PICKS ({len(manual_drafted_players)}) ===")
        if len(manual_drafted_players) > 0:
            for i, player in enumerate(sorted(manual_drafted_players), 1):
                # Find player info from dataframe
                player_info = df[df['Player'] == player]
                if len(player_info) > 0:
                    pos = player_info.iloc[0]['Position']
                    adp = player_info.iloc[0]['ADP']
                    adp_str = f"ADP: {adp}" if not pd.isna(adp) and adp != 'NA' else "ADP: N/A"
                    print(f"  {i}. {player} ({pos}) | {adp_str}")
                else:
                    print(f"  {i}. {player}")
        else:
            print("No manual picks added yet")
        
        # Show next likely picks
        print(f"\n=== NEXT LIKELY PICKS (Pick #{current_pick_number}) ===")
        available_df = df[~df['Player'].isin(drafted)]
        available_df = available_df.sort_values('ADP', ascending=True)
        
        print("Top 10 available by ADP:")
        for i, (_, player) in enumerate(available_df.head(10).iterrows(), 1):
            adp_str = f"ADP: {player['ADP']}" if not pd.isna(player['ADP']) and player['ADP'] != 'NA' else "ADP: N/A"
            print(f"  {i}. {player['Player']} ({player['Position']}) | {adp_str} | VOR: {player['VOR']:.1f}")
    elif choice == 'C':
        if len(manual_drafted_players) > 0:
            confirm = input(f"Clear all {len(manual_drafted_players)} manual picks? (y/n): ").strip().lower()
            if confirm == 'y':
                manual_drafted_players.clear()
                print("✅ Cleared all manual picks")
            else:
                print("Manual picks not cleared")
        else:
            print("No manual picks to clear")
    elif choice == '0':
        print("Exiting draft assistant...")
        break
    
    # Ask if user wants to continue
    input("\nPress Enter to continue or Ctrl+C to exit...")

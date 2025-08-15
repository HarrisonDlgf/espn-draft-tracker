#!/usr/bin/env python3

import pandas as pd
import time
import random
from config import *
from data_loader import load_and_clean_data
from draft_analyzer import print_draft_insights, is_my_pick

def simulate_espn_mock_draft():
    """Simulate a realistic ESPN mock draft scenario"""
    
    print("🎯 ESPN Mock Draft Simulator")
    print("=" * 50)
    print()
    
    # Load data
    df = load_and_clean_data()
    if df is None:
        print("Failed to load data. Exiting.")
        return
    
    # Common first round picks (realistic mock draft)
    first_round_picks = [
        "Bijan Robinson", "Christian McCaffrey", "Tyreek Hill", "Ja'Marr Chase",
        "Saquon Barkley", "CeeDee Lamb", "Breece Hall", "Amon-Ra St. Brown",
        "Jonathan Taylor", "Derrick Henry", "Travis Kelce", "Josh Jacobs"
    ]
    
    # Initialize draft state
    drafted_players = set()
    drafted_positions = {'QB': 0, 'RB': 0, 'WR': 0, 'TE': 0, 'K': 0, 'DST': 0}
    current_pick = 1
    
    print(f"🏈 Starting Mock Draft - You are pick #{YOUR_DRAFT_SLOT + 1}")
    print(f"📊 Total teams: {TOTAL_TEAMS}")
    print()
    
    # Simulate first round
    print("🔄 Simulating first round...")
    for i, player in enumerate(first_round_picks):
        if i >= TOTAL_TEAMS:
            break
            
        drafted_players.add(player)
        current_pick = i + 1
        
        # Update position counts
        player_data = df[df['Player'] == player]
        if len(player_data) > 0:
            pos = player_data.iloc[0]['Position']
            drafted_positions[pos] = drafted_positions.get(pos, 0) + 1
        
        print(f"Pick {current_pick}: {player} ({player_data.iloc[0]['Position'] if len(player_data) > 0 else 'Unknown'})")
        
        # Show analysis when it's your pick
        if is_my_pick(current_pick):
            print(f"\n🎯 IT'S YOUR TURN! (Pick #{current_pick})")
            print_draft_insights(df, current_pick, drafted_players, drafted_positions, is_my_pick=True)
            
            # Let user make a pick
            print("\nOptions:")
            print("1. Make your pick (type player name)")
            print("2. Continue simulation (type 'continue')")
            print("3. Quit (type 'quit')")
            
            user_input = input("\nEnter your choice: ").strip()
            
            if user_input.lower() == 'quit':
                print("Ending simulation.")
                return
            elif user_input.lower() == 'continue':
                # Auto-pick best available
                available_df = df[~df['Player'].isin(drafted_players)]
                if len(available_df) > 0:
                    best_pick = available_df.loc[available_df['VOR'].idxmax()]
                    user_pick = best_pick['Player']
                    print(f"Auto-picking: {user_pick}")
                else:
                    user_pick = "Auto Pick"
            else:
                user_pick = user_input
            
            # Add user's pick
            drafted_players.add(user_pick)
            player_data = df[df['Player'] == user_pick]
            if len(player_data) > 0:
                pos = player_data.iloc[0]['Position']
                drafted_positions[pos] = drafted_positions.get(pos, 0) + 1
            
            print(f"✅ You picked: {user_pick}")
        
        time.sleep(0.5)  # Brief pause for readability
    
    print("\n✅ First round complete!")
    print(f"📊 Your roster: {drafted_positions}")
    
    # Continue simulation
    continue_simulation = input("\nContinue simulation? (y/n): ").strip().lower()
    if continue_simulation == 'y':
        simulate_remaining_rounds(df, drafted_players, drafted_positions, current_pick)

def simulate_remaining_rounds(df, drafted_players, drafted_positions, start_pick):
    """Simulate remaining rounds with realistic picks"""
    
    print(f"\n🔄 Simulating rounds {start_pick + 1} onwards...")
    
    # Common picks by round (realistic)
    round_picks = {
        2: ["Justin Jefferson", "Josh Allen", "Patrick Mahomes", "Brock Bowers", "George Kittle", "Lamar Jackson"],
        3: ["Puka Nacua", "Nico Collins", "James Cook", "Chase Brown", "Bucky Irving", "Kyren Williams"],
        4: ["Jalen Hurts", "Joe Burrow", "Trey McBride", "Sam LaPorta", "Dalton Kincaid", "Mark Andrews"]
    }
    
    current_pick = start_pick + 1
    
    for round_num in range(2, 5):  # Simulate rounds 2-4
        print(f"\n📋 Round {round_num}:")
        
        round_players = round_picks.get(round_num, [])
        
        for i in range(TOTAL_TEAMS):
            current_pick = (round_num - 1) * TOTAL_TEAMS + i + 1
            
            # Pick a player for this slot
            if i < len(round_players):
                player = round_players[i]
            else:
                # Pick from available players
                available_df = df[~df['Player'].isin(drafted_players)]
                if len(available_df) > 0:
                    player = available_df.sample(n=1).iloc[0]['Player']
                else:
                    player = f"Player_{current_pick}"
            
            drafted_players.add(player)
            
            # Update position counts
            player_data = df[df['Player'] == player]
            if len(player_data) > 0:
                pos = player_data.iloc[0]['Position']
                drafted_positions[pos] = drafted_positions.get(pos, 0) + 1
            
            print(f"Pick {current_pick}: {player} ({player_data.iloc[0]['Position'] if len(player_data) > 0 else 'Unknown'})")
            
            # Show analysis when it's your pick
            if is_my_pick(current_pick):
                print(f"\n🎯 IT'S YOUR TURN! (Pick #{current_pick})")
                print_draft_insights(df, current_pick, drafted_players, drafted_positions, is_my_pick=True)
                
                # Let user make a pick
                print("\nOptions:")
                print("1. Make your pick (type player name)")
                print("2. Continue simulation (type 'continue')")
                print("3. Quit (type 'quit')")
                
                user_input = input("\nEnter your choice: ").strip()
                
                if user_input.lower() == 'quit':
                    print("Ending simulation.")
                    return
                elif user_input.lower() == 'continue':
                    # Auto-pick best available
                    available_df = df[~df['Player'].isin(drafted_players)]
                    if len(available_df) > 0:
                        best_pick = available_df.loc[available_df['VOR'].idxmax()]
                        user_pick = best_pick['Player']
                        print(f"Auto-picking: {user_pick}")
                    else:
                        user_pick = "Auto Pick"
                else:
                    user_pick = user_input
                
                # Add user's pick
                drafted_players.add(user_pick)
                player_data = df[df['Player'] == user_pick]
                if len(player_data) > 0:
                    pos = player_data.iloc[0]['Position']
                    drafted_positions[pos] = drafted_positions.get(pos, 0) + 1
                
                print(f"✅ You picked: {user_pick}")
            
            time.sleep(0.3)
    
    print(f"\n✅ Simulation complete!")
    print(f"📊 Final roster: {drafted_positions}")
    print(f"📋 Total players drafted: {len(drafted_players)}")

def main():
    print("🎯 Mock Draft Testing Options:")
    print("1. Simulate ESPN mock draft")
    print("2. Test specific scenarios")
    print("3. Exit")
    
    choice = input("\nEnter your choice (1-3): ").strip()
    
    if choice == '1':
        simulate_espn_mock_draft()
    elif choice == '2':
        print("Specific scenario testing coming soon...")
    else:
        print("Goodbye!")

if __name__ == "__main__":
    main()

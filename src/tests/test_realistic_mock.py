#!/usr/bin/env python3

import pandas as pd
from config import *
from data_loader import load_and_clean_data
from draft_analyzer import print_draft_insights, is_my_pick

def create_realistic_mock_draft():
    """Create a realistic mock draft scenario for testing"""
    
    print("🎯 Realistic Mock Draft Test")
    print("=" * 50)
    print()
    
    # Load data
    df = load_and_clean_data()
    if df is None:
        print("Failed to load data. Exiting.")
        return
    
    # Realistic first 2 rounds (based on ADP)
    realistic_picks = [
        # Round 1
        "Bijan Robinson", "Christian McCaffrey", "Tyreek Hill", "Ja'Marr Chase",
        "Saquon Barkley", "CeeDee Lamb", "Breece Hall", "Amon-Ra St. Brown",
        "Jonathan Taylor", "Derrick Henry", "Travis Kelce", "Josh Jacobs",
        
        # Round 2
        "Justin Jefferson", "Josh Allen", "Patrick Mahomes", "Brock Bowers",
        "George Kittle", "Lamar Jackson", "Puka Nacua", "Nico Collins",
        "James Cook", "Chase Brown", "Bucky Irving", "Kyren Williams"
    ]
    
    # Initialize
    drafted_players = set()
    drafted_positions = {'QB': 0, 'RB': 0, 'WR': 0, 'TE': 0, 'K': 0, 'DST': 0}
    
    print(f"🏈 You are pick #{YOUR_DRAFT_SLOT + 1} in a {TOTAL_TEAMS}-team draft")
    print()
    
    # Add realistic picks
    for i, player in enumerate(realistic_picks):
        if i >= TOTAL_TEAMS * 2:  # First 2 rounds
            break
            
        drafted_players.add(player)
        current_pick = i + 1
        
        # Update position counts
        player_data = df[df['Player'] == player]
        if len(player_data) > 0:
            pos = player_data.iloc[0]['Position']
            drafted_positions[pos] = drafted_positions.get(pos, 0) + 1
        
        print(f"Pick {current_pick}: {player} ({player_data.iloc[0]['Position'] if len(player_data) > 0 else 'Unknown'})")
    
    print(f"\n✅ Mock draft setup complete!")
    print(f"📊 Current roster: {drafted_positions}")
    print(f"📋 Players drafted: {len(drafted_players)}")
    
    # Test the system
    current_pick = len(drafted_players) + 1
    
    print(f"\n🎯 Testing pick #{current_pick}...")
    
    if is_my_pick(current_pick):
        print_draft_insights(df, current_pick, drafted_players, drafted_positions, is_my_pick=True)
    else:
        print_draft_insights(df, current_pick, drafted_players, drafted_positions, is_my_pick=False)
    
    return drafted_players, drafted_positions

def test_specific_scenarios():
    """Test specific draft scenarios"""
    
    print("🎯 Specific Scenario Testing")
    print("=" * 50)
    print()
    
    scenarios = {
        "Early Pick (1-4)": {"draft_slot": 0, "round": 1},
        "Middle Pick (5-8)": {"draft_slot": 4, "round": 1},
        "Late Pick (9-12)": {"draft_slot": 8, "round": 1},
        "Turn Pick (12/13)": {"draft_slot": 11, "round": 2},
        "Mid-Draft (Round 3)": {"draft_slot": 4, "round": 3},
        "Late Draft (Round 8)": {"draft_slot": 4, "round": 8}
    }
    
    print("Available scenarios:")
    for i, (name, _) in enumerate(scenarios.items(), 1):
        print(f"{i}. {name}")
    
    choice = input("\nSelect scenario (1-6): ").strip()
    
    try:
        choice_idx = int(choice) - 1
        scenario_name = list(scenarios.keys())[choice_idx]
        scenario = list(scenarios.values())[choice_idx]
        
        print(f"\n🎯 Testing: {scenario_name}")
        test_scenario(scenario)
        
    except (ValueError, IndexError):
        print("Invalid choice. Using default scenario.")
        test_scenario({"draft_slot": 3, "round": 1})

def test_scenario(scenario):
    """Test a specific draft scenario"""
    
    # Temporarily update config
    global YOUR_DRAFT_SLOT
    original_slot = YOUR_DRAFT_SLOT
    YOUR_DRAFT_SLOT = scenario["draft_slot"]
    
    print(f"📊 Draft slot: {YOUR_DRAFT_SLOT + 1}")
    print(f"📋 Round: {scenario['round']}")
    
    # Create realistic picks for this scenario
    df = load_and_clean_data()
    if df is None:
        return
    
    # Generate picks based on round
    picks_needed = (scenario["round"] - 1) * TOTAL_TEAMS + YOUR_DRAFT_SLOT
    drafted_players = set()
    drafted_positions = {'QB': 0, 'RB': 0, 'WR': 0, 'TE': 0, 'K': 0, 'DST': 0}
    
    # Add realistic picks
    top_players = df.nlargest(picks_needed, 'VOR')['Player'].tolist()
    for player in top_players:
        drafted_players.add(player)
        player_data = df[df['Player'] == player]
        if len(player_data) > 0:
            pos = player_data.iloc[0]['Position']
            drafted_positions[pos] = drafted_positions.get(pos, 0) + 1
    
    current_pick = len(drafted_players) + 1
    
    print(f"\n🎯 Testing pick #{current_pick}...")
    
    if is_my_pick(current_pick):
        print_draft_insights(df, current_pick, drafted_players, drafted_positions, is_my_pick=True)
    else:
        print_draft_insights(df, current_pick, drafted_players, drafted_positions, is_my_pick=False)
    
    # Restore original slot
    YOUR_DRAFT_SLOT = original_slot

def main():
    print("🎯 Mock Draft Testing Options:")
    print("1. Realistic mock draft test")
    print("2. Specific scenario testing")
    print("3. Exit")
    
    choice = input("\nEnter your choice (1-3): ").strip()
    
    if choice == '1':
        create_realistic_mock_draft()
    elif choice == '2':
        test_specific_scenarios()
    else:
        print("Goodbye!")

if __name__ == "__main__":
    main()


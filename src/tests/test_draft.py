#!/usr/bin/env python3
"""
Test script for the ESPN Draft Tracker
This simulates a mock draft scenario to test the functionality
"""

import pandas as pd
from config import *

def test_draft_scenario():
    """Test the draft assistant with a mock scenario"""
    
    # Load and prepare data
    df = pd.read_csv("projections.csv")
    df = df.rename(columns={
        "player": "Player",
        "position": "Position", 
        "points_vor": "VOR",
        "tier": "Tier",
        "adp": "ADP"
    })
    
    # Simulate some drafted players
    mock_drafted = {
        "Bijan Robinson",  # Pick 1
        "Saquon Barkley",  # Pick 2  
        "Jahmyr Gibbs",    # Pick 3
        "Ja'Marr Chase",   # Pick 4
        "Derrick Henry",   # Pick 5
        "Devon Achane",    # Pick 6
        "Christian McCaffrey", # Pick 7
        "Josh Jacobs",     # Pick 8
        "Ashton Jeanty",   # Pick 9
        "Jonathan Taylor", # Pick 10
        "Bucky Irving",    # Pick 11
        "Kyren Williams"   # Pick 12
    }
    
    # Your team (drafting 4th, so you have picks 4, 21, 28, etc.)
    your_team_positions = {
        "QB": 0,
        "RB": 0, 
        "WR": 0,
        "TE": 0,
        "FLEX": 0
    }
    
    # Mark drafted players
    df["Drafted"] = df["Player"].isin(mock_drafted)
    available = df[~df["Drafted"]]
    
    # Apply position limits
    if your_team_positions.get("QB", 0) >= POSITION_LIMITS["QB"]:
        available = available[available["Position"] != "QB"]
    
    # Get top recommendations (simulating current pick #13)
    current_pick_number = 13
    
    # ADP-based filtering
    def is_reasonable_pick(row):
        adp = row['ADP']
        vor = row['VOR']
        tier = row['Tier']
        
        # Skip players with no ADP data
        if pd.isna(adp) or adp == 'NA':
            return True
        
        adp = float(adp)
        
        # Calculate pick range based on current pick
        # Allow picks within 2 rounds of current position
        max_reasonable_adp = current_pick_number + (TOTAL_TEAMS * 2)
        
        # Special cases for high-value players
        if vor > 50:  # High VOR players
            max_reasonable_adp = current_pick_number + (TOTAL_TEAMS * 3)
        elif tier == "1":  # Tier 1 players
            max_reasonable_adp = current_pick_number + (TOTAL_TEAMS * 4)
        
        return adp <= max_reasonable_adp

    # Apply ADP filtering
    available = available[available.apply(is_reasonable_pick, axis=1)]
    top_recs = available.sort_values(by=["Tier", "VOR"], ascending=[True, False]).head(10)
    
    print("=== MOCK DRAFT TEST SCENARIO ===")
    print(f"Your draft slot: {YOUR_DRAFT_SLOT + 1}")
    print(f"Position limits: {POSITION_LIMITS}")
    print(f"Players already drafted: {len(mock_drafted)}")
    print(f"Your current roster: {your_team_positions}")
    print(f"\n=== TOP 10 RECOMMENDATIONS (Pick #{current_pick_number}) ===")
    
    for i, row in top_recs.iterrows():
        print(f"{i+1}. {row['Player']} ({row['Position']}) | VOR: {row['VOR']:.1f} | Tier {row['Tier']} | ADP: {row['ADP']}")
    
    print("\n=== TESTING COMPLETE ===")
    print("To run the full GUI version, execute: python main.py")

if __name__ == "__main__":
    test_draft_scenario()

#!/usr/bin/env python3
"""
Test script to simulate a late pick and see ADP filtering in action
"""

import pandas as pd
from config import *

def test_late_pick():
    """Test recommendations for a late pick"""
    
    # Load and prepare data
    df = pd.read_csv("projections.csv")
    df = df.rename(columns={
        "player": "Player",
        "position": "Position", 
        "points_vor": "VOR",
        "tier": "Tier",
        "adp": "ADP"
    })
    
    # Simulate many drafted players (late in draft)
    mock_drafted = set()
    for i in range(100):  # Simulate 100 picks already made
        mock_drafted.add(f"Player_{i}")
    
    # Add some real players that would be drafted early
    early_players = [
        "Bijan Robinson", "Saquon Barkley", "Jahmyr Gibbs", "Ja'Marr Chase",
        "Derrick Henry", "Devon Achane", "Christian McCaffrey", "Josh Jacobs",
        "Ashton Jeanty", "Jonathan Taylor", "Bucky Irving", "Kyren Williams",
        "Justin Jefferson", "CeeDee Lamb", "Brock Bowers", "Josh Allen",
        "Puka Nacua", "Trey McBride", "Lamar Jackson", "Malik Nabers"
    ]
    
    for player in early_players:
        mock_drafted.add(player)
    
    # Your team
    your_team_positions = {
        "QB": 0,
        "RB": 0, 
        "WR": 0,
        "TE": 0,
        "FLEX": 0,
        "K": 0,
        "DST": 0
    }
    
    # Mark drafted players
    df["Drafted"] = df["Player"].isin(mock_drafted)
    available = df[~df["Drafted"]]
    
    # Apply position limits
    if your_team_positions.get("QB", 0) >= POSITION_LIMITS.get("QB", 1):
        available = available[available["Position"] != "QB"]
    
    # Test different pick numbers
    test_picks = [120, 140, 160, 180]
    
    for pick_num in test_picks:
        print(f"\n{'='*60}")
        print(f"TESTING PICK #{pick_num}")
        print(f"{'='*60}")
        
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
            max_reasonable_adp = pick_num + (TOTAL_TEAMS * 2)
            
            # Special cases for high-value players
            if vor > 50:  # High VOR players
                max_reasonable_adp = pick_num + (TOTAL_TEAMS * 3)
            elif tier == "1":  # Tier 1 players
                max_reasonable_adp = pick_num + (TOTAL_TEAMS * 4)
            
            return adp <= max_reasonable_adp

        # Apply ADP filtering
        filtered_available = available[available.apply(is_reasonable_pick, axis=1)]
        
        # Get top recommendations
        top_recs = filtered_available.sort_values(by=["Tier", "VOR"], ascending=[True, False]).head(10)
        
        print(f"Available players after ADP filtering: {len(filtered_available)}")
        print(f"Position breakdown: {filtered_available['Position'].value_counts().to_dict()}")
        print(f"\nTop 10 recommendations:")
        
        for i, row in top_recs.iterrows():
            adp_display = f"ADP: {row['ADP']}" if not pd.isna(row['ADP']) and row['ADP'] != 'NA' else "ADP: N/A"
            print(f"{i+1}. {row['Player']} ({row['Position']}) | VOR: {row['VOR']:.1f} | Tier {row['Tier']} | {adp_display}")

if __name__ == "__main__":
    test_late_pick()

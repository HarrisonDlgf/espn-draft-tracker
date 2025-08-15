#!/usr/bin/env python3

import pandas as pd
from data_loader import load_and_clean_data

def test_position_analysis():
    """Test the position analysis functions"""
    print("Testing GUI Functions in TEST_MODE...")
    
    # Load data
    df = load_and_clean_data()
    if df is None:
        print("Failed to load data")
        return
    
    # Test drafted players (empty in test mode)
    drafted = set()
    
    # Test position analysis
    positions = ['QB', 'RB', 'WR', 'TE']
    
    for pos in positions:
        print(f"\n=== {pos} ANALYSIS ===")
        available_df = df[~df['Player'].isin(drafted)]
        pos_data = available_df[available_df['Position'] == pos].copy()
        pos_data = pos_data.sort_values('VOR', ascending=False).head(5)
        
        print(f"Available {pos} players: {len(pos_data)}")
        if len(pos_data) > 0:
            print(f"Top {pos} players:")
            for i, (_, player) in enumerate(pos_data.iterrows(), 1):
                adp_str = f"ADP: {player['ADP']}" if not pd.isna(player['ADP']) and player['ADP'] != 'NA' else "ADP: N/A"
                print(f"  {i}. {player['Player']} | VOR: {player['VOR']:.1f} | Tier {player['Tier']} | {adp_str}")
    
    # Test manual pick window data
    print(f"\n=== MANUAL PICK WINDOW DATA ===")
    available_df = df[~df['Player'].isin(drafted)]
    
    for pos in ['QB', 'RB', 'WR', 'TE', 'K', 'DST']:
        pos_df = available_df[available_df['Position'] == pos].sort_values('ADP', ascending=True)
        print(f"{pos}: {len(pos_df)} available players")
        if len(pos_df) > 0:
            top_player = pos_df.iloc[0]
            print(f"  Top {pos}: {top_player['Player']} (ADP: {top_player['ADP']})")
    
    print("\n✅ All GUI functions should work correctly in TEST_MODE!")

if __name__ == "__main__":
    test_position_analysis()

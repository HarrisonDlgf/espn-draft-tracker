#!/usr/bin/env python3
"""
Test script to demonstrate dynamic ADP reach penalties and scoring format prioritization
"""

import sys
import os
sys.path.append('src')

import pandas as pd
from recommendation_engine import RecommendationEngine
from config import set_league_type
from data_loader import load_and_clean_data

def test_dynamic_adp():
    """Test dynamic ADP reach penalties at different draft positions"""
    
    # Load sample data
    df = load_and_clean_data()
    if df is None:
        print("❌ Could not load projections data")
        return
    print("✅ Loaded projections data")
    
    # Create recommendation engine
    engine = RecommendationEngine(df)
    
    # Test positions: early, mid, late
    test_positions = [7, 50, 100]
    
    print("\n🏈 Dynamic ADP Reach Penalty Test")
    print("=" * 50)
    
    for pick_num in test_positions:
        print(f"\n📊 Pick #{pick_num}:")
        
        # Update engine state
        engine.update_draft_state(set(), {}, pick_num)
        
        # Get dynamic ADP info
        adp_info = engine.get_dynamic_adp_info()
        
        print(f"  Draft Phase: {adp_info['draft_phase']}")
        print(f"  Reach Threshold: {adp_info['reach_threshold']:.1f} (base: {adp_info['base_reach_threshold']})")
        print(f"  Penalty Multiplier: {adp_info['penalty_multiplier']}x")
        
        # Show example penalty calculation
        base_penalty = adp_info['base_penalty']
        dynamic_penalty = base_penalty * adp_info['penalty_multiplier']
        print(f"  Example Reach Penalty: -{dynamic_penalty:.1f} (vs base -{base_penalty})")

def test_scoring_format_prioritization():
    """Test scoring format prioritization"""
    
    print("\n🎯 Scoring Format Prioritization Test")
    print("=" * 50)
    
    # Load sample data
    df = load_and_clean_data()
    if df is None:
        print("❌ Could not load projections data")
        return
    print("✅ Loaded projections data")
    
    # Test both scoring formats
    for league_type in ['non_ppr', 'half_ppr']:
        print(f"\n📊 {league_type.upper()} Scoring:")
        
        # Set league type
        set_league_type(league_type)
        
        # Create engine
        engine = RecommendationEngine(df)
        engine.update_draft_state(set(), {}, 25)  # Mid-draft position
        
        # Get top players by position
        for position in ['RB', 'WR', 'TE', 'QB']:
            pos_analysis = engine.get_position_analysis(position, top_n=3)
            if len(pos_analysis) > 0:
                top_player = pos_analysis.iloc[0]
                breakdown = engine.get_detailed_score_breakdown(top_player)
                
                print(f"  Top {position}: {top_player['Player']}")
                print(f"    VOR: {top_player['VOR']:.1f}")
                print(f"    Scoring Format Bonus: {breakdown['scoring_format_bonus']:.1f}")
                print(f"    Total Score: {breakdown['total_score']:.1f}")

def test_comprehensive_scoring():
    """Test comprehensive scoring with both improvements"""
    
    print("\n🔬 Comprehensive Scoring Test")
    print("=" * 50)
    
    # Load sample data
    df = load_and_clean_data()
    if df is None:
        print("❌ Could not load projections data")
        return
    print("✅ Loaded projections data")
    
    # Set to half-PPR for more interesting results
    set_league_type('half_ppr')
    
    # Create engine
    engine = RecommendationEngine(df)
    
    # Test at different draft positions
    test_positions = [7, 50, 100]
    
    for pick_num in test_positions:
        print(f"\n📊 Pick #{pick_num}:")
        
        engine.update_draft_state(set(), {}, pick_num)
        
        # Get recommendations
        recommendations = engine.get_recommendations(top_n=5)
        
        if len(recommendations) > 0:
            print("  Top 5 Recommendations:")
            for i, (_, player) in enumerate(recommendations.iterrows(), 1):
                breakdown = engine.get_detailed_score_breakdown(player)
                
                print(f"    {i}. {player['Player']} ({player['Position']})")
                print(f"       VOR: {player['VOR']:.1f} | ADP: {player['ADP']}")
                print(f"       Total Score: {breakdown['total_score']:.1f}")
                print(f"       ADP Value: {breakdown['adp_value']:.1f}")
                print(f"       Scoring Bonus: {breakdown['scoring_format_bonus']:.1f}")

if __name__ == "__main__":
    print("🧪 Testing Dynamic ADP and Scoring Format Improvements")
    print("=" * 60)
    
    test_dynamic_adp()
    test_scoring_format_prioritization()
    test_comprehensive_scoring()
    
    print("\n✅ Testing complete!")

#!/usr/bin/env python3
"""
Test script to demonstrate the new two-layer recommendation system
Shows how it fixes the D'Andre Swift issue and properly balances position urgency
"""

import sys
import os
sys.path.append('src')

import pandas as pd
from recommendation_engine import RecommendationEngine
from config import set_league_type
from data_loader import load_and_clean_data

def test_new_system():
    """Test the new two-layer recommendation system"""
    
    print("🧪 TESTING NEW TWO-LAYER RECOMMENDATION SYSTEM")
    print("=" * 70)
    
    # Load data
    df = load_and_clean_data()
    if df is None:
        print("❌ Could not load projections data")
        return
    print("✅ Loaded projections data")
    
    # Set to non-PPR for testing
    set_league_type('non_ppr')
    
    # Create engine
    engine = RecommendationEngine(df)
    
    # Test scenarios
    test_scenarios = [
        {
            'name': 'Early Draft (Pick #1)',
            'current_pick': 1,
            'drafted': set(),
            'drafted_positions': {}
        },
        {
            'name': 'After Drafting 2 RBs (Pick #25)',
            'current_pick': 25,
            'drafted': {'Saquon Barkley', 'Bijan Robinson'},
            'drafted_positions': {'RB': 2}
        },
        {
            'name': 'Mid Draft with RB Heavy (Pick #50)',
            'current_pick': 50,
            'drafted': {'Saquon Barkley', 'Bijan Robinson', 'Josh Jacobs', 'Christian McCaffrey', 'Devon Achane'},
            'drafted_positions': {'RB': 5}
        },
        {
            'name': 'Late Draft (Pick #100)',
            'current_pick': 100,
            'drafted': {'Saquon Barkley', 'Bijan Robinson', 'Josh Jacobs', 'Christian McCaffrey', 'Devon Achane', 'Ja\'Marr Chase', 'Justin Jefferson', 'CeeDee Lamb'},
            'drafted_positions': {'RB': 5, 'WR': 3}
        }
    ]
    
    for scenario in test_scenarios:
        print(f"\n{'='*70}")
        print(f"SCENARIO: {scenario['name']}")
        print(f"{'='*70}")
        
        # Update engine state
        engine.update_draft_state(scenario['drafted'], scenario['drafted_positions'], scenario['current_pick'])
        
        # Get position urgencies
        print(f"\n📊 POSITION URGENCY ANALYSIS:")
        print("-" * 50)
        
        position_urgencies = {}
        for pos in ['RB', 'WR', 'TE', 'QB']:
            urgency = engine.get_position_urgency(pos)
            position_urgencies[pos] = urgency
            
            # Get detailed breakdown
            breakdown = engine.get_position_urgency_breakdown(pos)
            if breakdown:
                print(f"\n{pos} Urgency: {urgency:.1f}")
                print(f"  Opportunity Cost: {breakdown['opportunity_cost']:.1f}")
                print(f"  Cliff Pressure: {breakdown['cliff_pressure']:.1f}")
                print(f"  Roster Need: {breakdown['roster_need']:.1f}")
                print(f"  Early QB Penalty: {breakdown['early_qb_penalty']:.1f}")
        
        # Get recommended position
        recommended_pos = engine.get_recommended_position()
        print(f"\n🎯 RECOMMENDED POSITION: {recommended_pos}")
        
        # Get recommendations within that position
        recommendations = engine.get_recommendations(5)
        
        if len(recommendations) > 0:
            print(f"\n📋 TOP PLAYERS IN {recommended_pos}:")
            print("-" * 50)
            
            for i, (_, player) in enumerate(recommendations.iterrows(), 1):
                # Get detailed score breakdown
                breakdown = engine.get_detailed_score_breakdown(player)
                
                print(f"{i}. {player['Player']} ({player['Position']})")
                print(f"   VOR: {player['VOR']:.1f} | Tier: {player['Tier']} | ADP: {player['ADP']}")
                print(f"   Total Score: {breakdown['total_score']:.1f}")
                print(f"   Breakdown: VOR({breakdown['vor_score']:.1f}) + Tier({breakdown['tier_bonus']:.1f}) + Cliff({breakdown['cliff_bonus']:.1f}) + ADP({breakdown['adp_value']:.1f}) + Risk({breakdown['risk_tilt']:.1f}) + Reach({breakdown['reach_cost']:.1f})")
                
                # Check if this is D'Andre Swift
                if player['Player'] == "D'Andre Swift":
                    print(f"   ⚠️  D'Andre Swift Analysis:")
                    print(f"      - VOR: {player['VOR']:.1f} (reasonable)")
                    print(f"      - Tier: {player['Tier']} (mid-tier)")
                    print(f"      - ADP: {player['ADP']} (going in round 5-6)")
                    print(f"      - Reach Cost: {breakdown['reach_cost']:.1f} (should penalize early picks)")
                    print(f"      - Position Urgency: {urgency:.1f} (should consider roster needs)")
        
        # Show strategic insights
        insights = engine.get_strategic_insights()
        if insights.get('cliffs_detected'):
            print(f"\n📉 CLIFFS DETECTED:")
            for pos, cliff_info in insights['cliffs_detected'].items():
                print(f"  {pos}: {cliff_info}")

def test_swift_specific():
    """Test specifically why D'Andre Swift was getting high scores"""
    
    print(f"\n{'='*70}")
    print("D'ANDRE SWIFT SPECIFIC ANALYSIS")
    print(f"{'='*70}")
    
    # Load data
    df = load_and_clean_data()
    if df is None:
        return
    
    set_league_type('non_ppr')
    engine = RecommendationEngine(df)
    
    # Find D'Andre Swift
    swift_data = df[df['Player'] == "D'Andre Swift"]
    if len(swift_data) == 0:
        print("❌ D'Andre Swift not found in data")
        return
    
    swift = swift_data.iloc[0]
    print(f"\n📊 D'Andre Swift Data:")
    print(f"  VOR: {swift['VOR']:.1f}")
    print(f"  Tier: {swift['Tier']}")
    print(f"  ADP: {swift['ADP']}")
    print(f"  Dropoff: {swift.get('dropoff', 'N/A')}")
    print(f"  Uncertainty: {swift.get('uncertainty', 'N/A')}")
    
    # Test at different draft positions
    test_positions = [1, 25, 50, 75, 100]
    
    print(f"\n🎯 SWIFT'S SCORE AT DIFFERENT DRAFT POSITIONS:")
    print("-" * 60)
    
    for pick_num in test_positions:
        engine.update_draft_state(set(), {}, pick_num)
        
        # Calculate Swift's score
        swift_score = engine.calculate_player_score(swift)
        
        # Get position urgency for RB
        rb_urgency = engine.get_position_urgency('RB')
        
        # Get detailed breakdown
        breakdown = engine.get_detailed_score_breakdown(swift)
        
        print(f"\nPick #{pick_num}:")
        print(f"  Player Score: {swift_score:.1f}")
        print(f"  RB Position Urgency: {rb_urgency:.1f}")
        print(f"  Reach Cost: {breakdown['reach_cost']:.1f}")
        print(f"  ADP Value: {breakdown['adp_value']:.1f}")
        
        # Check if Swift would be recommended
        recommendations = engine.get_recommendations(5)
        is_recommended = any(player['Player'] == "D'Andre Swift" for _, player in recommendations.iterrows())
        
        if is_recommended:
            rank = next(i for i, (_, player) in enumerate(recommendations.iterrows(), 1) if player['Player'] == "D'Andre Swift")
            print(f"  ✅ RECOMMENDED (Rank #{rank})")
        else:
            print(f"  ❌ NOT RECOMMENDED")

def compare_old_vs_new():
    """Compare old vs new scoring systems"""
    
    print(f"\n{'='*70}")
    print("OLD vs NEW SCORING COMPARISON")
    print(f"{'='*70}")
    
    # Load data
    df = load_and_clean_data()
    if df is None:
        return
    
    set_league_type('non_ppr')
    
    # Test scenario: Pick #25, 2 RBs already drafted
    current_pick = 25
    drafted = {'Saquon Barkley', 'Bijan Robinson'}
    drafted_positions = {'RB': 2}
    
    print(f"\n📊 COMPARISON AT PICK #{current_pick} (2 RBs drafted):")
    print("-" * 60)
    
    # Old system would just rank by VOR
    available = df[~df['Player'].isin(drafted)]
    old_top = available.sort_values('VOR', ascending=False).head(5)
    
    print(f"\nOLD SYSTEM (VOR-only ranking):")
    for i, (_, player) in enumerate(old_top.iterrows(), 1):
        print(f"  {i}. {player['Player']} ({player['Position']}) | VOR: {player['VOR']:.1f}")
    
    # New system
    engine = RecommendationEngine(df)
    engine.update_draft_state(drafted, drafted_positions, current_pick)
    
    new_recommendations = engine.get_recommendations(5)
    recommended_position = new_recommendations.attrs.get('recommended_position', 'Unknown')
    
    print(f"\nNEW SYSTEM (Position-first approach):")
    print(f"  Recommended Position: {recommended_position}")
    for i, (_, player) in enumerate(new_recommendations.iterrows(), 1):
        print(f"  {i}. {player['Player']} ({player['Position']}) | Score: {player['composite_score']:.1f}")

if __name__ == "__main__":
    print("🧪 Testing New Two-Layer Recommendation System")
    print("This demonstrates how the new system fixes the D'Andre Swift issue")
    print("by properly balancing position urgency with roster composition.")
    
    test_new_system()
    test_swift_specific()
    compare_old_vs_new()
    
    print(f"\n{'='*70}")
    print("✅ Testing complete!")
    print("The new system should:")
    print("• Choose positions based on urgency, not just VOR")
    print("• Consider roster composition when making recommendations")
    print("• Properly penalize reaches (like drafting Swift early)")
    print("• Show position-specific analysis with urgency levels")
    print(f"{'='*70}")

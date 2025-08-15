#!/usr/bin/env python3
"""
Test script for the new Recommendation Engine
Demonstrates the modular composite scoring system
"""

from recommendation_engine import RecommendationEngine
from data_loader import load_and_clean_data
from config import set_league_type

def test_recommendation_engine():
    """Test the new recommendation engine with different scenarios"""
    
    print("🧪 Testing New Recommendation Engine")
    print("=" * 60)
    
    # Load data
    df = load_and_clean_data()
    if df is None:
        print("❌ Failed to load data")
        return
    
    # Test different league types
    for league_type in ['non_ppr', 'half_ppr']:
        print(f"\n📊 Testing {league_type.upper()} League")
        print("-" * 40)
        
        set_league_type(league_type)
        engine = RecommendationEngine(df)
        
        # Scenario 1: Early draft (pick #1)
        print("\n🎯 Early Draft (Pick #1):")
        engine.update_draft_state(set(), {}, 1)
        recs = engine.get_recommendations(5)
        for i, (_, player) in enumerate(recs.iterrows(), 1):
            print(f"  {i}. {player['Player']} ({player['Position']}) | VOR: {player['VOR']:6.1f} | Score: {player['composite_score']:.1f}")
        
        # Scenario 2: After drafting 2 RBs
        print("\n🏃 After Drafting 2 RBs:")
        drafted = {'Saquon Barkley', 'Bijan Robinson'}
        drafted_positions = {'RB': 2}
        engine.update_draft_state(drafted, drafted_positions, 25)
        recs = engine.get_recommendations(5)
        for i, (_, player) in enumerate(recs.iterrows(), 1):
            print(f"  {i}. {player['Player']} ({player['Position']}) | VOR: {player['VOR']:6.1f} | Score: {player['composite_score']:.1f}")
        
        # Scenario 3: Strategic insights
        print("\n🧠 Strategic Insights:")
        insights = engine.get_strategic_insights()
        print(f"  Total Available: {insights['total_available']}")
        print(f"  Cliffs Detected: {insights['cliffs_detected']}")
        print(f"  Value Opportunities: {len(insights['value_opportunities'])}")
        
        # Scenario 4: Position analysis
        print("\n📈 WR Position Analysis:")
        wr_analysis = engine.get_position_analysis('WR', 5)
        for i, (_, player) in enumerate(wr_analysis.iterrows(), 1):
            print(f"  {i}. {player['Player']} | VOR: {player['VOR']:6.1f} | Tier {player['Tier']} | Score: {player['composite_score']:.1f}")

def test_scoring_components():
    """Test individual scoring components"""
    
    print("\n🔍 Testing Scoring Components")
    print("=" * 60)
    
    df = load_and_clean_data()
    set_league_type('non_ppr')
    engine = RecommendationEngine(df)
    engine.update_draft_state(set(), {}, 1)
    
    # Get a sample player
    sample_player = engine.available_df.iloc[0]
    position = sample_player['Position']
    
    print(f"\n📊 Sample Player: {sample_player['Player']} ({position})")
    print(f"  VOR: {sample_player['VOR']:.1f}")
    print(f"  Tier: {sample_player['Tier']}")
    print(f"  ADP: {sample_player['ADP']}")
    
    # Test individual components
    tier_bonus = engine.calculate_tier_bonus(sample_player['Tier'])
    dropoff_bonus = engine.calculate_dropoff_bonus(sample_player, position)
    adp_bonus = engine.calculate_adp_value_bonus(sample_player, position)
    uncertainty_penalty = engine.calculate_uncertainty_penalty(sample_player)
    positional_adjustment = engine.calculate_positional_need_adjustment(sample_player)
    composite_score = engine.calculate_composite_score(sample_player)
    
    print(f"\n🧮 Scoring Breakdown:")
    print(f"  Tier Bonus: {tier_bonus:+.1f}")
    print(f"  Dropoff Bonus: {dropoff_bonus:+.1f}")
    print(f"  ADP Bonus: {adp_bonus:+.1f}")
    print(f"  Uncertainty Penalty: {uncertainty_penalty:+.1f}")
    print(f"  Positional Adjustment: {positional_adjustment:+.1f}")
    print(f"  Composite Score: {composite_score:.1f}")

if __name__ == "__main__":
    test_recommendation_engine()
    test_scoring_components()
    print("\n✅ Recommendation Engine Test Complete!")

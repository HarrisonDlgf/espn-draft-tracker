#!/usr/bin/env python3
"""
Analyze the NEW VOR-based scoring system breakdown
"""

from recommendation_engine import RecommendationEngine
from data_loader import load_and_clean_data
from config import set_league_type

def analyze_new_scoring():
    """Analyze the new VOR-based scoring system for different players"""
    
    print("🔍 NEW VOR-BASED SCORING SYSTEM ANALYSIS")
    print("=" * 60)
    
    # Load data
    df = load_and_clean_data()
    set_league_type('non_ppr')
    engine = RecommendationEngine(df)
    engine.update_draft_state(set(), {}, 1)
    
    # Test players
    players = ['Justin Jefferson', 'Josh Jacobs', 'Bijan Robinson', 'Saquon Barkley']
    
    for player_name in players:
        try:
            player = engine.available_df[engine.available_df['Player'] == player_name].iloc[0]
            
            print(f"\n{player_name} ({player['Position']}):")
            print(f"  VOR: {player['VOR']:.1f} | Tier: {player['Tier']} | ADP: {player['ADP']}")
            print(f"  Ceiling: {player.get('ceiling', 'N/A')} | Floor: {player.get('floor', 'N/A')} | Uncertainty: {player.get('uncertainty', 'N/A')}")
            
            # Calculate each component
            vor_score = engine.calculate_vor_score(player)
            tier_multiplier = engine.calculate_tier_multiplier(player)
            dropoff_bonus = engine.calculate_dropoff_bonus(player, player['Position'])
            adp_value = engine.calculate_adp_value(player)
            uncertainty_penalty = engine.calculate_uncertainty_penalty(player)
            positional_adjustment = engine.calculate_positional_adjustment(player)
            round_adjustment = engine.calculate_round_adjustment(player)
            opportunity_cost = engine.calculate_opportunity_cost(player)
            composite_score = engine.calculate_composite_score(player)
            
            print(f"  1. VOR Score: {vor_score:.1f}")
            print(f"  2. Tier Multiplier: {tier_multiplier:+.1f}")
            print(f"  3. Dropoff Bonus: {dropoff_bonus:+.1f}")
            print(f"  4. ADP Value: {adp_value:+.1f}")
            print(f"  5. Uncertainty Penalty: {uncertainty_penalty:+.1f}")
            print(f"  6. Positional Adjustment: {positional_adjustment:+.1f}")
            print(f"  7. Round Adjustment: {round_adjustment:+.1f}")
            print(f"  8. Opportunity Cost: {opportunity_cost:+.1f}")
            print(f"  TOTAL: {composite_score:.1f}")
            
        except IndexError:
            print(f"\n{player_name}: Not found in data")

def compare_old_vs_new():
    """Compare old vs new scoring systems"""
    
    print("\n🔄 OLD vs NEW SCORING COMPARISON")
    print("=" * 60)
    
    # Load data
    df = load_and_clean_data()
    set_league_type('non_ppr')
    engine = RecommendationEngine(df)
    engine.update_draft_state(set(), {}, 1)
    
    # Get top 10 recommendations with new system
    new_recs = engine.get_recommendations(10)
    
    print("\nNEW VOR-BASED RANKINGS:")
    for i, (_, player) in enumerate(new_recs.iterrows(), 1):
        print(f"  {i:2d}. {player['Player']} ({player['Position']}) | VOR: {player['VOR']:6.1f} | Score: {player['composite_score']:.1f}")

if __name__ == "__main__":
    analyze_new_scoring()
    compare_old_vs_new()

import pandas as pd
from config import *

def analyze_position_depth(df, position, drafted, top_n=5):
    available_df = df[~df['Player'].isin(drafted)]
    pos_data = available_df[available_df['Position'] == position].copy()
    pos_data = pos_data.sort_values('VOR', ascending=False).head(top_n)
    
    analysis = {
        'position': position,
        'total_players': len(available_df[available_df['Position'] == position]),
        'top_players': pos_data,
        'tier_breakdown': pos_data['Tier'].value_counts().to_dict(),
        'avg_uncertainty': pos_data['uncertainty'].mean() if 'uncertainty' in pos_data.columns else None,
        'avg_dropoff': pos_data['dropoff'].mean() if 'dropoff' in pos_data.columns else None
    }
    
    return analysis

def get_position_cliffs(df, position, drafted, threshold=10):
    available_df = df[~df['Player'].isin(drafted)]
    pos_data = available_df[available_df['Position'] == position].copy()
    pos_data = pos_data.sort_values('VOR', ascending=False)
    
    cliffs = []
    for i in range(len(pos_data) - 1):
        current_vor = pos_data.iloc[i]['VOR']
        next_vor = pos_data.iloc[i + 1]['VOR']
        dropoff = current_vor - next_vor
        
        if dropoff > threshold:
            cliffs.append({
                'player': pos_data.iloc[i]['Player'],
                'vor': current_vor,
                'tier': pos_data.iloc[i]['Tier'],
                'dropoff': dropoff,
                'next_player': pos_data.iloc[i + 1]['Player'],
                'next_vor': next_vor
            })
    
    return cliffs

def get_risk_analysis(df, position, drafted):
    available_df = df[~df['Player'].isin(drafted)]
    pos_data = available_df[available_df['Position'] == position].copy()
    pos_data = pos_data.sort_values('VOR', ascending=False).head(10)
    
    if 'uncertainty' not in pos_data.columns or 'sd_pts' not in pos_data.columns:
        return None
    
    high_risk = pos_data[pos_data['uncertainty'] > pos_data['uncertainty'].quantile(0.7)]
    low_risk = pos_data[pos_data['uncertainty'] < pos_data['uncertainty'].quantile(0.3)]
    
    return {
        'high_risk_high_reward': high_risk,
        'low_risk_steady': low_risk,
        'avg_uncertainty': pos_data['uncertainty'].mean(),
        'avg_volatility': pos_data['sd_pts'].mean() if 'sd_pts' in pos_data.columns else None
    }

def get_tier_analysis(df, drafted):
    available_df = df[~df['Player'].isin(drafted)]
    tier_counts = available_df['Tier'].value_counts().sort_index()
    
    analysis = {}
    for tier in tier_counts.index:
        tier_players = available_df[available_df['Tier'] == tier]
        analysis[f'tier_{tier}'] = {
            'count': tier_counts[tier],
            'positions': tier_players['Position'].value_counts().to_dict(),
            'avg_vor': tier_players['VOR'].mean(),
            'players': tier_players[['Player', 'Position', 'VOR', 'ADP']].to_dict('records')
        }
    
    return analysis

def get_strategic_insights(df, current_pick, total_teams, drafted):
    insights = []
    
    available_df = df[~df['Player'].isin(drafted)]
    
    # Only mention tiers that actually have players remaining
    for pos in ['QB', 'RB', 'WR', 'TE']:
        pos_data = available_df[available_df['Position'] == pos]
        
        # Check each tier and only mention if there are players
        for tier in ['1', '2', '3']:
            tier_count = len(pos_data[pos_data['Tier'] == tier])
            if tier_count > 0:
                if tier_count <= 2:
                    insights.append(f"⚠️  {pos} Tier {tier} players running low ({tier_count} remaining)")
                elif tier_count >= 8:
                    insights.append(f"✅ {pos} Tier {tier} depth available ({tier_count} remaining)")
    
    # analyze cliffs
    for pos in ['RB', 'WR']:
        cliffs = get_position_cliffs(df, pos, drafted, threshold=15)
        if cliffs:
            insights.append(f"📉 {pos} cliff detected: {cliffs[0]['player']} → {cliffs[0]['dropoff']:.1f} VOR drop")
    
    # analyze risk profiles
    for pos in ['WR', 'RB']:
        risk_analysis = get_risk_analysis(df, pos, drafted)
        if risk_analysis and risk_analysis['avg_uncertainty'] > 20:
            insights.append(f"🎲 {pos} has high uncertainty ({risk_analysis['avg_uncertainty']:.1f}) - consider steady options")
    
    return insights

def format_position_analysis(analysis):
    output = []
    output.append(f"\n=== {analysis['position']} ANALYSIS ===")
    output.append(f"Total players: {analysis['total_players']}")
    
    if analysis['avg_uncertainty']:
        output.append(f"Avg uncertainty: {analysis['avg_uncertainty']:.1f}")
    if analysis['avg_dropoff']:
        output.append(f"Avg dropoff: {analysis['avg_dropoff']:.1f}")
    
    output.append(f"Tier breakdown: {analysis['tier_breakdown']}")
    output.append("\nTop players:")
    
    for _, player in analysis['top_players'].iterrows():
        uncertainty_str = f" | Uncertainty: {player['uncertainty']:.1f}" if 'uncertainty' in player and not pd.isna(player['uncertainty']) else ""
        dropoff_str = f" | Dropoff: {player['dropoff']:.1f}" if 'dropoff' in player and not pd.isna(player['dropoff']) else ""
        adp_str = f"ADP: {player['ADP']}" if not pd.isna(player['ADP']) and player['ADP'] != 'NA' else "ADP: N/A"
        
        output.append(f"  {player['Player']} | VOR: {player['VOR']:.1f} | Tier {player['Tier']} | {adp_str}{uncertainty_str}{dropoff_str}")
    
    return "\n".join(output)

def get_best_by_position(df, positions=['QB', 'RB', 'WR', 'TE']):
    """Get best available player at each position"""
    best_by_pos = {}
    
    for pos in positions:
        pos_data = df[df['Position'] == pos]
        if len(pos_data) > 0:
            best = pos_data.loc[pos_data['VOR'].idxmax()]
            best_by_pos[pos] = best
    
    return best_by_pos

def get_best_by_position_available(df, drafted, positions=['QB', 'RB', 'WR', 'TE']):
    best_by_pos = {}
    
    available_df = df[~df['Player'].isin(drafted)]
    
    for pos in positions:
        pos_data = available_df[available_df['Position'] == pos]
        if len(pos_data) > 0:
            best = pos_data.loc[pos_data['VOR'].idxmax()]
            best_by_pos[pos] = best
    
    return best_by_pos

def analyze_roster_needs(drafted_positions, available_df):
    """Analyze roster needs and recommend positions to target"""
    needs = {}
    
    # Calculate current roster composition
    current_roster = {
        'QB': drafted_positions.get('QB', 0),
        'RB': drafted_positions.get('RB', 0),
        'WR': drafted_positions.get('WR', 0),
        'TE': drafted_positions.get('TE', 0),
        'K': drafted_positions.get('K', 0),
        'DST': drafted_positions.get('DST', 0)
    }
    
    total_drafted = sum(current_roster.values())
    
    # Determine needs based on ESPN standard roster limits
    for pos, limit in POSITION_LIMITS.items():
        current = current_roster.get(pos, 0)
        
        if current < limit:
            if current < STARTING_LINEUP.get(pos, 0):
                needs[pos] = {
                    'priority': 'critical',
                    'reason': f'Need {STARTING_LINEUP.get(pos, 0) - current} more {pos}(s) for starting lineup'
                }
            else:
                needs[pos] = {
                    'priority': 'high',
                    'reason': f'Need {limit - current} more {pos}(s) for bench depth'
                }
        elif current == limit:
            needs[pos] = {
                'priority': 'medium',
                'reason': f'Have {limit} {pos}(s), good depth but could add more'
            }
        else:
            needs[pos] = {
                'priority': 'low',
                'reason': f'Have {current} {pos}(s), excellent depth'
            }
    
    # Special handling for FLEX position
    flex_candidates = current_roster['RB'] + current_roster['WR'] + current_roster['TE']
    if flex_candidates < STARTING_LINEUP['FLEX']:
        needs['FLEX'] = {
            'priority': 'critical',
            'reason': f'Need {STARTING_LINEUP["FLEX"] - flex_candidates} more RB/WR/TE for FLEX spot'
        }
    
    # Overall roster size check
    if total_drafted >= TOTAL_ROSTER_SIZE:
        needs['ROSTER_FULL'] = {
            'priority': 'critical',
            'reason': f'Roster is full ({total_drafted}/{TOTAL_ROSTER_SIZE})'
        }
    
    return needs

def get_advanced_player_score(player, position_needs, current_pick, available_df):
    """Calculate advanced player score using strategic fantasy football principles"""
    score = 0
    pos = player['Position']
    
    # 1. VOR Weight (increased to be the primary driver)
    score += player['VOR'] * 0.6
    
    # 2. Tier Bonus (scaled down to avoid overshadowing VOR)
    tier = int(player['Tier']) if isinstance(player['Tier'], (int, float)) else 10
    tier_bonus = max(0, (10 - tier) * 2)  # Tier 1 gets +18, Tier 2 gets +16, etc.
    score += tier_bonus
    
    # 3. Roster Need (moderated to not override value)
    if pos in position_needs:
        if position_needs[pos]['priority'] == 'critical':
            score += 30
        elif position_needs[pos]['priority'] == 'high':
            score += 20
        elif position_needs[pos]['priority'] == 'medium':
            score += 10
    
    # 4. Scarcity Cliff Bonus for RBs/WRs (positional value protection)
    if 'dropoff' in player and not pd.isna(player['dropoff']):
        dropoff = player['dropoff']
        if dropoff > 20 and pos in ['RB', 'WR']:
            score += 25  # Protect against positional cliffs
    
    # 5. Positional Scarcity Analysis
    pos_players = available_df[available_df['Position'] == pos]
    if len(pos_players) <= 5:  # Very scarce position
        score += 15
    elif len(pos_players) <= 10:  # Moderately scarce
        score += 8
    
    # 6. QB/TE Deprioritization (unless elite tier)
    if pos in ['QB', 'TE'] and tier > 2:
        score -= 20  # Penalize non-elite QBs/TEs
    
    # 7. Risk Adjustment
    if 'uncertainty' in player and not pd.isna(player['uncertainty']):
        uncertainty = player['uncertainty']
        if uncertainty < 10:
            score += 10  # Low risk bonus
        elif uncertainty > 30:
            score -= 15  # High risk penalty
    
    # 8. Floor/Ceiling Analysis
    if 'floor' in player and 'ceiling' in player and not pd.isna(player['floor']) and not pd.isna(player['ceiling']):
        floor = player['floor']
        ceiling = player['ceiling']
        consistency = ceiling - floor
        if consistency < 50:  # High floor, consistent player
            score += 10
        elif consistency > 100:  # High ceiling, boom/bust
            score += 5
    
    # 9. ADP Value (contextual)
    if not pd.isna(player['ADP']) and player['ADP'] != 'NA':
        adp = float(player['ADP'])
        if adp > current_pick + 12:  # Going 1+ rounds later than current pick
            score += 15
        elif adp < current_pick - 12:  # Going 1+ rounds earlier than current pick
            score -= 10
    
    # 10. FLEX Bonus (only if truly needed)
    if pos in ['RB', 'WR', 'TE'] and 'FLEX' in position_needs:
        if position_needs['FLEX']['priority'] == 'critical':
            score += 15  # Reduced from 25
    
    return score

def get_overall_pick_recommendations(df, drafted, drafted_positions, current_pick, top_n=5):
    """Get overall pick recommendations considering roster needs and advanced stats"""
    available_df = df[~df['Player'].isin(drafted)]
    
    # Analyze roster needs
    position_needs = analyze_roster_needs(drafted_positions, available_df)
    
    # Calculate advanced scores for all available players
    scored_players = []
    for _, player in available_df.iterrows():
        score = get_advanced_player_score(player, position_needs, current_pick, available_df)
        scored_players.append({
            'player': player,
            'score': score,
            'position': player['Position'],
            'vor': player['VOR'],
            'tier': player['Tier']
        })
    
    # Sort by score and return top recommendations
    scored_players.sort(key=lambda x: x['score'], reverse=True)
    
    recommendations = []
    for i, item in enumerate(scored_players[:top_n]):
        player = item['player']
        recommendations.append({
            'rank': i + 1,
            'player': player,
            'score': item['score'],
            'position': item['position'],
            'vor': item['vor'],
            'tier': item['tier'],
            'need_priority': position_needs.get(item['position'], {}).get('priority', 'low'),
            'need_reason': position_needs.get(item['position'], {}).get('reason', 'Depth pick')
        })
    
    return recommendations, position_needs

def print_draft_insights(df, current_pick, drafted, drafted_positions=None, is_my_pick=False):
    if is_my_pick:
        print(f"\n🎯 IT'S YOUR PICK (#{current_pick})")
        print("=" * 50)
        
        # Show overall pick recommendations first
        if drafted_positions:
            recommendations, position_needs = get_overall_pick_recommendations(df, drafted, drafted_positions, current_pick, top_n=5)
            
            print("\n🎯 OVERALL PICK RECOMMENDATIONS:")
            for rec in recommendations:
                player = rec['player']
                uncertainty_str = f" | Uncertainty: {player['uncertainty']:.1f}" if 'uncertainty' in player and not pd.isna(player['uncertainty']) else ""
                dropoff_str = f" | Dropoff: {player['dropoff']:.1f}" if 'dropoff' in player and not pd.isna(player['dropoff']) else ""
                adp_str = f"ADP: {player['ADP']}" if not pd.isna(player['ADP']) and player['ADP'] != 'NA' else "ADP: N/A"
                
                priority_emoji = "🔴" if rec['need_priority'] == 'critical' else "🟠" if rec['need_priority'] == 'high' else "🟡" if rec['need_priority'] == 'medium' else "🟢"
                print(f"  {rec['rank']}. {priority_emoji} {player['Player']} ({rec['position']}) | Score: {rec['score']:.1f} | VOR: {rec['vor']:.1f} | Tier {rec['tier']} | {adp_str}{uncertainty_str}{dropoff_str}")
                print(f"     Reason: {rec['need_reason']}")
            
            print("\n📊 ROSTER NEEDS ANALYSIS:")
            for pos, need in position_needs.items():
                priority_emoji = "🔴" if need['priority'] == 'critical' else "🟠" if need['priority'] == 'high' else "🟡" if need['priority'] == 'medium' else "🟢"
                print(f"  {priority_emoji} {pos}: {need['reason']}")
    else:
        print(f"\n👀 DRAFT ANALYSIS (Pick #{current_pick})")
        print("=" * 50)
        
        best_by_pos = get_best_by_position_available(df, drafted)
        print("\n🏆 BEST AVAILABLE BY POSITION:")
        for pos, player in best_by_pos.items():
            uncertainty_str = f" | Uncertainty: {player['uncertainty']:.1f}" if 'uncertainty' in player and not pd.isna(player['uncertainty']) else ""
            adp_str = f"ADP: {player['ADP']}" if not pd.isna(player['ADP']) and player['ADP'] != 'NA' else "ADP: N/A"
            print(f"  {pos}: {player['Player']} | VOR: {player['VOR']:.1f} | Tier {player['Tier']} | {adp_str}{uncertainty_str}")
        
        insights = get_strategic_insights(df, current_pick, TOTAL_TEAMS, drafted)
        if insights:
            print("\n💡 STRATEGIC INSIGHTS:")
            for insight in insights:
                print(f"  {insight}")
        
        print("\n📊 POSITION DEPTH ANALYSIS:")
        for pos in ['RB', 'WR', 'QB', 'TE']:
            analysis = analyze_position_depth(df, pos, drafted, top_n=3)
            print(format_position_analysis(analysis))
        
        tier_analysis = get_tier_analysis(df, drafted)
        print("\n🏗️  TIER ANALYSIS:")
        for tier_key, tier_data in tier_analysis.items():
            if tier_data['count'] <= 5:  # Only show scarce tiers
                print(f"  {tier_key.upper()}: {tier_data['count']} players remaining")
                print(f"    Positions: {tier_data['positions']}")
                print(f"    Avg VOR: {tier_data['avg_vor']:.1f}")
    
    print("=" * 50)

def is_my_pick(current_pick_number):
    """Determine if it's our pick based on snake draft logic"""
    current_round = (current_pick_number - 1) // TOTAL_TEAMS + 1
    
    if current_round % 2 == 1:  # Odd round - forward
        my_pick_in_round = YOUR_DRAFT_SLOT + 1
    else:  # Even round - reverse
        my_pick_in_round = TOTAL_TEAMS - YOUR_DRAFT_SLOT
    
    pick_in_round = ((current_pick_number - 1) % TOTAL_TEAMS) + 1
    
    return pick_in_round == my_pick_in_round

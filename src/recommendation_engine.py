import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
from config import RECOMMENDATION_CONFIG, POSITION_LIMITS, TOTAL_TEAMS, YOUR_DRAFT_SLOT, POSITION_WEIGHTS

class RecommendationEngine:
    """Recommendation engine  proper VOR-based scoring"""
    
    def __init__(self, df: pd.DataFrame):
        self.df = df.copy()
        self.available_df = None
        self.drafted_players = set()
        self.drafted_positions = {}
        self.current_pick = 1
        
    def update_draft_state(self, drafted_players: set, drafted_positions: dict, current_pick: int):
        self.drafted_players = drafted_players
        self.drafted_positions = drafted_positions
        self.current_pick = current_pick
        self.available_df = self.df[~self.df['Player'].isin(drafted_players)].copy()
        
    def calculate_vor_score(self, player_row: pd.Series) -> float:
        """Calculate VOR-based score using points_vor, ceiling, and floor"""
        vor = player_row['VOR']
        ceiling = player_row.get('ceiling', vor)
        floor = player_row.get('floor', vor)
        
        if pd.isna(vor):
            return 0
            
        
        vor_score = vor * RECOMMENDATION_CONFIG["vor_weight"]
        
        ceiling_vor = ceiling if not pd.isna(ceiling) else vor
        ceiling_score = ceiling_vor * RECOMMENDATION_CONFIG["ceiling_vor_weight"]
        
        floor_vor = floor if not pd.isna(floor) else vor
        floor_score = floor_vor * RECOMMENDATION_CONFIG["floor_vor_weight"]
        
        return vor_score + ceiling_score + floor_score
    
    def calculate_tier_multiplier(self, player_row: pd.Series) -> float:
        tier = player_row['Tier']
        vor = player_row['VOR']
        
        if pd.isna(tier) or pd.isna(vor):
            return 0
            
        tier = int(tier)
        multiplier = RECOMMENDATION_CONFIG["tier_multipliers"].get(tier, 1.0)
        
        return vor * (multiplier - 1.0)  
    
    def calculate_dropoff_bonus(self, player_row: pd.Series, position: str) -> float:
        if position not in ['RB', 'WR', 'TE']:
            return 0
            
        pos_players = self.available_df[self.available_df['Position'] == position].sort_values('VOR', ascending=False)
        if len(pos_players) <= 1:
            return 0
            
        player_vor = player_row['VOR']
        higher_vor_players = pos_players[pos_players['VOR'] > player_vor]
        
        if len(higher_vor_players) == 0:
            return 0  
            
        next_player_vor = higher_vor_players.iloc[-1]['VOR']
        dropoff = next_player_vor - player_vor
        
        if dropoff > RECOMMENDATION_CONFIG["dropoff_threshold"]:
            return RECOMMENDATION_CONFIG["dropoff_bonus"]
        
        return 0
    
    def calculate_adp_value(self, player_row: pd.Series) -> float:
        adp = player_row['ADP']
        vor = player_row['VOR']
        
        if pd.isna(adp) or adp == "NA" or pd.isna(vor):
            return 0
            
        adp = float(adp)
        current_round = (self.current_pick - 1) // TOTAL_TEAMS + 1
        
        next_picks = self._calculate_next_picks(current_round)
        
        # Dynamic ADP reach penalty based on draft position
        # Early picks (1-36): More severe penalties for reaching
        # Mid picks (37-84): Moderate penalties
        # Late picks (85+): Less severe penalties
        if self.current_pick <= 36:  # Early rounds
            reach_threshold = RECOMMENDATION_CONFIG["adp_reach_threshold"] * 0.7  # More strict
            reach_penalty_multiplier = 1.5  # Higher penalty
        elif self.current_pick <= 84:  # Mid rounds
            reach_threshold = RECOMMENDATION_CONFIG["adp_reach_threshold"] * 1.0  # Standard
            reach_penalty_multiplier = 1.0  # Standard penalty
        else:  # Late rounds
            reach_threshold = RECOMMENDATION_CONFIG["adp_reach_threshold"] * 1.3  # Less strict
            reach_penalty_multiplier = 0.7  # Lower penalty
        
        if adp > max(next_picks) + RECOMMENDATION_CONFIG["adp_value_threshold"]:
            return RECOMMENDATION_CONFIG["adp_value_bonus"]
        
        elif adp < min(next_picks) - reach_threshold:
            base_penalty = RECOMMENDATION_CONFIG["adp_reach_penalty"]
            dynamic_penalty = base_penalty * reach_penalty_multiplier
            return -dynamic_penalty
        
        return 0
    
    def calculate_uncertainty_penalty(self, player_row: pd.Series) -> float:
        uncertainty = player_row.get('uncertainty', 0)
        
        if pd.isna(uncertainty):
            return 0
            
        if uncertainty < 20:
            return RECOMMENDATION_CONFIG["uncertainty_penalties"]["low"]
        elif uncertainty < 40:
            return RECOMMENDATION_CONFIG["uncertainty_penalties"]["medium"]
        elif uncertainty < 60:
            return RECOMMENDATION_CONFIG["uncertainty_penalties"]["high"]
        else:
            return RECOMMENDATION_CONFIG["uncertainty_penalties"]["extreme"]
    
    def calculate_positional_adjustment(self, player_row: pd.Series) -> float:
        position = player_row['Position']
        adjustment = 0
        
        # Get scoring format weights
        league_type = RECOMMENDATION_CONFIG.get("league_type", "non_ppr")
        position_weights = POSITION_WEIGHTS.get(league_type, POSITION_WEIGHTS["non_ppr"])
        pos_weights = position_weights.get(position, {"base": 1.0, "scarcity": 1.0, "tier_bonus": 1.0})
        
        # Apply scoring format prioritization
        vor = player_row['VOR']
        if not pd.isna(vor):
            # Base position weight adjustment
            adjustment += vor * (pos_weights["base"] - 1.0) * 0.1
            
            # Scarcity bonus for positions that are more valuable in this scoring format
            if pos_weights["scarcity"] > 1.0:
                adjustment += vor * (pos_weights["scarcity"] - 1.0) * 0.05
        
        # Roster balance penalties (existing logic)
        if position == 'RB' and self.drafted_positions.get('RB', 0) >= 3:
            adjustment -= RECOMMENDATION_CONFIG["positional_balance"]["rb_count_penalty"]
        elif position == 'WR' and self.drafted_positions.get('WR', 0) >= 4:
            adjustment -= RECOMMENDATION_CONFIG["positional_balance"]["wr_count_penalty"]
        
        current_round = (self.current_pick - 1) // TOTAL_TEAMS + 1
        if position == 'QB' and current_round <= 6:
            if player_row['VOR'] < RECOMMENDATION_CONFIG["positional_balance"]["qb_elite_threshold"]:
                adjustment -= RECOMMENDATION_CONFIG["positional_balance"]["qb_early_penalty"]
        
        return adjustment
    
    def calculate_round_adjustment(self, player_row: pd.Series) -> float:
        current_round = (self.current_pick - 1) // TOTAL_TEAMS + 1
        vor = player_row['VOR']
        ceiling = player_row.get('ceiling', vor)
        floor = player_row.get('floor', vor)
        
        if pd.isna(ceiling) or pd.isna(floor):
            return 0
        
        if current_round <= 3:
            return (floor - vor) * 0.1  
        
        elif current_round <= 8:
            return 0  
        
        else:
            return (ceiling - vor) * 0.1  
    
    def calculate_scoring_format_bonus(self, player_row: pd.Series) -> float:
        """Calculate bonus based on scoring format prioritization"""
        position = player_row['Position']
        vor = player_row['VOR']
        
        if pd.isna(vor):
            return 0
        
        league_type = RECOMMENDATION_CONFIG.get("league_type", "non_ppr")
        position_weights = POSITION_WEIGHTS.get(league_type, POSITION_WEIGHTS["non_ppr"])
        pos_weights = position_weights.get(position, {"base": 1.0, "scarcity": 1.0, "tier_bonus": 1.0})
        
        # Tier bonus based on scoring format
        tier = player_row.get('Tier', 3)
        if not pd.isna(tier):
            tier = int(tier)
            if tier <= 2:  # Top tiers get additional bonus in scoring-appropriate formats
                tier_bonus = vor * (pos_weights["tier_bonus"] - 1.0) * 0.15
                return tier_bonus
        
        return 0
    
    def calculate_opportunity_cost(self, player_row: pd.Series) -> float:
        """Calculate opportunity cost penalty for drafting above ADP when better value exists"""
        if not RECOMMENDATION_CONFIG["opportunity_cost"]["enabled"]:
            return 0
            
        adp = player_row['ADP']
        player_vor = player_row['VOR']
        position = player_row['Position']
        
        if pd.isna(adp) or adp == "NA":
            return 0
            
        adp = float(adp)
        current_pick_num = self.current_pick
        
        adp_difference = adp - current_pick_num
        
        if adp_difference > RECOMMENDATION_CONFIG["opportunity_cost"]["look_ahead_rounds"] * TOTAL_TEAMS:
            opportunity_penalty = 0
            
            all_players = self.available_df.sort_values('VOR', ascending=False)
            better_other_positions = all_players[
                (all_players['VOR'] > player_vor + RECOMMENDATION_CONFIG["opportunity_cost"]["vor_difference_threshold"]) &
                (all_players['Position'] != position) &
                (all_players['Position'].isin(['RB', 'WR']))  
            ]
            
            if len(better_other_positions) > 0:
                best_other_vor = better_other_positions.iloc[0]['VOR']
                other_vor_difference = best_other_vor - player_vor
                
                opportunity_penalty = other_vor_difference * 0.5
                
                if position == 'QB':
                    opportunity_penalty += RECOMMENDATION_CONFIG["opportunity_cost"]["qb_opportunity_penalty"]
                elif position == 'TE':
                    opportunity_penalty += RECOMMENDATION_CONFIG["opportunity_cost"]["te_opportunity_penalty"]
                else:
                    opportunity_penalty *= RECOMMENDATION_CONFIG["opportunity_cost"]["positional_penalty_multiplier"]
            
            pos_players = self.available_df[self.available_df['Position'] == position].sort_values('VOR', ascending=False)
            similar_later_options = pos_players[
                (pos_players['VOR'] >= player_vor - 15) &  
                (pos_players['ADP'] > adp + 12)  
            ]
            
            if len(similar_later_options) > 0:
                opportunity_penalty += 20
                
                if position == 'QB':
                    opportunity_penalty += 15
                elif position == 'TE':
                    opportunity_penalty += 10
            
            return -opportunity_penalty  
        
        return 0
    
    def _calculate_next_picks(self, current_round: int) -> List[int]:
        next_picks = []
        for i in range(3):
            round_num = current_round + i
            if round_num % 2 == 1:
                pick_num = (round_num - 1) * TOTAL_TEAMS + YOUR_DRAFT_SLOT + 1
            else:
                pick_num = round_num * TOTAL_TEAMS - YOUR_DRAFT_SLOT
            next_picks.append(pick_num)
        return next_picks
    
    def calculate_composite_score(self, player_row: pd.Series) -> float:
        score = 0
        
        score += self.calculate_vor_score(player_row)
        
        score += self.calculate_tier_multiplier(player_row)
        
        position = player_row['Position']
        score += self.calculate_dropoff_bonus(player_row, position)
        
        score += self.calculate_adp_value(player_row)
        
        score -= self.calculate_uncertainty_penalty(player_row)
        
        score += self.calculate_positional_adjustment(player_row)
        
        score += self.calculate_round_adjustment(player_row)
        
        score += self.calculate_opportunity_cost(player_row)
        
        # Add scoring format prioritization bonus
        score += self.calculate_scoring_format_bonus(player_row)
        
        return score
    
    def get_recommendations(self, top_n: int = 10) -> pd.DataFrame:
        if self.available_df is None or len(self.available_df) == 0:
            return pd.DataFrame()
        
        filtered_df = self.available_df.copy()
        for pos, limit in POSITION_LIMITS.items():
            if self.drafted_positions.get(pos, 0) >= limit:
                filtered_df = filtered_df[filtered_df['Position'] != pos]
        
        filtered_df['composite_score'] = filtered_df.apply(self.calculate_composite_score, axis=1)
        
        recommendations = filtered_df.sort_values('composite_score', ascending=False).head(top_n)
        
        return recommendations
    
    def get_position_analysis(self, position: str, top_n: int = 10) -> pd.DataFrame:
        if self.available_df is None:
            return pd.DataFrame()
            
        pos_df = self.available_df[self.available_df['Position'] == position].copy()
        if len(pos_df) == 0:
            return pd.DataFrame()
        
        pos_df['composite_score'] = pos_df.apply(self.calculate_composite_score, axis=1)
        
        return pos_df.sort_values('composite_score', ascending=False).head(top_n)
    
    def get_strategic_insights(self) -> Dict[str, any]:
        if self.available_df is None:
            return {}
        
        insights = {
            'total_available': len(self.available_df),
            'position_counts': self.available_df['Position'].value_counts().to_dict(),
            'tier_breakdown': self.available_df['Tier'].value_counts().sort_index().to_dict(),
            'cliffs_detected': {},
            'value_opportunities': []
        }
        
        for pos in ['RB', 'WR', 'TE']:
            pos_players = self.available_df[self.available_df['Position'] == pos].sort_values('VOR', ascending=False)
            if len(pos_players) > 1:
                top_vor = pos_players.iloc[0]['VOR']
                second_vor = pos_players.iloc[1]['VOR']
                dropoff = top_vor - second_vor
                
                if dropoff > RECOMMENDATION_CONFIG["dropoff_threshold"]:
                    insights['cliffs_detected'][pos] = f"Cliff: {dropoff:.1f} VOR drop"
        
        for pos in ['RB', 'WR', 'TE']:
            pos_players = self.available_df[self.available_df['Position'] == pos]
            if len(pos_players) > 3:
                high_vor_players = pos_players[pos_players['VOR'] > pos_players['VOR'].quantile(0.7)]
                for _, player in high_vor_players.iterrows():
                    if not pd.isna(player['ADP']) and player['ADP'] != "NA":
                        adp = float(player['ADP'])
                        current_round = (self.current_pick - 1) // TOTAL_TEAMS + 1
                        next_picks = self._calculate_next_picks(current_round)
                        
                        if adp > max(next_picks) + RECOMMENDATION_CONFIG["adp_value_threshold"]:
                            insights['value_opportunities'].append({
                                'player': player['Player'],
                                'position': pos,
                                'vor': player['VOR'],
                                'adp': player['ADP'],
                                'tier': player['Tier']
                            })
        
        return insights
    
    def get_detailed_score_breakdown(self, player_row: pd.Series) -> Dict[str, float]:
        """Get detailed breakdown of all scoring components for a player"""
        breakdown = {
            'vor_score': self.calculate_vor_score(player_row),
            'tier_multiplier': self.calculate_tier_multiplier(player_row),
            'dropoff_bonus': self.calculate_dropoff_bonus(player_row, player_row['Position']),
            'adp_value': self.calculate_adp_value(player_row),
            'uncertainty_penalty': -self.calculate_uncertainty_penalty(player_row),
            'positional_adjustment': self.calculate_positional_adjustment(player_row),
            'round_adjustment': self.calculate_round_adjustment(player_row),
            'opportunity_cost': self.calculate_opportunity_cost(player_row),
            'scoring_format_bonus': self.calculate_scoring_format_bonus(player_row)
        }
        
        breakdown['total_score'] = sum(breakdown.values())
        return breakdown
    
    def get_dynamic_adp_info(self) -> Dict[str, any]:
        """Get information about current dynamic ADP settings"""
        if self.current_pick <= 36:  # Early rounds
            reach_threshold = RECOMMENDATION_CONFIG["adp_reach_threshold"] * 0.7
            reach_penalty_multiplier = 1.5
            phase = "Early"
        elif self.current_pick <= 84:  # Mid rounds
            reach_threshold = RECOMMENDATION_CONFIG["adp_reach_threshold"] * 1.0
            reach_penalty_multiplier = 1.0
            phase = "Mid"
        else:  # Late rounds
            reach_threshold = RECOMMENDATION_CONFIG["adp_reach_threshold"] * 1.3
            reach_penalty_multiplier = 0.7
            phase = "Late"
        
        return {
            'current_pick': self.current_pick,
            'draft_phase': phase,
            'reach_threshold': reach_threshold,
            'penalty_multiplier': reach_penalty_multiplier,
            'base_reach_threshold': RECOMMENDATION_CONFIG["adp_reach_threshold"],
            'base_penalty': RECOMMENDATION_CONFIG["adp_reach_penalty"]
        }

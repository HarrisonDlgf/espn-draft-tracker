import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
from config import RECOMMENDATION_CONFIG, POSITION_LIMITS, TOTAL_TEAMS, YOUR_DRAFT_SLOT, POSITION_WEIGHTS, STARTING_LINEUP

class RecommendationEngine:
    """Recommendation engine with two-layer position-first approach"""
    
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
    
    def get_position_urgency(self, position: str) -> float:
        """Calculate position urgency using within-position normalization"""
        if self.available_df is None or len(self.available_df) == 0:
            return 0
            
        pos_players = self.available_df[self.available_df['Position'] == position]
        if len(pos_players) == 0:
            return 0
            
        # Get current round and next picks
        current_round = (self.current_pick - 1) // TOTAL_TEAMS + 1
        next_picks = self._calculate_next_picks(current_round)
        
        # top now and who is expected to be available next
        top_now = pos_players.loc[pos_players['VOR'].idxmax()]
        
        # expected best available at next pick
        expected_next = self._get_expected_player_at_pick(position, next_picks[0])
        
        # within-position normalization (percentile ranks)
        all_pos_vor = pos_players['VOR'].sort_values(ascending=False)
        vor_pct_now = (all_pos_vor == top_now['VOR']).idxmax() / len(all_pos_vor)
        vor_pct_next = (all_pos_vor == expected_next['VOR']).idxmax() / len(all_pos_vor) if expected_next is not None else 0.5
        
        # cliff pressure (dropoff)
        drop_now = top_now.get('dropoff', 0)
        drop_norm = min(1.0, drop_now / 25.0) if not pd.isna(drop_now) else 0
        
        # roster need (starters & flex)
        drafted_count = self.drafted_positions.get(position, 0)
        starter_need = max(0, STARTING_LINEUP.get(position, 0) - drafted_count) / max(1, STARTING_LINEUP.get(position, 1))
        
        # flex share for RB/WR/TE
        flex_need = 0
        if position in ['RB', 'WR', 'TE']:
            total_flex_candidates = sum(self.drafted_positions.get(pos, 0) for pos in ['RB', 'WR', 'TE'])
            if total_flex_candidates < STARTING_LINEUP.get('FLEX', 0):
                flex_need = 0.5
        
        # diminishing returns penalty
        diminishing_penalty = 0
        if drafted_count >= STARTING_LINEUP.get(position, 0) + (1 if flex_need > 0 else 0):
            diminishing_penalty = -0.2
        
        # step 5: Early-QB rule (1-QB leagues)
        early_qb_penalty = 0
        if position == 'QB' and current_round <= 6:
            early_qb_penalty = 12
        
        # position urgency calculation
        pos_urgency = (
            60 * (vor_pct_now - vor_pct_next) +  # opportunity cost if you wait
            25 * drop_norm +                      # cliff pressure
            15 * (starter_need + flex_need + diminishing_penalty) -  # roster need
            early_qb_penalty
        )
        
        return pos_urgency
    
    def _get_expected_player_at_pick(self, position: str, target_pick: int) -> Optional[pd.Series]:
        # estimate which player will be available at a specific pick
        pos_players = self.available_df[self.available_df['Position'] == position]
        if len(pos_players) == 0:
            return None
            
        # sort by ADP, then by VOR as fallback
        pos_players = pos_players.copy()
        pos_players['adp_num'] = pd.to_numeric(pos_players['ADP'], errors='coerce')
        
        # filter to players likely available at target pick
        available_at_pick = pos_players[
            (pos_players['adp_num'] >= target_pick) | 
            (pos_players['adp_num'].isna())
        ]
        
        if len(available_at_pick) > 0:
            # return the highest VOR player likely available
            return available_at_pick.loc[available_at_pick['VOR'].idxmax()]
        
        # fallback: return the k-th remaining player (where k is reasonable)
        k = max(1, (target_pick - self.current_pick) // TOTAL_TEAMS)
        if k < len(pos_players):
            return pos_players.nlargest(k, 'VOR').iloc[-1]
        
        return None
    
    def get_recommended_position(self) -> str:
        # get the position with highest urgency
        positions = ['RB', 'WR', 'TE', 'QB']
        position_urgencies = {}
        
        for pos in positions:
            # skip if at position limit
            if self.drafted_positions.get(pos, 0) >= POSITION_LIMITS.get(pos, 999):
                position_urgencies[pos] = -999
                continue
            if pos in ['QB', 'K', 'DST'] and self.drafted_positions.get(pos, 0) >= 1:
                position_urgencies[pos] = -999
                continue
            urgency = self.get_position_urgency(pos)
            position_urgencies[pos] = urgency
        
        # return position with highest urgency
        return max(position_urgencies, key=position_urgencies.get)
    
    def calculate_player_score(self, player_row: pd.Series) -> float:
        """Calculate player score within a position using the new system"""
        current_round = (self.current_pick - 1) // TOTAL_TEAMS + 1
        
        # Base VOR score (70% weight)
        vor_score = player_row['VOR'] * 0.70
        
        # Tier bonus (15% weight)
        tier = player_row.get('Tier', 10)
        if not pd.isna(tier):
            tier = int(tier)
            tier_bonus = max(0, (6 - tier)) * 1.5  
        else:
            tier_bonus = 0
        
        # Cliff bonus (10% weight)
        dropoff = player_row.get('dropoff', 0)
        if not pd.isna(dropoff):
            if dropoff > 25:
                cliff_bonus = 10
            elif dropoff > 15:
                cliff_bonus = 5
            else:
                cliff_bonus = 0
        else:
            cliff_bonus = 0
        
        # ADP value (5% weight)
        adp_value = self._calculate_adp_value_simple(player_row)
        
        # Risk tilt based on round
        risk_tilt = self._calculate_risk_tilt(player_row, current_round)
        
        # Reach cost
        reach_cost = self._calculate_reach_cost(player_row)
        
        # Total score
        total_score = (
            vor_score +
            tier_bonus * 0.15 +
            cliff_bonus * 0.10 +
            adp_value * 0.05 +
            risk_tilt -
            reach_cost
        )
        
        return total_score
    
    def _calculate_adp_value_simple(self, player_row: pd.Series) -> float:
        """Simplified ADP value calculation"""
        adp = player_row.get('ADP', 'NA')
        if pd.isna(adp) or adp == 'NA':
            return 0
            
        try:
            adp = float(adp)
            if adp > self.current_pick + 12:  # going 1+ rounds later
                return 5
            elif adp > self.current_pick + 6:  # going 0.5+ rounds later
                return 3
        except (ValueError, TypeError):
            pass
        
        return 0
    
    def _calculate_risk_tilt(self, player_row: pd.Series, current_round: int) -> float:
        # calculate risk tilt based on draft round
        vor = player_row['VOR']
        floor = player_row.get('floor', vor)
        ceiling = player_row.get('ceiling', vor)
        uncertainty = player_row.get('uncertainty', 0)
        
        if pd.isna(floor) or pd.isna(ceiling):
            return 0
        
        if current_round <= 5:  # early rounds - prefer floor
            risk_tilt = (floor - vor) * 0.2 - uncertainty * 0.1
        elif current_round <= 8:  # middle rounds - blend
            risk_tilt = ((floor + ceiling) / 2 - vor) * 0.1 - uncertainty * 0.05
        else:  # late rounds - prefer ceiling
            risk_tilt = (ceiling - vor) * 0.2 - uncertainty * 0.05
        
        return risk_tilt
    
    def _calculate_reach_cost(self, player_row: pd.Series) -> float:
        # calculate reach penalty
        adp = player_row.get('ADP', 'NA')
        if pd.isna(adp) or adp == 'NA':
            return 0
            
        try:
            adp = float(adp)
            reach_amount = self.current_pick - adp
            
            if reach_amount > 12:  # reaching by more than 1 round
                return 15
            elif reach_amount > 6:  # reaching by more than 0.5 rounds
                return reach_amount * 1.25
        except (ValueError, TypeError):
            pass
        
        return 0
    
    def get_recommendations(self, top_n: int = 10) -> pd.DataFrame:
        # get recommendations using the new two-layer system
        if self.available_df is None or len(self.available_df) == 0:
            return pd.DataFrame()
        
        # step 1: choose the position to draft
        recommended_position = self.get_recommended_position()
        
        # step 2: get top players within that position
        pos_players = self.available_df[self.available_df['Position'] == recommended_position].copy()
        
        if len(pos_players) == 0:
            return pd.DataFrame()
        
        # calculate player scores
        pos_players['composite_score'] = pos_players.apply(self.calculate_player_score, axis=1)
        
        # sort and return top recommendations
        recommendations = pos_players.sort_values('composite_score', ascending=False).head(top_n)
        
        # add position urgency info
        urgency = self.get_position_urgency(recommended_position)
        recommendations.attrs['recommended_position'] = recommended_position
        recommendations.attrs['position_urgency'] = urgency
        
        return recommendations
    
    def get_position_analysis(self, position: str, top_n: int = 10) -> pd.DataFrame:
        # get position analysis using the new scoring system
        if self.available_df is None:
            return pd.DataFrame()
            
        pos_df = self.available_df[self.available_df['Position'] == position].copy()
        if len(pos_df) == 0:
            return pd.DataFrame()
        
        pos_df['composite_score'] = pos_df.apply(self.calculate_player_score, axis=1)
        
        return pos_df.sort_values('composite_score', ascending=False).head(top_n)
    
    def get_strategic_insights(self) -> Dict[str, any]:
        """Get strategic insights including position urgency"""
        if self.available_df is None:
            return {}
        
        insights = {
            'total_available': len(self.available_df),
            'position_counts': self.available_df['Position'].value_counts().to_dict(),
            'tier_breakdown': self.available_df['Tier'].value_counts().sort_index().to_dict(),
            'position_urgencies': {},
            'recommended_position': None,
            'cliffs_detected': {},
            'value_opportunities': []
        }
        
        # Calculate position urgencies
        for pos in ['RB', 'WR', 'TE', 'QB']:
            if self.drafted_positions.get(pos, 0) < POSITION_LIMITS.get(pos, 999):
                urgency = self.get_position_urgency(pos)
                insights['position_urgencies'][pos] = urgency
        
        # Get recommended position
        if insights['position_urgencies']:
            insights['recommended_position'] = max(insights['position_urgencies'], key=insights['position_urgencies'].get)
        
        # Cliff detection
        for pos in ['RB', 'WR', 'TE']:
            pos_players = self.available_df[self.available_df['Position'] == pos].sort_values('VOR', ascending=False)
            if len(pos_players) > 1:
                top_vor = pos_players.iloc[0]['VOR']
                second_vor = pos_players.iloc[1]['VOR']
                dropoff = top_vor - second_vor
                
                if dropoff > 20:
                    insights['cliffs_detected'][pos] = f"Cliff: {dropoff:.1f} VOR drop"
        
        return insights
    
    def get_detailed_score_breakdown(self, player_row: pd.Series) -> Dict[str, float]:
        """Get detailed breakdown of player scoring components"""
        current_round = (self.current_pick - 1) // TOTAL_TEAMS + 1
        
        breakdown = {
            'vor_score': player_row['VOR'] * 0.70,
            'tier_bonus': max(0, (6 - int(player_row.get('Tier', 10)))) * 1.5 * 0.15,
            'cliff_bonus': (10 if player_row.get('dropoff', 0) > 25 else 5 if player_row.get('dropoff', 0) > 15 else 0) * 0.10,
            'adp_value': self._calculate_adp_value_simple(player_row) * 0.05,
            'risk_tilt': self._calculate_risk_tilt(player_row, current_round),
            'reach_cost': -self._calculate_reach_cost(player_row)
        }
        
        breakdown['total_score'] = sum(breakdown.values())
        return breakdown
    
    def get_position_urgency_breakdown(self, position: str) -> Dict[str, float]:
        """Get detailed breakdown of position urgency calculation"""
        if self.available_df is None or len(self.available_df) == 0:
            return {}
        
        pos_players = self.available_df[self.available_df['Position'] == position]
        if len(pos_players) == 0:
            return {}
        
        current_round = (self.current_pick - 1) // TOTAL_TEAMS + 1
        next_picks = self._calculate_next_picks(current_round)
        
        top_now = pos_players.loc[pos_players['VOR'].idxmax()]
        expected_next = self._get_expected_player_at_pick(position, next_picks[0])
        
        # Calculate components
        all_pos_vor = pos_players['VOR'].sort_values(ascending=False)
        vor_pct_now = (all_pos_vor == top_now['VOR']).idxmax() / len(all_pos_vor)
        vor_pct_next = (all_pos_vor == expected_next['VOR']).idxmax() / len(all_pos_vor) if expected_next is not None else 0.5
        
        drop_now = top_now.get('dropoff', 0)
        drop_norm = min(1.0, drop_now / 25.0) if not pd.isna(drop_now) else 0
        
        drafted_count = self.drafted_positions.get(position, 0)
        starter_need = max(0, STARTING_LINEUP.get(position, 0) - drafted_count) / max(1, STARTING_LINEUP.get(position, 1))
        
        flex_need = 0
        if position in ['RB', 'WR', 'TE']:
            total_flex_candidates = sum(self.drafted_positions.get(pos, 0) for pos in ['RB', 'WR', 'TE'])
            if total_flex_candidates < STARTING_LINEUP.get('FLEX', 0):
                flex_need = 0.5
        
        diminishing_penalty = 0
        if drafted_count >= STARTING_LINEUP.get(position, 0) + (1 if flex_need > 0 else 0):
            diminishing_penalty = -0.2
        
        early_qb_penalty = 12 if (position == 'QB' and current_round <= 6) else 0
        
        return {
            'opportunity_cost': 60 * (vor_pct_now - vor_pct_next),
            'cliff_pressure': 25 * drop_norm,
            'roster_need': 15 * (starter_need + flex_need + diminishing_penalty),
            'early_qb_penalty': -early_qb_penalty,
            'total_urgency': 60 * (vor_pct_now - vor_pct_next) + 25 * drop_norm + 15 * (starter_need + flex_need + diminishing_penalty) - early_qb_penalty
        }

    # Legacy methods for backward compatibility
    def calculate_vor_score(self, player_row: pd.Series) -> float:
        """Legacy method - now uses new scoring"""
        return self.calculate_player_score(player_row)
    
    def calculate_tier_multiplier(self, player_row: pd.Series) -> float:
        """Legacy method"""
        tier = player_row.get('Tier', 10)
        if not pd.isna(tier):
            tier = int(tier)
            return max(0, (6 - tier)) * 1.5 * 0.15
        return 0
    
    def calculate_dropoff_bonus(self, player_row: pd.Series, position: str) -> float:
        """Legacy method"""
        dropoff = player_row.get('dropoff', 0)
        if not pd.isna(dropoff):
            if dropoff > 25:
                return 10 * 0.10
            elif dropoff > 15:
                return 5 * 0.10
        return 0
    
    def calculate_adp_value(self, player_row: pd.Series) -> float:
        """Legacy method"""
        return self._calculate_adp_value_simple(player_row) * 0.05
    
    def calculate_uncertainty_penalty(self, player_row: pd.Series) -> float:
        """Legacy method"""
        uncertainty = player_row.get('uncertainty', 0)
        if pd.isna(uncertainty):
            return 0
        return uncertainty * 0.05
    
    def calculate_positional_adjustment(self, player_row: pd.Series) -> float:
        """Legacy method"""
        return 0  # Now handled by position urgency
    
    def calculate_round_adjustment(self, player_row: pd.Series) -> float:
        """Legacy method"""
        current_round = (self.current_pick - 1) // TOTAL_TEAMS + 1
        return self._calculate_risk_tilt(player_row, current_round)
    
    def calculate_scoring_format_bonus(self, player_row: pd.Series) -> float:
        """Legacy method"""
        return 0  # Now handled by position urgency
    
    def calculate_opportunity_cost(self, player_row: pd.Series) -> float:
        """Legacy method"""
        return 0  # Now handled by position urgency
    
    def calculate_composite_score(self, player_row: pd.Series) -> float:
        """Legacy method - now uses new scoring"""
        return self.calculate_player_score(player_row)
    
    def get_dynamic_adp_info(self) -> Dict[str, any]:
        """Legacy method"""
        return {
            'current_pick': self.current_pick,
            'draft_phase': 'Early' if self.current_pick <= 36 else 'Mid' if self.current_pick <= 84 else 'Late',
            'reach_threshold': 6,
            'penalty_multiplier': 1.0,
            'base_reach_threshold': 6,
            'base_penalty': 10
        }

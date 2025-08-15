LEAGUE_ID = 1296971572
YEAR = 2025
ESPN_S2 = "AECwvTudMsJwR8SOZpn6u8E1AsVsJsV4I2FsuNOExZzCpkvzzT7iEu9pJCYsYhvNuHA%2FpsSYkkixmTmvASX4ObW98D1gDwpyCZUbCMc5Q%2BKMl6DEnck7icrnyy8i3ShTClRsGaR%2B5jBZOvd4wT2ZWsvnuFML4Q8hLzHC63gTCmc%2F%2F8NfixnTC%2BRSGJM%2BgzKbeEq%2BmHt744NgbKIr2k5UqTxeE4SBOPc1%2B8L3GAtoO9VwqX7nQUhllqCGXat0769mhpYwxzVLqX%2FZZj5vWCCOjfT8%2FPkfeGZRRuS3Y1s9TpF6Sw%3D%3D"
SWID = "{787CAD8C-55A9-45CE-BCAD-8C55A9B5CECF}"
YOUR_DRAFT_SLOT = 5  # 0-based index; 5 = pick 6
TOTAL_TEAMS = 12

POSITION_LIMITS = {
    "QB": 3,      
    "RB": 6,      
    "WR": 6,      
    "TE": 3,      
    "K": 2,       
    "DST": 2      
}

STARTING_LINEUP = {
    "QB": 1,
    "RB": 2, 
    "WR": 2,
    "TE": 1,
    "FLEX": 1,    
    "K": 1,
    "DST": 1
}

TOTAL_ROSTER_SIZE = 16  

SCORING_CONFIG = {
    # Offensive scoring
    "passing_yards_per_point": 25,
    "passing_td": 4,
    "passing_40yd_td_bonus": 2,
    "rushing_yards_per_point": 10,
    "rushing_td": 6,
    "receiving_yards_per_point": 10,
    "receiving_td": 6,
    "rec_40yd_td_bonus": 2,
    "two_point_conversion": 2,
    "interception_thrown": -2,
    "fumble_lost": -2,
    "receptions": 0,

    # D/ST scoring
    "defense_sack": 1,
    "defense_interception": 2,
    "defense_fumble_recovered": 2,
    "defense_safety": 2,
    "defense_td": 6,
    "points_allowed_0": 5,
    "points_allowed_1_to_6": 4,
    "points_allowed_7_to_13": 3,
    "points_allowed_14_to_17": 1,
    "points_allowed_18_to_27": 0,
    "points_allowed_28_to_34": -1,
    "points_allowed_35_plus": -3,
}

RECOMMENDATION_CONFIG = {
    "vor_weight": 0.75,              
    "ceiling_vor_weight": 0.10,      
    "floor_vor_weight": 0.10,        
    
    "tier_multipliers": {
        1: 1.15,   
        2: 1.08,   
        3: 1.0,    
        4: 0.95,   
        5: 0.9,    
    },
    
    "dropoff_threshold": 20,         
    "dropoff_bonus": 20,             
    
    "adp_value_threshold": 12,       
    "adp_reach_threshold": 12,       
    "adp_value_bonus": 15,           
    "adp_reach_penalty": 10,         
    
        "opportunity_cost": {
        "enabled": True,             
        "look_ahead_rounds": 0.5,    
        "vor_difference_threshold": 20, 
        "positional_penalty_multiplier": 1.5, 
        "qb_opportunity_penalty": 30, 
        "te_opportunity_penalty": 20, 
    },
    
    "uncertainty_penalties": {
        "low": 0,           
        "medium": 8,        
        "high": 15,         
        "extreme": 25       
    },
    
    
    "positional_balance": {
        "rb_count_penalty": 10,      
        "wr_count_penalty": 8,       
        "qb_early_penalty": 25,      
        "qb_elite_threshold": 120,   
    },
    
    "round_adjustments": {
        "early_rounds": 1,           
        "mid_rounds": 2,             
        "late_rounds": 3,            
    },
    
    "league_type": "non_ppr",        # non_ppr or half_ppr
    "ppr_value": 0.0,                
}

POSITION_WEIGHTS = {
    "non_ppr": {
        "QB": {"base": 1.0, "scarcity": 1.0, "tier_bonus": 1.0},
        "RB": {"base": 1.0, "scarcity": 1.2, "tier_bonus": 1.1},
        "WR": {"base": 1.0, "scarcity": 1.2, "tier_bonus": 1.1},
        "TE": {"base": 0.9, "scarcity": 1.0, "tier_bonus": 0.9},
        "K": {"base": 0.3, "scarcity": 0.5, "tier_bonus": 0.3},
        "DST": {"base": 0.3, "scarcity": 0.5, "tier_bonus": 0.3}
    },
    "half_ppr": {
        "QB": {"base": 1.0, "scarcity": 1.0, "tier_bonus": 1.0},
        "RB": {"base": 1.0, "scarcity": 1.2, "tier_bonus": 1.1},
        "WR": {"base": 1.05, "scarcity": 1.2, "tier_bonus": 1.1},
        "TE": {"base": 0.95, "scarcity": 1.0, "tier_bonus": 0.95},
        "K": {"base": 0.3, "scarcity": 0.5, "tier_bonus": 0.3},
        "DST": {"base": 0.3, "scarcity": 0.5, "tier_bonus": 0.3}
    }
}

def set_league_type(league_type: str):
    global RECOMMENDATION_CONFIG
    
    if league_type == "half_ppr":
        RECOMMENDATION_CONFIG.update({
            "league_type": "half_ppr",
            "ppr_value": 0.5,
            "position_priorities": {
                "RB": "high",        
                "WR": "critical",    
                "TE": "high",        
                "QB": "medium",
                "K": "low",
                "DST": "low"
            }
        })
        print("✅ Updated to Half-PPR scoring (0.5 points per reception)")
        print("📁 Using projections_half_ppr.csv for data")
        
    elif league_type == "non_ppr":
        RECOMMENDATION_CONFIG.update({
            "league_type": "non_ppr",
            "ppr_value": 0.0,
            "position_priorities": {
                "RB": "high",        
                "WR": "critical",    
                "TE": "high",
                "QB": "medium",
                "K": "low",
                "DST": "low"
            }
        })
        print("✅ Updated to Non-PPR scoring")
        print("📁 Using projections_non_ppr.csv for data")
        
    else:
        raise ValueError(f"Unknown league type: {league_type}. Supported types: non_ppr, half_ppr")

def get_config_summary() -> str:
    config = RECOMMENDATION_CONFIG
    summary = f"League Type: {config['league_type'].upper()}\n"
    summary += f"VOR Multiplier: {config['vor_multiplier']}\n"
    summary += f"Tier Bonus Multiplier: {config['tier_bonus_multiplier']}\n"
    
    if config["ppr_value"] > 0:
        summary += f"PPR: {config['ppr_value']}\n"
        
    summary += "\nPosition Priorities:\n"
    for pos, priority in config["position_priorities"].items():
        bonus = config["priority_bonuses"][priority]
        summary += f"  {pos}: {priority} (+{bonus} points)\n"
        
    return summary

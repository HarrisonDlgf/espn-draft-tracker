import pandas as pd
import os
from config import RECOMMENDATION_CONFIG

def get_ppr_setting():
    return RECOMMENDATION_CONFIG.get("ppr_value", 0)

def select_csv_file():
    league_type = RECOMMENDATION_CONFIG.get("league_type", "non_ppr")
    
    if league_type == "half_ppr":
        return "projections_half_ppr.csv"
    elif league_type == "non_ppr":
        return "projections_non_ppr.csv"
    else:
        print(f"Warning: League type {league_type} not recognized. Using default projections_non_ppr.csv")
        return "projections_non_ppr.csv"

def clean_dataset(df):
    positions_to_keep = ['QB', 'RB', 'WR', 'TE', 'K', 'DST']
    df_cleaned = df[df['position'].isin(positions_to_keep)].copy()
    df_cleaned = df_cleaned.reset_index(drop=True)
    return df_cleaned

def load_and_clean_data():
    csv_file = select_csv_file()
    league_type = RECOMMENDATION_CONFIG.get("league_type", "non_ppr")
    
    if not os.path.exists(csv_file):
        print(f"Error: {csv_file} not found!")
        return None
    
    print(f"📊 Loading data from {csv_file} for {league_type.upper()} league")
    df = pd.read_csv(csv_file)
    df_cleaned = clean_dataset(df)
    
    df_cleaned = df_cleaned.rename(columns={
        "player": "Player",
        "position": "Position", 
        "points_vor": "VOR",
        "tier": "Tier",
        "adp": "ADP",
        "uncertainty": "uncertainty",
        "dropoff": "dropoff",
        "sd_pts": "sd_pts",
        "points": "points",
        "floor": "floor",
        "ceiling": "ceiling"
    })
    
    return df_cleaned

if __name__ == "__main__":
    df = load_and_clean_data()
    if df is not None:
        print(f"\nSuccessfully loaded {len(df)} players")
        print(f"Sample data:")
        print(df[['Player', 'Position', 'VOR', 'Tier', 'ADP']].head())

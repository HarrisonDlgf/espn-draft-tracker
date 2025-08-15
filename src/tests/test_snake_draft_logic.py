import pandas as pd
from config import *
from data_loader import load_and_clean_data

def old_adp_filtering(df, current_pick_number):
    def is_reasonable_pick(row):
        adp = row['ADP']
        vor = row['VOR']
        tier = row['Tier']
        
        if pd.isna(adp) or adp == 'NA':
            return True
        
        adp = float(adp)
        max_reasonable_adp = current_pick_number + (TOTAL_TEAMS * 2)
        
        if vor > 50:
            max_reasonable_adp = current_pick_number + (TOTAL_TEAMS * 3)
        elif tier == "1":
            max_reasonable_adp = current_pick_number + (TOTAL_TEAMS * 4)
        
        return adp <= max_reasonable_adp
    
    return df[df.apply(is_reasonable_pick, axis=1)]

def new_snake_draft_filtering(df, current_pick_number):
    def is_reasonable_pick(row):
        adp = row['ADP']
        vor = row['VOR']
        tier = row['Tier']
        
        if pd.isna(adp) or adp == 'NA':
            return True
        
        adp = float(adp)
        
        current_round = (current_pick_number - 1) // TOTAL_TEAMS + 1
        next_picks = []
        
        for i in range(3):
            round_num = current_round + i
            if round_num % 2 == 1:  
                pick_num = (round_num - 1) * TOTAL_TEAMS + YOUR_DRAFT_SLOT + 1
            else:  
                pick_num = round_num * TOTAL_TEAMS - YOUR_DRAFT_SLOT
            next_picks.append(pick_num)
        
        max_reasonable_adp = max(next_picks) + (TOTAL_TEAMS * 1)
        
        if vor > 50:
            max_reasonable_adp = max(next_picks) + (TOTAL_TEAMS * 2)
        elif tier == "1":
            max_reasonable_adp = max(next_picks) + (TOTAL_TEAMS * 3)
        
        return adp <= max_reasonable_adp
    
    return df[df.apply(is_reasonable_pick, axis=1)]

def test_comparison():
    
    df = load_and_clean_data()
    if df is None:
        print("Failed to load data. Exiting.")
        return
    
    mock_drafted = {
        "Bijan Robinson", "Saquon Barkley", "Jahmyr Gibbs", "Ja'Marr Chase",
        "Derrick Henry", "Devon Achane", "Christian McCaffrey", "Josh Jacobs",
        "Ashton Jeanty", "Jonathan Taylor", "Bucky Irving", "Kyren Williams"
    }
    
    df["Drafted"] = df["Player"].isin(mock_drafted)
    available = df[~df["Drafted"]]
    
    print(f"Your draft slot: {YOUR_DRAFT_SLOT + 1}")
    print(f"Total teams: {TOTAL_TEAMS}")
    print()
    
    test_picks = [13, 21, 28, 45, 52, 69]
    
    for pick_num in test_picks:
        print(f"{'='*60}")
        print(f"TESTING PICK #{pick_num}")
        print(f"{'='*60}")
        
        current_round = (pick_num - 1) // TOTAL_TEAMS + 1
        next_picks = []
        for i in range(3):
            round_num = current_round + i
            if round_num % 2 == 1:
                next_pick = (round_num - 1) * TOTAL_TEAMS + YOUR_DRAFT_SLOT + 1
            else:
                next_pick = round_num * TOTAL_TEAMS - YOUR_DRAFT_SLOT
            next_picks.append(next_pick)
        
        print(f"Current round: {current_round}")
        print(f"Your next 3 picks: {next_picks}")
        print()
        
        old_filtered = old_adp_filtering(available.copy(), pick_num)
        old_top = old_filtered.sort_values(by=["Tier", "VOR"], ascending=[True, False]).head(5)
        
        new_filtered = new_snake_draft_filtering(available.copy(), pick_num)
        new_top = new_filtered.sort_values(by=["Tier", "VOR"], ascending=[True, False]).head(5)
        
        print("OLD LOGIC (Linear):")
        print(f"Available players: {len(old_filtered)}")
        for i, row in old_top.iterrows():
            adp_display = f"ADP: {row['ADP']}" if not pd.isna(row['ADP']) and row['ADP'] != 'NA' else "ADP: N/A"
            print(f"  {row['Player']} ({row['Position']}) | VOR: {row['VOR']:.1f} | {adp_display}")
        
        print()
        print("NEW LOGIC (Snake Draft):")
        print(f"Available players: {len(new_filtered)}")
        for i, row in new_top.iterrows():
            adp_display = f"ADP: {row['ADP']}" if not pd.isna(row['ADP']) and row['ADP'] != 'NA' else "ADP: N/A"
            print(f"  {row['Player']} ({row['Position']}) | VOR: {row['VOR']:.1f} | {adp_display}")
        
        print()

if __name__ == "__main__":
    test_comparison()

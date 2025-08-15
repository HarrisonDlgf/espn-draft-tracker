#!/usr/bin/env python3

import pandas as pd
import os

def clean_projections_csv():
    
    # Read the original CSV
    print("Reading projections.csv...")
    df = pd.read_csv("projections.csv")
    
    # Show original stats
    print(f"Original CSV has {len(df)} rows")
    print(f"Position breakdown:")
    print(df['position'].value_counts())
    
    # Define positions to keep (offensive + DST)
    positions_to_keep = ['QB', 'RB', 'WR', 'TE', 'K', 'DST']
    
    # Filter the dataframe
    df_cleaned = df[df['position'].isin(positions_to_keep)].copy()
    
    # Reset the index to make it sequential
    df_cleaned = df_cleaned.reset_index(drop=True)
    
    # Show cleaned stats
    print(f"\nCleaned CSV has {len(df_cleaned)} rows")
    print(f"Position breakdown after cleaning:")
    print(df_cleaned['position'].value_counts())
    
    # Create backup of original file
    backup_filename = "projections_backup.csv"
    if not os.path.exists(backup_filename):
        print(f"\nCreating backup: {backup_filename}")
        df.to_csv(backup_filename, index=False)
    else:
        print(f"\nBackup already exists: {backup_filename}")
    
    # Save the cleaned CSV
    output_filename = "projections_cleaned.csv"
    df_cleaned.to_csv(output_filename, index=False)
    print(f"Saved cleaned CSV: {output_filename}")
    
    # Show some examples of what was kept
    print(f"\nSample of cleaned data:")
    print(df_cleaned[['player', 'position', 'team', 'points']].head(10))
    
    # Show what was removed
    removed_positions = df[~df['position'].isin(positions_to_keep)]['position'].unique()
    print(f"\nRemoved positions: {list(removed_positions)}")
    
    return df_cleaned

def replace_original_csv():
    
    # Check if cleaned file exists
    if not os.path.exists("projections_cleaned.csv"):
        print("Cleaned CSV not found. Run clean_projections_csv() first.")
        return False
    
    # Create backup if it doesn't exist
    if not os.path.exists("projections_backup.csv"):
        print("Creating backup of original file...")
        df_original = pd.read_csv("projections.csv")
        df_original.to_csv("projections_backup.csv", index=False)
    
    # Replace original with cleaned
    print("Replacing original projections.csv with cleaned version...")
    df_cleaned = pd.read_csv("projections_cleaned.csv")
    df_cleaned.to_csv("projections.csv", index=False)
    
    print("Original projections.csv has been replaced with cleaned version.")
    print("Original is backed up as projections_backup.csv")
    
    return True

if __name__ == "__main__":
    print("=== CSV Cleaner for ESPN Draft Tracker ===")
    print("This script will remove individual defensive players (DB, DL, LB)")
    print("and keep only offensive players and DST.\n")
    
    # Clean the CSV
    cleaned_df = clean_projections_csv()
    
    # Ask if user wants to replace original
    print("\n" + "="*50)
    response = input("Do you want to replace the original projections.csv with the cleaned version? (y/n): ")
    
    if response.lower() in ['y', 'yes']:
        replace_original_csv()
        print("\nDone! Your projections.csv is now cleaned.")
        print("Original file is backed up as projections_backup.csv")
    else:
        print("\nOriginal file unchanged. Cleaned version saved as projections_cleaned.csv")
        print("You can manually replace the original file if desired.")

import pandas as pd
import time
import warnings
import os
import sys
import requests
import json
import threading

original_stderr = sys.stderr
sys.stderr = open(os.devnull, 'w')

# Suppress warnings
os.environ['PYTHONWARNINGS'] = 'ignore'
warnings.filterwarnings('ignore')

import PySimpleGUI as sg

# Restore stderr
sys.stderr = original_stderr

from espn_api.football import League
from config import *
from data_loader import load_and_clean_data
from draft_analyzer import print_draft_insights, is_my_pick
from recommendation_engine import RecommendationEngine

# Load data
df = load_and_clean_data()
if df is None:
    print("Failed to load data. Exiting.")
    exit(1)

df["Drafted"] = False

# Initialize recommendation engine
recommendation_engine = RecommendationEngine(df)

# Set to False for live ESPN draft, True for testing
TEST_MODE = False

if TEST_MODE:
    mock_drafted_players = set()
    mock_draft_slot = YOUR_DRAFT_SLOT
    mock_total_teams = TOTAL_TEAMS

    def get_drafted_players():
        return mock_drafted_players

    def add_mock_pick(player_name):
        mock_drafted_players.add(player_name)
        return f"Mock pick added: {player_name}"

    print("Running in TEST MODE - using mock draft data")
else:
    league = League(
        league_id=LEAGUE_ID,
        year=YEAR,
        espn_s2=ESPN_S2,
        swid=SWID
    )

    def get_drafted_players():
        try:
            drafted_players = set()
            
            # Method 1: Direct draft picks (espn-api)
            try:
                picks = league.draft
                if picks and len(picks) > 0:
                    for pick in picks:
                        if hasattr(pick, 'playerName'):
                            drafted_players.add(pick.playerName)
                        elif hasattr(pick, 'name'):
                            drafted_players.add(pick.name)
            except Exception as e:
                pass
            
            # Method 2: Check all team rosters (most reliable during live draft)
            try:
                for team in league.teams:
                    for player in team.roster:
                        if hasattr(player, 'name'):
                            drafted_players.add(player.name)
                        elif hasattr(player, 'playerName'):
                            drafted_players.add(player.playerName)
                        elif hasattr(player, 'full_name'):
                            drafted_players.add(player.full_name)
            except Exception as e:
                pass
            
            # Method 3: Draft recap endpoint (most reliable for mock drafts)
            try:
                recap_picks = fetch_draft_recap(LEAGUE_ID, YEAR)
                drafted_players.update(recap_picks)
            except Exception as e:
                pass
            
            return drafted_players
            
        except Exception as e:
            return set()

    def fetch_draft_recap(league_id, year):
        """Fetch draft picks using ESPN's draft recap endpoint"""
        try:
            url = (
                f"https://fantasy.espn.com/apis/v3/games/ffl/seasons/{year}/segments/0/"
                f"leagues/{league_id}?view=mDraftDetail&view=mTeam"
            )
            
            headers = {
                'Cookie': f'espn_s2={ESPN_S2}; SWID={SWID}',
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
            }
            
            response = requests.get(url, headers=headers)
            if response.status_code != 200:
                return set()
                
            data = response.json()
            picks = data.get('draftDetail', {}).get('picks', [])
            return {p['player']['fullName'] for p in picks if 'player' in p}
            
        except Exception as e:
            return set()


# Old get_best_available function removed - now using RecommendationEngine class


def create_main_window():
    """Create the main GUI window with modern design"""
    sg.theme('DarkBlue3')  # Modern dark theme
    
    # Custom colors and styling - Softer, easier on the eyes
    title_color = '#66BB6A'  # Softer Green
    section_color = '#42A5F5'  # Softer Blue
    accent_color = '#FFB74D'  # Softer Orange
    
    # Main layout with modern design
    layout = [
        # Header
        [sg.Text('🏈 ESPN Draft Assistant', font=('Helvetica', 24, 'bold'), text_color=title_color, justification='center', expand_x=True)],
        [sg.Text(f'Draft Slot: {YOUR_DRAFT_SLOT + 1} | Teams: {TOTAL_TEAMS}', font=('Helvetica', 12), text_color='white', justification='center', expand_x=True)],
        [sg.HorizontalSeparator(color='gray')],
        
        # Draft Status Panel
        [sg.Frame('📊 Draft Status', [
            [sg.Column([
                [sg.Text('Current Pick:', font=('Helvetica', 10, 'bold'), text_color=section_color), 
                 sg.Text('#1', key='-CURRENT_PICK-', font=('Helvetica', 12, 'bold'), text_color='white')],
                [sg.Text('Round:', font=('Helvetica', 10, 'bold'), text_color=section_color), 
                 sg.Text('1', key='-CURRENT_ROUND-', font=('Helvetica', 12, 'bold'), text_color='white')],
                [sg.Text('Drafted:', font=('Helvetica', 10, 'bold'), text_color=section_color), 
                 sg.Text('0', key='-DRAFTED_COUNT-', font=('Helvetica', 12, 'bold'), text_color='white')],
                [sg.Text('Your Turn:', font=('Helvetica', 10, 'bold'), text_color=section_color), 
                 sg.Text('NO', key='-YOUR_TURN-', font=('Helvetica', 12, 'bold'), text_color='red')]
            ], expand_x=True)]
        ], font=('Helvetica', 12, 'bold'), expand_x=True)],
        
        # Manual Picks Panel
        [sg.Frame('✏️ Manual Picks', [
            [sg.Text('0 picks added', key='-MANUAL_PICKS-', font=('Helvetica', 10), text_color='white')],
            [sg.Button('➕ Add Pick', key='-ADD_PICK-', size=(12, 1), button_color=('white', accent_color)),
             sg.Button('👁️ Show Picks', key='-SHOW_PICKS-', size=(12, 1), button_color=('white', section_color)),
             sg.Button('🗑️ Clear All', key='-CLEAR_PICKS-', size=(12, 1), button_color=('white', 'red'))]
        ], font=('Helvetica', 12, 'bold'), expand_x=True)],
        
        # Legend Panel
        [sg.Frame('📋 Legend', [
            [sg.Column([
                [sg.Text('🟢 Tier 1 (Elite)', font=('Helvetica', 10), text_color='#66BB6A'), 
                 sg.Text('🟡 Tier 2 (Very Good)', font=('Helvetica', 10), text_color='#FFC107')],
                [sg.Text('🟠 Tier 3 (Good)', font=('Helvetica', 10), text_color='#FFB74D'), 
                 sg.Text('🔴 Tier 4+ (Average/Below)', font=('Helvetica', 10), text_color='#EF5350')],
                [sg.Text('📉 Cliff (Position Scarcity)', font=('Helvetica', 10), text_color='#EC407A'),
                 sg.Text('⏰ Early QB (Round 1-6)', font=('Helvetica', 10), text_color='#AB47BC')]
            ], expand_x=True)]
        ], font=('Helvetica', 10, 'bold'), expand_x=True)],
        
        # Recommendations Panel (SMALLER)
        [sg.Frame('🎯 Recommendations', [
            [sg.Multiline(size=(100, 8), key='-RECOMMENDATIONS-', disabled=True, 
                         background_color='#1e1e1e', text_color='#E0E0E0', font=('Consolas', 10))]
        ], font=('Helvetica', 12, 'bold'), expand_x=True)],
        
        # Position Analysis Panel (LARGER)
        [sg.Frame('📈 Position Analysis', [
            [sg.Button('QB', key='-QB_ANALYSIS-', size=(8, 1), button_color=('white', '#66BB6A')),
             sg.Button('RB', key='-RB_ANALYSIS-', size=(8, 1), button_color=('white', '#42A5F5')),
             sg.Button('WR', key='-WR_ANALYSIS-', size=(8, 1), button_color=('white', '#FFB74D')),
             sg.Button('TE', key='-TE_ANALYSIS-', size=(8, 1), button_color=('white', '#AB47BC'))],
            [sg.Multiline(size=(100, 15), key='-POSITION_ANALYSIS-', disabled=True,
                         background_color='#1e1e1e', text_color='#E0E0E0', font=('Consolas', 10))]
        ], font=('Helvetica', 12, 'bold'), expand_x=True)],
        
        # Control Panel
        [sg.Frame('⚙️ Controls', [
            [sg.Button('🔄 Refresh', key='-REFRESH-', size=(12, 1), button_color=('white', section_color)),
             sg.Button('🔍 Debug', key='-DEBUG-', size=(12, 1), button_color=('white', 'gray')),
             sg.Button('❌ Exit', key='-EXIT-', size=(12, 1), button_color=('white', 'red'))]
        ], font=('Helvetica', 12, 'bold'), expand_x=True)]
    ]
    
    return sg.Window('ESPN Draft Assistant', layout, finalize=True, resizable=True, 
                    size=(1200, 1100), location=(100, 100), icon='🏈')


def create_manual_pick_window(df, drafted, current_pick):
    """Create window for adding manual picks with modern design"""
    sg.theme('DarkBlue3')
    
    # Get available players sorted by ADP
    available_df = df[~df['Player'].isin(drafted)]
    
    return create_manual_pick_layout(available_df, current_pick)

def create_manual_pick_layout(available_df, current_pick):
    """Create the layout for manual pick window"""
    
    # Create tabs for each position with modern styling
    tab_layout = []
    positions = ['QB', 'RB', 'WR', 'TE', 'K', 'DST']
    colors = ['#66BB6A', '#42A5F5', '#FFB74D', '#AB47BC', '#8D6E63', '#78909C']
    
    for i, pos in enumerate(positions):
        pos_df = available_df[available_df['Position'] == pos].sort_values('ADP', ascending=True)
        
        # Create list of players for this position
        player_list = []
        for j, (_, player) in enumerate(pos_df.head(50).iterrows(), 1):
            adp_str = f"ADP: {player['ADP']}" if not pd.isna(player['ADP']) and player['ADP'] != 'NA' else "ADP: N/A"
            player_list.append(f"{j:2d}. {player['Player']} | {adp_str} | VOR: {player['VOR']:.1f}")
        
        # Create tab for this position
        tab_layout.append([
            sg.Tab(pos, [
                [sg.Text(f'🏈 Top {pos} Players (Pick #{current_pick})', font=('Helvetica', 14, 'bold'), text_color=colors[i])],
                [sg.Text(f'Available: {len(pos_df)} players', font=('Helvetica', 10), text_color='white')],
                [sg.Listbox(player_list, size=(75, 15), select_mode=sg.LISTBOX_SELECT_MODE_MULTIPLE, 
                           key=f'-{pos}_LIST-', background_color='#1e1e1e', text_color='#E0E0E0', font=('Consolas', 10))],
                [sg.Button(f'➕ Add Selected {pos}', key=f'-ADD_{pos}-', size=(20, 1), button_color=('white', colors[i]))]
            ])
        ])
    
    # Add "All Positions" tab
    all_df = available_df.sort_values('ADP', ascending=True)
    all_player_list = []
    for i, (_, player) in enumerate(all_df.head(60).iterrows(), 1):
        adp_str = f"ADP: {player['ADP']}" if not pd.isna(player['ADP']) and player['ADP'] != 'NA' else "ADP: N/A"
        all_player_list.append(f"{i:2d}. {player['Player']} ({player['Position']}) | {adp_str} | VOR: {player['VOR']:.1f}")
    
    tab_layout.append([
        sg.Tab('🎯 All', [
            [sg.Text('🎯 All Positions - Top 60 by ADP', font=('Helvetica', 14, 'bold'), text_color='#FF7043')],
            [sg.Text(f'Available: {len(all_df)} players', font=('Helvetica', 10), text_color='white')],
            [sg.Listbox(all_player_list, size=(75, 15), select_mode=sg.LISTBOX_SELECT_MODE_MULTIPLE, 
                       key='-ALL_LIST-', background_color='#1e1e1e', text_color='#E0E0E0', font=('Consolas', 10))],
            [sg.Button('➕ Add Selected Players', key='-ADD_ALL-', size=(20, 1), button_color=('white', '#FF7043'))]
        ])
    ])
    
    layout = [
        [sg.Text('✏️ Add Manual Picks', font=('Helvetica', 18, 'bold'), text_color='#4CAF50')],
        [sg.TabGroup(tab_layout, key='-TAB_GROUP-', tab_location='topleft', title_color='#CCCCCC', 
                    selected_title_color='white', selected_background_color='#2196F3', background_color='#555555')],
        [sg.HorizontalSeparator(color='gray')],
        [sg.Button('✅ Close', key='-CLOSE-', size=(15, 1), button_color=('white', '#4CAF50'))]
    ]
    
    return sg.Window('Add Manual Picks', layout, finalize=True, modal=True, 
                    size=(850, 700), location=(200, 200))


def update_main_window(window, df, drafted, current_pick, manual_picks):
    """Update the main window with current data"""
    # Update draft status
    is_my_turn = is_my_pick(current_pick)
    current_round = (current_pick - 1) // TOTAL_TEAMS + 1
    
    window['-CURRENT_PICK-'].update(f'Current Pick: #{current_pick}')
    window['-CURRENT_ROUND-'].update(f'Round: {current_round}')
    window['-DRAFTED_COUNT-'].update(f'Players Drafted: {len(drafted)}')
    window['-YOUR_TURN-'].update(f'Your Turn: {"YES" if is_my_turn else "NO"}')
    window['-MANUAL_PICKS-'].update(f'{len(manual_picks)} manual picks added')
    
    # Update recommendations
    if is_my_turn:
        recommendations = "🎯 IT'S YOUR PICK! 🎯\n"
        recommendations += "=" * 50 + "\n\n"
        
        # Update recommendation engine state
        recommendation_engine.update_draft_state(drafted, {}, current_pick)
        top_recs = recommendation_engine.get_recommendations(10)
        
        recommendations += "VOR-Based Ranking: VOR (75%) + Ceiling/Floor (20%) + Tier + Cliff + ADP + Risk + Opportunity Cost\n\n"
        for i, (_, player) in enumerate(top_recs.iterrows(), 1):
            adp_str = f"ADP: {player['ADP']}" if not pd.isna(player['ADP']) and player['ADP'] != 'NA' else "ADP: N/A"
            tier_icon = '🟢' if player['Tier'] == 1 else '🟡' if player['Tier'] == 2 else '🟠' if player['Tier'] == 3 else '🔴'
            score_str = f"Score: {player['composite_score']:.1f}" if 'composite_score' in player else ""
            
            # Add strategic reasoning
            reasoning = []
            if player['Position'] in ['RB', 'WR', 'TE']:
                # Check for cliff detection
                pos_players = df[~df['Player'].isin(drafted)]
                pos_players = pos_players[pos_players['Position'] == player['Position']].sort_values('VOR', ascending=False)
                if len(pos_players) > 1:
                    top_vor = pos_players.iloc[0]['VOR']
                    dropoff = top_vor - player['VOR']
                    if dropoff > 20:
                        reasoning.append("📉 Cliff")
                
            if player['Position'] == 'QB' and current_pick <= 72:  # Early rounds
                reasoning.append("⏰ Early QB")
            
            reasoning_str = f" | {' '.join(reasoning)}" if reasoning else ""
            
            recommendations += f"{tier_icon} {i:2d}. {player['Player']:<20} ({player['Position']}) | VOR: {player['VOR']:>6.1f} | Tier {player['Tier']} | {adp_str} | {score_str}{reasoning_str}\n"
    else:
        recommendations = "📊 Top 5 Available Players:\n"
        recommendations += "=" * 50 + "\n\n"
        available_df = df[~df['Player'].isin(drafted)]
        available_df = available_df.sort_values('VOR', ascending=False).head(5)
        for i, (_, player) in enumerate(available_df.iterrows(), 1):
            adp_str = f"ADP: {player['ADP']}" if not pd.isna(player['ADP']) and player['ADP'] != 'NA' else "ADP: N/A"
            tier_icon = '🟢' if player['Tier'] == 1 else '🟡' if player['Tier'] == 2 else '🟠' if player['Tier'] == 3 else '🔴'
            recommendations += f"{tier_icon} {i:2d}. {player['Player']:<20} ({player['Position']}) | VOR: {player['VOR']:>6.1f} | Tier {player['Tier']} | {adp_str}\n"
    
    window['-RECOMMENDATIONS-'].update(recommendations)


def show_position_analysis(df, drafted, position):
    """Show analysis for a specific position using the recommendation engine"""
    # Update recommendation engine state
    recommendation_engine.update_draft_state(drafted, {}, 1)  # Use pick 1 for analysis
    pos_data = recommendation_engine.get_position_analysis(position, 10)
    
    # Color coding for different tiers
    tier_colors = {
        1: '🟢',  # Green for Tier 1
        2: '🟡',  # Yellow for Tier 2  
        3: '🟠',  # Orange for Tier 3
        4: '🔴',  # Red for Tier 4+
    }
    
    analysis = f"🏈 {position} ANALYSIS 🏈\n"
    analysis += "=" * 50 + "\n"
    analysis += f"Available players: {len(pos_data)}\n\n"
    
    if len(pos_data) == 0:
        analysis += f"No {position} players available"
    else:
        analysis += f"Top {position} players by Composite Score:\n"
        analysis += "-" * 50 + "\n"
        
        for i, (_, player) in enumerate(pos_data.iterrows(), 1):
            tier = player['Tier']
            tier_icon = tier_colors.get(tier, '⚪')
            adp_str = f"ADP: {player['ADP']}" if not pd.isna(player['ADP']) and player['ADP'] != 'NA' else "ADP: N/A"
            score_str = f"Score: {player['composite_score']:.1f}" if 'composite_score' in player else ""
            
            # Format based on tier
            if tier == 1:
                analysis += f"{tier_icon} {i:2d}. {player['Player']:<20} | VOR: {player['VOR']:>6.1f} | Tier {tier} | {adp_str} | {score_str}\n"
            elif tier == 2:
                analysis += f"{tier_icon} {i:2d}. {player['Player']:<20} | VOR: {player['VOR']:>6.1f} | Tier {tier} | {adp_str} | {score_str}\n"
            else:
                analysis += f"{tier_icon} {i:2d}. {player['Player']:<20} | VOR: {player['VOR']:>6.1f} | Tier {tier} | {adp_str} | {score_str}\n"
    
    return analysis


def main():
    """Main GUI application"""
    # Initialize data
    drafted_positions = {}
    manual_drafted_players = set()
    current_pick_number = 1
    
    # Create main window
    window = create_main_window()
    
    # Main event loop
    while True:
        event, values = window.read(timeout=5000)  # Refresh every 5 seconds
        
        if event == sg.WIN_CLOSED or event == '-EXIT-':
            break
        
        # Get current drafted players
        drafted = get_drafted_players()
        drafted.update(manual_drafted_players)
        
        # Update main window
        update_main_window(window, df, drafted, current_pick_number, manual_drafted_players)
        
        # Handle events
        if event == '-ADD_PICK-':
            # Open manual pick window
            pick_window = create_manual_pick_window(df, drafted, current_pick_number)
            
            while True:
                pick_event, pick_values = pick_window.read()
                
                if pick_event == sg.WIN_CLOSED or pick_event == '-CLOSE-':
                    break
                
                # Check if we need to refresh the window (after adding players)
                refresh_window = False
                
                # Handle "Add All" button first
                if pick_event == '-ADD_ALL-':
                    if '-ALL_LIST-' in pick_values and pick_values['-ALL_LIST-']:
                        selected_items = pick_values['-ALL_LIST-']
                        added_count = 0
                        
                        # Get all available players
                        available_df = df[~df['Player'].isin(drafted)]
                        available_df = available_df.sort_values('ADP', ascending=True)
                        
                        for selection in selected_items:
                            try:
                                # Extract player number from selection (e.g., " 1. Josh Allen (QB) | ADP: 18.1 | VOR: 88.6")
                                player_num = int(selection.split('.')[0].strip())
                                if 1 <= player_num <= len(available_df):
                                    player_row = available_df.iloc[player_num - 1]
                                    player_name = player_row['Player']
                                    manual_drafted_players.add(player_name)
                                    added_count += 1
                            except (ValueError, IndexError):
                                continue
                        
                        if added_count > 0:
                            current_pick_number += added_count
                            sg.popup(f"Added {added_count} player(s) to drafted list!")
                            refresh_window = True
                
                # Handle position-specific add buttons
                elif pick_event.startswith('-ADD_') and pick_event.endswith('-'):
                    position = pick_event[5:-1]  # Extract position from button key
                    list_key = f'-{position}_LIST-'
                    
                    if list_key in pick_values and pick_values[list_key]:
                        selected_items = pick_values[list_key]
                        added_count = 0
                        
                        # Get available players for this position
                        available_df = df[~df['Player'].isin(drafted)]
                        pos_df = available_df[available_df['Position'] == position].sort_values('ADP', ascending=True)
                        
                        for selection in selected_items:
                            try:
                                # Extract player number from selection (e.g., " 1. Josh Allen | ADP: 18.1 | VOR: 88.6")
                                player_num = int(selection.split('.')[0].strip())
                                if 1 <= player_num <= len(pos_df):
                                    player_row = pos_df.iloc[player_num - 1]
                                    player_name = player_row['Player']
                                    manual_drafted_players.add(player_name)
                                    added_count += 1
                            except (ValueError, IndexError):
                                continue
                        
                        if added_count > 0:
                            current_pick_number += added_count
                            sg.popup(f"Added {added_count} {position} player(s) to drafted list!")
                            refresh_window = True
                
                # Refresh window if players were added
                if refresh_window:
                    pick_window.close()
                    # Recreate window with updated data
                    pick_window = create_manual_pick_window(df, drafted, current_pick_number)
                    refresh_window = False
                    continue
            
            pick_window.close()
        
        elif event == '-CLEAR_PICKS-':
            if len(manual_drafted_players) > 0:
                result = sg.popup_yes_no(f"Clear all {len(manual_drafted_players)} manual picks?")
                if result == 'Yes':
                    manual_drafted_players.clear()
                    current_pick_number = 1
                    sg.popup("Manual picks cleared!")
        
        elif event == '-SHOW_PICKS-':
            if len(manual_drafted_players) == 0:
                sg.popup("No manual picks added yet!")
            else:
                # Organize manual picks by position
                picks_by_position = {}
                for player in manual_drafted_players:
                    player_info = df[df['Player'] == player]
                    if len(player_info) > 0:
                        pos = player_info.iloc[0]['Position']
                        if pos not in picks_by_position:
                            picks_by_position[pos] = []
                        picks_by_position[pos].append(player)
                
                # Create display text
                display_text = f"=== MANUAL PICKS ({len(manual_drafted_players)}) ===\n\n"
                
                for pos in ['QB', 'RB', 'WR', 'TE', 'K', 'DST']:
                    if pos in picks_by_position:
                        display_text += f"{pos} ({len(picks_by_position[pos])}):\n"
                        for i, player in enumerate(sorted(picks_by_position[pos]), 1):
                            player_info = df[df['Player'] == player]
                            if len(player_info) > 0:
                                adp = player_info.iloc[0]['ADP']
                                adp_str = f"ADP: {adp}" if not pd.isna(adp) and adp != 'NA' else "ADP: N/A"
                                display_text += f"  {i}. {player} | {adp_str}\n"
                        display_text += "\n"
                
                # Show next likely picks
                available_df = df[~df['Player'].isin(drafted)]
                available_df = available_df.sort_values('ADP', ascending=True)
                
                display_text += f"=== NEXT LIKELY PICKS (Pick #{current_pick_number}) ===\n"
                display_text += "Top 10 available by ADP:\n"
                for i, (_, player) in enumerate(available_df.head(10).iterrows(), 1):
                    adp_str = f"ADP: {player['ADP']}" if not pd.isna(player['ADP']) and player['ADP'] != 'NA' else "ADP: N/A"
                    display_text += f"  {i}. {player['Player']} ({player['Position']}) | {adp_str} | VOR: {player['VOR']:.1f}\n"
                
                sg.popup_scrolled(display_text, title="Manual Picks", size=(60, 25))
        
        elif event == '-REFRESH-':
            # Force refresh of data
            try:
                if not TEST_MODE:
                    global league
                    league = League(league_id=LEAGUE_ID, year=YEAR, espn_s2=ESPN_S2, swid=SWID)
                    sg.popup("ESPN data refreshed successfully!")
                else:
                    sg.popup("Test mode - no ESPN connection needed!")
            except Exception as e:
                sg.popup(f"Error refreshing data: {e}")
                print(f"Refresh error details: {e}")
        
        elif event == '-DEBUG-':
            # Show debug information
            debug_info = f"League ID: {LEAGUE_ID}\n"
            debug_info += f"Year: {YEAR}\n"
            debug_info += f"Your Draft Slot: {YOUR_DRAFT_SLOT + 1}\n"
            debug_info += f"Total Teams: {TOTAL_TEAMS}\n"
            debug_info += f"Current Pick: {current_pick_number}\n"
            debug_info += f"Manual Picks: {len(manual_drafted_players)}\n"
            debug_info += f"API Picks: {len(drafted - manual_drafted_players)}\n"
            
            if len(manual_drafted_players) > 0:
                debug_info += f"\nManual Picks:\n"
                for player in sorted(manual_drafted_players):
                    debug_info += f"  - {player}\n"
            
            sg.popup_scrolled(debug_info, title="Debug Information", size=(50, 20))
        
        elif event in ['-QB_ANALYSIS-', '-RB_ANALYSIS-', '-WR_ANALYSIS-', '-TE_ANALYSIS-']:
            # Fix position extraction
            if event == '-QB_ANALYSIS-':
                position = 'QB'
            elif event == '-RB_ANALYSIS-':
                position = 'RB'
            elif event == '-WR_ANALYSIS-':
                position = 'WR'
            elif event == '-TE_ANALYSIS-':
                position = 'TE'
            
            analysis = show_position_analysis(df, drafted, position)
            window['-POSITION_ANALYSIS-'].update(analysis)
    
    window.close()


if __name__ == "__main__":
    main()

import pandas as pd
import time
import warnings
import os
import sys
import requests
import json
import threading

# Quiet noisy warnings
original_stderr = sys.stderr
sys.stderr = open(os.devnull, 'w')
os.environ['PYTHONWARNINGS'] = 'ignore'
warnings.filterwarnings('ignore')
import PySimpleGUI as sg
sys.stderr = original_stderr

from espn_api.football import League
from config import *
from data_loader import load_and_clean_data
from draft_analyzer import print_draft_insights, is_my_pick
from recommendation_engine import RecommendationEngine

df = load_and_clean_data()
if df is None:
    print("Failed to load data. Exiting.")
    raise SystemExit(1)

df["Drafted"] = False
recommendation_engine = RecommendationEngine(df)

TEST_MODE = False


class DraftState:
    def __init__(self, total_teams, your_draft_slot, current_pick=1):
        self.total_teams = total_teams
        self.your_draft_slot = your_draft_slot
        self.current_pick = current_pick
        self.all_drafted_players = set()
        self.your_roster = set()
        self.manual_picks = set()

    def is_my_pick(self):
        current_round = (self.current_pick - 1) // self.total_teams + 1
        my_pick_in_round = self.your_draft_slot + 1 if current_round % 2 == 1 else self.total_teams - self.your_draft_slot
        pick_in_round = ((self.current_pick - 1) % self.total_teams) + 1
        return pick_in_round == my_pick_in_round

    def get_next_my_pick(self):
        current_round = (self.current_pick - 1) // self.total_teams + 1
        my_pick_in_round = self.your_draft_slot + 1 if current_round % 2 == 1 else self.total_teams - self.your_draft_slot
        pick_in_round = ((self.current_pick - 1) % self.total_teams) + 1
        if pick_in_round == my_pick_in_round:
            return self.current_pick
        gap = my_pick_in_round - pick_in_round
        if gap <= 0:
            gap += self.total_teams
        return self.current_pick + gap

    def add_manual_pick(self, player_name):
        self.all_drafted_players.add(player_name)
        self.manual_picks.add(player_name)
        self.current_pick += 1

    def add_to_roster(self, player_name):
        self.all_drafted_players.add(player_name)
        self.your_roster.add(player_name)
        self.current_pick += 1

    def get_all_drafted(self):
        return self.all_drafted_players.copy()

    def get_your_roster(self):
        return self.your_roster.copy()

    def get_manual_picks(self):
        return self.manual_picks.copy()

draft_state = DraftState(TOTAL_TEAMS, YOUR_DRAFT_SLOT, current_pick=1)

if TEST_MODE:
    def get_drafted_players():
        return draft_state.get_all_drafted()

    def add_mock_pick(player_name):
        draft_state.add_manual_pick(player_name)
        return f"Mock pick added: {player_name}"

    print("Running in TEST MODE - using mock draft data")

else:
    try:
        league = League(league_id=LEAGUE_ID, year=YEAR, espn_s2=ESPN_S2, swid=SWID)
        print("Successfully connected to ESPN league")
    except Exception as e:
        print(f"Failed to connect to ESPN league: {e}")
        print("Falling back to TEST MODE")
        TEST_MODE = False

    def fetch_draft_recap(league_id, year):
        try:
            url = (f"https://fantasy.espn.com/apis/v3/games/ffl/seasons/{year}/segments/0/"
                   f"leagues/{league_id}?view=mDraftDetail&view=mTeam")
            headers = {
                'Cookie': f'espn_s2={ESPN_S2}; SWID={SWID}',
                'User-Agent': 'Mozilla/5.0'
            }
            r = requests.get(url, headers=headers, timeout=8)
            if r.status_code != 200:
                return set()
            data = r.json()
            picks = data.get('draftDetail', {}).get('picks', [])
            return {p['player']['fullName'] for p in picks if 'player' in p}
        except Exception:
            return set()

    def get_drafted_players():
        try:
            drafted_players = set()

            # espn_api draft object
            try:
                picks = league.draft
                if picks:
                    for pick in picks:
                        name = getattr(pick, 'playerName', None) or getattr(pick, 'name', None)
                        if name:
                            drafted_players.add(name)
            except Exception:
                pass

            # rosters (live drafts)
            try:
                for team in league.teams:
                    for player in team.roster:
                        name = getattr(player, 'name', None) or getattr(player, 'playerName', None) or getattr(player, 'full_name', None)
                        if name:
                            drafted_players.add(name)
            except Exception:
                pass

            # draft recap endpoint (mocks)
            try:
                drafted_players.update(fetch_draft_recap(LEAGUE_ID, YEAR))
            except Exception:
                pass

            return drafted_players
        except Exception as e:
            print(f"Error getting drafted players: {e}")
            return set()


def create_main_window():
    # Theme and color palette
    sg.theme('DarkGrey13')
    BG = '#0d1117'            # Background
    CARD_BG = '#161b22'       # Section background
    TEXT = '#e6edf3'          # Main text
    ACCENT = '#58a6ff'        # Accent blue
    SUCCESS = '#3fb950'
    WARNING = '#d29922'
    ERROR = '#f85149'
    MUTED = '#8b949e'

    def metric(label, key, color):
        return sg.Column([
            [sg.Text(label, font=('Helvetica', 10), text_color=MUTED, background_color=CARD_BG)],
            [sg.Text('-', key=key, font=('Helvetica', 18, 'bold'), text_color=color, background_color=CARD_BG)]
        ], pad=(10, 5), background_color=CARD_BG)

    # Header bar
    header_row = [
        sg.Column([
            [sg.Text('🏈 ESPN Draft Assistant', font=('Helvetica', 24, 'bold'), text_color=SUCCESS, background_color=BG)],
            [sg.Text(f'Draft Slot: {YOUR_DRAFT_SLOT + 1} | Teams: {TOTAL_TEAMS}',
                     font=('Helvetica', 12), text_color=MUTED, background_color=BG)],
            [sg.Text('', key='-HEADER_STATUS-', font=('Helvetica', 13, 'bold'), text_color=TEXT, background_color=BG)]
        ], expand_x=True, background_color=BG),
        sg.Column([
            [sg.Button('🔄 Refresh', key='-REFRESH-', size=(14, 1), font=('Helvetica', 11), button_color=('white', '#3498DB')),
             sg.Button('➕ Add Pick', key='-ADD_PICK-', size=(14, 1), font=('Helvetica', 11), button_color=('white', '#27AE60')),
             sg.Button('👥 Show Roster', key='-SHOW_ROSTER-', size=(14, 1), font=('Helvetica', 11), button_color=('white', '#E67E22')),
             sg.Button('👁️ Show Picks', key='-SHOW_PICKS-', size=(14, 1), font=('Helvetica', 11), button_color=('white', '#9B59B6'))],
            [sg.Button('🗑️ Clear All', key='-CLEAR_PICKS-', size=(14, 1), font=('Helvetica', 11), button_color=('white', '#E74C3C')),
             sg.Button('🔍 Debug', key='-DEBUG-', size=(14, 1), font=('Helvetica', 11), button_color=('white', '#95A5A6')),
             sg.Button('❌ Exit', key='-EXIT-', size=(14, 1), font=('Helvetica', 11), button_color=('white', '#C0392B'))]
        ], element_justification='right', pad=(20, 10), background_color=BG)
    ]

    # Draft Status as metric tiles
    draft_status_frame = sg.Frame(
        '📊 Draft Status',
        [[metric('Current Pick', '-CURRENT_PICK-', SUCCESS),
          metric('Round', '-CURRENT_ROUND-', ACCENT),
          metric('Drafted', '-DRAFTED_COUNT-', WARNING),
          metric('Your Turn', '-YOUR_TURN-', ERROR)]],
        font=('Helvetica', 13, 'bold'), background_color=CARD_BG, title_color=TEXT, relief=sg.RELIEF_FLAT, border_width=1
    )

    # Manual Picks
    manual_picks_frame = sg.Frame(
        '✏️ Manual Picks',
        [[sg.Text('0 picks added', key='-MANUAL_PICKS-', font=('Helvetica', 11), text_color=TEXT, background_color=CARD_BG)]],
        font=('Helvetica', 13, 'bold'), background_color=CARD_BG, title_color=TEXT, relief=sg.RELIEF_FLAT, border_width=1
    )

    # Collapsible roster
    roster_frame = sg.pin(
        sg.Frame(
            '👥 Roster',
            [[sg.Multiline(size=(80, 10), key='-CURRENT_ROSTER-', disabled=True,
                           background_color='#0d1117', text_color=TEXT, font=('Consolas', 11), border_width=0)]],
            font=('Helvetica', 13, 'bold'), background_color=CARD_BG, title_color=TEXT, relief=sg.RELIEF_FLAT, border_width=1,
            key='-ROSTER_FRAME-'
        )
    )

    # Legend
    legend_frame = sg.Frame(
        '📋 Legend',
        [[sg.Text('🟢 Tier 1   🟡 Tier 2   🟠 Tier 3   🔴 Tier 4+    📉 Cliff   ⏰ Early QB',
                  font=('Helvetica', 11), text_color=MUTED, background_color=CARD_BG)]],
        font=('Helvetica', 13, 'bold'), background_color=CARD_BG, title_color=TEXT, relief=sg.RELIEF_FLAT, border_width=1
    )

    # Recommendations
    recommendations_frame = sg.Frame(
        '🎯 Recommendations',
        [[sg.Multiline(size=(80, 8), key='-RECOMMENDATIONS-', disabled=True,
                       background_color='#0d1117', text_color=TEXT, font=('Consolas', 11), border_width=0)]],
        font=('Helvetica', 13, 'bold'), background_color=CARD_BG, title_color=TEXT, relief=sg.RELIEF_FLAT, border_width=1
    )

    # Position Analysis
    position_analysis_frame = sg.Frame(
        '📈 Position Analysis',
        [
            [sg.Button('QB', key='-QB_ANALYSIS-', size=(8, 1), font=('Helvetica', 11)),
             sg.Button('RB', key='-RB_ANALYSIS-', size=(8, 1), font=('Helvetica', 11)),
             sg.Button('WR', key='-WR_ANALYSIS-', size=(8, 1), font=('Helvetica', 11)),
             sg.Button('TE', key='-TE_ANALYSIS-', size=(8, 1), font=('Helvetica', 11)),
             sg.Button('📊 Overall', key='-OVERALL_ANALYSIS-', size=(12, 1), font=('Helvetica', 11))],
            [sg.Multiline(size=(70, 18), key='-POSITION_ANALYSIS-', disabled=True,
                          background_color='#0d1117', text_color=TEXT, font=('Consolas', 11), border_width=0)]
        ],
        font=('Helvetica', 13, 'bold'), background_color=CARD_BG, title_color=TEXT, relief=sg.RELIEF_FLAT, border_width=1
    )

    # Player Analysis
    player_analysis_frame = sg.Frame(
        '📊 Player Analysis (Top 10 by Ceiling)',
        [
            [sg.Button('QB', key='-QB_PLAYER_ANALYSIS-', size=(8, 1), font=('Helvetica', 11)),
             sg.Button('RB', key='-RB_PLAYER_ANALYSIS-', size=(8, 1), font=('Helvetica', 11)),
             sg.Button('WR', key='-WR_PLAYER_ANALYSIS-', size=(8, 1), font=('Helvetica', 11)),
             sg.Button('TE', key='-TE_PLAYER_ANALYSIS-', size=(8, 1), font=('Helvetica', 11)),
             sg.Button('📊 All', key='-ALL_PLAYER_ANALYSIS-', size=(12, 1), font=('Helvetica', 11))],
            [sg.Multiline(size=(70, 18), key='-PLAYER_ANALYSIS-', disabled=True,
                          background_color='#0d1117', text_color=TEXT, font=('Consolas', 11), border_width=0)]
        ],
        font=('Helvetica', 13, 'bold'), background_color=CARD_BG, title_color=TEXT, relief=sg.RELIEF_FLAT, border_width=1
    )

    # Layout
    layout = [
        [header_row],
        [sg.HorizontalSeparator(color='#30363d', pad=(0, 15))],
        [draft_status_frame],
        [manual_picks_frame],
        [roster_frame],
        [legend_frame],
        [recommendations_frame],
        [sg.Column([
            [position_analysis_frame]
        ], expand_x=True, expand_y=True, pad=(0, 0)),
         sg.Column([
            [player_analysis_frame]
        ], expand_x=True, expand_y=True, pad=(0, 0))]
    ]

    window = sg.Window('ESPN Draft Assistant', layout, finalize=True, resizable=True,
                       size=(1800, 1000), location=(100, 100), background_color=BG)

    window.roster_visible = False
    window['-ROSTER_FRAME-'].update(visible=False)
    window['-SHOW_ROSTER-'].update('👥 Show Roster', button_color=('white', '#2196F3'))
    return window

    sg.theme('DarkBlue3')
    title_color = '#66BB6A'
    section_color = '#42A5F5'

    # Roster (pinned so it collapses cleanly)
    roster_section = sg.pin(
        sg.Frame(
            '👥 Roster',
            [[sg.Multiline(size=(80, 10), key='-CURRENT_ROSTER-', disabled=True,
                           background_color='#1e1e1e', text_color='#E0E0E0', font=('Consolas', 11))]],
            font=('Helvetica', 13, 'bold'),
            key='-ROSTER_FRAME-',
            relief=sg.RELIEF_RAISED,
            border_width=3,
            background_color='#2C3E50'
        ),
        expand_x=True
    )

    # Header with title and controls
    header_row = [
        # Left side: Title and draft info
        sg.Column([
            [sg.Text('🏈 ESPN Draft Assistant', font=('Helvetica', 24, 'bold'),
                     text_color=title_color, justification='left')],
            [sg.Text(f'Draft Slot: {YOUR_DRAFT_SLOT + 1} | Teams: {TOTAL_TEAMS}',
                     font=('Helvetica', 12), text_color='white', justification='left')],
            [sg.Text('', key='-HEADER_STATUS-', font=('Helvetica', 13, 'bold'), 
                     text_color='white', justification='left')]  # Your Turn status
        ], expand_x=True, element_justification='left', pad=(20, 10)),
        
        # Right side: Controls in compact horizontal layout
        sg.Column([
            [sg.Button('🔄 Refresh', key='-REFRESH-', size=(14, 1), font=('Helvetica', 11), button_color=('white', '#3498DB')),
             sg.Button('➕ Add Pick', key='-ADD_PICK-', size=(14, 1), font=('Helvetica', 11), button_color=('white', '#27AE60')),
             sg.Button('👥 Show Roster', key='-SHOW_ROSTER-', size=(14, 1), font=('Helvetica', 11), button_color=('white', '#E67E22')),
             sg.Button('👁️ Show Picks', key='-SHOW_PICKS-', size=(14, 1), font=('Helvetica', 11), button_color=('white', '#9B59B6'))],
            [sg.Button('🗑️ Clear All', key='-CLEAR_PICKS-', size=(14, 1), font=('Helvetica', 11), button_color=('white', '#E74C3C')),
             sg.Button('🔍 Debug', key='-DEBUG-', size=(14, 1), font=('Helvetica', 11), button_color=('white', '#95A5A6')),
             sg.Button('❌ Exit', key='-EXIT-', size=(14, 1), font=('Helvetica', 11), button_color=('white', '#C0392B')),
             sg.Text('', size=(14, 1))]  # Spacer to align with 4-button row
        ], element_justification='right', pad=(20, 10))
    ]

    # Main content area (resizable when roster is hidden)
    main_content = sg.Column([
        [sg.HorizontalSeparator(color='#34495E', pad=(0, 15))],
        [sg.Frame('📊 Draft Status', [
            [sg.Column([
                [sg.Text('Current Pick:', font=('Helvetica', 11, 'bold'), text_color='#E3F2FD'),
                 sg.Text('#1', key='-CURRENT_PICK-', font=('Helvetica', 14, 'bold'), text_color='#4CAF50')],
                [sg.Text('Round:', font=('Helvetica', 11, 'bold'), text_color='#E3F2FD'),
                 sg.Text('R1', key='-CURRENT_ROUND-', font=('Helvetica', 14, 'bold'), text_color='#2196F3')],
                [sg.Text('Drafted:', font=('Helvetica', 11, 'bold'), text_color='#E3F2FD'),
                 sg.Text('0', key='-DRAFTED_COUNT-', font=('Helvetica', 14, 'bold'), text_color='#FF9800')],
                [sg.Text('Your Turn:', font=('Helvetica', 11, 'bold'), text_color='#E3F2FD'),
                 sg.Text('NO', key='-YOUR_TURN-', font=('Helvetica', 14, 'bold'), text_color='#F44336')]
            ], expand_x=True, pad=(10, 8))]
        ], font=('Helvetica', 13, 'bold'), expand_x=True, pad=(10, 10), relief=sg.RELIEF_RAISED, border_width=3, background_color='#2C3E50')],
        [sg.Frame('✏️ Manual Picks', [
            [sg.Text('0 picks added', key='-MANUAL_PICKS-', font=('Helvetica', 11), text_color='white')]
        ], font=('Helvetica', 13, 'bold'), expand_x=True, pad=(10, 10), relief=sg.RELIEF_RAISED, border_width=3, background_color='#34495E')],
        [roster_section],
        [sg.Frame('📋 Legend', [[
            sg.Text('🟢 Tier 1   🟡 Tier 2   🟠 Tier 3   🔴 Tier 4+    📉 Cliff   ⏰ Early QB', font=('Helvetica', 11))
        ]], font=('Helvetica', 13, 'bold'), expand_x=True, pad=(10, 10), relief=sg.RELIEF_RAISED, border_width=3, background_color='#34495E')],
        [sg.Frame('🎯 Recommendations', [
            [sg.Multiline(size=(80, 8), key='-RECOMMENDATIONS-', disabled=True,
                          background_color='#1e1e1e', text_color='#E0E0E0', font=('Consolas', 11))]
        ], font=('Helvetica', 13, 'bold'), expand_x=True, pad=(10, 10), relief=sg.RELIEF_RAISED, border_width=3, background_color='#2C3E50')],
        [sg.Column([
            [sg.Frame('📈 Position Analysis', [
                [sg.Button('QB', key='-QB_ANALYSIS-', size=(8, 1), font=('Helvetica', 11)),
                 sg.Button('RB', key='-RB_ANALYSIS-', size=(8, 1), font=('Helvetica', 11)),
                 sg.Button('WR', key='-WR_ANALYSIS-', size=(8, 1), font=('Helvetica', 11)),
                 sg.Button('TE', key='-TE_ANALYSIS-', size=(8, 1), font=('Helvetica', 11)),
                 sg.Button('📊 Overall', key='-OVERALL_ANALYSIS-', size=(12, 1), font=('Helvetica', 11))],
                [sg.Multiline(size=(70, 18), key='-POSITION_ANALYSIS-', disabled=True,
                              background_color='#1e1e1e', text_color='#E0E0E0', font=('Consolas', 11))]
            ], font=('Helvetica', 13, 'bold'), expand_x=True, expand_y=True, pad=(10, 10), relief=sg.RELIEF_RAISED, border_width=3, background_color='#2C3E50')],
        ], expand_x=True, expand_y=True, pad=(5, 0)),
         sg.Column([
            [sg.Frame('📊 Player Analysis (Top 10 by Ceiling)', [
                [sg.Button('QB', key='-QB_PLAYER_ANALYSIS-', size=(8, 1), font=('Helvetica', 11)),
                 sg.Button('RB', key='-RB_PLAYER_ANALYSIS-', size=(8, 1), font=('Helvetica', 11)),
                 sg.Button('WR', key='-WR_PLAYER_ANALYSIS-', size=(8, 1), font=('Helvetica', 11)),
                 sg.Button('TE', key='-TE_PLAYER_ANALYSIS-', size=(8, 1), font=('Helvetica', 11)),
                 sg.Button('📊 All', key='-ALL_PLAYER_ANALYSIS-', size=(12, 1), font=('Helvetica', 11))],
                [sg.Multiline(size=(70, 18), key='-PLAYER_ANALYSIS-', disabled=True,
                              background_color='#1e1e1e', text_color='#E0E0E0', font=('Consolas', 11))]
            ], font=('Helvetica', 13, 'bold'), expand_x=True, expand_y=True, pad=(10, 10), relief=sg.RELIEF_RAISED, border_width=3, background_color='#2C3E50')]
        ], expand_x=True, expand_y=True, pad=(5, 0))],
    ], expand_x=True, expand_y=True)

    # Main layout with header and content
    layout = [
        [header_row],
        [main_content]
    ]
    
    window = sg.Window('ESPN Draft Assistant', layout, finalize=True, resizable=True,
                       size=(1800, 1000), location=(100, 100))
    
    # remember roster visibility across refreshes
    window.roster_visible = False
    window['-ROSTER_FRAME-'].update(visible=window.roster_visible)
    window['-SHOW_ROSTER-'].update('👥 Show Roster', button_color=('white', '#2196F3'))
    return window


def create_manual_pick_window(df, drafted, current_pick):
    # Ensure drafted is a set for efficient lookup
    if not isinstance(drafted, set):
        drafted = set(drafted)
    
    available_df = df[~df['Player'].isin(drafted)]
    title_color = '#66BB6A'
    section_color = '#42A5F5'
    


    tabs = []

    # All
    all_players = available_df.sort_values('ADP', ascending=True).head(60)
    all_list = []
    for i, (_, p) in enumerate(all_players.iterrows(), 1):
        adp_str = f"ADP: {p['ADP']}" if not pd.isna(p['ADP']) and p['ADP'] != 'NA' else "ADP: N/A"
        all_list.append(f" {i:2d}. {p['Player']} ({p['Position']}) | {adp_str} | VOR: {p['VOR']:.1f}")

    all_tab = [
        [sg.Text('All (Top 60 by ADP)', font=('Helvetica', 12, 'bold'), text_color=title_color)],
        [sg.Listbox(all_list, size=(80, 20), key='-ALL_LIST-',
                    select_mode=sg.LISTBOX_SELECT_MODE_MULTIPLE,
                    background_color='#1e1e1e', text_color='#E0E0E0', font=('Consolas', 10))],
        [sg.Button('Add Selected', key='-ADD_ALL-', size=(16, 1))]
    ]
    tabs.append(sg.Tab('All', all_tab))

    # Positions
    for position in ['QB', 'RB', 'WR', 'TE', 'K', 'DST']:
        pos_players = available_df[available_df['Position'] == position].sort_values('ADP', ascending=True).head(50)
        pos_list = []
        for i, (_, p) in enumerate(pos_players.iterrows(), 1):
            adp_str = f"ADP: {p['ADP']}" if not pd.isna(p['ADP']) and p['ADP'] != 'NA' else "ADP: N/A"
            pos_list.append(f" {i:2d}. {p['Player']} | {adp_str} | VOR: {p['VOR']:.1f}")

        pos_tab = [
            [sg.Text(f'{position}', font=('Helvetica', 12, 'bold'), text_color=title_color)],
            [sg.Listbox(pos_list, size=(80, 20), key=f'-{position}_LIST-',
                        select_mode=sg.LISTBOX_SELECT_MODE_MULTIPLE,
                        background_color='#1e1e1e', text_color='#E0E0E0', font=('Consolas', 10))],
            [sg.Button('Add Selected', key=f'-ADD_{position}-', size=(16, 1))]
        ]
        tabs.append(sg.Tab(position, pos_tab))

    layout = [
        [sg.Text('Manual Pick', font=('Helvetica', 14, 'bold'), text_color=title_color)],
        [sg.Text(f'Pick #{current_pick} | Available: {len(available_df)} players', font=('Helvetica', 10), text_color=section_color)],
        [sg.TabGroup([tabs])],
        [sg.Button('Close', key='-CLOSE-', size=(10, 1))]
    ]

    return sg.Window('Manual Pick', layout, modal=True, finalize=True, resizable=True)


def update_main_window(window, df, drafted, current_pick, manual_picks):
    all_drafted = draft_state.get_all_drafted()
    recommendation_engine.update_draft_state(all_drafted, {}, current_pick)

    # Recommendations (position-first)
    top_recs = recommendation_engine.get_recommendations(5)
    if len(top_recs) > 0:
        recommended_position = top_recs.attrs.get('recommended_position', 'Unknown')
        position_urgency = top_recs.attrs.get('position_urgency', 0)
        lines = [f"RECOMMENDED POSITION: {recommended_position} (Urgency: {position_urgency:.1f})", ""]
        for i, (_, p) in enumerate(top_recs.iterrows(), 1):
            adp_str = f"ADP: {p['ADP']}" if not pd.isna(p['ADP']) and p['ADP'] != 'NA' else "ADP: N/A"
            tier_icon = '🟢' if p['Tier'] == 1 else '🟡' if p['Tier'] == 2 else '🟠' if p['Tier'] == 3 else '🔴'
            score_str = f"{p['composite_score']:.1f}" if 'composite_score' in p else ""
            lines.append(f"{tier_icon} {i}. {p['Player']} ({p['Position']}) | VOR {p['VOR']:.1f} | T{p['Tier']} | {adp_str} | Score {score_str}")
        recommendations = "\n".join(lines)
    else:
        recommendations = "No recommendations right now."

    # Overall position urgency (stored for popup)
    insights = recommendation_engine.get_strategic_insights()
    position_urgencies = insights.get('position_urgencies', {})
    overall = ["POSITION URGENCY", ""]
    if position_urgencies:
        for pos, urg in sorted(position_urgencies.items(), key=lambda x: x[1], reverse=True):
            your_roster = draft_state.get_your_roster()
            drafted_count = sum(1 for p in your_roster if df[df['Player'] == p]['Position'].iloc[0] == pos) if your_roster else 0
            need = max(0, STARTING_LINEUP.get(pos, 0) - drafted_count)
            emoji = "🔴" if urg > 30 else "🟠" if urg > 15 else "🟡" if urg > 0 else "🟢"
            overall.append(f"{emoji} {pos}: {urg:5.1f} | Drafted {drafted_count}/{POSITION_LIMITS.get(pos, 0)} | Need {need}")
    else:
        overall.append("No data.")
    window.overarching_analysis = "\n".join(overall)

    # Roster text
    your_roster = draft_state.get_your_roster()
    roster_text = ["👥 ROSTER", ""]
    is_my_turn = draft_state.is_my_pick()
    next_my_pick = draft_state.get_next_my_pick()
    if is_my_turn:
        roster_text += ["IT'S YOUR PICK!", ""]
    else:
        picks_until = next_my_pick - current_pick
        roster_text += [f"Next pick: #{next_my_pick} ({picks_until} away)", ""]
    if your_roster:
        by_pos = {}
        for player in your_roster:
            row = df[df['Player'] == player]
            if len(row) > 0:
                pos = row.iloc[0]['Position']
                by_pos.setdefault(pos, []).append(player)
        for pos in ['QB', 'RB', 'WR', 'TE', 'K', 'DST']:
            if pos in by_pos:
                roster_text.append(f"{pos} ({len(by_pos[pos])}/{POSITION_LIMITS.get(pos, 0)}):")
                for name in by_pos[pos]:
                    pdata = df[df['Player'] == name].iloc[0]
                    vor_str = f"VOR {pdata['VOR']:.1f}" if not pd.isna(pdata['VOR']) else "VOR N/A"
                    roster_text.append(f"  • {name} | {vor_str}")
                roster_text.append("")
    else:
        roster_text.append("No players drafted yet")
    manual_count = len(draft_state.get_manual_picks())
    if manual_count:
        roster_text.append(f"📝 Manual picks: {manual_count}")

    # Update UI elements (short labels)
    window['-RECOMMENDATIONS-'].update(recommendations)
    if hasattr(window, 'current_position_analysis'):
        window['-POSITION_ANALYSIS-'].update(window.current_position_analysis)
    else:
        window['-POSITION_ANALYSIS-'].update("Tap a position above to see details.")
    if hasattr(window, 'current_player_analysis'):
        window['-PLAYER_ANALYSIS-'].update(window.current_player_analysis)
    else:
        window['-PLAYER_ANALYSIS-'].update("Tap a position above to see ceiling analysis.")
    window['-CURRENT_ROSTER-'].update("\n".join(roster_text))

    current_round = (current_pick - 1) // TOTAL_TEAMS + 1
    window['-CURRENT_PICK-'].update(f"#{current_pick}", text_color='#4CAF50')
    window['-CURRENT_ROUND-'].update(f"R{current_round}", text_color='#2196F3')
    window['-DRAFTED_COUNT-'].update(f"{len(all_drafted)}", text_color='#FF9800')
    window['-YOUR_TURN-'].update("YES" if is_my_turn else "NO",
                                 text_color=('#4CAF50' if is_my_turn else '#F44336'))
    window['-MANUAL_PICKS-'].update(f"{manual_count} picks added")
    
    # Update header status for better visibility
    if is_my_turn:
        window['-HEADER_STATUS-'].update("🎯 YOUR TURN!", text_color='#4CAF50')
    else:
        picks_until = draft_state.get_next_my_pick() - current_pick
        window['-HEADER_STATUS-'].update(f"⏳ Next pick: #{draft_state.get_next_my_pick()} ({picks_until} away)", 
                                        text_color='#FF9800')


def show_position_analysis(df, drafted, position):
    all_drafted = draft_state.get_all_drafted()
    available_df = df[~df['Player'].isin(all_drafted)]
    pos_data = available_df[available_df['Position'] == position].sort_values('VOR', ascending=False).head(10)

    tier_icon = {1: '🟢', 2: '🟡', 3: '🟠'}
    lines = [f"{position} — Top by VOR", ""]
    if len(pos_data) == 0:
        lines.append("No players available.")
    else:
        for i, (_, p) in enumerate(pos_data.iterrows(), 1):
            icon = tier_icon.get(p['Tier'], '🔴')
            adp_str = f"ADP {p['ADP']}" if not pd.isna(p['ADP']) and p['ADP'] != 'NA' else "ADP N/A"
            lines.append(f"{icon} {i}. {p['Player']} | VOR {p['VOR']:.1f} | T{p['Tier']} | {adp_str}")
    return "\n".join(lines)


def show_player_analysis(df, drafted, position=None):
    """Show top 10 players by ceiling with detailed stats"""
    all_drafted = draft_state.get_all_drafted()
    available_df = df[~df['Player'].isin(all_drafted)]
    
    if position:
        # Show specific position
        pos_data = available_df[available_df['Position'] == position].sort_values('ceiling', ascending=False).head(10)
        title = f"Top 10 by Ceiling"
    else:
        # Show all positions
        pos_data = available_df.sort_values('ceiling', ascending=False).head(10)
        title = "All Positions — Top 10 by Ceiling"
    
    tier_icon = {1: '🟢', 2: '🟡', 3: '🟠'}
    lines = [title, ""]
    
    if len(pos_data) == 0:
        lines.append("No players available.")
    else:
        # Header with better alignment
        lines.append("Rank | Name            | Floor | Points | Ceiling | Tier | VOR")
        lines.append("-" * 70)
        
        for i, (_, p) in enumerate(pos_data.iterrows(), 1):
            icon = tier_icon.get(p['Tier'], '🔴')
            points = f"{p['points']:.0f}" if not pd.isna(p['points']) else "N/A"
            floor = f"{p['floor']:.0f}" if not pd.isna(p['floor']) else "N/A"
            ceiling = f"{p['ceiling']:.0f}" if not pd.isna(p['ceiling']) else "N/A"
            vor = f"{p['VOR']:.1f}" if not pd.isna(p['VOR']) else "N/A"
            
            # Better column alignment
            lines.append(f"{icon} {i:2d} | {p['Player']:<16} | {floor:>5} | {points:>6} | {ceiling:>7} | T{p['Tier']} | {vor:>5}")
    
    return "\n".join(lines)


def main():
    window = create_main_window()

    while True:
        event, values = window.read(timeout=5000)

        if event == sg.WIN_CLOSED or event == '-EXIT-':
            break

        drafted = get_drafted_players()
        update_main_window(window, df, drafted, draft_state.current_pick, draft_state.get_manual_picks())

        if event == '-ADD_PICK-':
            if draft_state.is_my_pick():
                sg.popup("It's your pick. The player you add goes to YOUR roster.", title="Your Turn")

            # Get current drafted players for the window
            current_drafted = draft_state.get_all_drafted()
            pick_window = create_manual_pick_window(df, current_drafted, draft_state.current_pick)

            while True:
                pe, pv = pick_window.read()
                if pe in (sg.WIN_CLOSED, '-CLOSE-'):
                    break

                refresh_needed = False

                if pe == '-ADD_ALL-':
                    if pv.get('-ALL_LIST-'):
                        selected = pv['-ALL_LIST-']
                        added = 0
                        # Get fresh available players (excluding newly drafted ones)
                        current_drafted = draft_state.get_all_drafted()
                        avail = df[~df['Player'].isin(current_drafted)].sort_values('ADP', ascending=True)
                        
                        for s in selected:
                            try:
                                num = int(s.split('.')[0].strip())
                                if 1 <= num <= len(avail):
                                    row = avail.iloc[num - 1]
                                    name = row['Player']
                                    if draft_state.is_my_pick():
                                        draft_state.add_to_roster(name)
                                        sg.popup(f"Added {name} to YOUR roster.", title="Added")
                                    else:
                                        draft_state.add_manual_pick(name)
                                    added += 1
                            except Exception as e:
                                print(f"Error adding player: {e}")
                                continue
                        if added:
                            sg.popup(f"Added {added} player(s).")
                            refresh_needed = True

                elif pe.startswith('-ADD_') and pe.endswith('-'):
                    pos = pe[5:-1]
                    key = f'-{pos}_LIST-'
                    if pv.get(key):
                        selected = pv[key]
                        added = 0
                        # Get fresh available players (excluding newly drafted ones)
                        current_drafted = draft_state.get_all_drafted()
                        avail = df[~df['Player'].isin(current_drafted)]
                        pos_df = avail[avail['Position'] == pos].sort_values('ADP', ascending=True)
                        
                        for s in selected:
                            try:
                                num = int(s.split('.')[0].strip())
                                if 1 <= num <= len(pos_df):
                                    row = pos_df.iloc[num - 1]
                                    name = row['Player']
                                    if draft_state.is_my_pick():
                                        draft_state.add_to_roster(name)
                                        sg.popup(f"Added {name} to YOUR roster.", title="Added")
                                    else:
                                        draft_state.add_manual_pick(name)
                                    added += 1
                            except Exception as e:
                                print(f"Error adding {pos}: {e}")
                                continue
                        if added:
                            sg.popup(f"Added {added} {pos}(s).")
                            refresh_needed = True

                if refresh_needed:
                    pick_window.close()
                    # Create new window with updated drafted players list
                    current_drafted = draft_state.get_all_drafted()
                    pick_window = create_manual_pick_window(df, current_drafted, draft_state.current_pick)

            pick_window.close()
            update_main_window(window, df, draft_state.get_all_drafted(), draft_state.current_pick, draft_state.get_manual_picks())

        elif event == '-CLEAR_PICKS-':
            if draft_state.get_manual_picks() or draft_state.get_your_roster():
                if sg.popup_yes_no(f"Clear all picks?\nManual: {len(draft_state.get_manual_picks())}\nYour roster: {len(draft_state.get_your_roster())}") == 'Yes':
                    draft_state.all_drafted_players.clear()
                    draft_state.your_roster.clear()
                    draft_state.manual_picks.clear()
                    draft_state.current_pick = 1
                    if hasattr(window, 'current_position_analysis'):
                        delattr(window, 'current_position_analysis')
                    sg.popup("Cleared.")

        elif event == '-SHOW_PICKS-':
            manual = draft_state.get_manual_picks()
            your = draft_state.get_your_roster()

            if not manual and not your:
                sg.popup("No picks yet.")
            else:
                txt = [f"Draft Status (Pick #{draft_state.current_pick})", ""]
                if your:
                    txt.append(f"YOUR ROSTER ({len(your)}):")
                    pbp = {}
                    for pl in your:
                        info = df[df['Player'] == pl]
                        if len(info) > 0:
                            pos = info.iloc[0]['Position']
                            pbp.setdefault(pos, []).append(pl)
                    for pos in ['QB', 'RB', 'WR', 'TE', 'K', 'DST']:
                        if pos in pbp:
                            txt.append(f"  {pos} ({len(pbp[pos])}):")
                            for i, pl in enumerate(sorted(pbp[pos]), 1):
                                info = df[df['Player'] == pl]
                                if len(info) > 0:
                                    adp = info.iloc[0]['ADP']
                                    adp_str = f"ADP {adp}" if not pd.isna(adp) and adp != 'NA' else "ADP N/A"
                                    txt.append(f"    {i}. {pl} | {adp_str}")
                            txt.append("")
                if manual:
                    txt.append(f"MANUAL PICKS ({len(manual)}):")
                    pbp = {}
                    for pl in manual:
                        info = df[df['Player'] == pl]
                        if len(info) > 0:
                            pos = info.iloc[0]['Position']
                            pbp.setdefault(pos, []).append(pl)
                    for pos in ['QB', 'RB', 'WR', 'TE', 'K', 'DST']:
                        if pos in pbp:
                            txt.append(f"  {pos} ({len(pbp[pos])}):")
                            for i, pl in enumerate(sorted(pbp[pos]), 1):
                                info = df[df['Player'] == pl]
                                if len(info) > 0:
                                    adp = info.iloc[0]['ADP']
                                    adp_str = f"ADP {adp}" if not pd.isna(adp) and adp != 'NA' else "ADP N/A"
                                    txt.append(f"    {i}. {pl} | {adp_str}")
                            txt.append("")
                avail = df[~df['Player'].isin(drafted)].sort_values('ADP', ascending=True)
                txt.append("NEXT UP (by ADP):")
                for i, (_, p) in enumerate(avail.head(10).iterrows(), 1):
                    adp_str = f"ADP {p['ADP']}" if not pd.isna(p['ADP']) and p['ADP'] != 'NA' else "ADP N/A"
                    txt.append(f"  {i}. {p['Player']} ({p['Position']}) | {adp_str} | VOR {p['VOR']:.1f}")
                sg.popup_scrolled("\n".join(txt), title="Draft Status", size=(60, 25))

        elif event == '-SHOW_ROSTER-':
            window.roster_visible = not window.roster_visible
            window['-ROSTER_FRAME-'].update(visible=window.roster_visible)
            
            # Update button text and color for visual feedback
            if window.roster_visible:
                window['-SHOW_ROSTER-'].update('👥 Hide Roster', button_color=('white', '#4CAF50'))
            else:
                window['-SHOW_ROSTER-'].update('👥 Show Roster', button_color=('white', '#2196F3'))
            
            # Force layout refresh to properly resize content
            window.refresh()

        elif event == '-REFRESH-':
            try:
                if not TEST_MODE:
                    global league
                    league = League(league_id=LEAGUE_ID, year=YEAR, espn_s2=ESPN_S2, swid=SWID)
                    sg.popup("Refreshed ESPN connection.")
                else:
                    sg.popup("Refreshed (TEST MODE).")
            except Exception as e:
                sg.popup(f"Refresh error: {e}")

        elif event == '-DEBUG-':
            info = [
                f"League ID: {LEAGUE_ID}",
                f"Year: {YEAR}",
                f"Slot: {YOUR_DRAFT_SLOT + 1}",
                f"Teams: {TOTAL_TEAMS}",
                f"Pick: {draft_state.current_pick}",
                f"My Pick Now: {draft_state.is_my_pick()}",
                f"Next My Pick: {draft_state.get_next_my_pick()}",
                f"Roster: {len(draft_state.get_your_roster())}",
                f"Manual: {len(draft_state.get_manual_picks())}",
                f"All Drafted: {len(draft_state.get_all_drafted())}"
            ]
            sg.popup_scrolled("\n".join(info), title="Debug", size=(50, 20))

        elif event in ['-QB_ANALYSIS-', '-RB_ANALYSIS-', '-WR_ANALYSIS-', '-TE_ANALYSIS-']:
            position = {'-QB_ANALYSIS-': 'QB', '-RB_ANALYSIS-': 'RB',
                        '-WR_ANALYSIS-': 'WR', '-TE_ANALYSIS-': 'TE'}[event]
            analysis = show_position_analysis(df, drafted, position)
            window['-POSITION_ANALYSIS-'].update(analysis)
            window.current_position_analysis = analysis

        elif event == '-OVERALL_ANALYSIS-':
            if hasattr(window, 'overarching_analysis'):
                sg.popup_scrolled(window.overarching_analysis, title="Overall", size=(80, 25))
            else:
                sg.popup("No analysis yet. Hit Refresh.")

        elif event in ['-QB_PLAYER_ANALYSIS-', '-RB_PLAYER_ANALYSIS-', '-WR_PLAYER_ANALYSIS-', '-TE_PLAYER_ANALYSIS-']:
            position = {'-QB_PLAYER_ANALYSIS-': 'QB', '-RB_PLAYER_ANALYSIS-': 'RB',
                        '-WR_PLAYER_ANALYSIS-': 'WR', '-TE_PLAYER_ANALYSIS-': 'TE'}[event]
            analysis = show_player_analysis(df, drafted, position)
            window['-PLAYER_ANALYSIS-'].update(analysis)
            window.current_player_analysis = analysis

        elif event == '-ALL_PLAYER_ANALYSIS-':
            analysis = show_player_analysis(df, drafted)
            window['-PLAYER_ANALYSIS-'].update(analysis)
            window.current_player_analysis = analysis

    window.close()


if __name__ == "__main__":
    main()

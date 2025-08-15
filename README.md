# 🏈 ESPN Draft Assistant

A sophisticated fantasy football draft recommendation system using **Value-Based Drafting (VBD)** with dynamic ADP penalties and scoring format prioritization.

## 🧠 How the Engine Works

### **VOR-Based Scoring (90% of total score)**
```python
score = (
    vor * 0.75 +                    # Base VOR (75%)
    ceiling_vor * 0.10 +            # Ceiling VOR (10%)
    floor_vor * 0.10 +              # Floor VOR (10%)
    vor * (tier_multiplier - 1.0) + # Tier bonus (scales with VOR)
    dropoff_bonus +                 # Cliff detection
    adp_value +                     # Market value
    - uncertainty_penalty +         # Risk management
    opportunity_cost +              # Opportunity cost analysis
    positional_adjustment +         # Roster balance
    round_adjustment               # Floor/ceiling preference
)
```

### **Dynamic ADP Reach Penalties**
- I configured a dynamic ADP reach penalty to ensure the user is still drafting closer to market trends. I read this interesting [article](https://fantasyfootballanalytics.net/2015/03/fantasy-football-is-like-stock-picking.htmlhttps://fantasyfootballanalytics.net/2015/03/fantasy-football-is-like-stock-picking.html) that draft selection is like picking stocks which was really interesting to me.
- **Early Picks (1-36)**: 1.5x penalty multiplier, stricter thresholds
- **Mid Picks (37-84)**: Standard penalties  
- **Late Picks (85+)**: 0.7x penalty multiplier, more lenient thresholds

### **Scoring Format Prioritization**
- **Non-PPR**: Prioritizes RBs, penalizes WRs slightly
- **Half-PPR**: Boosts WRs, adjusts TE values
- **Position weights** scale with actual VOR values

### **Z-Score Style Urgency**
- The new methodology is to not compare value over replacement absolutely because running backs on average, possess a higher mean VOD. So, now we analyze intra-positionally
which players might be drafted (based on composite ADP) in between your next pick. This produces an urgency value, what position will you benefit from the most given
your roster composition and the available players. This factors in the standard deviations from the FFAnalysis data set.

## 🔌 ESPN API Connection

### **Authentication**
Uses ESPN's cookie-based authentication by going into the developer tools (fn + f12):
- `espn_s2`: Session cookie from browser
- `SWID`: User identification cookie
- `league_id`: Extracted from ESPN URL

### **Data Sources**
1. **Direct Draft Picks**: `league.draft` endpoint
2. **Team Rosters**: `league.teams[].roster` (most reliable during live draft)
3. **Draft Recap**: ESPN's `mDraftDetail` endpoint (best for mock drafts)
4. **League Settings**: Fallback for draft status

### **Main Data Used**
- I utilized this [data source](https://apps.fantasyfootballanalytics.net/) from FFAnalytics, I really enjoy that their projections are not just a singular number, but have variance, cutoff, VOR, and a range of numbers over simulations. Their methodology is really interesting when it comes to optimizing your draft strategy.

### **Connection Setup**
```bash
# Automated setup
python src/setup_mock_draft.py

# Manual setup
# Edit src/config.py with your credentials
```

## 🎮 Manual Mode

### **GUI Interface**
- **Real-time updates**: Live draft status and recommendations
- **Position analysis**: Detailed breakdowns by position
- **Floor, Projected Points, Ceiling Tab** View which available players have the highest ceiling and assess your own risk of drafting those 
- **Manual pick system**: Tabbed interface for marking drafted players
- **Auto-refresh**: Window updates after adding players

### **Features**
- **50 players per position** in manual pick tabs
- **60 players** in "All Positions" tab
- **Color-coded tiers**: 🟢🟡🟠🔴 for easy identification
- **Legend panel**: Explains all emoji indicators

### **Usage**
```bash
# GUI Version (Recommended)
python src/main_gui.py

# Console Version  
python src/main.py

# Test Mode (No ESPN connection)
# Set TEST_MODE = True in src/main_gui.py
```

## 📊 Data Requirements

### **Projections**
-The projections are from [FFAnalytics](https://apps.fantasyfootballanalytics.net/), so no importing of csv necessary 
```

## ⚙️ Configuration

### **League Settings**
```python
LEAGUE_ID = 123456789
YOUR_DRAFT_SLOT = 5  # 0-based (5 = pick 6)
TOTAL_TEAMS = 12
```

### **Scoring Format**
```python
from config import set_league_type
set_league_type('non_ppr')    # or 'half_ppr'
```
- Everything you may need is found in the config.py file

## 🚀 Quick Start

1. **Install dependencies**: `pip install -r requirements.txt`
2. **Setup ESPN connection**: `python src/setup_mock_draft.py`
3. **Test connection**: `python src/tests/test_espn_connection.py`
4. **Run draft assistant**: `python src/main_gui.py`

## 📁 Project Structure

```
espn-draft-tracker/
├── src/
│   ├── main_gui.py              # GUI application
│   ├── main.py                  # Console version
│   ├── config.py               # Configuration
│   ├── recommendation_engine.py # VOR-based engine
│   ├── data_loader.py          # Data loading
│   ├── draft_analyzer.py       # Draft analysis
│   ├── utils/                  # Utility scripts
│   └── tests/                  # Test suite
├── projections_*.csv           # Data files
└── requirements.txt            # Dependencies
```

## 🏆 Key Features

## 🎯 Advanced Recommendation Engine
- **Two-Layer Position-First Strategy**: Prioritizes positions based on urgency, then selects best players within that position
- **Dynamic Position Urgency**: Calculates real-time position scarcity using within-position normalization and opportunity cost analysis
- **Composite Scoring System**: 70% VOR + 15% Tier Bonus + 10% Cliff Bonus + 5% ADP Value + Risk/Round Adjustments

## 🧠 Strategic Analysis & Insights
- **Position Urgency Breakdown**: Detailed analysis of opportunity cost, cliff pressure, roster needs, and early-QB penalties
- **Risk-Adjusted Scoring**: Floor/ceiling analysis with round-specific risk preferences (floor early, ceiling late)
- **Cliff Detection**: Identifies significant VOR dropoffs (>20 points) to protect against positional scarcity
- **Strategic Insights**: Real-time analysis of tier scarcity, position depth, and value opportunities

## 🎲 Advanced Player Analytics
- **Ceiling/Floor Analysis**: Top 10 players by ceiling with detailed floor/ceiling/points breakdown
- **Uncertainty Scoring**: Risk assessment based on player volatility and projection uncertainty
- **ADP Value Analysis**: Reach cost calculations and value opportunity identification
- **Tier-Based Visualization**: Color-coded tiers (🟢🟡🟠🔴) with cliff and early-QB indicators

## ⚙️ Scoring Format Intelligence
- **PPR/Half-PPR/Non-PPR Awareness**: Automatic data source switching and position weight adjustments
- **Position-Specific Weighting**: Dynamic multipliers based on league type and positional scarcity
- **Reception Value Integration**: Proper PPR adjustments for WR/TE value calculations

## 🔄 Real-Time Draft Integration
- **Live ESPN Connection**: Automatic draft state updates with fallback to manual mode
- **Snake Draft Logic**: Accurate pick prediction and turn tracking
- **Auto-Refresh**: Continuous updates after adding players or refreshing data
- **Draft State Management**: Comprehensive tracking of drafted players, roster composition, and pick timing

## 📈 Enhanced Position Analysis
- **Position-Specific Insights**: Detailed analysis for QB/RB/WR/TE with tier breakdowns and risk profiles
- **Roster Need Analysis**: Critical/high/medium priority recommendations based on starting lineup requirements
- **FLEX Position Optimization**: Smart recommendations considering RB/WR/TE flex eligibility
- **Depth Analysis**: Real-time assessment of position scarcity and tier availability

## 🎮 User Experience Features
- **Modern Dark UI**: Professional interface with collapsible sections and intuitive controls
- **Visual Status Indicators**: Color-coded urgency levels and turn notifications
- **Manual Pick System**: Comprehensive GUI for testing without ESPN connection
- **Debug & Analytics**: Detailed breakdowns of scoring calculations and strategic reasoning

--- Created by Harrison Dolgoff, thank you to FFAnalytics for the open source data set and ESPNApi for connecting to live ESPN draft data

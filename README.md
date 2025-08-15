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
- I utilized this data source

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

### **CSV Format**
```csv
Player,Position,VOR,Tier,ADP,ceiling,floor,uncertainty
Josh Allen,QB,88.6,1,18.1,95.2,82.1,15.3
```

### **Supported Files**
- `projections_non_ppr.csv`: Non-PPR projections
- `projections_half_ppr.csv`: Half-PPR projections

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

- **VOR-First Approach**: 90% of score based on Value Over Replacement
- **Dynamic ADP Penalties**: Scales with draft position
- **Scoring Format Awareness**: Adjusts for PPR vs Non-PPR
- **Real-time ESPN Integration**: Live draft data
- **Manual Mode**: GUI for testing without ESPN
- **Auto-refresh**: Updates after adding players
- **Color-coded Tiers**: Visual player quality indicators

---

**Ready to dominate your fantasy football draft!** 🏈⚡

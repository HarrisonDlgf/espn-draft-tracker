# 🏈 ESPN Draft Assistant

The draft assistant analyzes historical fantasy football trends and factors in projections for the upcoming football season to become the
best draft companion possible. The program is meant to recommend what position to draft next, and give the user a range 
of recommended players within that scope. 

Built for on the clock urgency and live synced updating after every pick.


## 📌 Table of Contents
- [Who This Is For](#who-this-is-for)
- [What It Does](#what-it-does)
- [How The Engine Decides](#how-the-engine-decides)
- [How To Use This in a Real Draft](#how-to-use-this-in-a-real-draft)
- [How to navigate](#how-to-navigate)
- [The Data Source](#the-data-source)
- [How the Data Is Formatted](#how-the-data-is-formatted)
- [The Math](#the-math)
- [Project Structure](#-project-structure)
- [Final Disclaimer and Thanks](#final-disclaimer-and-thanks)

## Who This Is For
This is built for fantasy football players who want confidence and direction in their drafting strategy, rather than solely rankings

Casual players: You want help making picks from a high-level strategy standpoint. The idea of drafting an entire roster
without prior knowledge of how to do well is daunting, however, I hope this allows you to be able to retain some autonomy in your 
drafting process while still guiding you towards well-informed picks that will improve your chances of winning it all!

Competitive players: This type of player may already use rankings websites, knows a lot about average draft positions and tiers, but 
wants to add a tool that factors in the drafting habits of your leaguemates and what position may be the most valuable to take.

Builders/Contributions/Data Scientists: The option to contribute makes this project more meaningful to me as open-source projects always
end up being better. I attempted to share all of my passion for coding and fantasy football within this project, so I hope to allow others who 
want to code a clear blueprint on how to tune this to your own liking and the option to extend this codebase into something more.

#### Some Common Use Cases
- I don't want to reach early on this player but I want high upside
- I don't know when to draft quarterbacks because they seem so valuable
- My next pick is so far away, what position will not be on the board when it is my turn?

#### 🎮 User Experience Features
- **Modern Dark UI**: Professional interface with collapsible sections and intuitive controls
- **Visual Status Indicators**: Color-coded urgency levels and turn notifications
- **Manual Pick System**: Comprehensive GUI for testing without ESPN connection
- **Debug & Analytics**: Detailed breakdowns of scoring calculations and strategic reasoning

## What It Does
There are two decisions every time a user picks a player in fantasy football: <i> What position and who? </i>

When people go to ice cream stores with a million flavors, it can sometimes seem impossible to choose. That same thing happens to me in fantasy football drafts, so
I put position analysis at the forefront of the recommendation engine.

#### Recommendation Engine
- Position urgency recommendation
    The engine will recommend what position is most costly to wait on: in other words, even if there are some very talented players of one position available,
    it may be more important to take a different position due to the scarcity.

- Top players within that position:
    A ranked list with how much potential they possess, their projected worse possible outcome, and an average outcome for a player with that profile.

- Context Clues
    The context clues indicate whether there is time sensitive decisions to make; such as if there are large cliffs in availability, the engine hopes to make clear the urgency to take specific players. Also, if your roster composition requires strengthing in certain areas, it may be in your best interest to draft in an unusual sense.

#### How The User Sees This (UI Behavior)
- Updated recommendations after every pick
- Icons/Emojis for drop-offs
- Color Coding and Status Messages

## How The Engine Decides
The core concept centers on two layers of strategy; position urgency and player scoring
- What position is going to get worse <b> the fastest </b> before my next pick?
- Now that I have picked that position, who gives me the best chance given risk, tiers, and ADP?

#### Why This is Different
My goal was to give you autonomy in your final decision after giving the user an array of options. By recommending a position, the end user
may then select who they think best fits their needs. Most lists compare players across positions however I attempt to compare players using relative value within
their own positions. Then, when listing the available options, the engine utilizing a projection data source that predicts (across 10,000 simulations) the selected player's
floor (their worst case scenario), their projection (average outcome), and ceiling (their best case).

## How To Use This in a Real Draft
### 🚀 Quick Start

1. **Install dependencies**: `pip install -r requirements.txt`
2. **Setup ESPN connection**: `python src/setup_mock_draft.py`
3. **Test connection**: `python src/tests/test_espn_connection.py`
4. **Run draft assistant**: `python src/main_gui.py`

1. Run this command in your terminal by opening a terminal
```bash
python src/main_gui.py
```
2. Configure your league settings
Set the scoring format 
#### ⚙️ Configuration

#### **League Settings**
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

3. ESPN Live Sync (UNDER CONSTRUCTION)
Instructions for this are not needded as of right now, due to API issues
But essentially:
### 🔌 ESPN API Connection

**Authentication**
Uses ESPN's cookie-based authentication by going into the developer tools (fn + f12):
- `espn_s2`: Session cookie from browser
- `SWID`: User identification cookie
- `league_id`: Extracted from ESPN URL

**Data Sources**
1. **Direct Draft Picks**: `league.draft` endpoint
2. **Team Rosters**: `league.teams[].roster` (most reliable during live draft)
3. **Draft Recap**: ESPN's `mDraftDetail` endpoint (best for mock drafts)
4. **League Settings**: Fallback for draft status

4. During the draft
Recommendations update automatically after each pick. You must enter your own picks in the GUI. Use the "➕ Add Pick" to manually mark picks 

5. Make your pick
Review recommendations, check position analysis, and select your player

## How to navigate
Position Analysis Panel:
- By Position: Click QB/RB/WR/TE buttons to see top 10 players at that position
- Overall Analysis: Shows position urgency breakdown for all positions
- Urgency scores (higher = more urgent)
- Drafted count vs. position limits
- Roster needs (critical/high/medium/low priority)
### Visual Indicators:
🟢 Tier 1: Elite players (highest value)
🟡 Tier 2: Strong players
🟠 Tier 3: Solid players
🔴 Tier 4+: Lower-tier players
📉 Cliff: Large dropoff detected (positional scarcity warning)
⏰ Early QB: QB recommended too early (penalty applied)


## The Data Source
- The program utilizes this [data source](https://apps.fantasyfootballanalytics.net/) from FFAnalytics. The projections are not just a singular number, but have variance, cutoff, VOR, and a range of numbers over simulations. Their methodology optimizes your draft strategy by allowing you to make statistics based decisions and understand the probablity of outcomes.

Due to the wide range of data, I was able to provide lots of advanced analytics.

#### 🎲 Advanced Player Analytics
- **Ceiling/Floor Analysis**: The top 10 players sorted by their ceiling with detailed breakdown on their range of potential outcomes
- **Uncertainty Scoring**: An uncertainty score provides depth into the risk assessment on each players which is based on player volatility and projection uncertainty
- **ADP Value Analysis**: Reach cost calculations and value opportunity identification
- **Tier-Based Visualization**: Color-coded tiers (🟢🟡🟠🔴) with cliff and indicators if it is too early to take certain positions

## How the Data Is Formatted
- points: baseline projection
- floor: the projected **worse** case scenario of total points a player may accumulate over a season (excluding injury)
- ceiling: the projected **best** case scenario of total points a player may accumulate over a season (excluding injury)
- uncertainty: a penalty based on the variability this player may experience
- tier: The player quality tier, the lower the number is, the more elite of a status that player tends to maintain.
- ADP (average draft position): The market consensus draft position of that players, aggregated across multiple platforms and mostly calculated from mock drafts from real users.
- dropoff: the value drop to the next player at that position; used to detect urgency and cliffs.
- sd_pts: the standard deviation of points utilized as a measure of volatility 
- cliff_bonus: The bonus for players with large dropoffs meant to protect users from positional scarcity.
- adp_value: A bonus for players that go later than expected as it may be beneficial to go with public consensus at times
- composite_score: An overall value rankings for relative position comparisons
```python
composite_score = 
    vor_score +                    # 70% weight
    tier_bonus * 0.15 +           # 15% weight
    cliff_bonus * 0.10 +           # 10% weight
    adp_value * 0.05 +             # 5% weight
    risk_tilt -                    # Round-dependent
    reach_cost                     # Penalty
```
- VOR stands for value over replacement, essentially acting as an overview on how valuable a player is projected to be compared to the average replacement.
The final score weights the VOR very heavily while factoring in other variables:
### **VOR-Based Scoring (70% of total score)**
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

## The Math 
Here comes the methodology behind the recommendation engine. There is not a lot of advanced techniques behind this, and I would love to receive feedback 
on improvements or additions with machine learning to optimize performance. 
#### Position Urgency
Urgency determines how much value you lose at a position if you wait until a further pick to choose this position. The system employed a within-position normalization process to compare positions fairly. Normalization levels the comparison field so decisions can be comparable while otherwise harder to do so (attempting to compare apples to oranges). However, the engine attempts to favor RBs and WRs more as they tend to be the main reason people win fantasy championships. After normalizing the positional VOR distribution, the engine measures how the best available player degrades relative to that position. 
    - Breakdown
        - Opportunity Cost (60% of the weight)
            - Measures how important it is to take that player now compared to their replacements at a further point in time. The logic here utilizes percentile ranks within that
            position (e.g if the 10th percentile RB drops to the 22nd percentile), that registers as a 12 point loss in relative value. By capturing the cost of waiting, the present decision is weighted properly. 
        - Cliff Pressure (25% weight)
            - Adds urgency when there is a **significant** dropoff to the next tier of player. If a decision is urgent, then it must be made now. This normalizes dropoff values,
            but caps the maximum when the change is over 25 VOR points, to protect the user from positional scarcity. A large cliff indicates that waiting leaves you with weak options
        - Roster Need (15 % weight)
            - If the urgency for a position is critical, but you don't need them nor the depth, then this roster need calculation accounts for that. This prioritizes filling starter requirements and proper FLEX depth (RB/WR/TE) based on your scoring format.
        - Early QB Penalty
            - This constant reduction encourages users not to draft QBs too early if the advantage is not significant as empirical evidence points to the strategy of drafting a QB in a 1-QB league can be detrimental to your chances. 
#### Player Score
Player scoring ranks candidates within selected filters using their value, tiers, cliffs, ADP, and round specific risk preferences. Once a position is selected, players are then
scored within that position only. This avoids cross-position VOR bias and lets you compare players on a level playing field. The composite score from above includes the formula for this.
| Round | Phase	| Formula Strategy
| ---|---|---|
|Early (1-5)|	(floor - vor) * 0.2 - uncertainty * 0.1|Prefer floor and consistency|
|Mid (6-8)|	((floor + ceiling) / 2 - vor) * 0.1 - uncertainty * 0.05|	Balanced approach|
|Late (9+)|	(ceiling - vor) * 0.2 - uncertainty * 0.05	|Prefer ceiling and upside|
Early rounds favor safe, high-floor players. Mid rounds balance floor and ceiling. Late rounds favor high-ceiling players. Therefore, any uncertainty is penalized more in early rounds.
- Reach Costs
These are meant to be a guardrail rather than a strict rule to adhere to. This discourages reaching too far above a player's ADP but some exceptions do exist such as:
    - Large dropoffs
    - Critical roster needs
    - Elite tier players

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
- The new methodology is to not compare value over replacement absolutely because running backs on average, possess a higher mean VOR. So, now we analyze intra-positionally
which players might be drafted (based on composite ADP) in between your next pick. This produces an urgency value, what position will you benefit from the most given
your roster composition and the available players. This factors in the standard deviations from the FFAnalysis data set.

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

## Final Disclaimer and Thanks
First and foremost, projections are not guarantees. This tools depends on statistical projections based on historical data and simulations. However,
projections are merely a reflection of probabilities, not reliabilities. They are the expected outcomes and not the certanities. Player performance will vary for some many reasons, this tool is meant to support decision making, not replace it. Use recommendatinos as one input amonge many.
Also, currently there is no injury projections therefore it is hard to factor that into the engine's decision making even though it is a big part of fantasy football.
The algorithm is also limited in its current state as it is meant for single quarterback leagues and only support half PPR and non-PPR. Hopefully, with others contributions,
this tool can expand to superflex, auction, keeper, dynasty, full PPR, and more league options. 
This engine also depends only FFAnalytics for projection data and if they change their data format or stop providing data, this system will need lots of adjustment. There is no guarantee in results, but it is very fun to try.

Use at your own discretion, contribute if you'd love to help, and most of all: Have fun!
--- Created by Harrison Dolgoff, thank you to FFAnalytics for the open source data set and ESPNApi for connecting to live ESPN draft data
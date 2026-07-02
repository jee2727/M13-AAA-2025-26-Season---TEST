# Player Stats Extraction & Aggregation Structure

This document describes the complete structure for extracting player statistics from game PDF sheets and populating them to the GitHub Pages website.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    Game PDF Sheet                            │
│              (from LHEQ / Spordle)                           │
└────────────────────────┬────────────────────────────────────┘
                         │
                    extract_stats.py
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│            Individual Game JSON Files                        │
│              data/games/*.json                              │
│  (date, teams, scores, player stats)                        │
└────────────────────────┬────────────────────────────────────┘
                         │
         ┌───────────────┼───────────────┐
         │               │               │
         ▼               ▼               ▼
   data_validator.py  build_index.py  stats_aggregator.py
         │               │               │
         ▼               ▼               ▼
   [Validation]   [Index Building]  [Stats Compilation]
         │               │               │
         ▼               ▼               ▼
   (validates)   games-index.js   aggregated_stats.json
                         │               │
                         │               │
         ┌───────────────┴───────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────┐
│          GitHub Pages Website (docs/)                        │
│                                                               │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ index.html (template)                               │   │
│  └──────────────────────────────────────────────────────┘   │
│         │                                                    │
│    ┌────┴──────────────────────────────────────────────┐    │
│    │                                                   │    │
│    ▼                                                   ▼    │
│  app.js (client-side aggregation)      games-index.js     │
│  • Loads game JSON files               (game file list)    │
│  • Aggregates stats                                        │
│  • Renders tables/cards                                    │
│                                                            │
│    ┌────────────────────────────────────────────────────┐   │
│    │ Rendered Output:                                   │   │
│    │ • Season Totals (sortable table)                  │   │
│    │ • Game Log (card grid with top scorers)           │   │
│    └────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

## Data Flow

### 1. **Extraction Phase** (`extract_stats.py`)
- **Input**: Game PDF sheet (from LHEQ/Spordle)
- **Output**: Game JSON file in `data/games/`
- **Process**:
  - Downloads PDF from URL or uses local file
  - Parses PDF tables to extract player statistics
  - Extracts date, team names, scores
  - Saves structured JSON with player stats

**Example usage**:
```bash
# From LHEQ game page
python scripts/extract_stats.py "https://masculin.lheq.ca/fr/schedule/614322"

# From PDF URL
python scripts/extract_stats.py "https://example.com/sheet.pdf"

# From local file
python scripts/extract_stats.py ~/Downloads/sheet.pdf
```

### 2. **Validation Phase** (`data_validator.py`)
- **Input**: All JSON files in `data/games/`
- **Output**: Validation report
- **Process**:
  - Checks JSON structure validity
  - Verifies required fields (date, teams, players)
  - Validates data types and value ranges
  - Reports any issues found

**Example usage**:
```bash
python scripts/data_validator.py
python scripts/data_validator.py --strict  # Fail on errors
```

### 3. **Aggregation Phase** (`stats_aggregator.py`)
- **Input**: All JSON files in `data/games/`
- **Output**: `data/aggregated_stats.json`
- **Process**:
  - Loads all game files
  - Aggregates player statistics across games
  - Compiles team performance stats
  - Generates ordered lists (by points, wins, etc.)

**Example usage**:
```bash
python scripts/stats_aggregator.py
```

### 4. **Index Building Phase** (`build_index.py`)
- **Input**: All JSON files in `data/games/`
- **Output**: `docs/js/games-index.js` + `data/aggregated_stats.json`
- **Process**:
  - Scans `data/games/` for all `.json` files
  - Generates JavaScript array of filenames
  - Triggers stats aggregation
  - Called by CI/CD pipeline on every push

**Example usage**:
```bash
python scripts/build_index.py
```

### 5. **Website Rendering Phase** (Client-side JavaScript)
- **Input**: `games-index.js` + all game JSON files
- **Output**: Rendered website
- **Process**:
  - `app.js` loads games asynchronously
  - Aggregates stats in browser (fallback approach)
  - Renders season totals table (sortable)
  - Renders game cards with top scorers
  - Styling applied from `style.css`

## File Structures

### Game JSON Format
```json
{
  "date": "2025-10-05",
  "home_team": "M13 AAA Bears",
  "away_team": "Rival Hawks",
  "home_score": 4,
  "away_score": 2,
  "players": [
    {
      "team": "M13 AAA Bears",
      "number": "11",
      "name": "John Doe",
      "goals": 1,
      "assists": 2,
      "points": 3,
      "pim": 2
    }
  ]
}
```

### Aggregated Stats Format
```json
{
  "meta": {
    "total_games": 7,
    "total_players": 206,
    "total_teams": 14
  },
  "players": [
    {
      "name": "Player Name",
      "team": "Team Name",
      "number": "11",
      "gp": 7,
      "goals": 15,
      "assists": 12,
      "points": 27,
      "pim": 8
    }
  ],
  "teams": [
    {
      "name": "Team Name",
      "games_played": 7,
      "wins": 5,
      "losses": 2,
      "goals_for": 28,
      "goals_against": 18,
      "total_points": 12
    }
  ],
  "games": [
    { /* game objects */ }
  ]
}
```

### Games Index Format (`docs/js/games-index.js`)
```javascript
const GAMES_INDEX = [
  "2025-09-13_Lions_Black_vs_Vert_Noir_Ecole_Fadette.json",
  "2025-10-04_Rival_Hawks_vs_M13_AAA_Bears.json"
];
```

## Workflow Integration

### GitHub Actions (`deploy-pages.yml`)
The CI/CD pipeline automatically:
1. Triggers on any push to `main` branch
2. Runs `build_index.py` (which calls `stats_aggregator.py`)
3. Commits updated `games-index.js` if changed
4. Deploys `docs/` directory to GitHub Pages

## Complete Workflow

### To add a new game:

1. **Extract stats from PDF**:
   ```bash
   python scripts/extract_stats.py "https://masculin.lheq.ca/fr/schedule/614322"
   ```
   Creates: `data/games/2025-10-04_Teams_vs_Teams.json`

2. **Validate the data** (optional):
   ```bash
   python scripts/data_validator.py
   ```

3. **Rebuild index and stats**:
   ```bash
   python scripts/build_index.py
   ```
   Updates:
   - `docs/js/games-index.js`
   - `data/aggregated_stats.json`

4. **Commit and push**:
   ```bash
   git add data/games/*.json data/aggregated_stats.json docs/js/games-index.js
   git commit -m "Add game: 2025-10-04_Teams_vs_Teams"
   git push origin main
   ```

5. **Website auto-deploys** via GitHub Actions

6. **Visit the site**: `https://<username>.github.io/M13-AAA-2025-26-Season---TEST/`

## Key Features

✅ **Automated Data Extraction**
- Parses LHEQ/Spordle PDF game sheets
- Extracts player stats, team names, scores, dates
- Handles both team rosters automatically

✅ **Data Validation**
- Checks JSON structure and required fields
- Validates data types and value ranges
- Reports validation issues

✅ **Stats Aggregation**
- Combines stats across all games
- Tracks games played per player
- Computes team win-loss records
- Generates ranked lists (by points, wins, etc.)

✅ **Website Display**
- Season totals table (sortable by any column)
- Game log with top scorers per game
- Responsive design for mobile/desktop
- Dark theme with color-coded stats
- Auto-updates when new games are added

## Troubleshooting

### Stats not showing on website?
1. Verify JSON files exist: `ls data/games/`
2. Run validator: `python scripts/data_validator.py`
3. Rebuild index: `python scripts/build_index.py`
4. Check browser console for JavaScript errors

### Aggregated stats not updating?
1. Run `python scripts/stats_aggregator.py` manually
2. Check for errors in the script output
3. Verify JSON files have correct structure

### GitHub Pages not deploying?
1. Check repo Settings → Pages → Source is "GitHub Actions"
2. Look at GitHub Actions workflow run logs
3. Verify `docs/` directory contains all files
4. Try manual workflow dispatch in GitHub Actions UI

## Dependencies

- **pdfplumber** – PDF parsing and table extraction
- **requests** – HTTP downloads from LHEQ/Spordle
- **Python 3.9+** – Script runtime
- **No frontend dependencies** – Pure JavaScript + CSS


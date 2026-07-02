# M13 AAA – 2025–26 Season Stats

A set of tools to **download game-sheet PDFs from LHEQ / Spordle**, extract
individual player statistics (goals, assists, points, penalty minutes), store
them as JSON, and publish a live stats website on **GitHub Pages**.

---

## Project layout

```
.
├── data/
│   ├── games/               ← one JSON file per game (auto-generated)
│   └── aggregated_stats.json ← compiled stats across all games
├── docs/                    ← GitHub Pages website source
│   ├── index.html
│   ├── css/style.css
│   ├── data/
│   │   └── games/           ← games copied here for deployment
│   └── js/
│       ├── app.js
│       └── games-index.js        ← rebuilt automatically by CI
├── scripts/
│   ├── extract_stats.py          ← download PDF → extract stats → save JSON
│   ├── lheq_pdf_downloader.py    ← download PDFs from LHEQ game pages
│   ├── build_index.py            ← rebuild docs/js/games-index.js & stats
│   ├── stats_aggregator.py        ← compile stats from all games
│   ├── data_validator.py          ← validate game JSON structure
│   ├── test_integration.py        ← integration tests for the workflow
│   └── requirements.txt
├── STATS_STRUCTURE.md       ← detailed architecture & data flow
└── .github/workflows/
    └── deploy-pages.yml     ← CI: rebuild index + deploy site on every push
```

---

## Quick start

### 1. Install Python dependencies

```bash
pip install -r scripts/requirements.txt
```

### 2. Download PDFs from LHEQ game pages

For advanced use or debugging, use `lheq_pdf_downloader.py` to find and download PDFs directly from LHEQ game schedule pages:

```bash
# Game #1000 (gameId 614322)
python scripts/lheq_pdf_downloader.py 614322

# Specify output filename
python scripts/lheq_pdf_downloader.py 614322 --output game_1000.pdf

# Use Playwright if static HTML parsing fails (e.g., for JavaScript-heavy pages)
python scripts/lheq_pdf_downloader.py 614322 --method playwright
```

See [LHEQ_PDF_DOWNLOADER.md](LHEQ_PDF_DOWNLOADER.md) for full documentation.

### 3. Extract stats from a game-sheet PDF

The script supports three types of sources:

#### From an LHEQ game page (recommended)

Pass the LHEQ schedule URL directly – the script will auto-detect the game ID and fetch the PDF:

```bash
# Game #1000 (gameId 614322)
python scripts/extract_stats.py "https://masculin.lheq.ca/fr/schedule/614322?gameId=614322"
```

The script automatically:
1. Extracts the game ID from the URL
2. Constructs the PDF download URL
3. Downloads and parses the PDF
4. Saves the extracted stats to `data/games/`

#### From a direct PDF URL

```bash
python scripts/extract_stats.py https://example.spordle.com/game/12345/sheet.pdf
```

#### From a local PDF file

```bash
python scripts/extract_stats.py ~/Downloads/game_sheet.pdf
```

#### With a custom game ID

For any source, you can optionally specify how the output JSON file is named:

```bash
python scripts/extract_stats.py "https://masculin.lheq.ca/fr/schedule/614322?gameId=614322" \
  --game-id "2025-10-04_Game1000"
```

Without `--game-id`, the script auto-generates a filename like `2025-10-04_away_vs_home.json`.

### 4. Rebuild the website index

After adding one or more game JSON files, regenerate the index that the website
uses:

```bash
python scripts/build_index.py
```

This script will:
- Update `docs/js/games-index.js` with the list of game files
- Regenerate `data/aggregated_stats.json` with compiled player stats
- Validate all JSON files for structure correctness

### 6. Validate your game data

To check that all game JSON files have the correct structure:

```bash
python scripts/data_validator.py
```

Use `--strict` to fail with an error code if any issues are found:

```bash
python scripts/data_validator.py --strict
```

### 7. Run integration tests

To verify the entire stats extraction and website workflow is working:

```bash
python scripts/test_integration.py
```

This will verify:
- All game JSON files are valid
- Games index is generated correctly
- Aggregated stats are compiled
- Game files are copied to docs/data/games
- Website assets are present
- Paths are correct for GitHub Pages deployment

### 8. Preview the website locally

Open `docs/index.html` in your browser, **or** serve it with any static server:

```bash
cd docs && python -m http.server 8080
# → open http://localhost:8080
```

---

## Complete Architecture & Data Flow

For a detailed explanation of how player stats flow from PDF extraction through to the website display, see **[STATS_STRUCTURE.md](STATS_STRUCTURE.md)**.

This document includes:
- Detailed architecture diagrams
- Complete workflow for adding new games
- File format specifications
- Troubleshooting guide

---

Each file in `data/games/` follows this schema:

```jsonc
{
  "date": "2025-10-05",       // YYYY-MM-DD
  "home_team": "Bears HC",
  "away_team": "Hawks HC",
  "home_score": 4,
  "away_score": 2,
  "players": [
    {
      "team":    "Bears HC",
      "number":  "11",
      "name":    "John Doe",
      "goals":   2,
      "assists": 1,
      "points":  3,
      "pim":     2
    }
  ]
}
```

You can also create or edit these files by hand.

---

## GitHub Pages deployment

The site is deployed automatically by **GitHub Actions** every time you push:

* a new game JSON to `data/games/`
* any change to `docs/`

To enable GitHub Pages in your repository:

1. Go to **Settings → Pages**
2. Set **Source** to **GitHub Actions**

The live URL will be:
`https://<your-username>.github.io/M13-AAA-2025-26-Season---TEST/`

---

## Stats website features

* **Season Totals** – sortable table (click any column header) showing GP, G, A,
  PTS, PIM for every player across all games
* **Game Log** – card grid showing the score and top scorers for each game,
  sorted newest-first

---

## Scripts Reference

| Script | Purpose |
|--------|---------|
| `extract_stats.py` | Extract player stats from game-sheet PDFs (LHEQ/Spordle) and save as JSON |
| `stats_aggregator.py` | Compile player and team stats across all games into `data/aggregated_stats.json` |
| `data_validator.py` | Validate JSON files for correct structure and data types |
| `test_integration.py` | Run integration tests to verify entire workflow is working |
| `build_index.py` | Rebuild `docs/js/games-index.js`, regenerate aggregated stats, and copy games to `docs/data/games` |
| `lheq_pdf_downloader.py` | Download PDF game sheets directly from LHEQ game schedule pages |

---

## Dependencies

| Package | Purpose |
|---------|---------|
| `pdfplumber` | Extract text and tables from PDF game sheets |
| `requests` | Download PDFs from URLs (including LHEQ game pages) |

---

## Supported game sources

The `extract_stats.py` script supports:

1. **LHEQ game page URLs** (e.g., `https://masculin.lheq.ca/fr/schedule/614322?gameId=614322`)
   - Auto-extracts the game ID and fetches the PDF from the LHEQ CDN
   - Supported regions: `masculin.lheq.ca` (and `feminin.lheq.ca`, etc.)

2. **Direct PDF URLs** (any HTTPS link ending in `.pdf`)
   - Spordle game sheets, Dropbox links, etc.

3. **Local PDF files** (relative or absolute paths)
   - Useful for offline processing or testing


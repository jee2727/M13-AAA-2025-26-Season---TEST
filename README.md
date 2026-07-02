# M13 AAA – 2025–26 Season Stats

A set of tools to **download game-sheet PDFs from LHEQ / Spordle**, extract
individual player statistics (goals, assists, points, penalty minutes), store
them as JSON, and publish a live stats website on **GitHub Pages**.

---

## Project layout

```
.
├── data/
│   └── games/          ← one JSON file per game (auto-generated)
├── docs/               ← GitHub Pages website source
│   ├── index.html
│   ├── css/style.css
│   └── js/
│       ├── app.js
│       └── games-index.js   ← rebuilt automatically by CI
├── scripts/
│   ├── extract_stats.py     ← download PDF → extract stats → save JSON
│   ├── build_index.py       ← rebuild docs/js/games-index.js
│   └── requirements.txt
└── .github/workflows/
    └── deploy-pages.yml     ← CI: rebuild index + deploy site on every push
```

---

## Quick start

### 1. Install Python dependencies

```bash
pip install -r scripts/requirements.txt
```

### 2. Extract stats from a game-sheet PDF

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

### 3. Rebuild the website index

After adding one or more game JSON files, regenerate the index that the website
uses:

```bash
python scripts/build_index.py
```

### 4. Preview the website locally

Open `docs/index.html` in your browser, **or** serve it with any static server:

```bash
cd docs && python -m http.server 8080
# → open http://localhost:8080
```

---

## Game JSON format

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


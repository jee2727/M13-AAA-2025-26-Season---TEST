# LHEQ Game URL Integration

This document shows how to use the LHEQ game page URLs directly with `extract_stats.py`.

## How it works

When you pass an LHEQ game schedule URL like:
```
https://masculin.lheq.ca/fr/schedule/614322?gameId=614322
```

The script automatically:
1. **Detects** that it's an LHEQ URL
2. **Extracts** the game ID (614322)
3. **Constructs** the PDF download URL:
   ```
   https://lheq-sport.azureedge.net/pdfs/614322_gamesheet.pdf
   ```
4. **Downloads** the PDF from the LHEQ CDN
5. **Extracts** player stats and game info
6. **Saves** the JSON to `data/games/`

## Example usage

### Extract game #1000 (gameId 614322)

```bash
python scripts/extract_stats.py "https://masculin.lheq.ca/fr/schedule/614322?gameId=614322"
```

Expected output:
```
Detected LHEQ game page URL
  Game ID: 614322
  Resolved PDF URL: https://lheq-sport.azureedge.net/pdfs/614322_gamesheet.pdf
Downloading PDF from https://lheq-sport.azureedge.net/pdfs/614322_gamesheet.pdf …
  Saved to /tmp/tmpXXXXXX.pdf
Parsing /tmp/tmpXXXXXX.pdf …

✓  Saved game data → /home/…/data/games/2025-10-04_away_vs_home.json
   Players found : 22
   Date          : 2025-10-04
   Home team     : Team Home
   Away team     : Team Away
```

### Extract and specify game ID

```bash
python scripts/extract_stats.py "https://masculin.lheq.ca/fr/schedule/614322?gameId=614322" \
  --game-id "game_1000"
```

Output file: `data/games/game_1000.json`

## Supported URL formats

The script recognizes LHEQ URLs by looking for:
- `lheq.ca` in the domain
- `/schedule/` in the path

It extracts the game ID from:
1. Query parameter `?gameId=XXX` (preferred)
2. Path component `/schedule/XXX`

Examples:
- `https://masculin.lheq.ca/fr/schedule/614322?gameId=614322` ✓
- `https://feminin.lheq.ca/fr/schedule/614322` ✓ (extracts from path)
- Any other format → falls back to treating as direct URL

## LHEQ CDN details

The LHEQ PDF CDN is hosted on Azure:
```
https://lheq-sport.azureedge.net/pdfs/{gameId}_gamesheet.pdf
```

If the PDF doesn't exist or the CDN is unavailable, the download will fail with an HTTP error.

## Batch processing

To extract multiple games, create a script:

```bash
#!/bin/bash

# Array of game IDs
GAMES=(614322 614323 614324 614325)

for game_id in "${GAMES[@]}"; do
  url="https://masculin.lheq.ca/fr/schedule/${game_id}?gameId=${game_id}"
  python scripts/extract_stats.py "$url"
done

# Rebuild the index
python scripts/build_index.py
```

Then commit the new JSON files:

```bash
git add data/games/*.json
git commit -m "Add extracted game stats"
git push
```

The GitHub Actions workflow will automatically rebuild the index and deploy the updated website.

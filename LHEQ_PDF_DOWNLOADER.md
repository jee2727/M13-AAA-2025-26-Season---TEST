# LHEQ PDF Downloader

`lheq_pdf_downloader.py` is a standalone script for **finding and downloading game-sheet PDFs directly from LHEQ game schedule pages**.

## Overview

The LHEQ website (https://masculin.lheq.ca, https://feminin.lheq.ca, etc.) displays game information on schedule pages. This script:

1. **Fetches** the game schedule page for a given game ID
2. **Finds** the PDF link using multiple detection strategies
3. **Downloads** the PDF to a local file

## Why a separate script?

While `extract_stats.py` also downloads PDFs, this script is optimized for:
- **Direct LHEQ page access** – works even if the direct CDN PDF URL pattern changes
- **Debugging** – helps troubleshoot if extraction fails
- **Flexibility** – supports both static HTML and JavaScript-rendered pages
- **Multiple regions** – handles `masculin.lheq.ca`, `feminin.lheq.ca`, etc.

## Installation

Install required dependencies:

```bash
# Base requirements
pip install requests beautifulsoup4

# Optional: for JavaScript-heavy pages (if static parsing fails)
pip install playwright
playwright install  # Download browser binaries
```

Or install from the requirements file:

```bash
pip install -r scripts/requirements.txt
```

## Usage

### Basic usage

Download PDF for game #1000 (gameId 614322):

```bash
python scripts/lheq_pdf_downloader.py 614322
# Output: 614322.pdf
```

### Specify output filename

```bash
python scripts/lheq_pdf_downloader.py 614322 --output game_1000.pdf
```

### Choose download method

Three methods are available:

#### `auto` (default) – Try requests first, fall back to Playwright

```bash
python scripts/lheq_pdf_downloader.py 614322 --method auto
```

**Best for:** Most cases. Tries the fast method first.

#### `requests` – Static HTML parsing only

```bash
python scripts/lheq_pdf_downloader.py 614322 --method requests
```

**Best for:** Speed, when JavaScript isn't needed.

#### `playwright` – Browser automation

```bash
python scripts/lheq_pdf_downloader.py 614322 --method playwright
```

**Best for:** Pages where PDF links are loaded by JavaScript.

### Specify LHEQ region

```bash
python scripts/lheq_pdf_downloader.py 614322 --region masculin
python scripts/lheq_pdf_downloader.py 614322 --region feminin
```

## How it works

### Method 1: requests + BeautifulSoup (Static parsing)

The script uses multiple patterns to find PDF links:

1. **Direct PDF links** – `<a href="...pdf">`
2. **French text** – "feuille", "résumé"
3. **English text** – "gamesheet", "match sheet"
4. **Download buttons** – `<a>Download</a>`, `<button>Download</button>`
5. **PDF references** – Links containing "pdf" in text or attributes
6. **Fallback** – Any link containing the game ID and `.pdf`

This is **fast** (< 1 second) but only works if the PDF link is in the static HTML.

### Method 2: Playwright (Browser automation)

Launches a browser (Chromium) that:

1. Navigates to the game page
2. Waits for JavaScript to execute (networkidle)
3. Extracts links from the rendered DOM
4. Finds PDF links

This is **slower** (5–10 seconds) but handles JavaScript-rendered content.

## Examples

### Download game #1000

```bash
python scripts/lheq_pdf_downloader.py 614322
```

### Download and save with specific name

```bash
python scripts/lheq_pdf_downloader.py 614322 -o "2025-10-04_M13_AAA.pdf"
```

### Force Playwright for a specific game

```bash
python scripts/lheq_pdf_downloader.py 614322 --method playwright
```

### Download from feminin.lheq.ca

```bash
python scripts/lheq_pdf_downloader.py 614322 --region feminin
```

## Batch downloading

Create a shell script to download multiple games:

```bash
#!/bin/bash

# Array of game IDs
GAMES=(614322 614323 614324 614325)

for game_id in "${GAMES[@]}"; do
  echo "Downloading game $game_id..."
  python scripts/lheq_pdf_downloader.py "$game_id" --output "game_$game_id.pdf"
done

echo "Done! All PDFs downloaded."
```

Then use with `extract_stats.py`:

```bash
python scripts/lheq_pdf_downloader.py 614322 -o /tmp/sheet.pdf
python scripts/extract_stats.py /tmp/sheet.pdf --game-id "my_game_id"
```

## Integration with extract_stats.py

You can now use the full pipeline:

```bash
# Option 1: Direct LHEQ URL (auto-resolves)
python scripts/extract_stats.py "https://masculin.lheq.ca/fr/schedule/614322?gameId=614322"

# Option 2: Use this downloader first, then extract
python scripts/lheq_pdf_downloader.py 614322 -o /tmp/sheet.pdf
python scripts/extract_stats.py /tmp/sheet.pdf
```

Both approaches work. The downloader is useful for:
- Debugging if extraction fails
- Testing the PDF download separately
- Batch downloading before processing
- Custom PDF handling

## Troubleshooting

### "No PDF link found in static HTML"

The PDF link might be loaded by JavaScript. Try:

```bash
python scripts/lheq_pdf_downloader.py 614322 --method playwright
```

### "Playwright not installed"

Install Playwright:

```bash
pip install playwright
playwright install
```

### HTTP 404 or connection error

Possible causes:

1. **Game ID doesn't exist** – Check the URL on LHEQ website
2. **Network issue** – Try again; LHEQ may be temporarily down
3. **Region mismatch** – Try different region (`--region feminin`, etc.)

### PDF is corrupted or incomplete

Try with a longer timeout or Playwright:

```bash
python scripts/lheq_pdf_downloader.py 614322 --method playwright
```

## Return codes

- `0` – Success
- `1` – Failed to find or download PDF

## Notes

- The script respects LHEQ's server with reasonable timeouts (10–30 seconds)
- It uses a realistic User-Agent to avoid blocking
- Playwright's browser is cached after first install (`playwright install`)
- No authentication is required (LHEQ pages are public)

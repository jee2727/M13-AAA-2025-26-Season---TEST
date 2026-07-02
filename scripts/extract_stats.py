#!/usr/bin/env python3
"""
extract_stats.py

Download a game-sheet PDF from an LHEQ / Spordle URL and extract
individual player statistics (goals, assists, points, penalty minutes).
The result is saved as a JSON file under data/games/.

Usage:
    python scripts/extract_stats.py <source> [--game-id GAME_ID]

Where <source> can be:
    • A direct PDF URL: https://example.spordle.com/game/12345/sheet.pdf
    • An LHEQ game page URL: https://masculin.lheq.ca/fr/schedule/614322?gameId=614322
    • A local file path: ./sheet.pdf

Examples:
    python scripts/extract_stats.py https://example.spordle.com/game/12345/sheet.pdf
    python scripts/extract_stats.py https://masculin.lheq.ca/fr/schedule/614322?gameId=614322
    python scripts/extract_stats.py ./sheet.pdf --game-id 2025-10-05_TeamA_vs_TeamB
"""

import argparse
import json
import re
import sys
import tempfile
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse, parse_qs

import pdfplumber
import requests

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
REPO_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = REPO_ROOT / "data" / "games"


# ---------------------------------------------------------------------------
# LHEQ URL handling
# ---------------------------------------------------------------------------

def extract_game_id_from_url(url: str) -> str | None:
    """Extract game ID from LHEQ URL or return None."""
    parsed = urlparse(url)
    
    # Try query parameters first
    if parsed.query:
        qs = parse_qs(parsed.query)
        if "gameId" in qs:
            return qs["gameId"][0]
    
    # Try path: /fr/schedule/614322
    match = re.search(r'/schedule/(\d+)', parsed.path)
    if match:
        return match.group(1)
    
    return None


def resolve_lheq_pdf_url(game_id: str) -> str:
    """
    Attempt to construct a PDF download URL from an LHEQ game ID.
    
    LHEQ CDN URL patterns (may vary by region/language):
        • https://lheq-sport.azureedge.net/pdfs/{gameId}_gamesheet.pdf
        • https://lheq-sport.azureedge.net/pdfs/gamesheet_{gameId}.pdf
    """
    # Try the most common pattern first
    pdf_url = f"https://lheq-sport.azureedge.net/pdfs/{game_id}_gamesheet.pdf"
    return pdf_url


def download_pdf(url: str) -> Path:
    """
    Download a PDF from *url* to a temporary file and return its path.
    
    If *url* is an LHEQ game page URL, automatically extract the game ID
    and construct the PDF download URL.
    """
    # Check if this is an LHEQ game page URL
    if "lheq.ca" in url and "/schedule/" in url:
        print(f"Detected LHEQ game page URL")
        game_id = extract_game_id_from_url(url)
        if game_id:
            print(f"  Game ID: {game_id}")
            url = resolve_lheq_pdf_url(game_id)
            print(f"  Resolved PDF URL: {url}")
        else:
            print(f"  Could not extract game ID, will try page URL directly")
    
    print(f"Downloading PDF from {url} …")
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    response = requests.get(url, timeout=30, headers=headers)
    response.raise_for_status()
    suffix = ".pdf"
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    tmp.write(response.content)
    tmp.close()
    print(f"  Saved to {tmp.name}")
    return Path(tmp.name)


# ---------------------------------------------------------------------------
# Text helpers
# ---------------------------------------------------------------------------

def _clean(text: str) -> str:
    """Normalise whitespace in a string."""
    return " ".join(text.split()) if text else ""


def _int(value: str) -> int:
    """Parse an integer, returning 0 when the cell is empty or non-numeric."""
    try:
        return int(str(value).strip())
    except (ValueError, TypeError):
        return 0


# ---------------------------------------------------------------------------
# Game-sheet parsing
# ---------------------------------------------------------------------------

# Spordle / LHEQ game-sheet column headers (case-insensitive substring match)
_STAT_COLUMNS = {
    "no":     "number",
    "#":      "number",
    "name":   "name",
    "nom":    "name",
    "g":      "goals",
    "but":    "goals",
    "a":      "assists",
    "pass":   "assists",
    "pts":    "points",
    "pim":    "pim",
    "min":    "pim",
}

_TEAM_PATTERNS = [
    re.compile(r"(?:équipe|team)[:\s]+(.+)", re.IGNORECASE),
    re.compile(r"^([A-Z][A-Za-zÀ-ÿ '\-]+(?:HC|Hockey|AAA|AA|A|B)?)\s*$"),
]

_DATE_PATTERNS = [
    re.compile(r"(\d{4}-\d{2}-\d{2})"),
    re.compile(r"(\d{2}/\d{2}/\d{4})"),
    re.compile(r"(\d{2}-\d{2}-\d{4})"),
]


def _detect_columns(header_row: list) -> dict:
    """
    Map column indices to canonical stat names by matching header cell text
    against the _STAT_COLUMNS lookup.  Returns {index: canonical_name}.
    """
    mapping = {}
    for idx, cell in enumerate(header_row):
        if cell is None:
            continue
        cell_text = _clean(str(cell)).lower()
        for keyword, canonical in _STAT_COLUMNS.items():
            if cell_text == keyword or cell_text.startswith(keyword):
                if canonical not in mapping.values():
                    mapping[idx] = canonical
                    break
    return mapping


def _rows_to_players(rows: list, col_map: dict) -> list:
    """Convert table rows into a list of player-stat dicts."""
    players = []
    for row in rows:
        if not row or all(cell is None or str(cell).strip() == "" for cell in row):
            continue
        # Skip rows that look like sub-headers or totals
        first = _clean(str(row[0] or "")).lower()
        if first in ("", "no", "#", "total", "totaux"):
            continue

        player = {
            "number":  "",
            "name":    "",
            "goals":   0,
            "assists": 0,
            "points":  0,
            "pim":     0,
        }
        for idx, canonical in col_map.items():
            if idx >= len(row):
                continue
            val = row[idx]
            if canonical == "number":
                player["number"] = _clean(str(val or ""))
            elif canonical == "name":
                player["name"] = _clean(str(val or ""))
            elif canonical in ("goals", "assists", "pim"):
                player[canonical] = _int(val)

        if not player["name"]:
            continue

        # Recompute points in case the PDF column is missing
        player["points"] = player["goals"] + player["assists"]

        players.append(player)
    return players


def _extract_meta(page_text: str) -> dict:
    """Extract date and team names from raw page text."""
    meta = {"date": "", "home_team": "", "away_team": ""}

    for pattern in _DATE_PATTERNS:
        m = pattern.search(page_text)
        if m:
            raw = m.group(1)
            for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y"):
                try:
                    meta["date"] = datetime.strptime(raw, fmt).strftime("%Y-%m-%d")
                    break
                except ValueError:
                    continue
            break

    teams = []
    for line in page_text.splitlines():
        line = line.strip()
        for pat in _TEAM_PATTERNS:
            m = pat.match(line)
            if m:
                candidate = _clean(m.group(1))
                if 3 < len(candidate) < 60 and candidate not in teams:
                    teams.append(candidate)
                    break
        if len(teams) == 2:
            break

    if len(teams) >= 2:
        meta["away_team"], meta["home_team"] = teams[0], teams[1]
    elif len(teams) == 1:
        meta["home_team"] = teams[0]

    return meta


def parse_pdf(pdf_path: Path) -> dict:
    """
    Open the PDF at *pdf_path* and return a structured game dict:

    {
        "date": "YYYY-MM-DD",
        "home_team": "...",
        "away_team": "...",
        "home_score": 0,
        "away_score": 0,
        "players": [
            {
                "team": "...",
                "number": "...",
                "name": "...",
                "goals": 0,
                "assists": 0,
                "points": 0,
                "pim": 0
            },
            ...
        ]
    }
    """
    game = {
        "date": "",
        "home_team": "",
        "away_team": "",
        "home_score": 0,
        "away_score": 0,
        "players": [],
    }

    with pdfplumber.open(pdf_path) as pdf:
        full_text = ""
        all_tables = []

        for page in pdf.pages:
            text = page.extract_text() or ""
            full_text += text + "\n"

            tables = page.extract_tables()
            for table in tables:
                if table:
                    all_tables.append(table)

        meta = _extract_meta(full_text)
        game.update(meta)

        current_team = game["home_team"]
        for table in all_tables:
            if not table:
                continue

            header = table[0]
            col_map = _detect_columns(header)

            # Need at least a name column to be a roster/stats table
            if not any(v == "name" for v in col_map.values()):
                # Try to detect team name from a merged header cell
                header_text = " ".join(
                    _clean(str(c or "")) for c in header
                ).strip()
                if header_text and len(header_text) < 80:
                    current_team = header_text
                continue

            players = _rows_to_players(table[1:], col_map)
            for p in players:
                p["team"] = current_team
            game["players"].extend(players)

            # Alternate team after the first roster table is processed
            if current_team == game["home_team"] and game["away_team"]:
                current_team = game["away_team"]

    return game


# ---------------------------------------------------------------------------
# Score extraction helper (best-effort)
# ---------------------------------------------------------------------------

_SCORE_PATTERN = re.compile(
    r"(\d+)\s*[-–]\s*(\d+)"
)


def _try_extract_scores(pdf_path: Path, game: dict) -> None:
    """Attempt to fill home_score / away_score from the PDF text."""
    with pdfplumber.open(pdf_path) as pdf:
        text = ""
        for page in pdf.pages:
            text += (page.extract_text() or "") + "\n"

    matches = _SCORE_PATTERN.findall(text)
    if matches:
        # Take the first plausible score (both sides < 30)
        for a, b in matches:
            if int(a) < 30 and int(b) < 30:
                game["away_score"] = int(a)
                game["home_score"] = int(b)
                break


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Extract player stats from an LHEQ / Spordle game-sheet PDF."
    )
    parser.add_argument(
        "source",
        help=(
            "Source to extract from. Can be:\n"
            "  • Direct PDF URL (e.g., https://example.com/sheet.pdf)\n"
            "  • LHEQ game page (e.g., https://masculin.lheq.ca/fr/schedule/614322?gameId=614322)\n"
            "  • Local file path (e.g., ./sheet.pdf)"
        ),
    )
    parser.add_argument(
        "--game-id",
        default="",
        help=(
            "Optional identifier used as the JSON filename "
            "(e.g. 2025-10-05_TeamA_vs_TeamB).  "
            "Defaults to auto-generated name from date and teams."
        ),
    )
    args = parser.parse_args()

    source: str = args.source
    tmp_pdf: Path | None = None

    try:
        if source.startswith("http://") or source.startswith("https://"):
            tmp_pdf = download_pdf(source)
            pdf_path = tmp_pdf
        else:
            pdf_path = Path(source)
            if not pdf_path.exists():
                print(f"ERROR: File not found: {pdf_path}", file=sys.stderr)
                sys.exit(1)

        print(f"Parsing {pdf_path} …")
        game = parse_pdf(pdf_path)
        _try_extract_scores(pdf_path, game)

        # Determine output filename
        game_id = args.game_id
        if not game_id:
            date_part = game.get("date") or "unknown-date"
            home = re.sub(r"[^A-Za-z0-9]", "_", game.get("home_team", "home"))
            away = re.sub(r"[^A-Za-z0-9]", "_", game.get("away_team", "away"))
            game_id = f"{date_part}_{away}_vs_{home}"

        DATA_DIR.mkdir(parents=True, exist_ok=True)
        out_path = DATA_DIR / f"{game_id}.json"

        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(game, f, ensure_ascii=False, indent=2)

        print(f"\n✓  Saved game data → {out_path}")
        print(f"   Players found : {len(game['players'])}")
        if game["date"]:
            print(f"   Date          : {game['date']}")
        if game["home_team"]:
            print(f"   Home team     : {game['home_team']}")
        if game["away_team"]:
            print(f"   Away team     : {game['away_team']}")

    finally:
        if tmp_pdf and tmp_pdf.exists():
            tmp_pdf.unlink()


if __name__ == "__main__":
    main()

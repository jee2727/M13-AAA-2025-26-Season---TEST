#!/usr/bin/env python3
"""
build_index.py

Scan data/games/ for all *.json files and regenerate docs/js/games-index.js
so that the GitHub Pages site knows which game files to load.

This script also:
1. Regenerates aggregated stats (data/aggregated_stats.json)
2. Copies game files to docs/data/games/ for GitHub Pages deployment

Run this script after adding or removing game JSON files:
    python scripts/build_index.py
"""

import json
import shutil
import sys
from pathlib import Path

REPO_ROOT  = Path(__file__).resolve().parent.parent
GAMES_DIR  = REPO_ROOT / "data" / "games"
INDEX_FILE = REPO_ROOT / "docs" / "js" / "games-index.js"
DOCS_GAMES_DIR = REPO_ROOT / "docs" / "data" / "games"

HEADER = """\
/**
 * games-index.js
 *
 * Auto-generated list of available game JSON files.
 * This file is rebuilt by the GitHub Actions workflow every time a new
 * game JSON is added to data/games/.
 *
 * DO NOT edit manually – run `scripts/build_index.py` or push a new game file.
 */

// eslint-disable-next-line no-unused-vars
"""


def build_games_index(game_files: list) -> None:
    """Build and write the games index JavaScript file."""
    js_array = json.dumps(game_files, indent=2)
    content  = HEADER + f"const GAMES_INDEX = {js_array};\n"

    INDEX_FILE.parent.mkdir(parents=True, exist_ok=True)
    INDEX_FILE.write_text(content, encoding="utf-8")

    print(f"✓ Written {INDEX_FILE}  ({len(game_files)} game(s))")
    for name in game_files:
        print(f"   - {name}")


def copy_games_to_docs() -> None:
    """Copy game JSON files to docs/data/games/ for GitHub Pages deployment."""
    DOCS_GAMES_DIR.parent.mkdir(parents=True, exist_ok=True)
    
    # Remove old docs/data/games directory if it exists
    if DOCS_GAMES_DIR.exists():
        shutil.rmtree(DOCS_GAMES_DIR)
    
    # Copy entire games directory
    shutil.copytree(GAMES_DIR, DOCS_GAMES_DIR)
    
    print(f"\n✓ Copied game files to {DOCS_GAMES_DIR}")
    game_count = len(list(DOCS_GAMES_DIR.glob("*.json")))
    print(f"   {game_count} file(s) copied for deployment")


def build_aggregated_stats(game_files: list) -> None:
    """Build aggregated stats from all games."""
    # Import the stats_aggregator module
    stats_aggregator_path = REPO_ROOT / "scripts" / "stats_aggregator.py"
    
    # Dynamically import stats_aggregator
    import importlib.util
    spec = importlib.util.spec_from_file_location("stats_aggregator", stats_aggregator_path)
    if spec and spec.loader:
        stats_agg = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(stats_agg)
        
        # Load games and build aggregated stats
        games = stats_agg.load_all_games()
        if games:
            aggregated = stats_agg.build_aggregated_stats(games)
            stats_output = REPO_ROOT / "data" / "aggregated_stats.json"
            
            with open(stats_output, "w", encoding="utf-8") as f:
                json.dump(aggregated, f, ensure_ascii=False, indent=2)
            
            print(f"\n✓ Written {stats_output}  ({len(games)} game(s))")


def main() -> None:
    """Main entry point."""
    game_files = sorted(
        p.name for p in GAMES_DIR.glob("*.json")
        if p.is_file()
    )

    print("=== Building Games Index ===\n")
    build_games_index(game_files)
    
    print("\n=== Copying Games to Docs ===")
    copy_games_to_docs()
    
    print("\n=== Building Aggregated Stats ===")
    try:
        build_aggregated_stats(game_files)
    except Exception as e:
        print(f"⚠ Warning: Could not build aggregated stats: {e}")
        # Don't fail on stats build errors


if __name__ == "__main__":
    main()

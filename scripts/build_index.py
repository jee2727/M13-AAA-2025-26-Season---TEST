#!/usr/bin/env python3
"""
build_index.py

Scan data/games/ for all *.json files and regenerate docs/js/games-index.js
so that the GitHub Pages site knows which game files to load.

Run this script after adding or removing game JSON files:
    python scripts/build_index.py
"""

import json
from pathlib import Path

REPO_ROOT  = Path(__file__).resolve().parent.parent
GAMES_DIR  = REPO_ROOT / "data" / "games"
INDEX_FILE = REPO_ROOT / "docs" / "js" / "games-index.js"

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


def main() -> None:
    game_files = sorted(
        p.name for p in GAMES_DIR.glob("*.json")
        if p.is_file()
    )

    js_array = json.dumps(game_files, indent=2)
    content  = HEADER + f"const GAMES_INDEX = {js_array};\n"

    INDEX_FILE.parent.mkdir(parents=True, exist_ok=True)
    INDEX_FILE.write_text(content, encoding="utf-8")

    print(f"✓  Written {INDEX_FILE}  ({len(game_files)} game(s))")
    for name in game_files:
        print(f"   - {name}")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
data_validator.py

Validate the structure and content of game JSON files in data/games/.

This script:
1. Checks for valid JSON structure
2. Verifies required fields (date, teams, players)
3. Validates player stats (goals, assists, pim are non-negative integers)
4. Reports any issues found

Run this script to audit your data:
    python scripts/data_validator.py
    python scripts/data_validator.py --strict  (exit with error on any issues)
"""

import json
import sys
from pathlib import Path
from typing import List, Tuple

REPO_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = REPO_ROOT / "data" / "games"


def validate_game(json_file: Path) -> Tuple[bool, List[str]]:
    """
    Validate a single game JSON file.
    
    Returns (is_valid, list_of_issues).
    """
    issues = []
    
    # Load JSON
    try:
        with open(json_file, "r", encoding="utf-8") as f:
            game = json.load(f)
    except json.JSONDecodeError as e:
        return False, [f"Invalid JSON: {e}"]
    except IOError as e:
        return False, [f"Cannot read file: {e}"]
    
    if not isinstance(game, dict):
        return False, ["Game data must be a dict"]
    
    # Check required fields
    required_fields = ["date", "home_team", "away_team", "players"]
    for field in required_fields:
        if field not in game:
            issues.append(f"Missing required field: '{field}'")
    
    # Validate date format (YYYY-MM-DD)
    if "date" in game:
        date_val = game["date"]
        if date_val and not isinstance(date_val, str):
            issues.append(f"'date' must be a string, got {type(date_val).__name__}")
        elif date_val and not __validate_date_format(date_val):
            issues.append(f"'date' has invalid format: '{date_val}' (expected YYYY-MM-DD)")
    
    # Validate team names
    for team_field in ["home_team", "away_team"]:
        if team_field in game and not isinstance(game[team_field], str):
            issues.append(f"'{team_field}' must be a string")
    
    # Validate scores if present
    for score_field in ["home_score", "away_score"]:
        if score_field in game:
            score = game[score_field]
            if not isinstance(score, int):
                issues.append(f"'{score_field}' must be an integer, got {type(score).__name__}")
            elif score < 0:
                issues.append(f"'{score_field}' cannot be negative: {score}")
    
    # Validate players array
    if "players" in game:
        players = game["players"]
        if not isinstance(players, list):
            issues.append(f"'players' must be a list, got {type(players).__name__}")
        else:
            for i, player in enumerate(players):
                player_issues = __validate_player(player, i)
                issues.extend(player_issues)
    
    return len(issues) == 0, issues


def __validate_date_format(date_str: str) -> bool:
    """Check if date string matches YYYY-MM-DD format."""
    if len(date_str) != 10:
        return False
    parts = date_str.split("-")
    if len(parts) != 3:
        return False
    try:
        year, month, day = parts
        int(year), int(month), int(day)
        return True
    except ValueError:
        return False


def __validate_player(player: dict, index: int) -> List[str]:
    """Validate a single player object."""
    issues = []
    
    if not isinstance(player, dict):
        return [f"Player {index}: must be a dict"]
    
    # Check required player fields
    required = ["name", "team", "goals", "assists", "pim"]
    for field in required:
        if field not in player:
            issues.append(f"Player {index}: missing '{field}'")
    
    # Validate name and team are strings
    for field in ["name", "team", "number"]:
        if field in player and not isinstance(player[field], str):
            issues.append(f"Player {index}: '{field}' must be a string")
    
    # Validate stats are non-negative integers
    for field in ["goals", "assists", "pim", "points"]:
        if field in player:
            val = player[field]
            if not isinstance(val, int):
                issues.append(f"Player {index}: '{field}' must be an integer, got {type(val).__name__}")
            elif val < 0:
                issues.append(f"Player {index}: '{field}' cannot be negative: {val}")
    
    return issues


def main() -> None:
    """Validate all game JSON files."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Validate game JSON files")
    parser.add_argument("--strict", action="store_true", help="Exit with error code if any issues found")
    args = parser.parse_args()
    
    if not DATA_DIR.exists():
        print(f"Data directory not found: {DATA_DIR}")
        sys.exit(1)
    
    json_files = sorted(DATA_DIR.glob("*.json"))
    if not json_files:
        print(f"No JSON files found in {DATA_DIR}")
        return
    
    print(f"Validating {len(json_files)} game file(s)…\n")
    
    total_issues = 0
    valid_count = 0
    
    for json_file in json_files:
        is_valid, issues = validate_game(json_file)
        
        if is_valid:
            print(f"✓ {json_file.name}")
            valid_count += 1
        else:
            print(f"✗ {json_file.name}")
            for issue in issues:
                print(f"  - {issue}")
            total_issues += len(issues)
    
    print()
    print(f"Summary: {valid_count}/{len(json_files)} file(s) valid, {total_issues} issue(s) found")
    
    if args.strict and total_issues > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()

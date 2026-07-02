#!/usr/bin/env python3
"""
test_integration.py

Integration test to verify the complete stats extraction and website workflow.

Tests:
1. All game JSON files are valid
2. build_index.py generates correct index
3. Aggregated stats are compiled correctly
4. Game files are copied to docs/data/games
5. Website assets are present

Run: python scripts/test_integration.py
"""

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


def test_game_files_valid() -> bool:
    """Verify all game JSON files have correct structure."""
    print("\n✓ Testing: Game JSON files are valid")
    
    games_dir = REPO_ROOT / "data" / "games"
    if not games_dir.exists():
        print("  ✗ data/games directory not found")
        return False
    
    json_files = list(games_dir.glob("*.json"))
    if not json_files:
        print("  ✗ No JSON files found in data/games")
        return False
    
    for json_file in json_files:
        try:
            with open(json_file, "r", encoding="utf-8") as f:
                game = json.load(f)
            
            # Check required fields
            if not all(k in game for k in ["date", "players"]):
                print(f"  ✗ {json_file.name}: Missing required fields")
                return False
            
            if not isinstance(game.get("players"), list):
                print(f"  ✗ {json_file.name}: 'players' must be a list")
                return False
        
        except json.JSONDecodeError as e:
            print(f"  ✗ {json_file.name}: Invalid JSON - {e}")
            return False
    
    print(f"  ✓ All {len(json_files)} game files are valid")
    return True


def test_games_index_exists() -> bool:
    """Verify games-index.js exists and contains all games."""
    print("\n✓ Testing: Games index is generated")
    
    index_file = REPO_ROOT / "docs" / "js" / "games-index.js"
    if not index_file.exists():
        print(f"  ✗ {index_file} not found")
        return False
    
    content = index_file.read_text(encoding="utf-8")
    if "GAMES_INDEX" not in content:
        print("  ✗ games-index.js does not contain GAMES_INDEX")
        return False
    
    games_dir = REPO_ROOT / "data" / "games"
    game_files = list(games_dir.glob("*.json"))
    game_count = len(game_files)
    
    # Check that all game files are listed
    missing_games = []
    for game_file in game_files:
        if game_file.name not in content:
            missing_games.append(game_file.name)
    
    if missing_games:
        print(f"  ✗ games-index.js missing {len(missing_games)} games:")
        for game in missing_games:
            print(f"      - {game}")
        return False
    
    print(f"  ✓ games-index.js contains all {game_count} games")
    return True


def test_aggregated_stats_exists() -> bool:
    """Verify aggregated_stats.json is generated."""
    print("\n✓ Testing: Aggregated stats file exists")
    
    stats_file = REPO_ROOT / "data" / "aggregated_stats.json"
    if not stats_file.exists():
        print(f"  ✗ {stats_file} not found")
        return False
    
    try:
        with open(stats_file, "r", encoding="utf-8") as f:
            stats = json.load(f)
        
        required_keys = ["meta", "players", "teams", "games"]
        if not all(k in stats for k in required_keys):
            print(f"  ✗ aggregated_stats.json missing required keys")
            return False
        
        if not isinstance(stats["meta"], dict):
            print(f"  ✗ aggregated_stats.json 'meta' must be a dict")
            return False
        
        print(f"  ✓ aggregated_stats.json is valid with {len(stats['players'])} players")
        return True
    
    except json.JSONDecodeError as e:
        print(f"  ✗ aggregated_stats.json is invalid: {e}")
        return False


def test_games_copied_to_docs() -> bool:
    """Verify game files are copied to docs/data/games."""
    print("\n✓ Testing: Games are copied to docs/data/games")
    
    docs_games_dir = REPO_ROOT / "docs" / "data" / "games"
    if not docs_games_dir.exists():
        print(f"  ✗ {docs_games_dir} directory not found")
        return False
    
    docs_games = list(docs_games_dir.glob("*.json"))
    source_games = list((REPO_ROOT / "data" / "games").glob("*.json"))
    
    if len(docs_games) != len(source_games):
        print(f"  ✗ Only {len(docs_games)} games copied (expected {len(source_games)})")
        return False
    
    print(f"  ✓ All {len(docs_games)} games copied to docs/data/games")
    return True


def test_website_assets_exist() -> bool:
    """Verify all website assets exist."""
    print("\n✓ Testing: Website assets exist")
    
    required_files = [
        "docs/index.html",
        "docs/js/app.js",
        "docs/js/games-index.js",
        "docs/css/style.css",
    ]
    
    missing = []
    for rel_path in required_files:
        file_path = REPO_ROOT / rel_path
        if not file_path.exists():
            missing.append(rel_path)
    
    if missing:
        for path in missing:
            print(f"  ✗ {path} not found")
        return False
    
    print(f"  ✓ All {len(required_files)} website assets present")
    return True


def test_app_js_has_correct_path() -> bool:
    """Verify app.js uses correct data path."""
    print("\n✓ Testing: app.js uses correct data path")
    
    app_file = REPO_ROOT / "docs" / "js" / "app.js"
    content = app_file.read_text(encoding="utf-8")
    
    # Should NOT have ../data/games (relative path from docs)
    if "../data/games" in content:
        print(f"  ✗ app.js uses old relative path '../data/games'")
        return False
    
    # Should have data/games (relative path within docs)
    if 'GAMES_BASE = "data/games/"' not in content:
        print(f"  ✗ app.js does not use correct path 'data/games/'")
        return False
    
    print(f"  ✓ app.js uses correct path for GitHub Pages deployment")
    return True


def main() -> int:
    """Run all tests."""
    print("\n" + "="*60)
    print("  M13 AAA Season Stats – Integration Tests")
    print("="*60)
    
    tests = [
        test_game_files_valid,
        test_games_index_exists,
        test_aggregated_stats_exists,
        test_games_copied_to_docs,
        test_website_assets_exist,
        test_app_js_has_correct_path,
    ]
    
    results = []
    for test in tests:
        try:
            results.append(test())
        except Exception as e:
            print(f"  ✗ Test failed with exception: {e}")
            results.append(False)
    
    print("\n" + "="*60)
    passed = sum(results)
    total = len(results)
    print(f"  Results: {passed}/{total} tests passed")
    print("="*60 + "\n")
    
    return 0 if all(results) else 1


if __name__ == "__main__":
    sys.exit(main())

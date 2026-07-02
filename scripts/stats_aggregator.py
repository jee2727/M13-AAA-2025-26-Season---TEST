#!/usr/bin/env python3
"""
stats_aggregator.py

Aggregate player statistics from all game JSON files in data/games/
and generate a compiled stats JSON file for easy consumption.

This script:
1. Reads all game JSON files
2. Aggregates player stats across all games
3. Generates data/aggregated_stats.json with season totals
4. Optionally generates team summaries

Run this script after adding game JSON files:
    python scripts/stats_aggregator.py
"""

import json
from pathlib import Path
from typing import Dict, List, Tuple
from collections import defaultdict

REPO_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = REPO_ROOT / "data" / "games"
STATS_OUTPUT = REPO_ROOT / "data" / "aggregated_stats.json"


def load_all_games() -> List[dict]:
    """Load all game JSON files from data/games/."""
    games = []
    if not DATA_DIR.exists():
        return games
    
    for json_file in sorted(DATA_DIR.glob("*.json")):
        try:
            with open(json_file, "r", encoding="utf-8") as f:
                game = json.load(f)
                games.append(game)
        except (json.JSONDecodeError, IOError) as e:
            print(f"⚠ Warning: Could not load {json_file.name}: {e}")
    
    return games


def aggregate_player_stats(games: List[dict]) -> Dict[Tuple[str, str], dict]:
    """
    Aggregate player statistics across all games.
    
    Returns a dict keyed by (player_name, team) with aggregated stats.
    """
    player_stats = defaultdict(lambda: {
        "name": "",
        "team": "",
        "number": "",
        "gp": 0,
        "goals": 0,
        "assists": 0,
        "points": 0,
        "pim": 0,
    })
    
    for game in games:
        for player in game.get("players", []):
            key = (player.get("name", ""), player.get("team", ""))
            if key[0]:  # Skip empty names
                stats = player_stats[key]
                stats["name"] = player.get("name", "")
                stats["team"] = player.get("team", "")
                stats["number"] = player.get("number", stats["number"])
                stats["gp"] += 1
                stats["goals"] += player.get("goals", 0)
                stats["assists"] += player.get("assists", 0)
                stats["points"] += player.get("goals", 0) + player.get("assists", 0)
                stats["pim"] += player.get("pim", 0)
    
    return dict(player_stats)


def aggregate_team_stats(games: List[dict]) -> Dict[str, dict]:
    """
    Aggregate team statistics across all games.
    
    Returns a dict with team performance stats.
    """
    team_stats = defaultdict(lambda: {
        "name": "",
        "games_played": 0,
        "wins": 0,
        "losses": 0,
        "goals_for": 0,
        "goals_against": 0,
        "total_points": 0,
    })
    
    for game in games:
        home_team = game.get("home_team", "")
        away_team = game.get("away_team", "")
        home_score = game.get("home_score", 0)
        away_score = game.get("away_score", 0)
        
        if home_team:
            home_stats = team_stats[home_team]
            home_stats["name"] = home_team
            home_stats["games_played"] += 1
            home_stats["goals_for"] += home_score
            home_stats["goals_against"] += away_score
            
            if home_score > away_score:
                home_stats["wins"] += 1
                home_stats["total_points"] += 2
            elif home_score < away_score:
                home_stats["losses"] += 1
            else:
                home_stats["total_points"] += 1
        
        if away_team:
            away_stats = team_stats[away_team]
            away_stats["name"] = away_team
            away_stats["games_played"] += 1
            away_stats["goals_for"] += away_score
            away_stats["goals_against"] += home_score
            
            if away_score > home_score:
                away_stats["wins"] += 1
                away_stats["total_points"] += 2
            elif away_score < home_score:
                away_stats["losses"] += 1
            else:
                away_stats["total_points"] += 1
    
    return dict(team_stats)


def build_aggregated_stats(games: List[dict]) -> dict:
    """Build the complete aggregated stats structure."""
    player_stats = aggregate_player_stats(games)
    team_stats = aggregate_team_stats(games)
    
    # Convert player stats dict to sorted list (by points descending)
    player_list = sorted(
        player_stats.values(),
        key=lambda p: (-p["points"], -p["goals"], p["name"])
    )
    
    # Convert team stats dict to sorted list (by total points descending)
    team_list = sorted(
        team_stats.values(),
        key=lambda t: (-t["total_points"], -t["goals_for"])
    )
    
    return {
        "meta": {
            "total_games": len(games),
            "total_players": len(player_stats),
            "total_teams": len(team_stats),
        },
        "players": player_list,
        "teams": team_list,
        "games": games,
    }


def main() -> None:
    """Load games, aggregate stats, and write output."""
    print("Loading game files from data/games/…")
    games = load_all_games()
    
    if not games:
        print("⚠ No game JSON files found in data/games/")
        return
    
    print(f"✓ Loaded {len(games)} game(s)")
    
    print("Aggregating player and team statistics…")
    aggregated = build_aggregated_stats(games)
    
    # Write aggregated stats
    DATA_DIR.parent.mkdir(parents=True, exist_ok=True)
    with open(STATS_OUTPUT, "w", encoding="utf-8") as f:
        json.dump(aggregated, f, ensure_ascii=False, indent=2)
    
    print(f"✓ Wrote aggregated stats → {STATS_OUTPUT}")
    print(f"  Total games     : {aggregated['meta']['total_games']}")
    print(f"  Total players   : {aggregated['meta']['total_players']}")
    print(f"  Total teams     : {aggregated['meta']['total_teams']}")
    
    # Print top 5 scorers
    if aggregated["players"]:
        print("\n  Top 5 scorers:")
        for i, player in enumerate(aggregated["players"][:5], 1):
            print(f"    {i}. {player['name']} ({player['team']}) - {player['points']} pts ({player['goals']}G + {player['assists']}A)")


if __name__ == "__main__":
    main()

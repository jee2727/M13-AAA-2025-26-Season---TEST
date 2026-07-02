/**
 * app.js – M13 AAA Season Stats front-end
 *
 * Reads GAMES_INDEX (defined in games-index.js), fetches every game JSON,
 * then renders:
 *   • a sortable season-totals table
 *   • a grid of per-game cards with top scorers
 */

/* =========================================================
   Constants / config
   ========================================================= */
const GAMES_BASE = "../data/games/";
const LAST_UPDATED_EL = document.getElementById("last-updated");
const TOTALS_BODY     = document.getElementById("totals-body");
const GAMES_CONTAINER = document.getElementById("games-container");

/* =========================================================
   Data loading
   ========================================================= */

/**
 * Fetch a single game JSON file.
 * @param {string} filename  e.g. "2025-10-05_away_vs_home.json"
 * @returns {Promise<object|null>}
 */
async function fetchGame(filename) {
  try {
    const res = await fetch(GAMES_BASE + filename);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return await res.json();
  } catch (err) {
    console.warn(`Could not load ${filename}:`, err.message);
    return null;
  }
}

/**
 * Fetch all games listed in GAMES_INDEX in parallel.
 * @returns {Promise<object[]>}
 */
async function loadAllGames() {
  if (!window.GAMES_INDEX || GAMES_INDEX.length === 0) return [];
  const results = await Promise.all(GAMES_INDEX.map(fetchGame));
  return results.filter(Boolean);
}

/* =========================================================
   Aggregation
   ========================================================= */

/**
 * Build a map of playerKey → season totals across all games.
 * @param {object[]} games
 * @returns {Map<string, object>}
 */
function aggregateTotals(games) {
  const totals = new Map();

  for (const game of games) {
    for (const p of game.players || []) {
      const key = `${p.name}|${p.team}`;
      if (!totals.has(key)) {
        totals.set(key, {
          name:    p.name,
          team:    p.team || "",
          number:  p.number || "",
          gp:      0,
          goals:   0,
          assists: 0,
          points:  0,
          pim:     0,
        });
      }
      const row = totals.get(key);
      row.gp++;
      row.goals   += p.goals   || 0;
      row.assists += p.assists || 0;
      row.points  += (p.goals || 0) + (p.assists || 0);
      row.pim     += p.pim     || 0;
    }
  }

  return totals;
}

/* =========================================================
   Rendering – Season Totals
   ========================================================= */

let currentSort = { col: "points", dir: "desc" };

function renderTotals(totals) {
  const rows = Array.from(totals.values());

  // Sort
  rows.sort((a, b) => {
    let av = a[currentSort.col];
    let bv = b[currentSort.col];
    if (typeof av === "string") av = av.toLowerCase();
    if (typeof bv === "string") bv = bv.toLowerCase();
    if (av < bv) return currentSort.dir === "asc" ? -1 :  1;
    if (av > bv) return currentSort.dir === "asc" ?  1 : -1;
    return 0;
  });

  if (rows.length === 0) {
    TOTALS_BODY.innerHTML =
      '<tr><td colspan="8" class="no-data">No game data available yet.</td></tr>';
    return;
  }

  TOTALS_BODY.innerHTML = rows.map((p, i) => `
    <tr>
      <td class="rank num">${i + 1}</td>
      <td class="player-name">${esc(p.name)}</td>
      <td><span class="team-badge">${esc(p.team)}</span></td>
      <td class="num">${p.gp}</td>
      <td class="num stat-goals">${p.goals}</td>
      <td class="num">${p.assists}</td>
      <td class="num stat-points">${p.points}</td>
      <td class="num stat-pim">${p.pim}</td>
    </tr>
  `).join("");

  // Update sort indicators
  document.querySelectorAll("#totals-table th.sortable").forEach(th => {
    th.classList.remove("sort-asc", "sort-desc");
    if (th.dataset.col === currentSort.col) {
      th.classList.add(currentSort.dir === "asc" ? "sort-asc" : "sort-desc");
    }
  });
}

function initSortListeners(totals) {
  document.querySelectorAll("#totals-table th.sortable").forEach(th => {
    th.addEventListener("click", () => {
      const col = th.dataset.col;
      if (currentSort.col === col) {
        currentSort.dir = currentSort.dir === "asc" ? "desc" : "asc";
      } else {
        currentSort.col = col;
        currentSort.dir = ["goals","assists","points","pim","gp"].includes(col)
          ? "desc" : "asc";
      }
      renderTotals(totals);
    });
  });
}

/* =========================================================
   Rendering – Game Cards
   ========================================================= */

function renderGames(games) {
  if (games.length === 0) {
    GAMES_CONTAINER.innerHTML =
      '<p class="no-data">No games found.  Add JSON files to data/games/ and rebuild the index.</p>';
    return;
  }

  // Sort games by date descending (most recent first)
  const sorted = [...games].sort((a, b) =>
    (b.date || "").localeCompare(a.date || "")
  );

  GAMES_CONTAINER.innerHTML = sorted.map(game => {
    const topScorers = (game.players || [])
      .filter(p => (p.goals + p.assists) > 0)
      .sort((a, b) => (b.goals + b.assists) - (a.goals + a.assists))
      .slice(0, 5);

    const scorerRows = topScorers.map(p => `
      <tr>
        <td>${esc(p.name)}</td>
        <td><span class="team-badge">${esc(p.team || "")}</span></td>
        <td class="num stat-goals">${p.goals}</td>
        <td class="num">${p.assists}</td>
        <td class="num stat-points">${p.goals + p.assists}</td>
        <td class="num stat-pim">${p.pim}</td>
      </tr>
    `).join("");

    const scorerTable = topScorers.length > 0 ? `
      <table>
        <thead>
          <tr>
            <th>Player</th><th>Team</th>
            <th class="num">G</th><th class="num">A</th>
            <th class="num">PTS</th><th class="num">PIM</th>
          </tr>
        </thead>
        <tbody>${scorerRows}</tbody>
      </table>
    ` : '<p class="no-data">No scoring data.</p>';

    return `
      <div class="game-card">
        <div class="game-card-header">
          <span class="game-date">${esc(game.date || "Date unknown")}</span>
        </div>
        <div class="game-score">${game.away_score ?? "–"} – ${game.home_score ?? "–"}</div>
        <div class="game-teams">
          <span>${esc(game.away_team || "Away")}</span>
          <span>${esc(game.home_team || "Home")}</span>
        </div>
        ${scorerTable}
      </div>
    `;
  }).join("");
}

/* =========================================================
   Utilities
   ========================================================= */

/** Escape HTML special characters. */
function esc(str) {
  return String(str ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

/* =========================================================
   Bootstrap
   ========================================================= */

(async function init() {
  const games = await loadAllGames();

  if (LAST_UPDATED_EL) {
    LAST_UPDATED_EL.textContent = games.length > 0
      ? new Date().toLocaleDateString()
      : "No data yet";
  }

  const totals = aggregateTotals(games);

  renderTotals(totals);
  initSortListeners(totals);
  renderGames(games);
})();

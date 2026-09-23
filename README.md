# Marvel Rivals Team Optimization

This project explores how **combinatorial optimization** and **game theory** can enhance hero selection strategies in the team-based shooter **Marvel Rivals**. By modeling hero matchups using real-world performance data, we analyze how optimal team compositions can be constructed under various competitive conditions.

---

## Project Summary

We build a game-theoretic model around team selection in Marvel Rivals, treating each 6-hero lineup as a discrete strategy. A **payoff matrix** is derived from publicly available win rate data, and several optimization problems are formulated to reflect realistic scenarios such as:

- Optimal counter-teaming
- Banning mechanics
- Ultimate usage maximization
- Role-balanced team compositions
- Team-Up synergy optimization

---

## What’s Inside

| File | Description |
|------|-------------|
| `DataImport Script.py` | Script to scrape and update the latest win rate and matchup data from [rivalsmeta.com](https://rivalsmeta.com/) |
| `main.ipynb` | Full implementation of all optimization problems discussed in the project |
| `MarvelRivals_WinRate_Matrix.csv` | Raw win rate matrix (unprocessed) |
| `MarvelRivals_NumMatches_Matrix.csv` | Matrix of total match counts between heroes |
| `MarvelRivals_Payoff_Matrix.csv` | Normalized payoff matrix used in optimization |

---

## Optimization Topics Covered

- Counter-strategy generation using linear and binary programming
- Minimax strategies based on von Neumann’s theorem
- Banning constraints and feasible team construction
- Multi-objective optimization combining ultimates and win rates
- Role-based filtering and synergy-aware (Team-Up) team formation

---

## Data Source

All matchup data was obtained from:

**[rivalsmeta.com](https://rivalsmeta.com/)** — the most comprehensive source of performance analytics for Marvel Rivals.

---

## How to Run

1. **Install dependencies**: `python3 -m pip install -r requirements.txt`
2. **Update data**: Run `python3 "DataImport Script.py"`, or run all cells in `dataimport Script.ipynb`. The notebook contains the scraper in separate, inspectable cells, with cached downloads and retry support.
3. **Solve problems**: Open `main.ipynb` for the full suite of optimization tools and demonstrations.


The scraper reads the **Win Rate** and **Matches** table headings and normalizes
hero names using their URL slugs. Add newly released heroes to the role lists in
`DataImport Script.py`; an unknown or missing hero produces an explicit error.
All pages and the payoff calculation must succeed before the three CSVs are
written, so a failed scrape cannot replace them with empty matrices.

Rows represent the selected hero; columns represent the opponent. As in the
original model, diagonal win rates are set to 50%, and diagonal match counts
are the integer mean of that hero's opponent counts (synthetic, not scraped).
The source describes these matchups as Diamond through One Above All, updated
daily; the scraper uses the website's default dataset.

Run the offline regression checks with `python3 -m unittest discover -s tests -v`.

---

## Last Updated

September 23, 2026



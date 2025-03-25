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
| `dataImport_Script.py` | Script to scrape and update the latest win rate and matchup data from [rivalsmeta.com](https://rivalsmeta.com/) |
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

1. **Update data**: Run `dataImport_Script.py` to scrape the latest character matchup data.
2. **Solve problems**: Open `main.ipynb` for the full suite of optimization tools and demonstrations.


---

## Last Updated

March 17, 2025



"""Fetch Rivals Meta matchups; rows are heroes and columns are opponents."""

from pathlib import Path
import re
import time

import numpy as np
import pandas as pd
import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from scipy.stats import gaussian_kde
from urllib3.util.retry import Retry

vanguards = sorted([
    "Venom", "Emma Frost", "Magneto", "Doctor Strange", "The Thing", "Groot", "Hulk", "Thor", "Peni Parker",
    "Captain America", "Rogue", "Angela", "Deadpool Vanguard", "The Hood", "Devil Dinosaur"
])

duelists = sorted([
    "Moon Knight", "Squirrel Girl", "Human Torch", "Black Widow", "Namor", "The Punisher",
    "Hawkeye", "Scarlet Witch", "Psylocke", "Winter Soldier", "Wolverine", "Iron Man", "Hela",
    "Mister Fantastic", "Spider Man", "Iron Fist", "Star Lord", "Black Panther", "Storm", "Magik",
    "Phoenix", "Blade", "Daredevil", "Deadpool Duelist", "Cyclops", "Gorr The God Butcher", "Elsa Bloodstone",
    "Black Cat"
])

strategists = sorted([
    "Jeff The Land Shark", "Luna Snow", "Cloak & Dagger", "Invisible Woman", "Adam Warlock",
    "Loki", "Mantis", "Rocket Raccoon", "Gambit", "Ultron", "Deadpool Strategist", "Jubilee", "White Fox",
])

sorted_heroes = vanguards + duelists + strategists
BASE_URL = "https://rivalsmeta.com/characters/{}/matchups"
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; OptimalRivalry/1.0)"}


def format_hero_name(hero_name):
    """Use the URL slug as identity, independent of punctuation/display names."""
    name = hero_name.lower().replace("&", " ")
    return re.sub(r"[^a-z0-9]+", "-", name).strip("-")


def parse_matchups(html, hero, heroes=None):
    """Read named columns, without depending on image classes or cell order."""
    heroes = sorted_heroes if heroes is None else list(heroes)
    names_by_slug = {format_hero_name(name): name for name in heroes}
    soup = BeautifulSoup(html, "html.parser")
    matchups = {}
    for table in soup.find_all("table"):
        headings = [th.get_text(" ", strip=True).casefold()
                    for th in table.select("thead th")]
        if not {"hero", "win rate", "matches"}.issubset(headings):
            continue
        hero_col, rate_col, matches_col = (
            headings.index(name) for name in ("hero", "win rate", "matches")
        )
        for row in table.select("tbody tr"):
            cells = row.find_all("td", recursive=False)
            if len(cells) <= max(hero_col, rate_col, matches_col):
                raise ValueError(f"{hero}: incomplete matchup row")
            hero_cell = cells[hero_col]
            link = hero_cell.find("a", href=re.compile(r"^/characters/"))
            if link:
                slug = link["href"].split("/")[2]
            else:
                img = hero_cell.find("img", alt=True)
                name = img["alt"] if img else hero_cell.get_text(" ", strip=True)
                slug = format_hero_name(name)
            opponent = names_by_slug.get(slug)
            if opponent is None:
                raise ValueError(f"{hero}: unknown opponent {slug!r}; update the hero lists")
            rate_text = cells[rate_col].get_text("", strip=True)
            count_text = re.sub(r"[,\s]", "", cells[matches_col].get_text(strip=True))
            if not re.fullmatch(r"\d+(?:\.\d+)?\s*%", rate_text):
                raise ValueError(f"{hero} vs {opponent}: invalid win rate {rate_text!r}")
            if not re.fullmatch(r"\d+", count_text):
                raise ValueError(f"{hero} vs {opponent}: invalid match count {count_text!r}")
            rate, count = float(rate_text.rstrip("%")), int(count_text)
            if not 0 <= rate <= 100 or count <= 0:
                raise ValueError(f"{hero} vs {opponent}: win rate/count out of range")
            if opponent in matchups:
                raise ValueError(f"{hero}: duplicate matchup for {opponent}")
            matchups[opponent] = (rate, count)

    missing = set(heroes) - {hero} - matchups.keys()
    if not matchups or missing:
        raise ValueError(
            f"{hero}: missing matchup data for {', '.join(sorted(missing)) or 'all heroes'}. "
            "The page may be unavailable or its layout may have changed."
        )
    # Preserve the original model's synthetic self-match convention.
    opponent_counts = [count for name, (_, count) in matchups.items() if name != hero]
    matchups[hero] = (50.0, int(np.mean(opponent_counts)))
    return matchups


def scrape_matrices(heroes=None, delay=0.5):
    """Fetch each hero once for both matrices; fail before exporting partial data."""
    heroes = sorted_heroes if heroes is None else list(heroes)
    if len(heroes) < 2 or len(set(map(format_hero_name, heroes))) != len(heroes):
        raise ValueError("Provide at least two distinct heroes")
    rates = pd.DataFrame(index=heroes, columns=heroes, dtype=float)
    counts = pd.DataFrame(index=heroes, columns=heroes, dtype=float)
    retry = Retry(total=3, backoff_factor=1, status_forcelist=[429, 500, 502, 503, 504])
    with requests.Session() as session:
        session.headers.update(HEADERS)
        session.mount("https://", HTTPAdapter(max_retries=retry))
        for i, hero in enumerate(heroes):
            if i:
                time.sleep(delay)
            print(f"Fetching {hero} ({i + 1}/{len(heroes)})...", flush=True)
            response = session.get(BASE_URL.format(format_hero_name(hero)), timeout=30)
            response.raise_for_status()
            matchups = parse_matchups(response.text, hero, heroes)
            for opponent, (rate, count) in matchups.items():
                rates.at[hero, opponent] = rate
                counts.at[hero, opponent] = count
    return rates, counts.astype("int64")


def build_payoff_matrix(win_rates, num_matches):
    """Keep the existing weighted KDE payoff, using its analytic integral."""
    if not (win_rates.index.equals(num_matches.index)
            and win_rates.columns.equals(num_matches.columns)):
        raise ValueError("Win-rate and match-count labels must match")
    values = win_rates.to_numpy(dtype=float)
    weights = num_matches.to_numpy(dtype=float)
    if (not np.isfinite(values).all() or not np.isfinite(weights).all()
            or (weights <= 0).any() or (values < 0).any() or (values > 100).any()):
        raise ValueError("Cannot calculate payoffs from missing or invalid matchup data")
    low, high = values.min(), values.max()
    if low == high:
        raise ValueError("Cannot fit a KDE to constant win rates")
    kde = gaussian_kde(values.ravel(), weights=weights.ravel())
    total_cdf = kde.integrate_box_1d(low, high)
    # Repeated win rates share a payoff; integrate each distinct value once.
    utilities = {rate: round(2 * kde.integrate_box_1d(low, rate) / total_cdf - 1, 2)
                 for rate in np.unique(values)}
    payoff = np.array([utilities[rate] for rate in values.ravel()]).reshape(values.shape)
    return pd.DataFrame(payoff, index=win_rates.index, columns=win_rates.columns)


def export_matrices(win_rates, num_matches, payoff, output_dir="."):
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    for name, frame in (("WinRate", win_rates), ("NumMatches", num_matches), ("Payoff", payoff)):
        path = output_dir / f"MarvelRivals_{name}_Matrix.csv"
        frame.to_csv(path, index=True)
        print(f"Exported {path}")


def main(output_dir="."):
    win_rates, num_matches = scrape_matrices()
    payoff = build_payoff_matrix(win_rates, num_matches)
    # All requests, parsing, and payoff calculation must succeed before writing.
    export_matrices(win_rates, num_matches, payoff, output_dir)
    return win_rates, num_matches, payoff

if __name__ == "__main__":
    WinRate_df, NumMatches_df, Payoff_df = main()

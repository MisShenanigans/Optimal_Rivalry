import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import gaussian_kde
from scipy.integrate import quad

vanguards = sorted([
    "Venom", "Emma Frost", "Magneto", "Doctor Strange", "The Thing", "Groot", "Hulk", "Thor", "Peni Parker", "Captain America", "Rogue", "Angela"
])

duelists = sorted([
    "Moon Knight", "Squirrel Girl", "Human Torch", "Black Widow", "Namor", "The Punisher",
    "Hawkeye", "Scarlet Witch", "Psylocke", "Winter Soldier", "Wolverine", "Iron Man", "Hela",
    "Mister Fantastic", "Spider Man", "Iron Fist", "Star Lord", "Black Panther", "Storm", "Magik", 
    "Phoenix", "Blade", "Daredevil"
])

strategists = sorted([
    "Jeff The Land Shark", "Luna Snow", "Cloak & Dagger", "Invisible Woman", "Adam Warlock",
    "Loki", "Mantis", "Rocket Raccoon", "Gambit", "Ultron"
])
sorted_heroes = vanguards + duelists + strategists
WinRate_df = pd.DataFrame(index=sorted_heroes)
base_url = "https://rivalsmeta.com/characters/{}/matchups"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}

def format_hero_name(hero_name):
    if hero_name == "Cloak & Dagger":
        return "cloak-dagger"  # Special case
    return hero_name.lower().replace(" ", "-")


for hero in sorted_heroes:
    print(f"Fetching matchups for {hero}...")
    hero_url_name = format_hero_name(hero)
    url = base_url.format(hero_url_name)
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        print(f"Failed to fetch {hero}, status code: {response.status_code}")
        continue
    soup = BeautifulSoup(response.text, "html.parser")
    tables = soup.find_all("tbody")
    matchup_data = {}
    for table in tables:
        for row in table.find_all("tr"):
            columns = row.find_all("td")
            if len(columns) < 3:
                continue 
            opponent_name_tag = columns[0].find("img", class_="hero-img")
            if opponent_name_tag:
                opponent_name = opponent_name_tag["alt"].strip()
            else:
                continue
            win_rate = columns[1].text.strip().replace("%", "")
            if opponent_name in sorted_heroes:  # Ensure the opponent is a valid in-game hero
                matchup_data[opponent_name] = float(win_rate)

    matchup_data[hero] = 50.0
    win_rate_series = pd.Series(matchup_data, name=hero)
    WinRate_df[hero] = win_rate_series
    time.sleep(0.5)
WinRate_df = WinRate_df.loc[sorted_heroes]

NumMatchesdf = pd.DataFrame(index=sorted_heroes)

for hero in sorted_heroes:
    print(f"Fetching match counts for {hero}...")

    hero_url_name = format_hero_name(hero)
    url = base_url.format(hero_url_name)
    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        print(f"Failed to fetch {hero}, status code: {response.status_code}")
        continue

    soup = BeautifulSoup(response.text, "html.parser")
    tables = soup.find_all("tbody")

    match_count_data = {}

    for table in tables:
        for row in table.find_all("tr"):
            columns = row.find_all("td")
            if len(columns) < 4:
                continue 

            opponent_tag = columns[0].find("img", class_="hero-img")
            if not opponent_tag:
                continue

            opponent_name = opponent_tag["alt"].strip()

            match_count_text = columns[3].text.strip().replace(",", "")
            if not match_count_text.isdigit():
                continue

            match_count = int(match_count_text)

            if opponent_name in sorted_heroes:
                match_count_data[opponent_name] = match_count

    if match_count_data:
        match_count_data[hero] = int(np.mean(list(match_count_data.values())))

    NumMatchesdf[hero] = pd.Series(match_count_data, name=hero)
    time.sleep(0.5)

NumMatchesdf = NumMatchesdf.loc[sorted_heroes]

WinRate_df = WinRate_df.T
NumMatches_df = NumMatchesdf.T
print(f"Outporting MarvelRivals_WinRate_Matrix.csv")
WinRate_df.to_csv("MarvelRivals_WinRate_Matrix.csv", index=True)
print(f"Outporting MarvelRivals_NumMatches_Matrix.csv")
NumMatches_df.to_csv("MarvelRivals_NumMatches_Matrix.csv", index=True)

min_value = WinRate_df.min().min()
max_value = WinRate_df.max().max()

win_rates = WinRate_df.astype(float).values.flatten()
num_matches = NumMatches_df.astype(float).values.flatten()
valid_indices = np.isfinite(win_rates) & np.isfinite(num_matches)
win_rates = win_rates[valid_indices]
num_matches = num_matches[valid_indices]

kde = gaussian_kde(win_rates, weights=num_matches)

def utility_score(kde, winrate, min_value, max_value):
    total_cdf, _ = quad(kde, min_value, max_value)
    cdf, _ = quad(kde, min_value, winrate)
    utility = ((cdf - (total_cdf / 2)) / (total_cdf / 2))
    return round(utility, 2)

Payoff_df = WinRate_df.copy()

print(f"Making Payoff Dataframe")
for row_hero in WinRate_df.index:
    for col_hero in WinRate_df.columns:
        winrate = WinRate_df.at[row_hero, col_hero]
        Payoff_df.at[row_hero, col_hero] = utility_score(kde, winrate, min_value, max_value)

Payoff_df = Payoff_df.astype(float)

print(f"Outporting MarvelRivals_Payoff_Matrix.csv")
Payoff_df.to_csv("MarvelRivals_Payoff_Matrix.csv", index=True)




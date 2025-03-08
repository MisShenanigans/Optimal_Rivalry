import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import numpy as np

vanguards = sorted([
    "Venom", "Magneto", "Doctor Strange", "The Thing", "Groot", "Hulk", "Thor", "Peni Parker", "Captain America"
])

duelists = sorted([
    "Moon Knight", "Squirrel Girl", "Human Torch", "Black Widow", "Namor", "The Punisher",
    "Hawkeye", "Scarlet Witch", "Psylocke", "Winter Soldier", "Wolverine", "Iron Man", "Hela",
    "Mister Fantastic", "Spider Man", "Iron Fist", "Star Lord", "Black Panther", "Storm", "Magik"
])

strategists = sorted([
    "Jeff The Land Shark", "Luna Snow", "Cloak & Dagger", "Invisible Woman", "Adam Warlock",
    "Loki", "Mantis", "Rocket Raccoon"
])
sorted_heroes = vanguards + duelists + strategists
WinRate_df = pd.DataFrame(index=sorted_heroes)
base_url = "https://rivalsmeta.com/characters/{}/matchups"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}

def format_hero_name(hero_name):
    """Converts hero names to the correct URL format."""
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
    time.sleep(2)
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
            if len(columns) < 3:
                continue 
            opponent_name_tag = columns[0].find("img", class_="hero-img")
            if opponent_name_tag:
                opponent_name = opponent_name_tag["alt"].strip()
            else:
                continue
            match_count_text = columns[2].text.strip().replace(",", "")  # Remove commas
            if match_count_text.isdigit():
                match_count = int(match_count_text)
            else:
                continue  
            if opponent_name in sorted_heroes: 
                match_count_data[opponent_name] = match_count
    if match_count_data:
        match_count_data[hero] = int(np.mean(list(match_count_data.values())))
    match_count_series = pd.Series(match_count_data, name=hero)
    NumMatchesdf[hero] = match_count_series
    time.sleep(2)

NumMatchesdf = NumMatchesdf.loc[sorted_heroes]

WinRate_df.to_csv("MarvelRivals_WinRate_Matrix.csv")
NumMatchesdf.to_csv("MarvelRivals_NumMatches_Matrix.csv")

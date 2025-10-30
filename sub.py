import requests
import json
import sys
import os

api_key = os.environ.get("SUBDL_API_KEY")

is_show = sys.argv[3] == "show"
film_name = sys.argv[1]
season_number = sys.argv[2] if is_show else None

headers = {'Accept': 'application/json'}

def fetch_options():
    base_url = f'https://api.subdl.com/api/v1/subtitles?api_key={api_key}&film_name={film_name}&languages=EN'
    url = f'{base_url}&type=tv' if is_show else f'{base_url}&type=movie'
    return requests.get(url, headers=headers).json().get('results', [])

def choose_id(option):
    return option['imdb_id'] or option['sd_id'] or option['tmdb_id']

def fetch_subtitles(id_value, id_type):
    key = f"{id_type}={id_value}"
    url = f"https://api.subdl.com/api/v1/subtitles?api_key={api_key}&{key}"
    if is_show:
        url += f"&season_number={season_number}&type=tv"
    else:
        url += "&type=movie"
    res = requests.get(url, headers=headers).json()
    return [s for s in res.get("subtitles", []) if s.get("episode") is None]

# Main logic
options = fetch_options()
if not options:
    exit()

first = options[0]
id_value = choose_id(first)
id_type = 'imdb_id' if first['imdb_id'] else 'sd_id' if first['sd_id'] else 'tmdb_id'

subtitles = fetch_subtitles(id_value, id_type)
with open("selections.json", "w") as f:
    json.dump(subtitles, f)

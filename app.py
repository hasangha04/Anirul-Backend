from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
import subprocess
import requests
import os
import json

load_dotenv()
api_key = os.environ.get("SUBDL_API_KEY")

app = Flask(__name__)
CORS(app)

DOWNLOADS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "downloaded.json")

def get_downloaded_items():
    if not os.path.exists(DOWNLOADS_FILE):
        return []

    try:
        with open(DOWNLOADS_FILE, "r", encoding="utf-8") as file:
            items = json.load(file)

        if not isinstance(items, list):
            return []

        return [
            item for item in items
            if isinstance(item, dict)
            and {"selection", "is_show", "season", "folder"}.issubset(item)
        ]

    except (json.JSONDecodeError, OSError):
        return []

def mark_item_downloaded(selection, is_show, idValue, season=None):
    downloaded_items = get_downloaded_items()

    new_item = {
        "selection": str(selection),
        "is_show": bool(is_show),
        "season": int(season) if is_show else None,
        "id": str(idValue)
    }

    # Avoid adding the same show season or movie twice.
    downloaded_items = [
        item for item in downloaded_items
        if not (
            str(item["selection"]) == str(selection)
            and bool(item["is_show"]) == bool(is_show)
            and item["season"] == new_item["season"]
            and str(item["id"]) == str(idValue)
        )
    ]

    downloaded_items.append(new_item)

    with open(DOWNLOADS_FILE, "w", encoding="utf-8") as file:
        json.dump(downloaded_items, file, indent=2)


def is_item_downloaded(folder, is_show, idValue, season=None):
    target_season = int(season) if is_show else None

    for item in get_downloaded_items():
        if (
            str(item["name"]) == str(folder)
            and bool(item["is_show"]) == bool(is_show)
            and item["season"] == target_season
            and str(item["id"]) == str(idValue)
        ):
            return True

    return False

@app.route("/")
def home():
    return "Subtitle backend is live"

@app.route("/search", methods=["POST"])
def search_subtitles():
    data = request.get_json()
    name = data["name"]
    season = data["season"]
    idValue = data["id"]
    selection = data["selection"]
    query = data["query"]
    is_show = data["isShow"]

    if is_show:
        season_folder = f"Season {season}"
    else:
        season_folder = ""
    full_path = os.path.join(name, season_folder)
    os.makedirs(full_path, exist_ok=True)


    if not is_item_downloaded(name, is_show, idValue, season):
        download_args = ["python", "download.py", name, selection, str( not is_show), str(season) if is_show else "1"]
        subprocess.run(download_args, check=True)
        mark_item_downloaded(name, is_show, idValue, season)

    # search_args = ["python", "search.py", os.path.join(name, season_folder), query]
    # result = subprocess.run(search_args, capture_output=True, text=True)

    # return jsonify({"results": result.stdout})
    return jsonify({"results": "Search functionality is currently disabled."})

@app.route("/search", methods=["GET"])
def search():
    headers = {'Accept': 'application/json'}
    name = request.args.get("name")
    type = request.args.get("type")
    base_url = f'https://api.subdl.com/api/v1/subtitles?api_key={api_key}&film_name={name}&languages=EN'
    url = f'{base_url}&type=tv' if type == "tv" else f'{base_url}&type=movie'
    return requests.get(url, headers=headers, verify=False).json().get('results', [])

@app.route("/options", methods=["GET"])
def options():
    headers = {'Accept': 'application/json'}
    value = request.args.get("value")
    type = request.args.get("type")
    idType = request.args.get("idType")

    if type == "tv":
        season = request.args.get("season")
        if (idType == '1'):
            url = f'https://api.subdl.com/api/v1/subtitles?api_key={api_key}&imdb_id={value}&season_number={season}&type=tv&languages=EN'
            res = requests.get(url, headers=headers).json()
            return [s for s in res.get("subtitles", []) if s.get("episode") is None]
        elif (idType == '2'):
            url = f'https://api.subdl.com/api/v1/subtitles?api_key={api_key}&sd_id={value}&season_number={season}&type=tv&languages=EN'
            res = requests.get(url, headers=headers).json()
            return [s for s in res.get("subtitles", []) if s.get("episode") is None]
        elif (idType == '3'):
            url = f'https://api.subdl.com/api/v1/subtitles?api_key={api_key}&tmdb_id={value}&season_number={season}&type=tv&languages=EN'
            res = requests.get(url, headers=headers).json()
            return [s for s in res.get("subtitles", []) if s.get("episode") is None]
    else:
        if (idType == '1'):
            url = f'https://api.subdl.com/api/v1/subtitles?api_key={api_key}&imdb_id={value}&type=movie&languages=EN'
            res = requests.get(url, headers=headers).json()
            return [s for s in res.get("subtitles", []) if s.get("episode") is None]
        elif (idType == '2'):
            url = f'https://api.subdl.com/api/v1/subtitles?api_key={api_key}&sd_id={value}&type=movie&languages=EN'
            res = requests.get(url, headers=headers).json()
            return [s for s in res.get("subtitles", []) if s.get("episode") is None]
        elif (idType == '3'):
            url = f'https://api.subdl.com/api/v1/subtitles?api_key={api_key}&tmdb_id={value}&type=movie&languages=EN'
            res = requests.get(url, headers=headers).json()
            return [s for s in res.get("subtitles", []) if s.get("episode") is None]

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

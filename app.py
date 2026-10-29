from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
from pymongo import MongoClient
import subprocess
import requests
import os

load_dotenv()
api_key = os.environ.get("SUBDL_API_KEY")
MONGODB_URI = os.getenv("MONGODB_URI")

app = Flask(__name__)
CORS(app)

if not MONGODB_URI:
    raise ValueError("MONGODB_URI is missing from .env")

client = MongoClient(
    MONGODB_URI,
    serverSelectionTimeoutMS=15000
)

db = client["Anirul"]
downloaded = db["Downloaded"]

client.admin.command("ping")

def mark_item_downloaded(name, is_show, idValue, season=None):
    downloaded.insert_one({
        "id": str(idValue),
        "name": str(name),
        "is_show": bool(is_show),
        "season": int(season) if is_show else None,
    })  

def is_item_downloaded(name, is_show, idValue, season=None):
    target_season = int(season) if is_show else None

    if downloaded.find_one({
        "id": str(idValue),
        "name": str(name),
        "is_show": bool(is_show),
        "season": target_season
    }):
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

    if not is_item_downloaded(name, is_show, idValue, season):
        download_args = ["python", "download.py", name, selection, str(not is_show), idValue, str(season) if is_show else "1"]
        subprocess.run(download_args, check=True)
        mark_item_downloaded(name, is_show, idValue, season)

    search_args = ["python", "search.py", idValue, query]
    result = subprocess.run(search_args, capture_output=True, text=True)

    return jsonify({"results": result.stdout})

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

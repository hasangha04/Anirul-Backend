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

@app.route("/")
def home():
    return "Subtitle backend is live"

@app.route("/search", methods=["POST"])
def search_subtitles():
    data = request.get_json()
    folder = data["folder"]
    season = data["season"]
    selection = data["selection"]
    query = data["query"]
    is_show = data["isShow"]

    if is_show:
        season_folder = f"Season {season}"
    else:
        season_folder = ""
    full_path = os.path.join(folder, season_folder)
    os.makedirs(full_path, exist_ok=True)

    download_args = ["python", "download.py", full_path, selection, str(is_show)]
    subprocess.run(download_args, check=True)

    search_args = ["python", "search.py", os.path.join(folder, season_folder), query]
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

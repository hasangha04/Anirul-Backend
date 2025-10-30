from flask import Flask, request, jsonify
from flask_cors import CORS
import subprocess
import os
import json

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
    query = data["query"]
    is_show = data["isShow"]

    season_folder = f"Season {season}"
    full_path = os.path.join(folder, season_folder)
    os.makedirs(full_path, exist_ok=True)

    # 1. Run sub.py
    sub_args = ["python", "sub.py", folder, season, "show" if is_show else "movie"]
    subprocess.run(sub_args, check=True)

    if not os.path.exists("selections.json"):
        return jsonify({"error": "No subtitle selections found"}), 404

    # 2. Run download.py (always select first option)
    download_args = ["python", "download.py", full_path, "0"]
    subprocess.run(download_args, check=True)

    # 3. Run search.py
    search_args = ["python", "search.py", os.path.join(folder, season_folder), query]
    result = subprocess.run(search_args, capture_output=True, text=True)

    return jsonify({"results": result.stdout})

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

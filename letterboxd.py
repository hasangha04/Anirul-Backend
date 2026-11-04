import os
import requests
import zipfile
import re
import tempfile
import csv
import urllib.request
import sys

from dotenv import load_dotenv
from pymongo import MongoClient

imdbregex = r"imdb.com/title/(tt\d+)"
http = urllib.request

load_dotenv()

MONGODB_URI = os.getenv("MONGODB_URI")
SUBDL_API_KEY = os.getenv("SUBDL_API_KEY")

client = MongoClient(MONGODB_URI)
db = client["Anirul"]

subtitles = db["Subtitles"]
downloaded = db["Downloaded"]

letterboxd_movies = {}

def parse_csv(args):
    with open(args[0], mode="r", encoding="utf-8-sig") as csv_file:
        csv_reader = csv.DictReader(csv_file)

        for row in csv_reader:

            html = getHTML(row)

            imdbid = getIMDBIDFromHTML(html)

            letterboxd_movies[row["Name"]] = imdbid

        for item in letterboxd_movies:
            if downloaded.find_one(
                {
                    "name": item,
                    "is_show": False,
                    "id": letterboxd_movies[item],
                }):
                letterboxd_movies.popitem(item)
                

            

def getHTML(row):
    if "Letterboxd URI" in row and row["Letterboxd URI"].startswith("https://"):
        request = urllib.request.Request(
            row["Letterboxd URI"],
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.9",
            }
        )

        try:
            response = http.urlopen(request, timeout=15)
            html = response.read().decode("utf-8")
            response.close()
            return html

        except urllib.error.HTTPError as e:
            print(f"HTTP Error {e.code} for {row['Letterboxd URI']}")
            return ""

        except urllib.error.URLError as e:
            print(f"URL Error: {e.reason}")
            return ""

    return ""

def getIMDBIDFromHTML(htmlstring: str):
    matches = re.finditer(imdbregex, htmlstring, re.MULTILINE)
    for matchNum, match in enumerate(matches, start=1):
        groups = match.groups()
        if len(groups):
            return groups[0]
    return ""

def get_movie_options(imdb_id):
    url = (
        f"https://api.subdl.com/api/v1/subtitles"
        f"?api_key={SUBDL_API_KEY}"
        f"&imdb_id={imdb_id}"
        f"&type=movie&languages=EN"
    )

    response = requests.get(url, timeout=30)
    response.raise_for_status()

    return [
        option for option in response.json().get("subtitles", [])
        if option.get("episode") is None
    ]



# Keep your existing functions:
# sanitize_filename()
# is_valid_srt()
# download_and_store()
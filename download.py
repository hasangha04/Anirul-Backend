import os
import sys
import requests
import zipfile
import re
import tempfile

from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()

MONGODB_URI = os.getenv("MONGODB_URI")

if not MONGODB_URI:
    raise ValueError("MONGODB_URI is missing from .env")

client = MongoClient(
    MONGODB_URI,
    serverSelectionTimeoutMS=15000
)

# Select the database and collection.
db = client["Anirul"]
subtitles = db["Subtitles"]

def sanitize_filename(filename):
    invalid_chars = ['::', ':', '<', '>', '?', '*', '|', '"', '/', '\\']
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    return filename

def is_valid_srt(subtitle_file):
    with open(subtitle_file, "r", encoding="utf-8-sig", errors="replace") as file:
        first_line = next((line.strip() for line in file if line.strip()), "")
    return first_line == "1"

def download_and_store(url, title, is_movie, season_number=1):
    with tempfile.TemporaryDirectory() as temp_folder:
        zip_path = os.path.join(temp_folder,"subtitle.zip")

        # Download the ZIP file temporarily.
        with requests.get(url, stream=True, timeout=60) as response:
            response.raise_for_status()

            with open(zip_path, "wb") as file:
                for chunk in response.iter_content(8192):
                    if chunk:
                        file.write(chunk)

        # Extract files safely into temporary storage.
        with zipfile.ZipFile(zip_path, "r") as zip_file:
            temp_root = os.path.realpath(temp_folder)

            for member in zip_file.infolist():
                    if member.is_dir():
                        continue

                    target_path = os.path.realpath(os.path.join(temp_folder, member.filename))

                    if os.path.commonpath([temp_root, target_path]) != temp_root: continue

                    zip_file.extract(member, temp_folder)

        subtitle_files = []
        for root, _, files in os.walk(temp_folder):
            for filename in files:
                if filename.lower().endswith(".srt"):
                    path = os.path.join(root, filename)

                    if is_valid_srt(path):
                        subtitle_files.append(path)

        if not subtitle_files:
            print("No valid SRT files found; nothing was saved.")
            return

        # Sort files to make fallback episode numbering predictable.
        subtitle_files.sort()

        for file_number, subtitle_file in enumerate(
            subtitle_files,
            start=1
        ):
            episode_number = None

            if is_movie:
                filename = sanitize_filename(title) + ".srt"

            else:
                episode_match = re.search(
                    r"(?:s\d{1,2}[ ._-]*)?e(\d{1,3})|episode[ ._-]*(\d{1,3})",
                    os.path.basename(subtitle_file),
                    re.IGNORECASE
                )

                if episode_match:
                    episode_number = int(next(group for group in episode_match.groups() if group))
                else:
                    episode_number = file_number

                filename = (
                    f"{sanitize_filename(title)} "
                    f"S{season_number:02d}"
                    f"E{episode_number:02d}.srt"
                )

            with open(subtitle_file,"r", encoding="utf-8-sig", errors="replace") as file:
                content = file.read()

            document = {
                "filename": filename,
                "title": title,
                "content": content,
                "type": "movie" if is_movie else "tv",
            }

            if not is_movie:
                document["season"] = season_number
                document["episode"] = episode_number

            result = subtitles.insert_one(document)

            print(
                f"Saved {filename} to MongoDB "
                f"(ID: {result.inserted_id})"
            )

if len(sys.argv) < 4:
    print('Usage: python download.py "<title>" ''<index> <is_movie> [season_number]')
    sys.exit(1)

title = sys.argv[1]
choice = sys.argv[2]
is_movie = sys.argv[3].lower() == "true"

season_number = int(sys.argv[4]) if len(sys.argv) > 4 and sys.argv[4] else 1

url = f"https://dl.subdl.com/{choice}"

try:
    # Verify the database connection before downloading.
    client.admin.command("ping")
    print("Connected to MongoDB successfully!")

    download_and_store(url, title, is_movie, season_number)

except Exception as error:
    print(f"Error: {error}")
    sys.exit(1)

finally:
    client.close()

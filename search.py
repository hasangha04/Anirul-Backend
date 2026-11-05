import os
import sys
import json
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()
MONGODB_URI = os.getenv("MONGODB_URI")

if not MONGODB_URI:
    raise ValueError("MONGODB_URI is missing from .env")

client = MongoClient(
    MONGODB_URI,
    serverSelectionTimeoutMS=15000
)

db = client["Anirul"]
subtitles_collection = db["Subtitles"]

client.admin.command("ping")

def search(idValue, term, checkAll, season=None):
    results = []

    if not checkAll:
        search_filter = {
            "id": str(idValue)
        }

        if season is not None:
            search_filter["season"] = season

        subtitles = subtitles_collection.find(search_filter)
    else:
        subtitles = subtitles_collection.find({})

    for item in subtitles:
        content = item.get("content", "")

        # download.py saves the subtitle content as a string.
        if not isinstance(content, str):
            continue

        # Split the subtitle content into individual lines.
        lines = content.splitlines()

        sections = []
        block = []

        # Separate the SRT file into subtitle blocks.
        for line in lines:
            if not line.strip():
                if block:
                    sections.append(block)
                    block = []
            else:
                block.append(line)

        # Include the last block if the file doesn't end with a blank line.
        if block:
            sections.append(block)

        for section in sections:
            if len(section) < 3:
                continue

            timestamp = section[1]
            timestamp = " --> ".join(
                timestamp_part.split(",")[0]
                for timestamp_part in timestamp.split(" --> ")
            )
            subtitle_text = "\n".join(section[2:])

            if term.casefold() in subtitle_text.casefold():
                if (item.get("type") == "tv"):
                    results.append(
                        f"{item.get('title')} Season {item.get('season')} Episode {item.get('episode')}\n"
                        f"{timestamp}\n"
                        f"{subtitle_text}"
                    )
                else:
                    results.append(
                        f"{item.get('title')}\n"
                        f"{timestamp}\n"
                        f"{subtitle_text}"
                    )

    return results

if __name__ == "__main__":
    idValue = sys.argv[1]
    term = sys.argv[2]
    checkAll = sys.argv[3].lower() == "true"
    season = int(sys.argv[4]) if len(sys.argv) > 4 else None
    results = search(idValue, term, checkAll, season)
    print(json.dumps(results))

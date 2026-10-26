import os
import sys
import requests
import json
import zipfile
import re
import shutil
import tempfile

def sanitize_filename(filename):
    invalid_chars = ['::', ':', '<', '>', '?', '*', '|', '"', '/', '\\']
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    return filename

def is_valid_srt(subtitle_file):
    with open(subtitle_file, "r", encoding="utf-8-sig", errors="replace") as file:
        first_line = next((line.strip() for line in file if line.strip()), "")
    return first_line == "1"

def download_and_extract(url, dest_folder, filename, rename_subtitle=False):
    os.makedirs(dest_folder, exist_ok=True)
    with tempfile.TemporaryDirectory() as temp_folder:
        zip_path = os.path.join(temp_folder, filename + ".zip")
        with requests.get(url, stream=True) as r:
            r.raise_for_status()
            with open(zip_path, 'wb') as f:
                for chunk in r.iter_content(8192):
                    f.write(chunk)
        with zipfile.ZipFile(zip_path, 'r') as z:
            z.extractall(temp_folder)

        subtitle_files = []
        for root, _, files in os.walk(temp_folder):
            subtitle_files.extend(
                os.path.join(root, subtitle_file)
                for subtitle_file in files
                if subtitle_file.lower().endswith(".srt")
                and is_valid_srt(os.path.join(root, subtitle_file))
            )

        if not subtitle_files:
            print("No valid SRT files found; nothing was saved.")
            return

        if rename_subtitle:
            season_match = re.search(r"season\s*(\d+)", os.path.basename(dest_folder), re.IGNORECASE)
            season_number = int(season_match.group(1)) if season_match else 1
            show_name = os.path.basename(os.path.dirname(os.path.normpath(dest_folder)))
            show_name = sanitize_filename(show_name)

            for file_number, subtitle_file in enumerate(subtitle_files, start=1):
                episode_match = re.search(
                    r"(?:s\d{1,2}[ ._-]*)?e(\d{1,3})|episode[ ._-]*(\d{1,3})",
                    os.path.basename(subtitle_file),
                    re.IGNORECASE,
                )
                episode_number = next(
                    (group for group in episode_match.groups() if group),
                    str(file_number),
                ) if episode_match else str(file_number)
                target_name = f"{show_name} S{season_number:02d}E{int(episode_number):02d}.srt"
                target_path = os.path.join(dest_folder, sanitize_filename(target_name))
                shutil.move(subtitle_file, target_path)
        else:
            folder_name = os.path.basename(os.path.normpath(dest_folder))
            target_path = os.path.join(dest_folder, sanitize_filename(folder_name) + ".srt")
            shutil.move(subtitle_files[0], target_path)

if len(sys.argv) < 4:
    print("Usage: python download.py <dest_folder> <index> <is_movie>")
    sys.exit(1)

dest_folder = sys.argv[1]
choice = sys.argv[2]
rename_subtitle = sys.argv[3]
rename_subtitle = rename_subtitle.lower() == "true"

url = f"https://dl.subdl.com/{choice}"
name = sanitize_filename(choice)

download_and_extract(url, dest_folder, name, rename_subtitle)

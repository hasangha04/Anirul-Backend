import os
import sys
import requests
import json
import zipfile

def sanitize_filename(filename):
    invalid_chars = ['::', ':', '<', '>', '?', '*', '|', '"', '/', '\\']
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    return filename

def download_and_extract(url, dest_folder, filename):
    os.makedirs(dest_folder, exist_ok=True)
    zip_path = os.path.join(dest_folder, filename + ".zip")
    with requests.get(url, stream=True) as r:
        r.raise_for_status()
        with open(zip_path, 'wb') as f:
            for chunk in r.iter_content(8192):
                f.write(chunk)
    with zipfile.ZipFile(zip_path, 'r') as z:
        z.extractall(dest_folder)
    os.remove(zip_path)

if len(sys.argv) < 3:
    print("Usage: python download.py <dest_folder> <index>")
    sys.exit(1)

dest_folder = sys.argv[1]
selection_index = int(sys.argv[2])

with open("selections.json") as f:
    data = json.load(f)

choice = data[selection_index]
url = f"https://dl.subdl.com/{choice['url']}"
name = sanitize_filename(choice['name'])

download_and_extract(url, dest_folder, name)

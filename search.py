import os
import chardet
import sys

def detect_encoding(file_path):
    with open(file_path, 'rb') as f:
        return chardet.detect(f.read())['encoding']

def search(directory, term):
    results = []
    for fname in os.listdir(directory):
        if not fname.endswith(".srt"):
            continue
        path = os.path.join(directory, fname)
        encoding = detect_encoding(path)
        with open(path, 'r', encoding=encoding) as f:
            lines = f.read().splitlines()

        sections = []
        block = []
        for line in lines:
            if not line.strip():
                if block: sections.append(block)
                block = []
            else:
                block.append(line.strip())
        if block: sections.append(block)

        for section in sections:
            if len(section) < 3:
                continue
            time = section[1]
            text = " ".join(section[2:]).lower()
            if term.lower() in text:
                results.append(f"{fname} @ {time}\n{text}\n")
    return results

if __name__ == "__main__":
    directory = sys.argv[1]
    term = sys.argv[2]
    for match in search(directory, term):
        print(match)

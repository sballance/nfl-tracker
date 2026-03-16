import requests
import json
import os

GIST_TOKEN = os.getenv("GIST_TOKEN")
GIST_ID = os.getenv("GIST_ID")

HEADERS = {
    "Authorization": f"token {GIST_TOKEN}",
    "Accept": "application/vnd.github+json"
}

def load_snapshot(filename):
    r = requests.get(f"https://api.github.com/gists/{GIST_ID}", headers=HEADERS)
    r.raise_for_status()
    content = r.json()["files"][filename]["content"]
    return json.loads(content)


def save_snapshot(filename, data):
    payload = {
        "files": {
            filename: {
                "content": json.dumps(data)
            }
        }
    }
    r = requests.patch(f"https://api.github.com/gists/{GIST_ID}", headers=HEADERS, json=payload)
    r.raise_for_status()
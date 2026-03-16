import requests
from bs4 import BeautifulSoup
import json
import os
from dotenv import load_dotenv

load_dotenv()

NFL_WEBHOOK = os.getenv("NFL_WEBHOOK")
SEAHAWKS_WEBHOOK = os.getenv("SEAHAWKS_WEBHOOK")

URL = "https://www.spotrac.com/nfl/transactions"
HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

def fetch_transactions():
    r = requests.get(URL, headers=HEADERS)
    print(r.status_code)  # check if request succeeded
    soup = BeautifulSoup(r.text, "html.parser")

    items = soup.select("ul.list-group li.list-group-item")
    print(f"Found {len(items)} items")  # check if selector is matching anything

    if items:
        print(items[0])  # print the first item's raw HTML to inspect it

    transactions = []

    for item in items:
        try:
            player_tag = item.select_one("a[href*='/nfl/player/']")
            if not player_tag:
                continue
            # ... rest of parsing
        except Exception as e:
            print(f"Skipping item due to error: {e}")
            continue
        player_text = player_tag.text.strip()
        player_link = player_tag["href"]

        name = player_text.split("(")[0].strip()
        position = player_text.split("(")[1].replace(")", "").strip()

        logo = item.select_one("img")["src"]

        small = item.select_one("small")

        date = small.select_one("strong").text.strip()

        description = small.get_text(" ", strip=True).replace(date, "").replace("-", "").strip()

        tx_id = player_text + date + description

        transactions.append({
            "id": tx_id,
            "name": name,
            "position": position,
            "date": date,
            "description": description,
            "logo": logo,
            "link": player_link
        })

    return transactions


def send_alert(tx, webhooks):
    embed = {
        "title": f"{tx['name']} ({tx['position']})",
        "url": tx["link"],
        "description": tx["description"],
        "color": 15158332,  # red
        "thumbnail": {
            "url": tx["logo"]
        },
        "fields": [
            {
                "name": "Date",
                "value": tx["date"],
                "inline": True
            }
        ]
    }

    for webhook in webhooks:
        requests.post(webhook, json={"embeds": [embed]})


def main():

    transactions = fetch_transactions()

    try:
        with open("seen_transactions.json") as f:
            seen = json.load(f)
    except:
        seen = []

    seen_ids = set(seen)

    new_seen = list(seen_ids)

    if not transactions:
        requests.post(NFL_WEBHOOK, json={"content": "⚠️ Scraper returned no transactions — the page structure may have changed."})
        return

    for tx in transactions:

        if tx["id"] in seen_ids:
            continue  # stop scanning once we hit known transaction

        webhooks = [NFL_WEBHOOK]
        if "Seahawks" in tx["description"]:
            webhooks.append(SEAHAWKS_WEBHOOK)

        send_alert(tx, webhooks)

        new_seen.append(tx["id"])

    with open("seen_transactions.json", "w") as f:
        json.dump(new_seen, f)


if __name__ == "__main__":
    main()

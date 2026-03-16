import requests
import os
from dotenv import load_dotenv
from gist_storage import load_snapshot, save_snapshot

load_dotenv()

INJURIES_WEBHOOK = os.getenv("INJURIES_WEBHOOK")
SEAHAWKS_WEBHOOK = os.getenv("SEAHAWKS_WEBHOOK")
API_URL = "https://www.rotowire.com/football/tables/injury-report.php?team=ALL&pos=ALL"
SNAPSHOT_FILE = "seen_injuries.json"

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

def fetch_injuries():
    r = requests.get(API_URL, headers=HEADERS)
    r.raise_for_status()
    players = r.json()
    return [p for p in players if p.get("team") != "FA"]


def send_alert(player, change_type, webhooks):
    colors = {
        "new": 15158332,      # red
        "status": 16776960,   # yellow
        "injury": 3447003,    # blue
    }

    embed = {
        "title": f"{player['player']} ({player['position']} - {player['team']})",
        "url": f"https://www.rotowire.com{player['URL']}",
        "description": f"**{change_type}**",
        "color": colors.get(change_type, 15158332),
        "fields": [
            {"name": "Injury", "value": player["injury"], "inline": True},
            {"name": "Status", "value": player["status"], "inline": True},
        ]
    }

    for webhook in webhooks:
        requests.post(webhook, json={"embeds": [embed]})


def main():
    current_players = fetch_injuries()
    try:
        snapshot = load_snapshot(SNAPSHOT_FILE)
    except:
        snapshot = {}

    new_snapshot = {}

    for player in current_players:
        pid = player["ID"]
        new_snapshot[pid] = {
            "injury": player["injury"],
            "status": player["status"]
        }

        webhooks = [INJURIES_WEBHOOK]
        if player["team"] == "SEA":
            webhooks.append(SEAHAWKS_WEBHOOK)
        if pid not in snapshot:
            send_alert(player, "New Injury Report", webhooks)
        else:
            prev = snapshot[pid]
            if player["status"] != prev["status"]:
                send_alert(player, f"Status Change: {prev['status']} → {player['status']}", webhooks)
            if player["injury"] != prev["injury"]:
                send_alert(player, f"Injury Change: {prev['injury']} → {player['injury']}", webhooks)

    save_snapshot(SNAPSHOT_FILE, new_snapshot)

    if not current_players:
        requests.post(INJURIES_WEBHOOK, json={"content": "⚠️ Injury tracker returned no players — the API may be down."})


if __name__ == "__main__":
    main()
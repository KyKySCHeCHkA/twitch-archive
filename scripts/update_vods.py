import json
import os
from pathlib import Path
from datetime import datetime, timezone

import requests

CLIENT_ID = os.environ["TWITCH_CLIENT_ID"]
CLIENT_SECRET = os.environ["TWITCH_CLIENT_SECRET"]
CHANNEL = os.environ["TWITCH_CHANNEL"]

API = "https://api.twitch.tv/helix"


def get_app_token():
    response = requests.post(
        "https://id.twitch.tv/oauth2/token",
        params={
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "grant_type": "client_credentials",
        },
        timeout=20,
    )
    response.raise_for_status()
    return response.json()["access_token"]


def get_user_id(token):
    response = requests.get(
        f"{API}/users",
        params={"login": CHANNEL},
        headers={
            "Client-Id": CLIENT_ID,
            "Authorization": f"Bearer {token}",
        },
        timeout=20,
    )
    response.raise_for_status()

    users = response.json().get("data", [])

    if not users:
        raise ValueError(
            f"Не найден Twitch-канал с логином: {CHANNEL}. "
            "Проверьте значение секрета TWITCH_CHANNEL."
        )

    return users[0]["id"]


def get_all_vods(token, user_id):
    vods = []
    cursor = None

    while True:
        params = {
            "user_id": user_id,
            "type": "archive",
            "first": 100,
        }

        if cursor:
            params["after"] = cursor

        response = requests.get(
            f"{API}/videos",
            params=params,
            headers={
                "Client-Id": CLIENT_ID,
                "Authorization": f"Bearer {token}",
            },
            timeout=20,
        )
        response.raise_for_status()
        payload = response.json()

        vods.extend(payload.get("data", []))

        cursor = payload.get("pagination", {}).get("cursor")

        if not cursor:
            break

    return vods


def normalize_vod(vod):
    created_at = datetime.fromisoformat(
        vod["created_at"].replace("Z", "+00:00")
    )

    return {
        "id": vod["id"],
        "title": vod["title"],
        "date": created_at.astimezone().strftime("%Y-%m-%d"),
        "datetime": created_at.astimezone().isoformat(),
        "duration": vod["duration"],
        "game_id": vod.get("game_id") or "",
        "game": vod.get("game_name") or "Другое",
        "tags": vod.get("tags") or [],
        "views": vod["view_count"],
        "thumbnail": vod["thumbnail_url"]
            .replace("%{width}", "640")
            .replace("%{height}", "360"),
        "url": vod["url"],
    }


def main():
    token = get_app_token()
    user_id = get_user_id(token)
    raw_vods = get_all_vods(token, user_id)

    vods = sorted(
        [normalize_vod(vod) for vod in raw_vods],
        key=lambda vod: vod["datetime"],
        reverse=True,
    )

    games = sorted({vod["game"] for vod in vods})
    tags = sorted({
        tag
        for vod in vods
        for tag in vod["tags"]
    })

    archive = {
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "games": games,
        "tags": tags,
        "vods": vods,
    }

    Path("data").mkdir(exist_ok=True)

    Path("data/vods.json").write_text(
        json.dumps(archive, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()

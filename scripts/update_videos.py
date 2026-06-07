from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from yt_videos_list import ListCreator

CHANNEL_ID = "UCT39S1m8Kr-Np0XZ2UA1D1Q"
CHANNEL_NAME = "Deadlock PRO POVS"
CHANNEL_URL = "https://www.youtube.com/@DeadlockPROPOVS/videos"
CHANNEL_SCRAPE_URL = f"https://www.youtube.com/channel/{CHANNEL_ID}"
OUTPUT_PATH = Path(__file__).resolve().parents[1] / "videos.json"


def _to_video_entry(item: list[Any]) -> dict[str, Any] | None:
    if len(item) < 3:
        return None

    number: Any = item[0]
    title = str(item[1]).strip()
    link = str(item[2]).strip()

    if not title or not link:
        return None

    try:
        number = int(str(number).strip())
    except ValueError:
        number = str(number).strip()

    return {
        "title": title,
        "link": link,
        "number": number,
    }


def scrape_videos() -> list[dict[str, Any]]:
    creator = ListCreator(
        txt=False,
        csv=False,
        md=False,
        file_suffix=False,
        all_video_data_in_memory=True,
        video_data_returned=True,
        reverse_chronological=True,
        headless=True,
        driver="firefox",
    )

    video_data, _ = creator.create_list_for(CHANNEL_SCRAPE_URL, log_silently=True, file_name="id")

    videos: list[dict[str, Any]] = []
    seen_links: set[str] = set()
    for item in video_data:
        if not isinstance(item, list):
            continue

        entry = _to_video_entry(item)
        if not entry:
            continue

        if entry["link"] in seen_links:
            continue

        seen_links.add(entry["link"])
        videos.append(entry)

    return videos


def build_payload(videos: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "channel": {
            "id": CHANNEL_ID,
            "name": CHANNEL_NAME,
            "url": CHANNEL_URL,
        },
        "last_updated": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "total_videos": len(videos),
        "videos": videos,
    }


def load_existing(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None

    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None


def main() -> None:
    existing = load_existing(OUTPUT_PATH)
    videos = scrape_videos()
    payload = build_payload(videos)

    if existing and existing.get("videos") == payload["videos"]:
        print("No new videos found. videos.json unchanged.")
        return

    OUTPUT_PATH.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Updated {OUTPUT_PATH} with {payload['total_videos']} videos.")


if __name__ == "__main__":
    main()

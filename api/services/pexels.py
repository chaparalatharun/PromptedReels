# api/services/pexels.py
import os
import httpx

PEXELS_API_KEY = os.getenv("PEXELS_API_KEY")
PEXELS_BASE_URL = "https://api.pexels.com/videos/search"

HEADERS = {
    "Authorization": PEXELS_API_KEY
}

async def search_pexels_videos(query: str, per_page: int = 10):
    """
    Search Pexels for videos matching a query.
    Returns a list of vertical-format videos with metadata.
    """
    params = {
        "query": query,
        "per_page": per_page
    }

    async with httpx.AsyncClient() as client:
        try:
            res = await client.get(PEXELS_BASE_URL, headers=HEADERS, params=params)
            res.raise_for_status()
            data = res.json()

            vertical_videos = []
            for video in data.get("videos", []):
                width = video.get("width", 0)
                height = video.get("height", 0)
                if height <= width:
                    continue  # skip horizontal or square

                best_file = sorted(video.get("video_files", []), key=lambda f: f.get("width", 0))[-1]

                vertical_videos.append({
                    "id": video.get("id"),
                    "description": query,
                    "url": video.get("url"),
                    "duration": video.get("duration"),
                    "thumbnail": video.get("image"),
                    "video_url": best_file.get("link"),
                    "user": {
                        "name": video.get("user", {}).get("name"),
                        "url": video.get("user", {}).get("url")
                    },
                    "width": width,
                    "height": height
                })

            return vertical_videos

        except Exception as e:
            print("❌ Pexels API error:", e)
            return []
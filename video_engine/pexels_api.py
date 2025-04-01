import os
import requests
from dotenv import load_dotenv

load_dotenv()

PEXELS_API_KEY = os.getenv("PEXELS_API_KEY")
PEXELS_API_URL = "https://api.pexels.com/videos/search?query={query}&per_page=1"

def get_pexels_video_url(query):
    headers = {"Authorization": PEXELS_API_KEY}
    url = PEXELS_API_URL.format(query=query)
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        video_data = response.json()
        video_files = []

        for video in video_data.get("videos", []):
            if video["width"] > video["height"]:
                video_files.extend(video["video_files"])

        if not video_files:
            print("❌ No landscape video files found.")
            return None

        best_video_file = sorted(video_files, key=lambda x: x["width"], reverse=True)[0]
        return best_video_file["link"]
    except Exception as e:
        print(f"❌ Pexels API Error: {e}")
        return None

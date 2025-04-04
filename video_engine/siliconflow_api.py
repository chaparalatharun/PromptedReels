import os
import requests
from dotenv import load_dotenv

load_dotenv()

SILICONFLOW_API_URL = "https://api.siliconflow.cn/v1/video/submit"
SILICONFLOW_API_TOKEN = os.getenv("SILICONFLOW_API_TOKEN")  # Store your token in .env

def generate_siliconflow_video(prompt, image_url=None, model="Wan-AI/Wan2.1-I2V-14B-720P", size="1280x720", seed=None, negative_prompt=""):
    if not SILICONFLOW_API_TOKEN:
        print("❌ Missing SiliconFlow API token.")
        return None

    headers = {
        "Authorization": f"Bearer {SILICONFLOW_API_TOKEN}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": model,
        "prompt": prompt,
        "image_size": size,
        "negative_prompt": negative_prompt
    }

    if image_url:
        payload["image"] = image_url
    if seed is not None:
        payload["seed"] = seed

    try:
        response = requests.post(SILICONFLOW_API_URL, json=payload, headers=headers)
        response.raise_for_status()
        result = response.json()
        return result.get("requestId", None)
    except Exception as e:
        print(f"❌ SiliconFlow API Error: {e}")
        return None

import os
from runwayml import RunwayML
from dotenv import load_dotenv

from video_engine.encode_image import encode_image_to_base64

load_dotenv()

# Init RunwayML client
RUNWAY_API_KEY = os.getenv("RUNWAY_KEY")
runway_client = RunwayML(api_key=RUNWAY_API_KEY)

def generate_runway_video_from_image(prompt_text: str, image_path: str, model: str = "gen4_turbo") -> str | None:
    """
    Submit image-to-video task to Runway and return the video generation ID.

    Args:
        prompt_text (str): Prompt describing what should happen in the video.
        image_url (str): Publicly accessible URL of the image.
        model (str): Runway model name, default is "gen4_turbo".

    Returns:
        str | None: Runway video generation task ID or None if failed.
    """
    print(f"📤 Encoding image from: {image_path}")
    image_base64 = encode_image_to_base64(image_path)
    print(f"Encoded imaged base64={image_base64[:10]}, len={(len(image_base64))}")

    try:
        print(f"🌀 Submitting Runway task with model={model}")
        result = runway_client.image_to_video.create(
            model=model,
            prompt_image=image_base64,
            prompt_text=prompt_text,
            ratio="1280:720",
        )
        print(f"✅ Runway task submitted: id={result.id}")
        return result.id
    except Exception as e:
        print(f"❌ Runway API Error: {e}")
        return None

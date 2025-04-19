import os
from runwayml import RunwayML
from dotenv import load_dotenv

load_dotenv()

# Init RunwayML client
RUNWAY_API_KEY = os.getenv("RUNWAY_KEY")
runway_client = RunwayML(api_key=RUNWAY_API_KEY)

def generate_runway_video_from_image(prompt_text: str, image_url: str, model: str = "gen4_turbo") -> str | None:
    """
    Submit image-to-video task to Runway and return the video generation ID.

    Args:
        prompt_text (str): Prompt describing what should happen in the video.
        image_url (str): Publicly accessible URL of the image.
        model (str): Runway model name, default is "gen4_turbo".

    Returns:
        str | None: Runway video generation task ID or None if failed.
    """
    try:
        print(f"🌀 Submitting Runway task with model={model}")
        result = runway_client.image_to_video.create(
            model=model,
            prompt_image=image_url,
            prompt_text=prompt_text,
        )
        print(f"✅ Runway task submitted: id={result.id}")
        return result.id
    except Exception as e:
        print(f"❌ Runway API Error: {e}")
        return None

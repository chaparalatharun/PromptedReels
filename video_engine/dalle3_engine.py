# dalle3_generator.py

import os
from dotenv import load_dotenv
from langchain_community.utilities.dalle_image_generator import DallEAPIWrapper

# Load .env file to get the OpenAI API key
load_dotenv()
openai_key = os.getenv("OPENAI_API_KEY")

# Ensure the key is set in the environment for langchain to use
os.environ["OPENAI_API_KEY"] = openai_key


def generate_dalle3_image_url(prompt: str) -> str:
    """
    Generate an image using OpenAI's DALL·E 3 API given a text prompt.

    Args:
        prompt (str): Text description of the image to generate.

    Returns:
        str: URL of the generated image or None if error occurred.
    """
    try:
        api_wrapper = DallEAPIWrapper()
        image_url = api_wrapper.run(prompt)
        return image_url
    except Exception as e:
        print(f"❌ DALL·E API Error: {e}")
        return None


# Example usage
if __name__ == "__main__":
    test_prompt = "Comic book illustration of a man in a white tuxedo with slicked-back hair standing on a large balcony, gazing across the bay under a moonlit sky, champagne glass in hand, elegant and enigmatic expression, 1920s vibe"
    image_url = generate_dalle3_image_url(test_prompt)
    if image_url:
        print(f"✅ Image URL: {image_url}")
    else:
        print("❌ Failed to generate image.")

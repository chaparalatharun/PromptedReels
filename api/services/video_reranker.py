# api/services/video_reranker.py

import os
from openai import AsyncOpenAI
from typing import List

client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

async def rerank_with_gpt4v(
    scene_description: str,
    thumbnail_urls: List[str],
    block_text: str,
    user_prompt: str = ""
) -> int:
    """
    Uses GPT-4o to choose the best thumbnail given a scene description,
    the full narration block, and optional user guidance.
    Returns the index (0-based) of the best-matching thumbnail.
    """

    system_message = {
        "role": "system",
        "content": (
            "You are a video assistant helping select the most visually relevant video thumbnail "
            "based on a given scene description. You are provided with:\n"
            "1. The original narration block (voiceover script).\n"
            "2. The user's visual guidance (if any).\n"
            "3. A specific scene description (generated from the narration).\n"
            "4. A list of thumbnail images from videos.\n\n"
            "Your job is to visually inspect the thumbnails and return the index (0-based) of the one "
            "that best matches the scene description, considering both the narration and user intent."
        ),
    }

    # Construct textual context
    user_prompt_section = f"User Prompt:\n{user_prompt.strip()}\n\n" if user_prompt.strip() else ""
    text_part = {
        "type": "text",
        "text": (
            f"Narration Block:\n\"\"\"{block_text.strip()}\"\"\"\n\n"
            f"{user_prompt_section}"
            f"Scene Description to Match:\n\"\"\"{scene_description.strip()}\"\"\"\n\n"
            f"Now look at the thumbnails below and return a single number (0 to {len(thumbnail_urls) - 1}) "
            f"indicating the best visual match.\n\n"
            f"IMPORTANT: Reply ONLY with a single number (0 to {len(thumbnail_urls) - 1}). "
            f"Do NOT include any explanation or text."
        )
    }

    image_parts = [
        {"type": "image_url", "image_url": {"url": url}} for url in thumbnail_urls
    ]

    response = await client.chat.completions.create(
        model="gpt-4o",
        messages=[
            system_message,
            {"role": "user", "content": [text_part] + image_parts}
        ],
        max_tokens=5,
    )

    try:
        content = response.choices[0].message.content.strip()
        return int(content)
    except Exception as e:
        print("❌ Failed to parse GPT-4o response:", e)
        print("Raw content:", response.choices[0].message.content)
        return 0
import os
import json
import re
from openai import AsyncOpenAI

client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

async def plan_visual_scenes(block_text: str, total_target_sec: int = 8, user_prompt: str = ""):
    """
    Given a narration block and optional user guidance, return a list of visual scenes:
    [{ "description": ..., "target_sec": ... }]
    """

    user_guidance = f"User Visual Guidance:\n{user_prompt.strip()}\n" if user_prompt.strip() else ""

    prompt = f"""
You are a creative but precise video planning assistant.

Your task is to take a short narration block (used in a voiceover) and divide it into multiple distinct visual scenes. These scenes will be used to fetch relevant stock video clips from the Pexels API. You must carefully match the tone and content of the narration with highly *searchable*, *visually specific*, and *concrete* scene descriptions.

Each scene must include:
1. A **short, vivid visual description** (what the video should visually depict). This should be optimized to return relevant Pexels videos when used as a search query.
2. An **integer duration in seconds** under the key `target_sec`. The total across all scenes should **add up exactly** to the total narration duration provided.

Only use realistic visual descriptions — avoid abstract metaphors, emotions, or symbolic phrases. Describe exactly what should appear visually, like “man brushing teeth in mirror,” “alarm clock ringing at 6 AM,” “woman sprinting in park at sunrise,” etc.

Narration Block:
\"\"\"
{block_text.strip()}
\"\"\"

{user_guidance}Total desired video duration: {total_target_sec} seconds

Respond ONLY in this strict JSON format:
[
  {{ "description": "...", "target_sec": ... }},
  ...
]
Your output MUST be valid JSON.
"""

    response = await client.chat.completions.create(
        model="gpt-4o",
        temperature=0.7,
        messages=[{"role": "user", "content": prompt}]
    )

    raw_content = response.choices[0].message.content
    print("📦 Raw LLM output:\n", raw_content)

    try:
        # Strip ```json or ``` from beginning and end if present
        cleaned = re.sub(r"^```(?:json)?|```$", "", raw_content.strip(), flags=re.MULTILINE).strip()
        return json.loads(cleaned)
    except Exception as e:
        print("❌ Failed to parse JSON from LLM:", e)
        return [
            {
                "description": "scenic forest landscape with sunlight filtering through trees",
                "target_sec": total_target_sec
            }
        ]
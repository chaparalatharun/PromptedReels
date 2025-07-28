import os
import json
from typing import List
from openai import OpenAI
from api.schemas.projects import BlockOut
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

SYSTEM_PROMPT = """
You are a script structuring assistant for 9:16 vertical short videos.

Return STRICT JSON ONLY with this exact shape:

{
  "blocks": [
    { "text": "<≤220 chars, plain text>", "target_sec": <number> }
  ]
}

Hard rules:
- Output ONLY the JSON object. No prose, no explanations, no code fences.
- Exactly two keys at the top level: "blocks" (array) and nothing else.
- Each block is an object with ONLY:
    - "text": speakable line (≤ 220 characters, no markdown, no quotes, no emojis)
    - "target_sec": number in seconds (1.0-10.0), with at most 2 decimal places
- Total duration: sum of all target_sec must be within ±2 seconds of the requested target_seconds.
- Number of blocks: prefer 5-7 blocks (min 3, max 10).
- Structure:
    - Block 1 must be a strong HOOK (pull the viewer in immediately).
    - Middle blocks progress clearly and concisely.
    - Final block may include a brief CTA if relevant (e.g., “Follow for more”).
- Language/tone/style should follow the user's “clip style” if provided:
    - "Explainer": direct, factual, concise.
    - "Listicle": number the items in the text (e.g., "1) …").
    - "Story": vivid but tight; clear beginning → middle → payoff.
    - If style is "N/A" or not provided, use a neutral, punchy style.
- If the idea is too short for the requested duration, expand with relevant, tight lines.
- If the idea is too long, compress while preserving the core message.
- Do not invent technical facts; keep claims generic unless provided.

Validation reminders:
- No extra keys anywhere.
- Ensure sum(target_sec) ≈ target_seconds (±2s).
- Keep each target_sec between 1.0 and 10.0 inclusive, rounded to 1-2 decimals.
"""

def generate_blocks_from_idea(script_idea: str) -> List[BlockOut]:
    user_prompt = f"Script Idea:\n{script_idea}\n\nFormat as a JSON object with a 'blocks' key."

    try:
        response = client.chat.completions.create(
            model="gpt-4",  # or "gpt-3.5-turbo"
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT.strip()},
                {"role": "user", "content": user_prompt.strip()}
            ],
            temperature=0.6,
        )

        content = response.choices[0].message.content.strip()

        # 🔍 Debug: print raw LLM output
        print("\n🔍 Raw LLM response:\n", content)

        parsed = json.loads(content)
        return [BlockOut(**block) for block in parsed["blocks"]]

    except Exception as e:
        raise ValueError(f"LLM block generation failed: {e}")
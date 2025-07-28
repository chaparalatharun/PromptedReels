# api/services/video_manager.py

import os
from pydub import AudioSegment

from .video_planner import plan_visual_scenes
from .pexels import search_pexels_videos
from .video_reranker import rerank_with_gpt4v  # ✅ corrected import
from .video_stitcher import stitch_and_trim_scenes


async def generate_block_video(
    project_name: str,
    block_id: str,
    block_text: str,
    user_prompt: str = ""
):
    """
    Full pipeline to generate a trimmed + stitched video for a given narration block.
    Returns the final video file path.
    """

    # Step 0: Determine duration from audio file
    audio_path = os.path.join("projects", project_name, "media", "audio", f"{block_id}.mp3")
    try:
        audio = AudioSegment.from_file(audio_path)
        target_sec = int(audio.duration_seconds)
    except Exception as e:
        print(f"❌ Failed to load audio for duration fallback to 8s: {e}")
        target_sec = 8

    # Step 1: Plan scenes from narration
    scene_plan = await plan_visual_scenes(
        block_text=block_text,
        total_target_sec=target_sec,
        user_prompt=user_prompt
    )

    final_results = []

    # Step 2: For each scene, get best-matching video
    for scene in scene_plan:
        description = scene["description"]
        duration = scene["target_sec"]

        # Search Pexels videos
        candidates = await search_pexels_videos(description)

        # Rerank using GPT-4V
        best_video = await rerank_with_gpt4v(  # ✅ corrected function name
            scene_description=description,
            thumbnail_urls=[c["thumbnail"] for c in candidates],
            block_text=block_text,
            user_prompt=user_prompt,
        )

        # If needed, attach the best candidate (by index)
        selected_video = candidates[best_video] if candidates else {}

        final_results.append({
            "description": description,
            "target_sec": duration,
            "selected_video": selected_video
        })

    # Step 3: Stitch and trim selected videos into final clip
    final_video_path = await stitch_and_trim_scenes(
        scenes=final_results,
        project_name=project_name,
        block_id=block_id
    )

    return final_video_path
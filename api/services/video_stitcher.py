# api/services/video_stitcher.py

import os
import json
from datetime import datetime
import subprocess

from moviepy.editor import VideoFileClip, concatenate_videoclips
import httpx
import tempfile


def get_video_json_path(project_name: str):
    return os.path.join("projects", project_name, "media", "video", "video.json")


async def download_and_trim(video_url: str, target_sec: int) -> str:
    """
    Downloads video and trims to target_sec using ffmpeg. Returns path to trimmed temp file.
    """
    async with httpx.AsyncClient() as client:
        r = await client.get(video_url)
        r.raise_for_status()
        tmp_input = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
        tmp_input.write(r.content)
        tmp_input.close()

    tmp_output = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
    tmp_output.close()

    subprocess.run([
        "ffmpeg", "-y",
        "-i", tmp_input.name,
        "-t", str(target_sec),
        "-c", "copy",
        tmp_output.name
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    return tmp_output.name


async def stitch_and_trim_scenes(scenes, project_name: str, block_id: str) -> str:
    """
    Downloads and trims each selected video, then stitches into final video for block.
    Stores video in /media/video/{block_id}.mp4 and updates video.json metadata.
    """
    trimmed_paths = []

    for scene in scenes:
        url = scene["selected_video"]["video_url"]
        sec = scene["target_sec"]
        trimmed_path = await download_and_trim(url, sec)
        trimmed_paths.append(trimmed_path)

    # Load and slightly extend each clip
    clips = []
    extra_duration = 0.3  # seconds to extend each clip
    for path in trimmed_paths:
        clip = VideoFileClip(path)
        padded_clip = clip.set_duration(clip.duration + extra_duration)
        clips.append(padded_clip)

    final = concatenate_videoclips(clips, method="compose")

    # Create folder if needed
    output_dir = os.path.join("projects", project_name, "media", "video")
    os.makedirs(output_dir, exist_ok=True)

    final_path = os.path.join(output_dir, f"{block_id}.mp4")
    final.write_videofile(final_path, codec="libx264", audio=False, logger=None)

    # Clean up
    for clip in clips:
        clip.close()
    for path in trimmed_paths:
        os.remove(path)

    # ✅ Update video.json
    metadata_path = get_video_json_path(project_name)
    video_url = f"/static/{project_name}/media/video/{block_id}.mp4"
    now = datetime.utcnow().isoformat()

    if os.path.exists(metadata_path):
        with open(metadata_path, "r") as f:
            metadata = json.load(f)
    else:
        metadata = {}

    metadata[block_id] = {
        "updated_at": now,
        "url": video_url
    }

    with open(metadata_path, "w") as f:
        json.dump(metadata, f, indent=2)

    return final_path
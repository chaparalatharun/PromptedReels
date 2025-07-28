import os
import subprocess

async def mux_audio_and_video(project_name: str) -> str:
    project_path = os.path.join("projects", project_name)
    video_path = os.path.join(project_path, "media", "video", "final_video.mp4")
    audio_path = os.path.join(project_path, "media", "audio", "full_audio.mp3")
    mux_dir = os.path.join(project_path, "media", "mux")
    os.makedirs(mux_dir, exist_ok=True)

    if not os.path.exists(video_path):
        raise FileNotFoundError(f"Video not found: {video_path}")
    if not os.path.exists(audio_path):
        raise FileNotFoundError(f"Audio not found: {audio_path}")

    output_path = os.path.join(mux_dir, "full_video.mp4")

    cmd = [
        "ffmpeg", "-y",
        "-i", video_path,
        "-i", audio_path,
        "-c:v", "copy",       # Copy video without re-encoding
        "-c:a", "aac",        # Encode audio to AAC (widely supported)
        "-shortest",          # Stop at shortest stream
        output_path
    ]

    print(f"🎧 Muxing video + audio to {output_path}")
    subprocess.run(cmd, check=True)
    return output_path
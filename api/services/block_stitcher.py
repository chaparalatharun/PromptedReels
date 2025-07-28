import os
import subprocess

async def stitch_block_videos(project_name: str, output_path: str):
    video_dir = os.path.join("projects", project_name, "media", "video")
    block_files = sorted([
        f for f in os.listdir(video_dir)
        if f.startswith("block_") and f.endswith(".mp4")
    ])

    if not block_files:
        raise FileNotFoundError("No block video segments found.")

    input_paths = [os.path.join(video_dir, f) for f in block_files]
    input_args = []
    scale_labels = []
    concat_labels = []

    for i, path in enumerate(input_paths):
        input_args.extend(["-i", path])
        scale_labels.append(f"[v{i}]")
        concat_labels.append(f"[v{i}]")

    # Apply scale filter to each input
    filter_parts = []
    for i in range(len(input_paths)):
        filter_parts.append(f"[{i}:v:0]scale=1080:1920[v{i}]")
    
    filter_complex = (
        ";".join(filter_parts) +
        f";{''.join(concat_labels)}concat=n={len(input_paths)}:v=1:a=0[outv]"
    )

    cmd = [
        "ffmpeg", "-y",
        *input_args,
        "-filter_complex", filter_complex,
        "-map", "[outv]",
        "-r", "30",
        "-c:v", "libx264",
        "-crf", "23",
        "-preset", "fast",
        "-pix_fmt", "yuv420p",
        output_path
    ]

    print(f"[STITCH] Running fixed FFmpeg command with scaling inside filter_complex")

    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        print("❌ FFmpeg concat filter failed:", e)
        raise
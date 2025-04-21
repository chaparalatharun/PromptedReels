import os
import subprocess
import random

from moviepy.editor import (
    VideoFileClip, AudioFileClip, concatenate_videoclips, concatenate_audioclips
)
# from moviepy.editor import *
import moviepy.video.fx.all as vfx
from moviepy.video.VideoClip import ImageClip
from moviepy.video.compositing.CompositeVideoClip import CompositeVideoClip


def add_subtitles_with_ffmpeg(input_path, srt_path, output_path, font_name="WenQuanYi Micro Hei", font_size=28):
    import subprocess

    style = f"FontName={font_name},FontSize={font_size}"

    command = [
        "ffmpeg", "-y",
        "-i", input_path,
        "-vf", f"subtitles='{srt_path}':force_style='{style}'",
        "-c:a", "copy",
        output_path
    ]

    try:
        subprocess.run(command, check=True)
        print(f"🎬 Subtitled video saved to: {output_path}")
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to add subtitles with FFmpeg: {e}")



def resize_and_crop(clip, target_size=(1280, 720)):
    """Resize and crop video clip to match target_size (w, h)."""
    # Scale clip while keeping aspect ratio
    clip = clip.fx(vfx.resize, height=target_size[1])
    w, h = clip.size

    if w > target_size[0]:
        x_center = w // 2
        x1 = x_center - target_size[0] // 2
        x2 = x1 + target_size[0]
        clip = clip.crop(x1=x1, x2=x2)
    elif w < target_size[0]:
        # Optional: add black bars instead of crop
        clip = clip.fx(vfx.resize, width=target_size[0])

    return clip.set_position(("center", "center"))
def compose_final_video(processed_json, project_folder, output_path, insert_subtitle=True):
    temp_no_sub_path = output_path.replace(".mp4", "_nosub.mp4")
    subtitle_path = os.path.join(project_folder, "subtitles.srt")

    video_clips = []

    for i, block in enumerate(processed_json["script"]):
        video_path = os.path.join(project_folder, block.get("video", ""))
        audio_paths = [os.path.join(project_folder, audio) for audio in block.get("audio", [])]

        if not os.path.exists(video_path) or not all(os.path.exists(path) for path in audio_paths):
            print(f"⚠️ Skipping clip {i + 1} due to missing video or audio.")
            continue

        try:
            video_clip = VideoFileClip(video_path)
            video_clip = resize_and_crop(video_clip, target_size=(1280, 720))

            # Load and concatenate audio
            audio_clips = [AudioFileClip(path) for path in audio_paths]
            audio_clip = concatenate_audioclips(audio_clips)

            # Repeat video to match audio duration
            if video_clip.duration < audio_clip.duration:
                repeat_count = int(audio_clip.duration // video_clip.duration) + 1
                video_clip = concatenate_videoclips([video_clip] * repeat_count)

            video_clip = video_clip.subclip(0, audio_clip.duration)
            final_clip = video_clip.set_audio(audio_clip)

            video_clips.append(final_clip)
            print(f"✅ Processed clip {i + 1}")

        except Exception as e:
            print(f"❌ Error processing clip {i + 1}: {e}")

    if not video_clips:
        print("❌ No valid clips to compose.")
        return

    try:
        final_video = concatenate_videoclips(video_clips, method="compose")
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        # Step 1: Export video without subtitles
        final_video.write_videofile(
            temp_no_sub_path,
            codec="libx264",
            audio_codec="aac",
            threads=4,
            ffmpeg_params=["-preset", "fast"],
        )

        # Step 2: Add subtitles via FFmpeg
        if insert_subtitle and os.path.exists(subtitle_path):
            add_subtitles_with_ffmpeg(temp_no_sub_path, subtitle_path, output_path)
            os.remove(temp_no_sub_path)
        else:
            os.rename(temp_no_sub_path, output_path)
            print("⚠️ No subtitles added, final video saved without subs.")

    except Exception as e:
        print(f"❌ Error during final video composition: {e}")

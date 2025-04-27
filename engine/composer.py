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




def compose_final_video(processed_json, project_folder, output_path, insert_subtitle=True, haveChar=True):
    from moviepy.editor import VideoFileClip, AudioFileClip, ImageClip, CompositeVideoClip, concatenate_videoclips, concatenate_audioclips
    import os
    import random

    temp_no_sub_path = output_path.replace(".mp4", "_nosub.mp4")
    subtitle_path = os.path.join(project_folder, "subtitles.srt")

    video_clips = []
    scene_mappings = {}

    # 先建立 scene -> script_idx 的映射
    for scene in processed_json.get("scene", []):
        source_path = os.path.join(project_folder, scene.get("image", ""))
        mode = scene.get("mode", "generate_image")
        for match in scene.get("matches", []):
            idx = match.get("script_idx")
            effect = match.get("effect", "None")
            scene_mappings[idx] = {
                "source_path": source_path,
                "mode": mode,
                "effect": effect
            }

    for i, block in enumerate(processed_json["script"]):
        audio_paths = [os.path.join(project_folder, audio) for audio in block.get("audio", [])]

        if not all(os.path.exists(path) for path in audio_paths):
            print(f"⚠️ Skipping clip {i + 1} due to missing audio.")
            continue

        try:
            # 默认 None，待会判断是 scene提供媒体 还是 自己的视频
            base_clip = None

            if i in scene_mappings:
                mapping = scene_mappings[i]
                source_path = mapping["source_path"]
                mode = mapping["mode"]

                if mode == "generate_image":
                    if os.path.exists(source_path):
                        base_clip = ImageClip(source_path).set_duration(0.1)  # 先短一点，后面跟音频同步
                        base_clip = resize_and_crop(base_clip, target_size=(1280, 720))
                    else:
                        print(f"⚠️ Scene image not found: {source_path}")
                        continue

                elif mode == "generate_video":
                    if os.path.exists(source_path):
                        base_clip = VideoFileClip(source_path)
                        base_clip = resize_and_crop(base_clip, target_size=(1280, 720))
                    else:
                        print(f"⚠️ Scene video not found: {source_path}")
                        continue

            else:
                # 没有 scene指定，则读自己的 video
                video_path = os.path.join(project_folder, block.get("video", ""))
                if os.path.exists(video_path):
                    base_clip = VideoFileClip(video_path)
                    base_clip = resize_and_crop(base_clip, target_size=(1280, 720))
                else:
                    print(f"⚠️ Video file not found for script_idx {i}: {video_path}")
                    continue

            if base_clip is None:
                print(f"⚠️ No base clip found for script_idx {i}.")
                continue

            # 处理角色头像 (如果有的话)
            if haveChar and i not in scene_mappings:  # 如果已经有 scene 全屏图了，就不再额外叠角色图
                character = block.get("character", "")
                picture = block.get("picture", "random")
                character_folder = os.path.join("assets", character)

                if picture == "random":
                    images = [f for f in os.listdir(character_folder) if f.endswith((".jpg", ".png"))]
                    if not images:
                        print(f"⚠️ No images found for character {character}.")
                        continue
                    picture_file = random.choice(images)
                else:
                    picture_file = picture if picture.endswith((".jpg", ".png")) else picture + ".jpg"

                picture_path = os.path.join(character_folder, picture_file)
                if os.path.exists(picture_path):
                    img_clip = ImageClip(picture_path).set_duration(base_clip.duration)
                    img_clip = img_clip.resize(width=base_clip.w * 0.2).set_position(("left", "bottom"))
                    base_clip = CompositeVideoClip([base_clip, img_clip])
                else:
                    print(f"⚠️ Character picture not found: {picture_path}")
                    continue

            # 合并音频
            audio_clips = [AudioFileClip(path) for path in audio_paths]
            audio_clip = concatenate_audioclips(audio_clips)

            # 让画面长度匹配音频
            if base_clip.duration < audio_clip.duration:
                repeat_count = int(audio_clip.duration // base_clip.duration) + 1
                base_clip = concatenate_videoclips([base_clip] * repeat_count)

            base_clip = base_clip.subclip(0, audio_clip.duration)
            final_clip = base_clip.set_audio(audio_clip)

            video_clips.append(final_clip)
            print(f"✅ Processed script_idx {i} {'with' if haveChar else 'without'} character/scene image.")

        except Exception as e:
            print(f"❌ Error processing script_idx {i}: {e}")

    if not video_clips:
        print("❌ No valid clips to compose.")
        return

    try:
        final_video = concatenate_videoclips(video_clips, method="compose")
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        final_video.write_videofile(
            temp_no_sub_path,
            codec="libx264",
            audio_codec="aac",
            threads=4,
            ffmpeg_params=["-preset", "fast"],
            fps=24,
        )

        if insert_subtitle and os.path.exists(subtitle_path):
            add_subtitles_with_ffmpeg(temp_no_sub_path, subtitle_path, output_path)
            os.remove(temp_no_sub_path)
        else:
            os.rename(temp_no_sub_path, output_path)
            print("⚠️ No subtitles added, final video saved without subs.")

    except Exception as e:
        print(f"❌ Error during final video composition: {e}")

import os
import pysrt
from moviepy.editor import (
    VideoFileClip, AudioFileClip, concatenate_videoclips,
    concatenate_audioclips, TextClip, CompositeVideoClip
)



def add_subtitles_to_video(video_clip, srt_path, font_path):
    try:
        import pysrt
        subs = pysrt.open(srt_path, encoding='utf-8')  # Ensure UTF-8 decoding
        subtitle_clips = []

        for sub in subs:
            text = sub.text.replace('\n', ' ')  # Inline any line breaks
            start_time = sub.start.ordinal / 1000.0
            duration = (sub.end.ordinal - sub.start.ordinal) / 1000.0

            fontsize = int(video_clip.h * 0.05)

            txt_clip = TextClip(
                text,
                fontsize=fontsize,
                font=font_path,
                color='white',
                stroke_color='black',
                stroke_width=1,
                method='label'  # Needed for non-ASCII characters
            ).set_start(start_time).set_duration(duration).set_position(("center", "bottom"))

            subtitle_clips.append(txt_clip)

        return CompositeVideoClip([video_clip, *subtitle_clips])
    except Exception as e:
        print(f"⚠️ Failed to add subtitles: {e}")
        return video_clip

def compose_final_video(processed_json, project_folder, output_path, insert_subtitle=True, chinese_font_path=None):

    font_path = os.path.join(project_folder, "ali.ttf")
    chinese_font_path = font_path

    video_clips = []
    subtitle_path = os.path.join(project_folder, "subtitles.srt")

    for i, block in enumerate(processed_json["script"]):
        video_path = os.path.join(project_folder, block.get("video", ""))
        audio_paths = [os.path.join(project_folder, audio) for audio in block.get("audio", [])]

        if not os.path.exists(video_path) or not all(os.path.exists(path) for path in audio_paths):
            print(f"⚠️ Skipping clip {i + 1} due to missing video or audio.")
            continue

        try:
            video_clip = VideoFileClip(video_path)
            audio_clips = [AudioFileClip(path) for path in audio_paths]
            audio_clip = concatenate_audioclips(audio_clips)

            if video_clip.duration < audio_clip.duration:
                repeat_count = int(audio_clip.duration // video_clip.duration) + 1
                video_clip = concatenate_videoclips([video_clip] * repeat_count)
            video_clip = video_clip.subclip(0, audio_clip.duration)

            final_clip = video_clip.set_audio(audio_clip)

            if insert_subtitle and os.path.exists(subtitle_path) and chinese_font_path:
                final_clip = add_subtitles_to_video(final_clip, subtitle_path, chinese_font_path)

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

        final_video.write_videofile(
            output_path,
            codec="h264_videotoolbox",  # Replace with "libx264" if not macOS
            audio_codec="aac",
            ffmpeg_params=["-pix_fmt", "yuv420p"]
        )

        print(f"🎬 Final video saved to: {output_path}")
    except Exception as e:
        print(f"❌ Error during final video composition: {e}")

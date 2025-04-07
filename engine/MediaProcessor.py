import os

from audio_engine.audio_block_generator import generate_audio_for_block
from audio_engine.audio_generator import generate_tts_audio
from engine.project_manager import load_json, save_json
from video_engine.video_block_generator import generate_video_for_block
from video_engine.video_generator import generate_video_clip


class MediaProcessor:
    def __init__(self, project_name, projects_dir, reGen_audio=True, reGen_video=True, theme=""):
        self.project_path = os.path.join(projects_dir, project_name)
        self.output_name = os.path.basename(self.project_path)
        self.reGen_audio = reGen_audio
        self.reGen_video = reGen_video
        self.theme = theme

        # 优先加载 processed.json，如果不存在则加载 input.json
        processed_path = os.path.join(self.project_path, "processed.json")
        input_path = os.path.join(self.project_path, "input.json")

        if os.path.exists(processed_path):
            print(f"📂 Loading existing progress from: {processed_path}")
            self.data = load_json(processed_path)
        else:
            print(f"📂 No processed.json found, loading from: {input_path}")
            self.data = load_json(input_path)


    def process(self):

        srt_segments = []
        current_time = 0

        for idx, block in enumerate(self.data["script"]):
            if self.reGen_video:
                generate_video_for_block(block, self.project_path, idx, self.theme,self.reGen_video)
            if self.reGen_audio:
                block_srt, current_time = generate_audio_for_block(
                    block, self.project_path, idx,
                    output_name=self.output_name,
                    reGen=self.reGen_audio,
                    current_time=current_time
                )
                srt_segments.extend(block_srt)
            self.save()

        # 所有 audio 生成完成后保存 srt
        srt_path = os.path.join(self.project_path, "subtitles.srt")
        with open(srt_path, "w", encoding="utf-8") as f:
            f.writelines(srt_segments)
        print(f"✅ Saved SRT: {srt_path}")
        print("process done!")

    def save(self):
        save_json(self.data, os.path.join(self.project_path, "processed.json"))

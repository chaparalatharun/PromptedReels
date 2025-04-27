import os

from audio_engine import generate_audio_for_block
from engine.project_manager import load_json, save_json
from video_engine import generate_video_for_block


class MediaProcessor:
    def __init__(self, project_name, projects_dir, reGen_audio=True, reGen_image = True,reGen_video=True, theme=""):
        self.project_path = os.path.join(projects_dir, project_name)
        self.output_name = os.path.basename(self.project_path)
        self.reGen_audio = reGen_audio
        self.reGen_video = reGen_video
        self.reGen_image = reGen_image
        self.theme = theme

        # 优先加载 processed.json，如果不存在则加载 input.json
        # processed_path = os.path.join(self.project_path, "processed.json")
        input_path = os.path.join(self.project_path, "input.json")
        self.data = load_json(input_path)

        # if os.path.exists(processed_path):
        #     print(f"📂 Loading existing progress from: {processed_path}")
        #     self.data = load_json(processed_path)
        # else:
        #     print(f"📂 No processed.json found, loading from: {input_path}")
        #     self.data = load_json(input_path)


    def process_all(self):

        srt_segments = []
        current_time = 0

        for idx, block in enumerate(self.data["script"]):
        #     generate_video_for_block(block, self.project_path, idx, self.theme,self.reGen_image, self.reGen_video, None)
            block_srt, current_time = generate_audio_for_block(
                    block, self.project_path, idx,
                    output_name=self.output_name,
                    reGen=self.reGen_audio,
                    current_time=current_time
                )
            srt_segments.extend(block_srt)
            self._save()

        # 所有 audio 生成完成后保存 srt
        srt_path = os.path.join(self.project_path, "subtitles.srt")
        with open(srt_path, "w", encoding="utf-8") as f:
            f.writelines(srt_segments)
        print(f"✅ Saved SRT: {srt_path}")
        self._save()
        print("process done! and saved!")

    def process_single_block(self, idx: int):
        """Process a single script block by index, save updated JSON and update the SRT file."""
        if idx < 0 or idx >= len(self.data["script"]):
            print(f"❌ Invalid index: {idx}")
            return

        block = self.data["script"][idx]
        current_time = 0

        print(f"🎬 Processing block {idx}...")

        generate_video_for_block(block, self.project_path, idx, self.theme, self.reGen_image, self.reGen_video, None)

        block_srt = []
        if self.reGen_audio:
            block_srt, _ = generate_audio_for_block(
                block, self.project_path, idx,
                output_name=self.output_name,
                reGen=self.reGen_audio,
                current_time=current_time  # We reset to 0 for single block timing
            )

        self._save()

        if self.reGen_audio and block_srt:
            srt_path = os.path.join(self.project_path, "subtitles.srt")

            # Try to load existing lines
            existing_srt = []
            if os.path.exists(srt_path):
                with open(srt_path, "r", encoding="utf-8") as f:
                    existing_srt = f.read().split("\n\n")

            # Replace the block's srt segment (1-based index)
            block_idx = idx + 1
            if block_idx <= len(existing_srt):
                existing_srt[block_idx - 1] = block_srt[0].strip()
            else:
                # If out of range, just append
                existing_srt.append(block_srt[0].strip())

            # Rewrite
            with open(srt_path, "w", encoding="utf-8") as f:
                f.write("\n\n".join(existing_srt).strip() + "\n")
            print(f"📝 SRT block {block_idx} updated at {srt_path}")


        self._save()
        print(f"✅ Block {idx} processed and saved.")



    def _save(self):
        save_path = os.path.join(self.project_path, "input.json")
        save_json(self.data, save_path)

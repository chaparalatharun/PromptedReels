import os
import requests
import re
import yaml
from dotenv import load_dotenv
from pydub import AudioSegment

load_dotenv()

# === TTS Server Config ===
TTS_SERVER_IP =  os.getenv("TTS_SERVER_IP")
TTS_PORT =  os.getenv("TTS_PORT")
TTS_URL = f"http://{TTS_SERVER_IP}:{TTS_PORT}/tts?"

# Load audio config
with open("./config/audio_config.yaml", "r", encoding="utf-8") as f:
    AUDIO_CONFIG = yaml.safe_load(f)

# Default TTS params (mutable copy will be used)
DEFAULT_TTS_PARAMS = {
    "text_lang": "zh",
    "cut_punc": "。，？",
    "speed": "1.2",
    "ref_audio_path": "output/reference.wav",
    "prompt_text": "就是跟他这个成长的外部环境有关系，和本身的素质也有关系，他是一个",
    "prompt_lang": "zh",
    "text_split_method": "cut5",
    "batch_size": 1,
    "media_type": "wav",
    "streaming_mode": "true",
}


def split_text_into_clips(text):
    clips = re.split(r'[，。？]', text)
    return [clip.strip() for clip in clips if clip.strip()]


def format_time(seconds):
    mins, secs = divmod(seconds, 60)
    hours, mins = divmod(mins, 60)
    return f"{int(hours):02}:{int(mins):02}:{int(secs):02},{int((seconds % 1) * 1000):03}"


def get_audio_duration(audio_path):
    try:
        audio = AudioSegment.from_wav(audio_path)
        return len(audio) / 1000
    except Exception as e:
        print(f"❌ Error reading audio file: {e}")
        return 0


def switch_character_model(character: str, emotion: str):
    char_cfg = AUDIO_CONFIG.get("characters", {}).get(character)
    if not char_cfg:
        print(f"⚠️ No config found for character: {character}")
        return

    try:
        if "gpt_weights" in char_cfg:
            requests.get(f"http://{TTS_SERVER_IP}:{TTS_PORT}/set_gpt_weights", params={"weights_path": char_cfg["gpt_weights"]})
        if "sovits_weights" in char_cfg:
            requests.get(f"http://{TTS_SERVER_IP}:{TTS_PORT}/set_sovits_weights", params={"weights_path": char_cfg["sovits_weights"]})
        print(f"✅ Switched models for {character}")
    except Exception as e:
        print(f"❌ Error switching models: {e}")

    # Update global TTS params
    emotion_cfg = char_cfg.get("emotions", {}).get(emotion)
    if not emotion_cfg:
        print(f"⚠️ No emotion config for {character} - {emotion}")
        return

    DEFAULT_TTS_PARAMS["ref_audio_path"] = emotion_cfg.get("ref_audio_path", DEFAULT_TTS_PARAMS["ref_audio_path"])
    DEFAULT_TTS_PARAMS["prompt_text"] = emotion_cfg.get("prompt_text", DEFAULT_TTS_PARAMS["prompt_text"])


def generate_audio_for_block(block, project_path, index, output_name=None, reGen=True, current_time=0):
    """Generate audio clips for a block. Returns list of SRT segment strings and updated current_time."""
    if output_name is None:
        output_name = os.path.basename(project_path)

    output_audio = os.path.join(project_path, "audio")
    os.makedirs(output_audio, exist_ok=True)

    character = block.get("character", "default")
    emotion = block.get("emotion", "愤怒")

    # Switch speaker before processing
    switch_character_model(character, emotion)

    script = block["text"]
    clips = split_text_into_clips(script)
    audio_filenames = []
    srt_segments = []

    for i, clip in enumerate(clips):
        audio_filename = f"{output_name}_{index + 1}_{i + 1}.wav"
        audio_file_path = os.path.join(output_audio, audio_filename)

        if os.path.exists(audio_file_path) and not reGen:
            print(f"✅ Audio exists, skipping: {audio_file_path}")
        else:
            print(f"[TTS] Generating audio for: {clip}")
            params = DEFAULT_TTS_PARAMS.copy()
            params["text"] = clip
            try:
                response = requests.get(TTS_URL, params=params)
                if response.status_code == 200:
                    with open(audio_file_path, "wb") as f:
                        f.write(response.content)
                    print(f"✅ Saved: {audio_file_path}")
                else:
                    print(f"❌ Failed for {clip} - HTTP {response.status_code} {response.reason}")
            except Exception as e:
                print(f"❌ Error requesting TTS: {e}")

        duration = get_audio_duration(audio_file_path)
        start_time = current_time
        end_time = current_time + duration
        current_time = end_time

        audio_filenames.append(f"audio/{audio_filename}")
        srt_segments.append(
            f"{len(srt_segments) + 1}\n{format_time(start_time)} --> {format_time(end_time)}\n{clip}\n\n"
        )

    block["audio"] = audio_filenames
    return srt_segments, current_time

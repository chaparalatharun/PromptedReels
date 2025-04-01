import os
import requests
from pydub import AudioSegment
import re

# === TTS Server Config ===
TTS_SERVER_IP = "168.4.124.31"
TTS_PORT = 9880
TTS_URL = f"http://{TTS_SERVER_IP}:{TTS_PORT}/tts?"

# Default parameters (can be modified globally)
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


# Split text into clips based on Chinese punctuation marks (，。？)
def split_text_into_clips(text):
    # Split by Chinese punctuation (Chinese comma, period, and question mark)
    clips = re.split(r'[，。？]', text)
    return [clip.strip() for clip in clips if clip.strip()]


def generate_tts_audio(data, project_path, reGen=True):
    output_name = os.path.basename(project_path)
    output_audio = os.path.join(project_path, "audio")
    os.makedirs(output_audio, exist_ok=True)

    # This will store the SRT file content
    srt_content = []
    current_time = 0  # Starting time for the first segment

    for index, block in enumerate(data["script"]):
        script = block["text"]
        clips = split_text_into_clips(script)

        audio_filenames = []

        for i, clip in enumerate(clips):
            audio_filename = f"{output_name}_{index + 1}_{i + 1}.wav"
            audio_file_path = os.path.join(output_audio, audio_filename)

            if os.path.exists(audio_file_path) and not reGen:
                print(f"Audio exists, skipping: {audio_file_path}")
                audio_filenames.append(f"audio/{audio_filename}")
                # Calculate the duration of the current audio using pydub
                audio_duration = get_audio_duration(audio_file_path)
                start_time = current_time
                end_time = current_time + audio_duration
                srt_content.append(
                    f"{len(srt_content) + 1}\n{format_time(start_time)} --> {format_time(end_time)}\n{clip}\n\n")
                current_time = end_time
                continue

            print(f"[TTS] Generating audio for: {clip}")

            # Clone the default and override with current text
            params = DEFAULT_TTS_PARAMS.copy()
            params["text"] = clip

            try:
                response = requests.get(TTS_URL, params=params)
                if response.status_code == 200:
                    with open(audio_file_path, "wb") as f:
                        f.write(response.content)
                    audio_filenames.append(f"audio/{audio_filename}")
                    print(f"✅ Saved: {audio_file_path}")
                else:
                    print(f"❌ Failed for {clip} - HTTP {response.status_code} {response.reason}")
            except Exception as e:
                print(f"❌ Error while requesting TTS: {e}")

            # Calculate the duration of the current audio using pydub
            audio_duration = get_audio_duration(audio_file_path)
            start_time = current_time
            end_time = current_time + audio_duration
            srt_content.append(
                f"{len(srt_content) + 1}\n{format_time(start_time)} --> {format_time(end_time)}\n{clip}\n\n")
            current_time = end_time

        # Store the audio file paths in the data for later use
        data["script"][index]["audio"] = audio_filenames

    # Write the SRT file
    srt_file_path = os.path.join(project_path, "subtitles.srt")
    with open(srt_file_path, "w", encoding="utf-8") as f:
        f.writelines(srt_content)
    print(f"✅ Saved SRT: {srt_file_path}")


def get_audio_duration(audio_path):
    """ Get the duration of the audio in seconds """
    try:
        audio = AudioSegment.from_wav(audio_path)  # Ensure it's WAV
        duration_ms = len(audio)  # Duration in milliseconds
        return duration_ms / 1000  # Convert to seconds
    except Exception as e:
        print(f"❌ Error reading audio file: {e}")
        return 0  # Return 0 if there's an error


def format_time(seconds):
    """Convert time in seconds to SRT format: hh:mm:ss,ms"""
    mins, secs = divmod(seconds, 60)
    hours, mins = divmod(mins, 60)
    return f"{int(hours):02}:{int(mins):02}:{int(secs):02},{int((seconds % 1) * 1000):03}"


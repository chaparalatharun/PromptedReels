"""
This file is deprecated

    NP_123
"""
# import os
# import requests
# from pydub import AudioSegment
# import re
# import yaml
# from dotenv import load_dotenv
#
# load_dotenv()
#
# # === TTS Server Config ===
# TTS_SERVER_IP =  os.getenv("TTS_SERVER_IP")
# TTS_PORT =  os.getenv("TTS_PORT")
# TTS_URL = f"http://{TTS_SERVER_IP}:{TTS_PORT}/tts?"
#
# # === Load audio config once ===
# with open("VideoAutoMaker/config/audio_config.yaml", "r", encoding="utf-8") as f:
#     AUDIO_CONFIG = yaml.safe_load(f)
#
# # === Default TTS Parameters ===
# DEFAULT_TTS_PARAMS = {
#     "text_lang": "zh",
#     "cut_punc": "。，？",
#     "speed": "1.2",
#     "ref_audio_path": "output/reference.wav",
#     "prompt_text": "就是跟他这个成长的外部环境有关系，和本身的素质也有关系，他是一个",
#     "prompt_lang": "zh",
#     "text_split_method": "cut5",
#     "batch_size": 1,
#     "media_type": "wav",
#     "streaming_mode": "true",
# }
#
#
# def split_text_into_clips(text):
#     clips = re.split(r'[，。？]', text)
#     return [clip.strip() for clip in clips if clip.strip()]
#
#
# def switch_character_model(character: str, emotion: str):
#     char_cfg = AUDIO_CONFIG.get("characters", {}).get(character)
#     if not char_cfg:
#         print(f"⚠️ No config found for character: {character}")
#         return
#
#     # Switch GPT/SOVITS models
#     try:
#         if "gpt_weights" in char_cfg:
#             res1 = requests.get(f"http://{TTS_SERVER_IP}:{TTS_PORT}/set_gpt_weights", params={"weights_path": char_cfg["gpt_weights"]})
#         if "sovits_weights" in char_cfg:
#             res2 = requests.get(f"http://{TTS_SERVER_IP}:{TTS_PORT}/set_sovits_weights", params={"weights_path": char_cfg["sovits_weights"]})
#         print(f"✅ Switched models for {character}")
#     except Exception as e:
#         print(f"❌ Error switching models for {character}: {e}")
#
#     # Set prompt voice based on emotion
#     emotion_cfg = char_cfg.get("emotions", {}).get(emotion)
#     if not emotion_cfg:
#         print(f"⚠️ No emotion config for {character} with emotion {emotion}, using defaults.")
#         return
#
#     DEFAULT_TTS_PARAMS["ref_audio_path"] = emotion_cfg.get("ref_audio_path", DEFAULT_TTS_PARAMS["ref_audio_path"])
#     DEFAULT_TTS_PARAMS["prompt_text"] = emotion_cfg.get("prompt_text", DEFAULT_TTS_PARAMS["prompt_text"])
#
#
#
# def get_audio_duration(audio_path):
#     try:
#         audio = AudioSegment.from_wav(audio_path)
#         return len(audio) / 1000  # in seconds
#     except Exception as e:
#         print(f"❌ Error reading audio file: {e}")
#         return 0
#
#
# def format_time(seconds):
#     mins, secs = divmod(seconds, 60)
#     hours, mins = divmod(mins, 60)
#     return f"{int(hours):02}:{int(mins):02}:{int(secs):02},{int((seconds % 1) * 1000):03}"
#
#
# def generate_tts_audio(data, project_path, reGen=True):
#     output_name = os.path.basename(project_path)
#     output_audio = os.path.join(project_path, "audio")
#     os.makedirs(output_audio, exist_ok=True)
#
#     srt_content = []
#     current_time = 0
#
#     last_character = None
#     last_emotion = None
#
#     for index, block in enumerate(data["script"]):
#         character = block.get("character", "default")
#         emotion = block.get("emotion", "愤怒")
#         if character != last_character or emotion != last_emotion:
#             switch_character_model(character, emotion)
#             last_character = character
#             last_emotion = emotion
#
#         script = block["text"]
#         clips = split_text_into_clips(script)
#         audio_filenames = []
#
#         for i, clip in enumerate(clips):
#             audio_filename = f"{output_name}_{index + 1}_{i + 1}.wav"
#             audio_file_path = os.path.join(output_audio, audio_filename)
#
#             if os.path.exists(audio_file_path) and not reGen:
#                 print(f"⏭️ Skipping existing: {audio_file_path}")
#                 audio_filenames.append(f"audio/{audio_filename}")
#                 duration = get_audio_duration(audio_file_path)
#                 srt_content.append(
#                     f"{len(srt_content) + 1}\n{format_time(current_time)} --> {format_time(current_time + duration)}\n{clip}\n\n"
#                 )
#                 current_time += duration
#                 continue
#
#             print(f"[TTS] Generating for: {clip}")
#             params = DEFAULT_TTS_PARAMS.copy()
#             params["text"] = clip
#
#             try:
#                 response = requests.get(TTS_URL, params=params)
#                 if response.status_code == 200:
#                     with open(audio_file_path, "wb") as f:
#                         f.write(response.content)
#                     print(f"✅ Saved: {audio_file_path}")
#                 else:
#                     print(f"❌ TTS Error [{response.status_code}]: {response.text}")
#                     continue
#             except Exception as e:
#                 print(f"❌ Request error: {e}")
#                 continue
#
#             audio_filenames.append(f"audio/{audio_filename}")
#             duration = get_audio_duration(audio_file_path)
#             srt_content.append(
#                 f"{len(srt_content) + 1}\n{format_time(current_time)} --> {format_time(current_time + duration)}\n{clip}\n\n"
#             )
#             current_time += duration
#
#         data["script"][index]["audio"] = audio_filenames
#
#     # Write subtitles
#     srt_path = os.path.join(project_path, "subtitles.srt")
#     with open(srt_path, "w", encoding="utf-8") as f:
#         f.writelines(srt_content)
#     print(f"✅ SRT saved: {srt_path}")

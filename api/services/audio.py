# api/services/audio.py
import os
import json
from pathlib import Path
import httpx
from fastapi import HTTPException
from datetime import datetime
from pydub import AudioSegment

from api.config import PROJECTS_DIR
from api.services.projects import _read_json_safe, atomic_write_json, update_block_text

ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
ELEVENLABS_BASE = "https://api.elevenlabs.io/v1"

def generate_audio_service(project: str, block_id: str, text: str, voice_id: str) -> dict:
    project_dir = os.path.join(PROJECTS_DIR, project)
    script_path = os.path.join(project_dir, "script.json")
    media_dir = os.path.join(project_dir, "media", "audio")
    audio_file = os.path.join(media_dir, f"{block_id}.mp3")
    audio_json_path = os.path.join(media_dir, "audio.json")

    if not os.path.exists(script_path):
        raise HTTPException(status_code=404, detail="Project not found")

    os.makedirs(media_dir, exist_ok=True)

    update_block_text(project, block_id, text)

    headers = {
        "xi-api-key": ELEVENLABS_API_KEY,
        "Content-Type": "application/json",
    }
    payload = {
        "text": text,
        "model_id": "eleven_monolingual_v1",
        "voice_settings": {
            "stability": 0.5,
            "similarity_boost": 0.5
        }
    }

    url = f"{ELEVENLABS_BASE}/text-to-speech/{voice_id}"

    try:
        with httpx.stream("POST", url, headers=headers, json=payload, timeout=60.0) as res:
            if res.status_code != 200:
                raise HTTPException(status_code=500, detail="Audio generation failed")
            with open(audio_file, "wb") as out_file:
                for chunk in res.iter_bytes():
                    out_file.write(chunk)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    audio_meta = _read_json_safe(audio_json_path)
    audio_url = f"/static/{project}/media/audio/{block_id}.mp3"
    audio_meta[block_id] = {
        "voice_id": voice_id,
        "updated_at": datetime.utcnow().isoformat(),
        "url": audio_url,
    }
    atomic_write_json(audio_json_path, audio_meta)

    return {
        "success": True,
        "audio_url": audio_url,
        "voice_id": voice_id
    }

def generate_full_audio_service(project: str) -> dict:
    project_dir = os.path.join(PROJECTS_DIR, project)
    media_dir = os.path.join(project_dir, "media", "audio")
    audio_json_path = os.path.join(media_dir, "audio.json")
    full_audio_path = os.path.join(media_dir, "full_audio.mp3")

    if not os.path.exists(audio_json_path):
        raise HTTPException(status_code=404, detail="No audio metadata found")

    os.makedirs(media_dir, exist_ok=True)

    audio_meta = _read_json_safe(audio_json_path)

    segments = []

    for block_id, entry in audio_meta.items():
        audio_path = os.path.join(media_dir, f"{block_id}.mp3")

        if not os.path.exists(audio_path):
            continue  # skip missing files

        try:
            segment = AudioSegment.from_mp3(audio_path)
            segments.append(segment)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error loading {block_id}.mp3: {e}")

    if not segments:
        raise HTTPException(status_code=400, detail="No audio segments available to merge")

    final = segments[0]
    for seg in segments[1:]:
        final += seg

    final.export(full_audio_path, format="mp3")

    return {
        "success": True,
        "url": f"/static/{project}/media/audio/full_audio.mp3",
        "updated_at": datetime.utcnow().isoformat()
    }
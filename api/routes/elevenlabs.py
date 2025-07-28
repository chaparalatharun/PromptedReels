# api/routes/elevenlabs.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import httpx
import os
from pathlib import Path
from api.services.audio import generate_audio_service
from api.services.audio import generate_full_audio_service

router = APIRouter()
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
ELEVENLABS_BASE = "https://api.elevenlabs.io/v1"


@router.get("/voices")
async def list_voices():
    headers = {
        "xi-api-key": ELEVENLABS_API_KEY,
    }
    async with httpx.AsyncClient() as client:
        res = await client.get(f"{ELEVENLABS_BASE}/voices", headers=headers)
        if res.status_code != 200:
            raise HTTPException(status_code=500, detail="Failed to fetch voices")
        return res.json()


# 👇 NEW: Generate Audio Request schema
class GenerateAudioRequest(BaseModel):
    project_name: str
    block_id: str
    text: str
    voice_id: str



@router.post("/generate_audio")
async def generate_audio(req: GenerateAudioRequest):
    return generate_audio_service(
        req.project_name, req.block_id, req.text, req.voice_id
    )


class GenerateFullAudioRequest(BaseModel):
    project_name: str


@router.post("/generate_full_audio")
async def generate_full_audio(req: GenerateFullAudioRequest):
    return generate_full_audio_service(req.project_name)
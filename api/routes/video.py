from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
import os
import json
import subprocess

from api.services.projects import get_project_path
from api.services.video_manager import generate_block_video
from api.services.block_stitcher import stitch_block_videos as stitch_video_blocks
from api.services.muxer import mux_audio_and_video 

router = APIRouter()

# ---- Block Video Generation ----

class GenerateVideoRequest(BaseModel):
    project_name: str
    block_id: str
    block_text: str
    user_prompt: Optional[str] = ""

@router.post("/generate_block_video")
async def generate_block_video_route(payload: GenerateVideoRequest):
    final_path = await generate_block_video(
        project_name=payload.project_name,
        block_id=payload.block_id,
        block_text=payload.block_text,
        user_prompt=payload.user_prompt
    )
    return {
        "status": "success",
        "video_path": final_path,
        "url": f"/static/{payload.project_name}/media/video/{payload.block_id}.mp4"
    }

# ---- Full Video Stitching ----

class GenerateFullVideoRequest(BaseModel):
    project_name: str

@router.post("/generate_full_video")
async def generate_full_video_route(payload: GenerateFullVideoRequest):
    project_name = payload.project_name
    project_path = get_project_path(project_name)
    video_dir = os.path.join(project_path, "media", "video")
    os.makedirs(video_dir, exist_ok=True)

    script_path = os.path.join(project_path, "script.json")
    if not os.path.exists(script_path):
        raise HTTPException(status_code=404, detail="script.json not found")

    with open(script_path) as f:
        script_data = json.load(f)
    blocks = script_data.get("blocks", [])

    print(f"📜 Found {len(blocks)} blocks in script.json")

    for i, block in enumerate(blocks):
        block_id = f"block_{i}"
        video_path = os.path.join(video_dir, f"{block_id}.mp4")
        if not os.path.exists(video_path):
            print(f"🎬 Generating video for {block_id}")
            await generate_block_video(
                project_name,
                block_id,
                block.get("text", ""),
                user_prompt=""
            )
        else:
            print(f"✅ Skipping {block_id}, already exists")

    stitched_path = os.path.join(video_dir, "final_video.mp4")
    try:
        await stitch_video_blocks(project_name, output_path=stitched_path)
    except subprocess.CalledProcessError as e:
        raise HTTPException(status_code=500, detail=f"FFmpeg failed: {e.stderr}")

    return {"success": True, "url": f"/static/{project_name}/media/video/final_video.mp4"}

# ---- Muxing Audio & Video ----

class MuxRequest(BaseModel):
    project_name: str

@router.post("/mux_audio_video")
async def mux_audio_video_route(payload: MuxRequest):
    try:
        output_path = await mux_audio_and_video(payload.project_name)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except subprocess.CalledProcessError as e:
        raise HTTPException(status_code=500, detail="FFmpeg failed")

    return {
        "success": True,
        "url": f"/static/{payload.project_name}/media/mux/full_video.mp4"
    }
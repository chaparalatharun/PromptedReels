# api.py

import os
from typing import Optional

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from engine.JsonProcessor import JsonProcessor
from engine.MediaProcessor import MediaProcessor
from engine.composer import compose_final_video
from engine.project_manager import create_project, load_json

app = FastAPI()

# Allow CORS for all domains (you can customize this!)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # ← Replace "*" with specific domains in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

projects_dir = "projects"


def get_project_choices():
    return [
        p for p in os.listdir(projects_dir)
        if not p.startswith(".") and os.path.isdir(os.path.join(projects_dir, p))
    ]


# ---------- MODELS ----------

class ProjectCreateRequest(BaseModel):
    project_name: str
    theme: str
    script: str


class MediaGenerateRequest(BaseModel):
    project_name: str
    reGen_audio: bool = True
    reGen_video: bool = True
    theme: Optional[str] = ""


class UpdateJsonRequest(BaseModel):
    project_name: str
    data: dict


class BlockProcessRequest(BaseModel):
    project_name: str
    block_index: int
    reGen_audio: bool = True
    reGen_video: bool = True
    theme: Optional[str] = ""


# ---------- ROUTES ----------

@app.get("/projects")
def list_projects():
    return {"projects": get_project_choices()}


@app.post("/create_project")
def create_project_api(req: ProjectCreateRequest):
    status = create_project(req.project_name, req.theme, req.script)
    return {"status": status}


@app.post("/generate_media")
def generate_media_api(req: MediaGenerateRequest):
    processor = MediaProcessor(
        project_name=req.project_name,
        projects_dir=projects_dir,
        reGen_audio=req.reGen_audio,
        reGen_video=req.reGen_video,
        theme=req.theme
    )
    processor.process_all()
    return {"status": f"✅ Media generated for {req.project_name}"}


@app.post("/process_block")
def process_block_api(req: BlockProcessRequest):
    processor = MediaProcessor(
        project_name=req.project_name,
        projects_dir=projects_dir,
        reGen_audio=req.reGen_audio,
        reGen_video=req.reGen_video,
        theme=req.theme
    )
    processor.process_single_block(req.block_index)
    return {"status": f"✅ Block {req.block_index} processed"}


@app.get("/project_json/{project_name}")
def get_project_json(project_name: str):
    path = os.path.join(projects_dir, project_name)
    processor = JsonProcessor(path)
    return processor.get_data()


@app.post("/update_project_json")
def update_project_json(req: UpdateJsonRequest):
    path = os.path.join(projects_dir, req.project_name)
    processor = JsonProcessor(path)
    processor.set_data(req.data)
    return {"status": "✅ Project JSON updated"}


@app.post("/compose")
def compose_video(project_name: str):
    project_path = os.path.join(projects_dir, project_name)
    data_path = os.path.join(project_path, "processed.json")
    if not os.path.isfile(data_path):
        data_path = os.path.join(project_path, "input.json")
    data = load_json(data_path)
    output_path = os.path.join(project_path, "final", "output.mp4")
    compose_final_video(data, project_path, output_path)
    return {"status": f"🎞️ Final video created at: {output_path}"}


# ---------- ERROR HANDLER ----------

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"detail": str(exc)}
    )

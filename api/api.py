from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Dict, Any
import os

from engine.json_processor import JsonProcessor
from engine.media_processor import MediaProcessor

app = FastAPI()

# CORS settings for frontend use
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve media files
MEDIA_ROOT = "projects"
app.mount("/projects", StaticFiles(directory=MEDIA_ROOT), name="projects")

class UpdateJsonRequest(BaseModel):
    data: Dict[str, Any]

@app.get("/api/project/{project_name}")
def get_project(project_name: str):
    project_path = os.path.join(MEDIA_ROOT, project_name)
    if not os.path.exists(project_path):
        raise HTTPException(status_code=404, detail="Project not found")
    jp = JsonProcessor(project_path)
    return jp.get_data()

@app.post("/api/project/{project_name}")
def update_project(project_name: str, req: UpdateJsonRequest):
    project_path = os.path.join(MEDIA_ROOT, project_name)
    if not os.path.exists(project_path):
        raise HTTPException(status_code=404, detail="Project not found")
    jp = JsonProcessor(project_path)
    jp.set_data(req.data)
    return {"status": "success"}

@app.post("/api/process/{project_name}/all")
def process_all(project_name: str):
    project_path = os.path.join(MEDIA_ROOT, project_name)
    if not os.path.exists(project_path):
        raise HTTPException(status_code=404, detail="Project not found")
    mp = MediaProcessor(project_name, MEDIA_ROOT)
    mp.process_all()
    return {"status": "all blocks processed"}

@app.post("/api/process/{project_name}/block/{index}")
def process_block(project_name: str, index: int):
    project_path = os.path.join(MEDIA_ROOT, project_name)
    if not os.path.exists(project_path):
        raise HTTPException(status_code=404, detail="Project not found")
    mp = MediaProcessor(project_name, MEDIA_ROOT)
    mp.process_single_block(index)
    return {"status": f"block {index} processed"}

@app.get("/api/project/{project_name}/media/{filename:path}")
def get_media(project_name: str, filename: str):
    file_path = os.path.join(MEDIA_ROOT, project_name, filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Media not found")
    return {"url": f"/projects/{project_name}/{filename}"}

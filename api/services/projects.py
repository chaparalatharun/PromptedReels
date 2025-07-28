# api/services/projects.py
import os, re, uuid, json
from datetime import datetime, timezone

from typing import List
from fastapi import HTTPException, status

from api.config import PROJECTS_DIR
from api.utils.fs import slugify, now_iso, atomic_write_json
from api.schemas.projects import CreateProjectRequest, BlockOut
from api.schemas.projects import ProjectSummary, ListProjectsResponse
from api.utils.llm_blocks import generate_blocks_from_idea
from api.schemas.projects import ProjectDetailResponse

 
_SENTENCE_SPLIT = re.compile(r"(?<=[\.\!\?])\s+")

def _split_idea(idea: str) -> List[str]:
    lines = [ln.strip() for ln in idea.splitlines() if ln.strip()]
    if lines:
        return lines
    parts = _SENTENCE_SPLIT.split(idea.strip())
    return [p.strip() for p in parts if p.strip()]

def _normalize_blocks(script_idea: str, target_seconds: int) -> List[BlockOut]:
    raw = _split_idea(script_idea)
    if not raw:
        raw = ["(Empty idea)"]
    # Cap to 10 blocks for Shorts MVP
    raw = raw[:10]
    n = len(raw)

    # Evenly distribute, then re-scale to hit target_seconds
    base = max(1.5, target_seconds / max(1, n))
    blocks = [BlockOut(text=t[:220], target_sec=base) for t in raw]

    total = sum(b.target_sec for b in blocks)
    if total > 0:
        scale = target_seconds / total
        for b in blocks:
            b.target_sec = round(max(1.0, min(20.0, b.target_sec * scale)), 2)

    return blocks

def create_project_service(req: CreateProjectRequest) -> tuple[str, dict, List[BlockOut]]:
    slug = slugify(req.project_name)
    project_root = os.path.join(PROJECTS_DIR, slug)

    if os.path.isdir(project_root):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Project '{slug}' already exists"
        )

    os.makedirs(project_root, exist_ok=True)

    now = now_iso()
    project_json = {
        "name": slug,
        "style": req.style or "",
        "target_seconds": int(req.target_seconds),
        "created_at": now,
        "updated_at": now,
    }

    blocks = generate_blocks_from_idea(req.script_idea)
    script_json = {
        "blocks": [b.model_dump() for b in blocks],
        "updated_at": now,
    }

    atomic_write_json(os.path.join(project_root, "project.json"), project_json)
    atomic_write_json(os.path.join(project_root, "script.json"), script_json)

    files = {
        "project": f"{project_root}/project.json",
        "script": f"{project_root}/script.json",
        "media": f"{project_root}/media/",
    }
    return slug, files, blocks



def _read_json_safe(path: str) -> dict:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

def list_projects_service() -> ListProjectsResponse:
    root = PROJECTS_DIR
    items: List[ProjectSummary] = []

    if not os.path.isdir(root):
        # Nothing yet — return empty response with gentle poll hint
        return ListProjectsResponse(
            projects=[],
            empty=True,
            last_scan=now_iso(),
            next_poll_ms=8000,
        )

    for name in sorted(os.listdir(root)):
        if name.startswith("."):
            continue
        pdir = os.path.join(root, name)
        if not os.path.isdir(pdir):
            continue

        project_path = os.path.join(pdir, "project.json")
        script_path  = os.path.join(pdir, "script.json")
        if not os.path.isfile(project_path) or not os.path.isfile(script_path):
            # Skip incomplete projects
            continue

        pj = _read_json_safe(project_path)
        sj = _read_json_safe(script_path)

        title = pj.get("title", name)
        style = pj.get("style", "")
        updated_at = pj.get("updated_at") or pj.get("created_at") or datetime.now(timezone.utc).isoformat()
        blocks = len(sj.get("blocks", []))

        has_final = os.path.isfile(os.path.join(pdir, "media", "final", "output.mp4"))

        items.append(ProjectSummary(
            name=name,
            title=title,
            style=style,
            updated_at=updated_at,
            blocks=blocks,
            has_final=has_final
        ))

    items.sort(key=lambda x: x.updated_at, reverse=True)

    return ListProjectsResponse(
        projects=items,
        empty=(len(items) == 0),
        last_scan=now_iso(),
        next_poll_ms=8000 if len(items) == 0 else 3000,
    )


def get_project_detail_service(name: str) -> ProjectDetailResponse:
    project_dir = os.path.join(PROJECTS_DIR, name)
    script_path = os.path.join(project_dir, "script.json")

    if not os.path.exists(script_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project '{name}' not found"
        )

    script_data = _read_json_safe(script_path)
    raw_blocks = script_data.get("blocks", [])

    blocks = [BlockOut(**b) for b in raw_blocks if b.get("text")]
    return ProjectDetailResponse(blocks=blocks)


def update_block_text(project: str, block_id: str, new_text: str):
    """
    Updates the `text` of a specific block in the script.json file for a project.
    Accepts block_id like "block_0", "block_1", etc., and maps it to the index.
    """
    project_dir = os.path.join(PROJECTS_DIR, project)
    script_path = os.path.join(project_dir, "script.json")

    data = _read_json_safe(script_path)
    blocks = data.get("blocks", [])

    try:
        index = int(block_id.replace("block_", ""))
        blocks[index]["text"] = new_text
    except (IndexError, ValueError):
        raise HTTPException(status_code=400, detail=f"Invalid block_id: {block_id}")

    atomic_write_json(script_path, data)


def get_project_path(project_name: str) -> str:
    return os.path.join(PROJECTS_DIR, project_name)
from typing import List, Optional, Dict
from pydantic import BaseModel, Field, conint, constr, confloat

class CreateProjectRequest(BaseModel):
    project_name: constr(strip_whitespace=True, min_length=1)
    style: Optional[constr(strip_whitespace=True)] = ""
    target_seconds: conint(ge=1, le=180) = 30
    script_idea: constr(strip_whitespace=True, min_length=1)

class BlockOut(BaseModel):
    text: constr(strip_whitespace=True, min_length=1, max_length=220)
    target_sec: confloat(ge=1.0, le=20.0)

class CreateProjectResponse(BaseModel):
    status: str = Field(default="ok")
    project: str
    files: Dict[str, str]
    blocks: List[BlockOut]

class ProjectSummary(BaseModel):
    name: str
    title: str
    style: str
    updated_at: str
    blocks: int
    has_final: bool

class ListProjectsResponse(BaseModel):
    projects: List[ProjectSummary]
    empty: bool
    last_scan: str
    next_poll_ms: int

class ProjectDetailResponse(BaseModel):
    blocks: List[BlockOut]
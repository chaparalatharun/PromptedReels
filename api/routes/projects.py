from fastapi import APIRouter, HTTPException
from api.schemas.projects import (
    CreateProjectRequest,
    CreateProjectResponse,
    ListProjectsResponse,
    ProjectDetailResponse 
)
from api.services.projects import (
    create_project_service,
    list_projects_service,
    get_project_detail_service
)

router = APIRouter()

@router.post("/create", response_model=CreateProjectResponse)
def create_project_clean(req: CreateProjectRequest):
    slug, files, blocks = create_project_service(req)
    return CreateProjectResponse(project=slug, files=files, blocks=blocks)

@router.get("", response_model=ListProjectsResponse)
def list_projects():
    return list_projects_service()

@router.get("/{name}", response_model=ProjectDetailResponse)
def get_project_detail(name: str):
    return get_project_detail_service(name)
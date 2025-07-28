# api/api.py
import os
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from .config import PROJECTS_DIR
from .routes.projects import router as projects_router
from api.routes import elevenlabs
from api.routes import video  # ✅ Import the video router

app = FastAPI()

# Ensure the data root exists before mounting static
data_root = Path(PROJECTS_DIR)
data_root.mkdir(parents=True, exist_ok=True)

app.mount("/static", StaticFiles(directory=str(data_root)), name="static")

# Register routers
app.include_router(projects_router, prefix="/projects", tags=["projects"])
app.include_router(elevenlabs.router, prefix="/elevenlabs")
app.include_router(video.router)  # ✅ Include the video router

@app.get("/")
def root():
    return {"message": "Hello from FastAPI!"}

# Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global error handler
@app.exception_handler(Exception)
async def global_exception_handler(_, exc: Exception):
    return JSONResponse(status_code=500, content={"detail": str(exc)})
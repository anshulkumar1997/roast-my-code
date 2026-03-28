import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.middleware.errors import register_error_handlers
from app.routers import roast

app = FastAPI(
    title="Roast My Code 🔥",
    description="Paste code. Get roasted. Learn something.",
    version="1.0.0",
)

# ─── CORS ────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Error handlers ──────────────────────────────────────────────────────────
register_error_handlers(app)

# ─── API routes ──────────────────────────────────────────────────────────────
app.include_router(roast.router, prefix="/api")

# ─── Serve frontend static files ─────────────────────────────────────────────
# In Docker the WORKDIR is /app, so frontend lands at /app/frontend
# Locally (running from backend/) we go up two levels to reach frontend/
_env_path = os.getenv("FRONTEND_PATH")
if _env_path:
    frontend_path = Path(_env_path)
else:
    frontend_path = Path(__file__).parent.parent.parent / "frontend"

app.mount("/static", StaticFiles(directory=frontend_path / "static"), name="static")


@app.get("/", include_in_schema=False)
async def serve_frontend():
    return FileResponse(frontend_path / "templates" / "index.html")


@app.get("/health")
async def health():
    return {"status": "ok"}

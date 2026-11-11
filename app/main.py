from contextlib import asynccontextmanager
import os
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.api.endpoints.browser import router as browser_router
from app.api.endpoints.changes import router as changes_router
from app.api.endpoints.crawler import router as crawler_router
from app.api.endpoints.dashboard import router as dashboard_router
from app.api.endpoints.exporter import router as exporter_router
from app.api.endpoints.health import router as health_router
from app.api.endpoints.jobs import router as jobs_router
from app.api.endpoints.logs import router as logs_router
from app.api.endpoints.metadata import router as metadata_router
from app.api.endpoints.normalizer import router as normalizer_router
from app.api.endpoints.opportunities import router as opportunities_router
from app.api.endpoints.preview import router as preview_router
from app.api.endpoints.quality import router as quality_router
from app.api.endpoints.replay import router as replay_router
from app.api.endpoints.schema import router as schema_router
from app.api.endpoints.selector import router as selector_router
from app.api.endpoints.snapshots import router as snapshots_router
from app.config import settings
from app.database import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(
    title=settings.APP_NAME,
    debug=settings.DEBUG,
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

os.makedirs("static", exist_ok=True)
os.makedirs("templates", exist_ok=True)

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Register Routers
app.include_router(preview_router)
app.include_router(selector_router)
app.include_router(crawler_router)
app.include_router(normalizer_router)
app.include_router(quality_router)
app.include_router(snapshots_router)
app.include_router(changes_router)
app.include_router(jobs_router)
app.include_router(exporter_router)
app.include_router(dashboard_router)
app.include_router(schema_router)
app.include_router(metadata_router)
app.include_router(health_router)
app.include_router(replay_router)
app.include_router(logs_router)
app.include_router(opportunities_router)
app.include_router(browser_router)


@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    return templates.TemplateResponse(request, "dashboard.html")


@app.get("/selector-builder", response_class=HTMLResponse)
async def selector_builder(request: Request):
    return templates.TemplateResponse(request, "selector_builder.html")


@app.get("/opportunities", response_class=HTMLResponse)
async def opportunities_page(request: Request):
    return templates.TemplateResponse(request, "opportunities.html")


@app.get("/api/health", tags=["Health"])
async def health_check():
    return {
        "status": "online",
        "app_name": settings.APP_NAME,
        "environment": settings.ENV
    }
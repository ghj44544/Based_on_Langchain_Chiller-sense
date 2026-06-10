from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import chat, diagnosis, meta, rag, report
from app.core.config import get_settings
from app.db.session import init_db
from app.utils.file_utils import ensure_dir


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    ensure_dir(settings.upload_path)
    ensure_dir(settings.report_path)
    ensure_dir(settings.knowledge_base_path)
    init_db()
    yield


settings = get_settings()
app = FastAPI(title=settings.app_name, lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(diagnosis.router, prefix="/api")
app.include_router(chat.router, prefix="/api")
app.include_router(report.router, prefix="/api")
app.include_router(meta.router, prefix="/api")
app.include_router(rag.router, prefix="/api")

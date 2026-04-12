from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.core.config import get_settings
from app.core.logging import logger
from app.db.session import engine, Base

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("startup", app=settings.APP_NAME, version=settings.APP_VERSION)
    # Create tables on startup in dev mode. In production use Alembic migrations.
    if settings.DEBUG:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    yield
    logger.info("shutdown")
    await engine.dispose()


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)


@app.get("/health", tags=["health"])
async def health():
    return {"status": "ok", "version": settings.APP_VERSION}

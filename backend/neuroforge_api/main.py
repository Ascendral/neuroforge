from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from neuroforge_api import __version__
from neuroforge_api.db import init_db
from neuroforge_api.routers import neurons as neurons_router


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    init_db()
    yield


app = FastAPI(title="NeuroForge API", version=__version__, lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(neurons_router.router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "version": __version__}

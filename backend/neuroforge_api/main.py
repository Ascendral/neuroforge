from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from neuroforge_api import __version__

app = FastAPI(title="NeuroForge API", version=__version__)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "version": __version__}

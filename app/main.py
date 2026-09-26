from fastapi import FastAPI

from app.api.routes import router

app = FastAPI(
    title="ScoutAI",
    description="Autonomous evidence-based research agent",
    version="0.1.0",
)

app.include_router(router)


@app.get("/", tags=["system"])
def root() -> dict[str, str]:
    return {"name": "ScoutAI", "status": "online", "version": "0.1.0"}


@app.get("/health", tags=["system"])
def health() -> dict[str, str]:
    return {"status": "healthy"}

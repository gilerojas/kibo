from fastapi import FastAPI

from app.config import get_settings
from app.routers.telegram import router as telegram_router

app = FastAPI(title="Kibo", version="0.1.0")
app.include_router(telegram_router)


@app.get("/health")
def health() -> dict[str, str]:
    settings = get_settings()
    return {"status": "ok", "env": settings.app_env}

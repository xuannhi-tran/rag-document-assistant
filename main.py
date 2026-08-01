from fastapi import FastAPI
from app.routes.health import router as health_router
from app.routes.upload import router as upload_router
from app.routes.ask import router as ask_router
import uvicorn

app = FastAPI()

app.include_router(health_router)
app.include_router(upload_router)
app.include_router(ask_router)
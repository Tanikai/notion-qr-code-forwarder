import uvicorn
from fastapi import FastAPI
from .routers import redirect
from contextlib import asynccontextmanager

# Middlewares
from fastapi.middleware.cors import CORSMiddleware
from .dependencies.notion import get_notion_forwarder
import logging

logger = logging.getLogger("uvicorn")

@asynccontextmanager
async def lifespan(app: FastAPI):
    #startup
    forwarder = get_notion_forwarder()
    await forwarder.populate_config()
    logger.info("Populated Configuration")
    yield
    # cleanup
    # (currently none)

app = FastAPI(lifespan=lifespan)

app.include_router(redirect.router, prefix="/r")

app.add_middleware(
CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "root path"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
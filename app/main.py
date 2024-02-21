import uvicorn
from fastapi import FastAPI
from .routers import redirect
from contextlib import asynccontextmanager

# Middlewares
from fastapi.middleware.cors import CORSMiddleware
from .dependencies.notion import get_notion_forwarder
from .config import get_configuration
import logging

logger = logging.getLogger("uvicorn")

config = get_configuration()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # startup
    forwarder = get_notion_forwarder()
    if config.lazy_load:
        logger.info("Lazy loading enabled, skipping Configuration Population")
        await forwarder.create_databases(populate=False)
    else:
        await forwarder.create_databases(populate=True)
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

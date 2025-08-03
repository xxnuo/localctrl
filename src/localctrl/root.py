from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from localctrl.config import Config
from localctrl.core import coreRouter
from localctrl.logger import logger

app = FastAPI(title="LocalCtrl", version=Config.version)

app.add_middleware(
    CORSMiddleware,
    allow_origins=Config.allow_origins,
    allow_credentials=Config.allow_credentials,
    allow_methods=Config.allow_methods,
    allow_headers=Config.allow_headers,
)

logger.info("Loading core router...")
app.include_router(coreRouter, prefix="/core", tags=["core"])

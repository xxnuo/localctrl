from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from localctrl.config import Config
from localctrl.logger import logger
from localctrl.plugins import pluginsRouter

app = FastAPI(title="LocalCtrl", version=Config.version)

app.add_middleware(
    CORSMiddleware,
    allow_origins=Config.allow_origins,
    allow_credentials=Config.allow_credentials,
    allow_methods=Config.allow_methods,
    allow_headers=Config.allow_headers,
)


logger.info("Loading plugins...")
app.include_router(pluginsRouter, prefix="/plugins", tags=["plugins"])

from fastapi import APIRouter

from localctrl.plugins.core import coreRouter
from localctrl.plugins.media import mediaRouter

pluginsRouter = APIRouter()

pluginsRouter.include_router(coreRouter, prefix="/core", tags=["core"])
pluginsRouter.include_router(mediaRouter, prefix="/media", tags=["media"])

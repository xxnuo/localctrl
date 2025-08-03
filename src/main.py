import uvicorn

from localctrl.config import Config
from localctrl.logger import logger


def main():
    logger.info("LocalCtrl is running")

    uvicorn.run(
        "localctrl.root:app",
        host=Config.host,
        port=Config.port,
        reload=Config.debug,
        log_level=Config.log_level.lower(),
    )


if __name__ == "__main__":
    main()

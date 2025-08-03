import os

import uvicorn

from localctrl.config import Config
from localctrl.data import KVStorage
from localctrl.logger import logger
from localctrl.utils import time_str, timezone_str

db = KVStorage("main")
db_log = KVStorage("main_log")


def main():
    if not os.path.exists(Config.config_dir):
        os.makedirs(Config.config_dir)

    db.set("timezone", timezone_str())
    db.set("last_run_time", time_str())
    run_times = db.get("run_times")
    if run_times is None:
        run_times = 0
    else:
        run_times = int(run_times)

    db.set("run_times", str(run_times + 1))
    db.set("version", Config.version)

    logger.info("LocalCtrl is running")
    db_log.log("Running")
    uvicorn.run(
        "localctrl.root:app",
        host=Config.host,
        port=Config.port,
        reload=Config.debug,
        log_level=Config.log_level.lower(),
    )
    db_log.log("Stopped")


if __name__ == "__main__":
    main()

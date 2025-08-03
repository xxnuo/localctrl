import os
from typing import List

from dotenv import load_dotenv

load_dotenv()


class Config:
    version: str = os.getenv("LC_VERSION", "0.1.0")
    host: str = os.getenv("LC_HOST", "0.0.0.0")
    port: int = int(os.getenv("LC_PORT", "9931"))
    debug: bool = os.getenv("LC_DEBUG", "False").lower() == "true"
    log_level: str = os.getenv("LC_LOG_LEVEL", "INFO").upper()
    log_file: str = os.getenv("LC_LOG_FILE", "")

    token: str = os.getenv("LC_ADMIN_TOKEN", "")

    allow_origins: List[str] = os.getenv("LC_ALLOW_ORIGINS", "*").split(",")
    allow_credentials: bool = (
        os.getenv("LC_ALLOW_CREDENTIALS", "True").lower() == "true"
    )
    allow_methods: List[str] = os.getenv("LC_ALLOW_METHODS", "*").split(",")
    allow_headers: List[str] = os.getenv("LC_ALLOW_HEADERS", "*").split(",")

    config_dir: str = os.getenv(
        "LC_CONFIG_DIR", os.path.expanduser("~") + "/.config/localctrl"
    )

    db_url: str = os.getenv("LC_DB_URL", f"sqlite:///{config_dir}/data.db")

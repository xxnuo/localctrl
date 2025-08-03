import os
import sys

from loguru import logger

from localctrl.config import Config

# 移除默认的处理器，避免重复输出
logger.remove()

# 定义美化的日志格式
FILE_FORMAT = "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
CONS_FORMAT = "<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"

# 配置日志文件
if Config.log_file != "":
    # 确保日志目录存在
    os.makedirs(os.path.dirname(Config.log_file), exist_ok=True)

    # 添加文件日志处理器
    logger.add(
        Config.log_file,
        rotation="10 MB",
        retention="10 days",
        level=Config.log_level,
        format=FILE_FORMAT,
        compression="zip",
        enqueue=True,
    )

if Config.debug or Config.log_file == "":
    # 设置控制台日志等级和美化输出
    logger.add(
        sink=sys.stderr,
        level=Config.log_level,
        format=CONS_FORMAT,
        colorize=True,
    )

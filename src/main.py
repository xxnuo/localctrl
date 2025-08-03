"""
LocalCtrl - 主程序入口
"""
import os
import sys
import argparse
import logging
from logging.handlers import RotatingFileHandler
import signal
import time

from localctrl.config.settings import settings, settings_manager
from localctrl.models.database import init_db
from localctrl.core.engine import get_engine
from localctrl.api.app import start_api_server

# 配置日志
def setup_logging():
    """设置日志"""
    log_level = getattr(logging, settings.logging.level)
    log_file = settings.logging.file
    
    # 确保日志目录存在
    log_dir = os.path.dirname(log_file)
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir, exist_ok=True)
    
    # 配置根日志记录器
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            RotatingFileHandler(
                log_file,
                maxBytes=settings.logging.max_size,
                backupCount=settings.logging.backup_count
            ),
            logging.StreamHandler()
        ]
    )

def main():
    """主函数"""
    # 解析命令行参数
    parser = argparse.ArgumentParser(description="LocalCtrl - 远程控制服务")
    parser.add_argument("--config", help="配置文件路径")
    parser.add_argument("--debug", action="store_true", help="启用调试模式")
    parser.add_argument("--host", help="API服务器主机")
    parser.add_argument("--port", type=int, help="API服务器端口")
    args = parser.parse_args()
    
    # 更新配置
    if args.config:
        os.environ["LOCALCTRL_CONFIG_DIR"] = os.path.dirname(os.path.abspath(args.config))
    
    # 确保目录存在
    settings_manager.ensure_directories()
    
    # 设置日志
    setup_logging()
    logger = logging.getLogger(__name__)
    
    # 更新调试模式
    if args.debug:
        settings.debug = True
        settings.server.debug = True
        logging.getLogger().setLevel(logging.DEBUG)
        logger.debug("Debug mode enabled")
    
    # 更新主机和端口
    if args.host:
        settings.server.host = args.host
    if args.port:
        settings.server.port = args.port
    
    logger.info(f"Starting LocalCtrl v{settings.version}")
    
    try:
        # 初始化数据库
        init_db()
        
        # 启动API服务器
        start_api_server()
        
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt, shutting down...")
    except Exception as e:
        logger.exception(f"Error starting LocalCtrl: {e}")
        sys.exit(1)
    finally:
        # 停止引擎
        engine = get_engine()
        if engine.running:
            engine.stop()
        
        logger.info("LocalCtrl shutdown complete")

if __name__ == "__main__":
    main()

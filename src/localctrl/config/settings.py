"""
配置模块 - 管理系统配置
"""
import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

# 默认配置目录
DEFAULT_CONFIG_DIR = os.path.expanduser("~/.localctrl")
CONFIG_FILE_NAME = "config.json"

class DatabaseSettings(BaseModel):
    """数据库配置"""
    url: str = Field(default="sqlite:///data/localctrl.db")
    

class ServerSettings(BaseModel):
    """服务器配置"""
    host: str = Field(default="127.0.0.1")
    port: int = Field(default=8000)
    debug: bool = Field(default=False)
    secret_key: str = Field(default="")
    allow_origins: List[str] = Field(default=["http://localhost:3000", "http://127.0.0.1:3000"])
    

class LoggingSettings(BaseModel):
    """日志配置"""
    level: str = Field(default="INFO")
    file: str = Field(default="logs/localctrl.log")
    max_size: int = Field(default=10485760)  # 10MB
    backup_count: int = Field(default=5)
    

class Settings(BaseModel):
    """应用配置"""
    debug: bool = Field(default=False)
    data_dir: str = Field(default="data")
    logs_dir: str = Field(default="logs")
    plugins_dir: str = Field(default="plugins")
    enabled_plugins: List[str] = Field(default=[])
    database: DatabaseSettings = Field(default_factory=DatabaseSettings)
    server: ServerSettings = Field(default_factory=ServerSettings)
    logging: LoggingSettings = Field(default_factory=LoggingSettings)
    

class ConfigManager:
    """配置管理器"""
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ConfigManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
            
        self.config_dir = os.environ.get("LOCALCTRL_CONFIG_DIR", DEFAULT_CONFIG_DIR)
        self.config_file = os.path.join(self.config_dir, CONFIG_FILE_NAME)
        self.settings = Settings()
        self._initialized = True
        
        # 确保配置目录存在
        os.makedirs(self.config_dir, exist_ok=True)
        
        # 加载配置
        self.load_config()
        
    def load_config(self) -> None:
        """加载配置文件"""
        if not os.path.exists(self.config_file):
            logger.info(f"Config file not found, creating default at {self.config_file}")
            self.save_config()
            return
            
        try:
            with open(self.config_file, "r") as f:
                config_data = json.load(f)
                self.settings = Settings.parse_obj(config_data)
                logger.info(f"Config loaded from {self.config_file}")
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            
    def save_config(self) -> None:
        """保存配置到文件"""
        try:
            with open(self.config_file, "w") as f:
                json.dump(self.settings.dict(), f, indent=2)
                logger.info(f"Config saved to {self.config_file}")
        except Exception as e:
            logger.error(f"Failed to save config: {e}")
            
    def update_config(self, config_dict: Dict[str, Any]) -> None:
        """
        更新配置
        
        Args:
            config_dict: 配置字典
        """
        for key, value in config_dict.items():
            if hasattr(self.settings, key):
                setattr(self.settings, key, value)
                
        self.save_config()
        
    def get_plugin_config(self, plugin_id: str) -> Dict[str, Any]:
        """
        获取插件配置
        
        Args:
            plugin_id: 插件ID
            
        Returns:
            Dict: 插件配置
        """
        # 从配置文件中获取插件配置，如果不存在则返回空字典
        plugin_config = getattr(self.settings, f"plugin_{plugin_id}", {})
        return plugin_config
        
    def save_plugin_config(self, plugin_id: str, config: Dict[str, Any]) -> None:
        """
        保存插件配置
        
        Args:
            plugin_id: 插件ID
            config: 插件配置
        """
        setattr(self.settings, f"plugin_{plugin_id}", config)
        self.save_config()
        
    def ensure_directories(self) -> None:
        """确保所需目录存在"""
        dirs = [
            self.settings.data_dir,
            self.settings.logs_dir,
            self.settings.plugins_dir
        ]
        
        for directory in dirs:
            path = Path(directory)
            if not path.is_absolute():
                # 如果是相对路径，则基于配置目录
                path = Path(self.config_dir) / path
                
            os.makedirs(path, exist_ok=True)
            logger.debug(f"Ensured directory exists: {path}")
            

# 单例模式获取配置管理器
settings_manager = ConfigManager()
settings = settings_manager.settings 
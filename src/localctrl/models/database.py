"""
数据库模型 - 定义数据库结构和操作
"""
import os
import logging
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Text, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, Session
from contextlib import contextmanager

from ..config.settings import settings

logger = logging.getLogger(__name__)

# 创建数据库引擎
engine = create_engine(settings.database.url)

# 创建会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 创建基类
Base = declarative_base()

@contextmanager
def get_db():
    """获取数据库会话"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class Plugin(Base):
    """插件表"""
    __tablename__ = "plugins"
    
    id = Column(String(36), primary_key=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    version = Column(String(20), nullable=False)
    enabled = Column(Boolean, default=False)
    config = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关联
    logs = relationship("PluginLog", back_populates="plugin", cascade="all, delete-orphan")

class PluginLog(Base):
    """插件日志表"""
    __tablename__ = "plugin_logs"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    plugin_id = Column(String(36), ForeignKey("plugins.id"), nullable=False)
    level = Column(String(20), nullable=False)
    message = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    # 关联
    plugin = relationship("Plugin", back_populates="logs")

class User(Base):
    """用户表"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    email = Column(String(100), unique=True, nullable=True)
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关联
    api_keys = relationship("ApiKey", back_populates="user", cascade="all, delete-orphan")

class ApiKey(Base):
    """API密钥表"""
    __tablename__ = "api_keys"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    key = Column(String(64), unique=True, nullable=False)
    name = Column(String(50), nullable=False)
    is_active = Column(Boolean, default=True)
    expires_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 关联
    user = relationship("User", back_populates="api_keys")

class Setting(Base):
    """系统设置表"""
    __tablename__ = "settings"
    
    key = Column(String(100), primary_key=True)
    value = Column(JSON, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

def init_db():
    """初始化数据库"""
    # 创建所有表
    Base.metadata.create_all(bind=engine)
    logger.info("Database initialized")
    
    # 检查是否需要创建初始管理员用户
    with get_db() as db:
        admin_exists = db.query(User).filter(User.is_admin == True).first()
        if not admin_exists:
            # 创建默认管理员用户
            from werkzeug.security import generate_password_hash
            default_password = "admin"  # 在生产环境中应该使用更强的密码
            admin_user = User(
                username="admin",
                password_hash=generate_password_hash(default_password),
                is_admin=True
            )
            db.add(admin_user)
            db.commit()
            logger.info("Created default admin user")

# 数据库操作类
class DatabaseManager:
    """数据库管理器"""
    
    @staticmethod
    def get_plugin(db: Session, plugin_id: str) -> Optional[Plugin]:
        """获取插件信息"""
        return db.query(Plugin).filter(Plugin.id == plugin_id).first()
    
    @staticmethod
    def get_plugins(db: Session, skip: int = 0, limit: int = 100) -> List[Plugin]:
        """获取所有插件"""
        return db.query(Plugin).offset(skip).limit(limit).all()
    
    @staticmethod
    def create_plugin(db: Session, plugin_data: Dict[str, Any]) -> Plugin:
        """创建插件记录"""
        plugin = Plugin(**plugin_data)
        db.add(plugin)
        db.commit()
        db.refresh(plugin)
        return plugin
    
    @staticmethod
    def update_plugin(db: Session, plugin_id: str, plugin_data: Dict[str, Any]) -> Optional[Plugin]:
        """更新插件记录"""
        plugin = db.query(Plugin).filter(Plugin.id == plugin_id).first()
        if not plugin:
            return None
            
        for key, value in plugin_data.items():
            setattr(plugin, key, value)
            
        db.commit()
        db.refresh(plugin)
        return plugin
    
    @staticmethod
    def delete_plugin(db: Session, plugin_id: str) -> bool:
        """删除插件记录"""
        plugin = db.query(Plugin).filter(Plugin.id == plugin_id).first()
        if not plugin:
            return False
            
        db.delete(plugin)
        db.commit()
        return True
    
    @staticmethod
    def log_plugin_event(db: Session, plugin_id: str, level: str, message: str) -> PluginLog:
        """记录插件事件"""
        log = PluginLog(plugin_id=plugin_id, level=level, message=message)
        db.add(log)
        db.commit()
        db.refresh(log)
        return log
    
    @staticmethod
    def get_plugin_logs(db: Session, plugin_id: str, skip: int = 0, limit: int = 100) -> List[PluginLog]:
        """获取插件日志"""
        return db.query(PluginLog).filter(PluginLog.plugin_id == plugin_id).order_by(PluginLog.timestamp.desc()).offset(skip).limit(limit).all()
    
    @staticmethod
    def get_setting(db: Session, key: str) -> Optional[Any]:
        """获取设置值"""
        setting = db.query(Setting).filter(Setting.key == key).first()
        return setting.value if setting else None
    
    @staticmethod
    def set_setting(db: Session, key: str, value: Any) -> Setting:
        """设置值"""
        setting = db.query(Setting).filter(Setting.key == key).first()
        if setting:
            setting.value = value
        else:
            setting = Setting(key=key, value=value)
            db.add(setting)
            
        db.commit()
        db.refresh(setting)
        return setting 
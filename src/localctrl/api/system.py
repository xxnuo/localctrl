"""
系统API模块 - 提供系统管理相关的API接口
"""
import logging
import os
import platform
import psutil
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..models.database import get_db, DatabaseManager
from ..config.settings import settings, settings_manager
from ..core.engine import get_engine
from .auth import get_current_active_user, get_current_admin_user, User

# 配置日志
logger = logging.getLogger(__name__)

# 创建路由
router = APIRouter()

# 模型
class SystemInfo(BaseModel):
    hostname: str
    platform: str
    python_version: str
    cpu_count: int
    memory_total: int
    memory_available: int
    disk_total: int
    disk_free: int

class SystemSettings(BaseModel):
    settings: Dict[str, Any]

class SystemStatus(BaseModel):
    status: str
    uptime: float
    cpu_percent: float
    memory_percent: float
    plugin_count: int
    active_plugin_count: int

@router.get("/info", response_model=SystemInfo)
async def get_system_info(current_user: User = Depends(get_current_active_user)):
    """获取系统信息"""
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    
    return SystemInfo(
        hostname=platform.node(),
        platform=f"{platform.system()} {platform.release()}",
        python_version=platform.python_version(),
        cpu_count=os.cpu_count(),
        memory_total=memory.total,
        memory_available=memory.available,
        disk_total=disk.total,
        disk_free=disk.free
    )

@router.get("/status", response_model=SystemStatus)
async def get_system_status(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """获取系统状态"""
    engine = get_engine()
    plugins = engine.plugins
    active_plugins = [p for p in plugins.values() if p.running]
    
    return SystemStatus(
        status="running" if engine.running else "stopped",
        uptime=psutil.boot_time(),
        cpu_percent=psutil.cpu_percent(),
        memory_percent=psutil.virtual_memory().percent,
        plugin_count=len(plugins),
        active_plugin_count=len(active_plugins)
    )

@router.get("/settings", response_model=SystemSettings)
async def get_system_settings(current_user: User = Depends(get_current_admin_user)):
    """获取系统设置"""
    return SystemSettings(settings=settings.dict())

@router.put("/settings", response_model=SystemSettings)
async def update_system_settings(
    settings_data: SystemSettings,
    current_user: User = Depends(get_current_admin_user)
):
    """更新系统设置"""
    settings_manager.update_config(settings_data.settings)
    return SystemSettings(settings=settings.dict())

@router.post("/restart")
async def restart_system(current_user: User = Depends(get_current_admin_user)):
    """重启系统"""
    engine = get_engine()
    
    # 停止引擎
    engine.stop()
    
    # 重新启动引擎
    engine.start()
    
    return {"detail": "System restarted"}

@router.get("/logs", response_model=List[Dict[str, Any]])
async def get_system_logs(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """获取系统日志"""
    # 这里可以实现从日志文件读取或数据库读取
    # 简单示例，返回空列表
    return []

@router.post("/backup", response_model=Dict[str, Any])
async def create_backup(current_user: User = Depends(get_current_admin_user)):
    """创建系统备份"""
    # 这里可以实现备份功能
    # 简单示例，返回成功信息
    return {"detail": "Backup created", "backup_id": "backup_20220101_120000"}

@router.get("/backups", response_model=List[Dict[str, Any]])
async def get_backups(current_user: User = Depends(get_current_admin_user)):
    """获取所有备份"""
    # 这里可以实现获取备份列表功能
    # 简单示例，返回空列表
    return []

@router.post("/restore/{backup_id}")
async def restore_backup(
    backup_id: str,
    current_user: User = Depends(get_current_admin_user)
):
    """从备份恢复系统"""
    # 这里可以实现从备份恢复功能
    # 简单示例，返回成功信息
    return {"detail": f"System restored from backup {backup_id}"} 
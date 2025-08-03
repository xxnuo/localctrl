"""
插件API模块 - 提供插件相关的API接口
"""
import logging
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..models.database import get_db, DatabaseManager, Plugin as DbPlugin
from ..core.engine import get_engine
from .auth import get_current_active_user, get_current_admin_user, User

# 配置日志
logger = logging.getLogger(__name__)

# 创建路由
router = APIRouter()

# 模型
class PluginInfo(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    version: str
    running: bool
    status: str

class PluginAction(BaseModel):
    action: str
    params: Dict[str, Any] = {}

class PluginConfig(BaseModel):
    config: Dict[str, Any]

class PluginResponse(BaseModel):
    success: bool
    message: Optional[str] = None
    data: Optional[Dict[str, Any]] = None

@router.get("/", response_model=List[PluginInfo])
async def get_plugins(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """获取所有插件信息"""
    engine = get_engine()
    plugins = engine.get_plugin_status()
    
    return [
        PluginInfo(
            id=plugin_id,
            name=info["name"],
            description=info["description"],
            version=info["version"],
            running=info["running"],
            status=info["status"]
        )
        for plugin_id, info in plugins.items()
    ]

@router.get("/available", response_model=List[str])
async def get_available_plugins(
    current_user: User = Depends(get_current_active_user)
):
    """获取所有可用的插件"""
    engine = get_engine()
    return engine.discover_plugins()

@router.get("/{plugin_id}", response_model=PluginInfo)
async def get_plugin(
    plugin_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """获取指定插件信息"""
    engine = get_engine()
    plugin_info = engine.get_plugin_status(plugin_id)
    
    if "error" in plugin_info:
        raise HTTPException(status_code=404, detail=plugin_info["error"])
        
    return PluginInfo(
        id=plugin_id,
        name=plugin_info["name"],
        description=plugin_info["description"],
        version=plugin_info["version"],
        running=plugin_info["running"],
        status=plugin_info["status"]
    )

@router.post("/load/{plugin_name}", response_model=PluginResponse)
async def load_plugin(
    plugin_name: str,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """加载插件"""
    engine = get_engine()
    success = engine.load_plugin(plugin_name)
    
    if not success:
        return PluginResponse(success=False, message=f"Failed to load plugin {plugin_name}")
        
    # 获取插件实例
    plugin_id = None
    for pid, plugin in engine.plugins.items():
        if plugin.name.lower() == plugin_name.lower():
            plugin_id = pid
            break
            
    if not plugin_id:
        return PluginResponse(success=False, message=f"Plugin loaded but ID not found")
        
    # 保存到数据库
    try:
        plugin = engine.plugins[plugin_id]
        db_plugin = DatabaseManager.get_plugin(db, plugin_id)
        
        if not db_plugin:
            DatabaseManager.create_plugin(db, {
                "id": plugin_id,
                "name": plugin.name,
                "description": plugin.description,
                "version": plugin.version,
                "enabled": True,
                "config": plugin.config
            })
        else:
            DatabaseManager.update_plugin(db, plugin_id, {
                "enabled": True
            })
            
    except Exception as e:
        logger.error(f"Error saving plugin to database: {e}")
        
    return PluginResponse(
        success=True, 
        message=f"Plugin {plugin_name} loaded successfully",
        data={"plugin_id": plugin_id}
    )

@router.post("/unload/{plugin_id}", response_model=PluginResponse)
async def unload_plugin(
    plugin_id: str,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """卸载插件"""
    engine = get_engine()
    success = engine.unload_plugin(plugin_id)
    
    if not success:
        return PluginResponse(success=False, message=f"Failed to unload plugin {plugin_id}")
        
    # 更新数据库
    try:
        db_plugin = DatabaseManager.get_plugin(db, plugin_id)
        if db_plugin:
            DatabaseManager.update_plugin(db, plugin_id, {
                "enabled": False
            })
    except Exception as e:
        logger.error(f"Error updating plugin in database: {e}")
        
    return PluginResponse(
        success=True, 
        message=f"Plugin {plugin_id} unloaded successfully"
    )

@router.post("/{plugin_id}/action", response_model=PluginResponse)
async def execute_plugin_action(
    plugin_id: str,
    action_data: PluginAction,
    current_user: User = Depends(get_current_active_user)
):
    """执行插件操作"""
    engine = get_engine()
    result = engine.execute_plugin_action(plugin_id, action_data.action, action_data.params)
    
    if "error" in result:
        return PluginResponse(success=False, message=result["error"])
        
    return PluginResponse(
        success=result.get("success", True),
        data=result.get("result", {})
    )

@router.get("/{plugin_id}/config", response_model=PluginConfig)
async def get_plugin_config(
    plugin_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """获取插件配置"""
    engine = get_engine()
    
    if plugin_id not in engine.plugins:
        raise HTTPException(status_code=404, detail=f"Plugin {plugin_id} not found")
        
    plugin = engine.plugins[plugin_id]
    return PluginConfig(config=plugin.config)

@router.put("/{plugin_id}/config", response_model=PluginResponse)
async def update_plugin_config(
    plugin_id: str,
    config_data: PluginConfig,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """更新插件配置"""
    engine = get_engine()
    
    if plugin_id not in engine.plugins:
        raise HTTPException(status_code=404, detail=f"Plugin {plugin_id} not found")
        
    plugin = engine.plugins[plugin_id]
    plugin.update_config(config_data.config)
    
    # 更新数据库
    try:
        db_plugin = DatabaseManager.get_plugin(db, plugin_id)
        if db_plugin:
            DatabaseManager.update_plugin(db, plugin_id, {
                "config": config_data.config
            })
    except Exception as e:
        logger.error(f"Error updating plugin config in database: {e}")
        
    return PluginResponse(
        success=True,
        message=f"Plugin {plugin_id} config updated"
    )

@router.get("/{plugin_id}/logs", response_model=List[Dict[str, Any]])
async def get_plugin_logs(
    plugin_id: str,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """获取插件日志"""
    # 检查插件是否存在
    engine = get_engine()
    if plugin_id not in engine.plugins:
        raise HTTPException(status_code=404, detail=f"Plugin {plugin_id} not found")
        
    # 从数据库获取日志
    logs = DatabaseManager.get_plugin_logs(db, plugin_id, skip, limit)
    
    return [
        {
            "id": log.id,
            "level": log.level,
            "message": log.message,
            "timestamp": log.timestamp
        }
        for log in logs
    ]

@router.get("/{plugin_id}/ui", response_model=List[Dict[str, Any]])
async def get_plugin_ui_components(
    plugin_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """获取插件UI组件"""
    engine = get_engine()
    
    if plugin_id not in engine.plugins:
        raise HTTPException(status_code=404, detail=f"Plugin {plugin_id} not found")
        
    plugin = engine.plugins[plugin_id]
    return plugin.ui_components 
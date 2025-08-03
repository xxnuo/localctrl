"""
FastAPI 应用 - 提供 HTTP API 接口
"""
import logging
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional

from ..config.settings import settings
from ..models.database import get_db, init_db
from ..core.engine import get_engine
from . import auth, plugins, users, system

# 配置日志
logging.basicConfig(level=getattr(logging, settings.logging.level))
logger = logging.getLogger(__name__)

# 创建 FastAPI 应用
app = FastAPI(
    title="LocalCtrl API",
    description="LocalCtrl 远程控制服务 API",
    version="0.1.0"
)

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.server.allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 包含路由
app.include_router(auth.router, prefix="/api/auth", tags=["认证"])
app.include_router(plugins.router, prefix="/api/plugins", tags=["插件"])
app.include_router(users.router, prefix="/api/users", tags=["用户"])
app.include_router(system.router, prefix="/api/system", tags=["系统"])

@app.on_event("startup")
async def startup_event():
    """应用启动时执行"""
    logger.info("Starting LocalCtrl API...")
    
    # 初始化数据库
    init_db()
    
    # 启动引擎
    engine = get_engine()
    engine.start()
    
    logger.info("LocalCtrl API started")

@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭时执行"""
    logger.info("Shutting down LocalCtrl API...")
    
    # 停止引擎
    engine = get_engine()
    engine.stop()
    
    logger.info("LocalCtrl API shutdown complete")

@app.get("/api/health")
async def health_check():
    """健康检查接口"""
    return {"status": "ok", "version": "0.1.0"}

def start_api_server():
    """启动 API 服务器"""
    import uvicorn
    
    uvicorn.run(
        "localctrl.api.app:app",
        host=settings.server.host,
        port=settings.server.port,
        reload=settings.server.debug
    ) 
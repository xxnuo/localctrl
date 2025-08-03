"""
用户API模块 - 提供用户管理相关的API接口
"""
import logging
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session
from werkzeug.security import generate_password_hash

from ..models.database import get_db, User as DbUser
from .auth import get_current_active_user, get_current_admin_user, User, UserResponse

# 配置日志
logger = logging.getLogger(__name__)

# 创建路由
router = APIRouter()

# 模型
class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    password: Optional[str] = None
    is_active: Optional[bool] = None

class AdminUserUpdate(UserUpdate):
    is_admin: Optional[bool] = None

@router.get("/me", response_model=UserResponse)
async def read_users_me(current_user: User = Depends(get_current_active_user)):
    """获取当前用户信息"""
    return current_user

@router.put("/me", response_model=UserResponse)
async def update_user_me(
    user_data: UserUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """更新当前用户信息"""
    # 获取用户
    db_user = db.query(DbUser).filter(DbUser.id == current_user.id).first()
    
    # 更新邮箱
    if user_data.email is not None:
        # 检查邮箱是否已被使用
        existing_user = db.query(DbUser).filter(DbUser.email == user_data.email, DbUser.id != current_user.id).first()
        if existing_user:
            raise HTTPException(status_code=400, detail="Email already registered")
            
        db_user.email = user_data.email
    
    # 更新密码
    if user_data.password is not None:
        db_user.password_hash = generate_password_hash(user_data.password)
    
    db.commit()
    db.refresh(db_user)
    
    return db_user

@router.get("/", response_model=List[UserResponse])
async def read_users(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """获取所有用户（仅管理员）"""
    users = db.query(DbUser).offset(skip).limit(limit).all()
    return users

@router.get("/{user_id}", response_model=UserResponse)
async def read_user(
    user_id: int,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """获取指定用户信息（仅管理员）"""
    db_user = db.query(DbUser).filter(DbUser.id == user_id).first()
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user

@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    user_data: AdminUserUpdate,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """更新用户信息（仅管理员）"""
    db_user = db.query(DbUser).filter(DbUser.id == user_id).first()
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    
    # 更新邮箱
    if user_data.email is not None:
        # 检查邮箱是否已被使用
        existing_user = db.query(DbUser).filter(DbUser.email == user_data.email, DbUser.id != user_id).first()
        if existing_user:
            raise HTTPException(status_code=400, detail="Email already registered")
            
        db_user.email = user_data.email
    
    # 更新密码
    if user_data.password is not None:
        db_user.password_hash = generate_password_hash(user_data.password)
    
    # 更新激活状态
    if user_data.is_active is not None:
        db_user.is_active = user_data.is_active
    
    # 更新管理员状态
    if user_data.is_admin is not None:
        # 确保至少有一个管理员
        if not user_data.is_admin and db_user.is_admin:
            admin_count = db.query(DbUser).filter(DbUser.is_admin == True).count()
            if admin_count <= 1:
                raise HTTPException(status_code=400, detail="Cannot remove the last admin")
                
        db_user.is_admin = user_data.is_admin
    
    db.commit()
    db.refresh(db_user)
    
    return db_user

@router.delete("/{user_id}")
async def delete_user(
    user_id: int,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """删除用户（仅管理员）"""
    # 不能删除自己
    if user_id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot delete yourself")
    
    db_user = db.query(DbUser).filter(DbUser.id == user_id).first()
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    
    # 如果是管理员，确保至少有一个管理员
    if db_user.is_admin:
        admin_count = db.query(DbUser).filter(DbUser.is_admin == True).count()
        if admin_count <= 1:
            raise HTTPException(status_code=400, detail="Cannot delete the last admin")
    
    db.delete(db_user)
    db.commit()
    
    return {"detail": "User deleted"} 
"""
认证模块 - 处理用户认证和授权
"""
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from pydantic import BaseModel
from sqlalchemy.orm import Session
from werkzeug.security import check_password_hash, generate_password_hash
import secrets
import string

from ..models.database import get_db, User, ApiKey
from ..config.settings import settings

# 配置日志
logger = logging.getLogger(__name__)

# 创建路由
router = APIRouter()

# OAuth2 密码流
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/token")

# 密钥，在生产环境中应该从环境变量或配置文件中读取
SECRET_KEY = settings.server.secret_key or "".join(secrets.choice(string.ascii_letters + string.digits) for _ in range(32))
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# 模型
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

class UserCreate(BaseModel):
    username: str
    password: str
    email: Optional[str] = None

class UserResponse(BaseModel):
    id: int
    username: str
    email: Optional[str]
    is_active: bool
    is_admin: bool

class ApiKeyCreate(BaseModel):
    name: str
    expires_days: Optional[int] = None

class ApiKeyResponse(BaseModel):
    id: int
    key: str
    name: str
    is_active: bool
    expires_at: Optional[datetime]

def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None):
    """创建访问令牌"""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def get_user(db: Session, username: str) -> Optional[User]:
    """通过用户名获取用户"""
    return db.query(User).filter(User.username == username).first()

def authenticate_user(db: Session, username: str, password: str) -> Optional[User]:
    """验证用户"""
    user = get_user(db, username)
    if not user:
        return None
    if not check_password_hash(user.password_hash, password):
        return None
    return user

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    """获取当前用户"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception
        
    user = get_user(db, username=token_data.username)
    if user is None:
        raise credentials_exception
        
    return user

def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """获取当前活跃用户"""
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

def get_current_admin_user(current_user: User = Depends(get_current_active_user)) -> User:
    """获取当前管理员用户"""
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    return current_user

def verify_api_key(api_key: str, db: Session) -> Optional[User]:
    """验证API密钥"""
    db_api_key = db.query(ApiKey).filter(ApiKey.key == api_key, ApiKey.is_active == True).first()
    
    if not db_api_key:
        return None
        
    # 检查是否过期
    if db_api_key.expires_at and db_api_key.expires_at < datetime.utcnow():
        return None
        
    # 获取关联的用户
    user = db.query(User).filter(User.id == db_api_key.user_id, User.is_active == True).first()
    return user

@router.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """登录获取访问令牌"""
    user = authenticate_user(db, form_data.username, form_data.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/register", response_model=UserResponse)
async def register_user(user_data: UserCreate, db: Session = Depends(get_db)):
    """注册新用户"""
    # 检查用户名是否已存在
    db_user = db.query(User).filter(User.username == user_data.username).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
        
    # 检查邮箱是否已存在
    if user_data.email:
        db_email = db.query(User).filter(User.email == user_data.email).first()
        if db_email:
            raise HTTPException(status_code=400, detail="Email already registered")
    
    # 创建新用户
    hashed_password = generate_password_hash(user_data.password)
    db_user = User(
        username=user_data.username,
        password_hash=hashed_password,
        email=user_data.email
    )
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    return db_user

@router.post("/api-keys", response_model=ApiKeyResponse)
async def create_api_key(
    api_key_data: ApiKeyCreate, 
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """创建API密钥"""
    # 生成随机密钥
    api_key_value = secrets.token_hex(32)
    
    # 计算过期时间
    expires_at = None
    if api_key_data.expires_days:
        expires_at = datetime.utcnow() + timedelta(days=api_key_data.expires_days)
    
    # 创建API密钥
    db_api_key = ApiKey(
        user_id=current_user.id,
        key=api_key_value,
        name=api_key_data.name,
        expires_at=expires_at
    )
    
    db.add(db_api_key)
    db.commit()
    db.refresh(db_api_key)
    
    return db_api_key

@router.get("/api-keys", response_model=list[ApiKeyResponse])
async def get_api_keys(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """获取当前用户的API密钥"""
    return db.query(ApiKey).filter(ApiKey.user_id == current_user.id).all()

@router.delete("/api-keys/{api_key_id}")
async def delete_api_key(
    api_key_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """删除API密钥"""
    db_api_key = db.query(ApiKey).filter(
        ApiKey.id == api_key_id,
        ApiKey.user_id == current_user.id
    ).first()
    
    if not db_api_key:
        raise HTTPException(status_code=404, detail="API key not found")
    
    db.delete(db_api_key)
    db.commit()
    
    return {"detail": "API key deleted"} 
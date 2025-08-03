from enum import Enum

from fastapi import Depends, status
from fastapi.exceptions import HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel

from localctrl.config import Config

oauth2_scheme = HTTPBearer(auto_error=False)


class Role(str, Enum):
    admin = "admin"
    user = "user"


class User(BaseModel):
    name: str
    role: Role
    token: str


async def get_user(
    credentials: HTTPAuthorizationCredentials = Depends(oauth2_scheme),
) -> User:
    if Config.token == "":
        return User(name="admin", role=Role.admin, token="")
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = credentials.credentials
    if token != Config.token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    pass  # TODO: 根据token查询数据库并返回用户对象
    return User(name="admin", role=Role.admin, token=token)

"""JWT 认证工具"""
import logging
from datetime import datetime, timedelta
from typing import Optional

import jwt
from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import get_db
from app.models.user import User

logger = logging.getLogger(__name__)
settings = get_settings()

SECRET_KEY = settings.jwt_secret
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_DAYS = 30

security_scheme = HTTPBearer(auto_error=False)


def create_access_token(user_id: int, openid: str) -> str:
    """生成 JWT access token"""
    expire = datetime.utcnow() + timedelta(days=ACCESS_TOKEN_EXPIRE_DAYS)
    payload = {
        "sub": str(user_id),
        "openid": openid,
        "exp": expire,
        "iat": datetime.utcnow(),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> Optional[dict]:
    """解码 JWT token，失败返回 None"""
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except jwt.ExpiredSignatureError:
        logger.warning("JWT token 已过期")
        return None
    except jwt.InvalidTokenError:
        logger.warning("JWT token 无效")
        return None


def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme),
    db: Session = Depends(get_db),
) -> User:
    """FastAPI 依赖：从请求头 Authorization Bearer 中提取当前用户

    若未提供 token 且配置 dev_mode=True，返回默认用户（用于 Web 前端开发调试）。
    """
    if settings.dev_mode and (credentials is None or not credentials.credentials):
        user = db.query(User).filter_by(id=1).first()
        if not user:
            user = User(id=1, openid="dev_user", nickname="开发用户")
            db.add(user)
            db.commit()
            db.refresh(user)
        return user

    if credentials is None or not credentials.credentials:
        raise HTTPException(status_code=401, detail="未提供认证令牌，请先登录")

    payload = decode_token(credentials.credentials)
    if payload is None:
        raise HTTPException(status_code=401, detail="认证令牌无效或已过期，请重新登录")

    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(status_code=401, detail="认证令牌格式错误")

    user = db.query(User).get(int(user_id))
    if user is None:
        raise HTTPException(status_code=401, detail="用户不存在")

    return user

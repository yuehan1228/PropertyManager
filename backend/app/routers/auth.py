"""用户认证路由 —— 微信小程序登录 / 开发模式登录"""
import logging
from datetime import datetime

import httpx
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import get_db
from app.models.user import User
from app.utils.auth import create_access_token, get_current_user

logger = logging.getLogger(__name__)
settings = get_settings()

router = APIRouter(prefix="/api/auth", tags=["auth"])


class LoginRequest(BaseModel):
    code: str = Field(..., description="wx.login() 返回的临时登录凭证")


class DevLoginRequest(BaseModel):
    openid: str = Field(..., description="开发模式下的模拟 openid")


class LoginResponse(BaseModel):
    token: str
    user_id: int
    openid: str
    nickname: str | None = None
    is_new: bool = False


class UserInfoResponse(BaseModel):
    id: int
    openid: str
    nickname: str | None = None
    avatar_url: str | None = None
    created_at: str

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# 微信小程序登录
# ---------------------------------------------------------------------------
WECHAT_LOGIN_URL = "https://api.weixin.qq.com/sns/jscode2session"


@router.post("/login", response_model=LoginResponse)
async def wechat_login(body: LoginRequest, db: Session = Depends(get_db)):
    """微信小程序登录：用 wx.login() 的 code 换取 openid，返回 JWT"""
    if not settings.wechat_appid or not settings.wechat_secret:
        raise HTTPException(
            status_code=500,
            detail="服务器未配置微信 AppID/Secret，请联系管理员",
        )

    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                WECHAT_LOGIN_URL,
                params={
                    "appid": settings.wechat_appid,
                    "secret": settings.wechat_secret,
                    "js_code": body.code,
                    "grant_type": "authorization_code",
                },
                timeout=settings.fund_api_timeout,
            )
            resp.raise_for_status()
            data = resp.json()
    except Exception as e:
        logger.exception("微信登录接口调用失败")
        raise HTTPException(status_code=502, detail=f"微信服务暂时不可用: {e}")

    if "errcode" in data and data["errcode"] != 0:
        logger.error(f"微信登录失败: {data}")
        raise HTTPException(status_code=400, detail=f"微信登录失败: {data.get('errmsg', '未知错误')}")

    openid = data.get("openid")
    unionid = data.get("unionid")
    if not openid:
        raise HTTPException(status_code=400, detail="无法获取 openid")

    return _login_or_register(db, openid, unionid)


@router.post("/dev-login", response_model=LoginResponse)
def dev_login(body: DevLoginRequest, db: Session = Depends(get_db)):
    """开发模式登录：直接使用 openid 登录，无需微信 code"""
    if not settings.dev_mode:
        raise HTTPException(status_code=403, detail="开发模式未开启")

    return _login_or_register(db, body.openid.strip())


@router.get("/me", response_model=UserInfoResponse)
def get_me(current_user: User = Depends(get_current_user)):
    """获取当前登录用户信息"""
    return current_user


# ---------------------------------------------------------------------------
# 内部工具
# ---------------------------------------------------------------------------

def _login_or_register(db: Session, openid: str, unionid: str | None = None) -> LoginResponse:
    """查找或创建用户，返回 JWT"""
    user = db.query(User).filter_by(openid=openid).first()
    is_new = False

    if user is None:
        user = User(openid=openid, unionid=unionid)
        db.add(user)
        db.flush()
        is_new = True

    user.last_login_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    db.commit()
    db.refresh(user)

    token = create_access_token(user.id, user.openid)
    logger.info(f"用户登录: openid={openid} id={user.id} 新用户={is_new}")

    return LoginResponse(
        token=token,
        user_id=user.id,
        openid=user.openid,
        nickname=user.nickname,
        is_new=is_new,
    )

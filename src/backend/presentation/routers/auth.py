import os
import secrets
from datetime import datetime, timedelta, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from pydantic import BaseModel

from ...bll.services.drivers_service import DriversService
from ...bll.services.users_service import UsersService
from ..dependencies import get_drivers_service, get_users_service

router = APIRouter(prefix="/auth", tags=["auth"])

SECRET_KEY = os.getenv("JWT_SECRET_KEY") or secrets.token_urlsafe(32)
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRES = timedelta(minutes=30)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")


class TokenResponse(BaseModel):
    access_token: str
    token_type: str


class CurrentUser(BaseModel):
    user_id: int
    username: str
    role: str


def create_access_token(username: str, user_id: int, role: str):
    payload = {
        "sub": username,
        "user_id": user_id,
        "role": role,
        "exp": datetime.now(timezone.utc) + ACCESS_TOKEN_EXPIRES,
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        raise HTTPException(
            status_code=401, detail="Сесія завершилася. Увійдіть знову."
        )

    username, user_id, role = (
        payload.get("sub"),
        payload.get("user_id"),
        payload.get("role"),
    )
    if not username or not user_id or not role:
        raise HTTPException(
            status_code=401, detail="Сесія завершилася. Увійдіть знову."
        )
    return CurrentUser(user_id=user_id, username=username, role=role)


async def require_admin(current_user: CurrentUser = Depends(get_current_user)):
    if current_user.role != "ADMIN":
        raise HTTPException(
            status_code=403, detail="У вас немає прав на цю дію."
        )
    return current_user


async def get_current_driver_id(
    current_user: CurrentUser = Depends(get_current_user),
    drivers_service: DriversService = Depends(get_drivers_service),
):
    """None for an admin (sees everything), the driver's id for a driver."""
    if current_user.role == "ADMIN":
        return None
    driver = await drivers_service.get_by_user_id(current_user.user_id)
    if driver.employment_status == "DISMISSED":
        raise HTTPException(
            status_code=403,
            detail="Ваш обліковий запис водія деактивовано. Зверніться до адміністратора.",
        )
    return driver.id


def ensure_visible(obj, visible):
    if obj.id not in {item.id for item in visible}:
        raise HTTPException(
            status_code=403, detail="У вас немає прав на цю дію."
        )


@router.post("/token", response_model=TokenResponse)
async def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    service: UsersService = Depends(get_users_service),
):
    user = await service.authenticate(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=401, detail="Неправильне ім'я користувача або пароль."
        )
    access_token = create_access_token(user.username, user.id, user.role)
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me", response_model=CurrentUser)
async def me(current_user: CurrentUser = Depends(get_current_user)):
    return current_user

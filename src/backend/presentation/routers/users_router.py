from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict

from ...bll.interfaces.users_interface import IUsersService
from ...bll.services.users_service import UserData
from ..dependencies import get_users_service
from .auth import ensure_visible, get_current_driver_id, require_admin

router = APIRouter(prefix="/users", tags=["users"])


class UserResponse(BaseModel):
    id: int
    username: str
    role: str
    model_config = ConfigDict(from_attributes=True)


@router.get("/", response_model=list[UserResponse])
async def get_all(
    driver_id: int | None = Depends(get_current_driver_id),
    service: IUsersService = Depends(get_users_service),
):
    if driver_id is None:
        return await service.get_all()
    return await service.get_by_driver(driver_id)


@router.get("/{id}", response_model=UserResponse)
async def get_by_id(
    id: int,
    driver_id: int | None = Depends(get_current_driver_id),
    service: IUsersService = Depends(get_users_service),
):
    obj = await service.get_by_id(id)
    if driver_id is not None:
        ensure_visible(obj, await service.get_by_driver(driver_id))
    return obj


@router.post(
    "/",
    response_model=UserResponse,
    status_code=201,
    dependencies=[Depends(require_admin)],
)
async def create(data: UserData, service: IUsersService = Depends(get_users_service)):
    return await service.create(data)


@router.put("/{id}", response_model=UserResponse, dependencies=[Depends(require_admin)])
async def update(
    id: int, data: UserData, service: IUsersService = Depends(get_users_service)
):
    return await service.update(id, data)


@router.delete(
    "/{id}", response_model=UserResponse, dependencies=[Depends(require_admin)]
)
async def delete(id: int, service: IUsersService = Depends(get_users_service)):
    return await service.delete(id)

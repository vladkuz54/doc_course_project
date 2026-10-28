from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict

from ...bll.services.users_service import UserData, UsersService
from ..dependencies import get_users_service

router = APIRouter(prefix="/users", tags=["users"])


class UserResponse(BaseModel):
    id: int
    username: str
    role: str
    model_config = ConfigDict(from_attributes=True)


@router.get("/", response_model=list[UserResponse])
async def get_all(service: UsersService = Depends(get_users_service)):
    return await service.get_all()


@router.get("/{id}", response_model=UserResponse)
async def get_by_id(id: int, service: UsersService = Depends(get_users_service)):
    return await service.get_by_id(id)


@router.post("/", response_model=UserResponse, status_code=201)
async def create(data: UserData, service: UsersService = Depends(get_users_service)):
    return await service.create(data)


@router.put("/{id}", response_model=UserResponse)
async def update(
    id: int, data: UserData, service: UsersService = Depends(get_users_service)
):
    return await service.update(id, data)


@router.delete("/{id}", response_model=UserResponse)
async def delete(id: int, service: UsersService = Depends(get_users_service)):
    return await service.delete(id)

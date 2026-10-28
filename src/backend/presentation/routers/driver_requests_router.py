from datetime import datetime

from fastapi import APIRouter, Depends
from pydantic import ConfigDict

from ...bll.services.driver_requests_service import (
    DriverRequestData,
    DriverRequestsService,
)
from ..dependencies import get_driver_requests_service

router = APIRouter(prefix="/driver-requests", tags=["driver-requests"])


class DriverRequestResponse(DriverRequestData):
    id: int
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


@router.get("/", response_model=list[DriverRequestResponse])
async def get_all(
    service: DriverRequestsService = Depends(get_driver_requests_service),
):
    return await service.get_all()


@router.get("/{id}", response_model=DriverRequestResponse)
async def get_by_id(
    id: int, service: DriverRequestsService = Depends(get_driver_requests_service)
):
    return await service.get_by_id(id)


@router.post("/", response_model=DriverRequestResponse, status_code=201)
async def create(
    data: DriverRequestData,
    service: DriverRequestsService = Depends(get_driver_requests_service),
):
    return await service.create(data)


@router.put("/{id}", response_model=DriverRequestResponse)
async def update(
    id: int,
    data: DriverRequestData,
    service: DriverRequestsService = Depends(get_driver_requests_service),
):
    return await service.update(id, data)


@router.delete("/{id}", response_model=DriverRequestResponse)
async def delete(
    id: int, service: DriverRequestsService = Depends(get_driver_requests_service)
):
    return await service.delete(id)

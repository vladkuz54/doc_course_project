from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import ConfigDict

from ...bll.services.driver_requests_service import (
    DriverRequestData,
    DriverRequestsService,
)
from ..dependencies import get_driver_requests_service
from .auth import ensure_visible, get_current_driver_id, require_admin

router = APIRouter(prefix="/driver-requests", tags=["driver-requests"])


class DriverRequestResponse(DriverRequestData):
    id: int
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


@router.get("/", response_model=list[DriverRequestResponse])
async def get_all(
    driver_id: int | None = Depends(get_current_driver_id),
    service: DriverRequestsService = Depends(get_driver_requests_service),
):
    if driver_id is None:
        return await service.get_all()
    return await service.get_by_driver(driver_id)


@router.get("/{id}", response_model=DriverRequestResponse)
async def get_by_id(
    id: int,
    driver_id: int | None = Depends(get_current_driver_id),
    service: DriverRequestsService = Depends(get_driver_requests_service),
):
    obj = await service.get_by_id(id)
    if driver_id is not None:
        ensure_visible(obj, await service.get_by_driver(driver_id))
    return obj


@router.post("/", response_model=DriverRequestResponse, status_code=201)
async def create(
    data: DriverRequestData,
    driver_id: int | None = Depends(get_current_driver_id),
    service: DriverRequestsService = Depends(get_driver_requests_service),
):
    if driver_id is not None:
        if data.driver_id != driver_id:
            raise HTTPException(
                status_code=403,
                detail="Drivers can only create requests for themselves",
            )
        if data.status != "PENDING":
            raise HTTPException(
                status_code=403,
                detail="Drivers can only create requests with PENDING status",
            )
    return await service.create(data)


@router.put(
    "/{id}", response_model=DriverRequestResponse, dependencies=[Depends(require_admin)]
)
async def update(
    id: int,
    data: DriverRequestData,
    service: DriverRequestsService = Depends(get_driver_requests_service),
):
    return await service.update(id, data)


@router.delete(
    "/{id}", response_model=DriverRequestResponse, dependencies=[Depends(require_admin)]
)
async def delete(
    id: int, service: DriverRequestsService = Depends(get_driver_requests_service)
):
    return await service.delete(id)

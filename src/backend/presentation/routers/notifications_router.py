from datetime import datetime

from fastapi import APIRouter, Depends
from pydantic import ConfigDict

from ...bll.observer import DomainEvent
from ...bll.services.deadline_monitor import DeadlineMonitor
from ...bll.services.notifications_service import (
    NotificationData,
    NotificationsService,
    NotificationUpdateData,
)
from ..dependencies import get_deadline_monitor, get_notifications_service
from .auth import ensure_visible, get_current_driver_id, require_admin

router = APIRouter(prefix="/notifications", tags=["notifications"])


class NotificationResponse(NotificationData):
    id: int
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


@router.get("/", response_model=list[NotificationResponse])
async def get_all(
    driver_id: int | None = Depends(get_current_driver_id),
    service: NotificationsService = Depends(get_notifications_service),
):
    if driver_id is None:
        return await service.get_for_admins()
    return await service.get_by_driver(driver_id)


@router.get(
    "/check-deadlines",
    response_model=list[DomainEvent],
    dependencies=[Depends(require_admin)],
)
async def check_deadlines(monitor: DeadlineMonitor = Depends(get_deadline_monitor)):
    return [
        *await monitor.check_maintenance_due(),
        *await monitor.check_insurance_expiring(),
        *await monitor.check_license_expiring(),
        *await monitor.check_medical_check_due(),
    ]


@router.get("/{id}", response_model=NotificationResponse)
async def get_by_id(
    id: int,
    driver_id: int | None = Depends(get_current_driver_id),
    service: NotificationsService = Depends(get_notifications_service),
):
    obj = await service.get_by_id(id)
    if driver_id is not None:
        ensure_visible(obj, await service.get_by_driver(driver_id))
    return obj


@router.post(
    "/",
    response_model=NotificationResponse,
    status_code=201,
    dependencies=[Depends(require_admin)],
)
async def create(
    data: NotificationData,
    service: NotificationsService = Depends(get_notifications_service),
):
    return await service.create(data)


@router.patch("/read-all", response_model=list[NotificationResponse])
async def mark_all_as_read(
    driver_id: int | None = Depends(get_current_driver_id),
    service: NotificationsService = Depends(get_notifications_service),
):
    return await service.mark_all_as_read(driver_id)


@router.patch("/{id}/read", response_model=NotificationResponse)
async def mark_as_read(
    id: int,
    driver_id: int | None = Depends(get_current_driver_id),
    service: NotificationsService = Depends(get_notifications_service),
):
    obj = await service.get_by_id(id)
    if driver_id is not None:
        ensure_visible(obj, await service.get_by_driver(driver_id))
    return await service.mark_as_read(id)


@router.put(
    "/{id}", response_model=NotificationResponse, dependencies=[Depends(require_admin)]
)
async def update(
    id: int,
    data: NotificationUpdateData,
    service: NotificationsService = Depends(get_notifications_service),
):
    return await service.update(id, data)


@router.delete(
    "/{id}", response_model=NotificationResponse, dependencies=[Depends(require_admin)]
)
async def delete(
    id: int, service: NotificationsService = Depends(get_notifications_service)
):
    return await service.delete(id)

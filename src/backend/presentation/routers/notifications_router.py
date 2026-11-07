from datetime import datetime, timedelta

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from pydantic import ConfigDict
from sqlalchemy.ext.asyncio import AsyncSession

from ...bll.live_notifications import live_notifications
from ...bll.observer import DomainEvent
from ...bll.services.deadline_monitor import DeadlineMonitor
from ...bll.services.notifications_service import (
    NotificationData,
    NotificationsService,
)
from ..dependencies import (
    get_db_session,
    get_deadline_monitor,
    get_notifications_service,
)
from .auth import (
    CurrentUser,
    ensure_visible,
    get_current_driver_id,
    get_current_user,
    require_admin,
)

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
async def check_deadlines(
    monitor: DeadlineMonitor = Depends(get_deadline_monitor),
    notifications: NotificationsService = Depends(get_notifications_service),
):
    notifications.quiet_period = timedelta(0)
    return [
        *await monitor.check_maintenance_due(),
        *await monitor.check_repair_cost_missing(),
        *await monitor.check_insurance_expiring(),
        *await monitor.check_license_expiring(),
        *await monitor.check_medical_check_due(),
    ]


@router.get("/stream")
async def stream(
    current_user: CurrentUser = Depends(get_current_user),
    driver_id: int | None = Depends(get_current_driver_id),
    session: AsyncSession = Depends(get_db_session),
):
    await session.close()
    return StreamingResponse(
        live_notifications.stream(current_user.user_id, driver_id is None),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache"},
    )


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


@router.delete(
    "/{id}", response_model=NotificationResponse, dependencies=[Depends(require_admin)]
)
async def delete(
    id: int, service: NotificationsService = Depends(get_notifications_service)
):
    return await service.delete(id)

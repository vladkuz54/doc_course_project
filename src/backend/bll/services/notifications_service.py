from typing import Literal

from pydantic import BaseModel

from ...dal.interfaces.driver_requests_interfaces import IDriverRequestsRepository
from ...dal.interfaces.drivers_interfaces import IDriversRepository
from ...dal.interfaces.notifications_interfaces import INotificationsRepository
from ...dal.interfaces.routes_interfaces import IRoutesRepository
from ...dal.interfaces.vehicles_interfaces import IVehiclesRepository
from ..exceptions import EntityNotFoundError
from ..interfaces.notifications_interface import INotificationsService
from ..observer import NotificationType, Observer
from .base_service import BaseService


class NotificationData(BaseModel):
    recipient_id: int | None = None
    type: NotificationType
    text: str
    related_entity: Literal["drivers", "vehicles", "routes", "driver_requests"]
    related_id: int
    is_read: bool = False


class NotificationUpdateData(NotificationData):
    recipient_id: int | None
    is_read: bool


class NotificationsService(INotificationsService, BaseService, Observer):
    entity_name = "Сповіщення"

    def __init__(
        self,
        repository: INotificationsRepository,
        drivers_repository: IDriversRepository,
        vehicles_repository: IVehiclesRepository,
        routes_repository: IRoutesRepository,
        driver_requests_repository: IDriverRequestsRepository,
    ):
        super().__init__(repository)
        self.related_repositories = {
            "drivers": drivers_repository,
            "vehicles": vehicles_repository,
            "routes": routes_repository,
            "driver_requests": driver_requests_repository,
        }

    async def _validate(self, data, id=None):
        repository = self.related_repositories[data.related_entity]
        if not await repository.get_by_id(data.related_id):
            label = {
                "drivers": "водія",
                "vehicles": "транспорт",
                "routes": "маршрут",
                "driver_requests": "запит",
            }[data.related_entity]
            raise EntityNotFoundError(
                f"Не вдалося знайти {label}, до якого належить сповіщення."
            )

    async def get_by_driver(self, driver_id):
        return await self.repository.get_by_driver(driver_id)

    async def get_for_admins(self):
        return await self.repository.get_for_admins()

    async def mark_as_read(self, id):
        obj = await self.get_by_id(id)
        obj.is_read = True
        return await self.repository.update(obj)

    async def mark_all_as_read(self, driver_id=None):
        rows = (
            await self.get_for_admins()
            if driver_id is None
            else await self.get_by_driver(driver_id)
        )
        unread = [row for row in rows if not row.is_read]
        for row in unread:
            row.is_read = True
        if unread:
            # They share a session, so one commit saves every row
            await self.repository.update(unread[0])
        return rows

    async def on_event(self, event):
        for n in await self.repository.get_unread():
            if (
                n.type == event.type
                and n.related_entity == event.related_entity
                and n.related_id == event.related_id
                and n.recipient_id == event.recipient_id
                and n.text == event.text
            ):
                return
        await self.repository.create(
            self.repository.model(
                type=event.type,
                related_entity=event.related_entity,
                related_id=event.related_id,
                recipient_id=event.recipient_id,
                text=event.text,
            )
        )

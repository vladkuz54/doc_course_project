from typing import Literal

from pydantic import BaseModel

from ...dal.interfaces.driver_requests_interfaces import IDriverRequestsRepository
from ...dal.interfaces.drivers_interfaces import IDriversRepository
from ...dal.interfaces.notifications_interfaces import INotificationsRepository
from ...dal.interfaces.routes_interfaces import IRoutesRepository
from ...dal.interfaces.vehicles_interfaces import IVehiclesRepository
from ..exceptions import EntityNotFoundError
from ..interfaces.notifications_interface import INotificationsService
from .base_service import BaseService


class NotificationData(BaseModel):
    recipient_id: int | None = None
    type: Literal[
        "LICENSE_UPDATE_REQUEST",
        "MEDICAL_CHECK_REQUEST",
        "MAINTENANCE_SCHEDULED",
        "MAINTENANCE_DUE",
        "INSURANCE_EXPIRING",
        "LICENSE_EXPIRING",
        "MEDICAL_CHECK_DUE",
        "ROUTE_ASSIGNED",
    ]
    text: str
    related_entity: Literal["drivers", "vehicles", "routes", "driver_requests"]
    related_id: int
    is_read: bool = False


class NotificationsService(INotificationsService, BaseService):
    entity_name = "Notification"

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
            raise EntityNotFoundError(
                f"{data.related_entity} record with ID {data.related_id} not found"
            )

    async def get_by_driver(self, driver_id):
        return await self.repository.get_by_driver(driver_id)

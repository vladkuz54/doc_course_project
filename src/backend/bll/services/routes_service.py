from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel

from ...dal.interfaces.drivers_interfaces import IDriversRepository
from ...dal.interfaces.routes_interfaces import IRoutesRepository
from ...dal.interfaces.vehicles_interfaces import IVehiclesRepository
from ..exceptions import EntityNotFoundError
from ..interfaces.routes_interface import IRoutesService
from .entity_management import EntityManagement


class RouteData(BaseModel):
    driver_id: int | None = None
    vehicle_id: int | None = None
    distance: float
    departure_at: datetime
    started_at: datetime | None = None
    completed_at: datetime | None = None
    status: Literal["PLANNED", "IN_PROGRESS", "COMPLETED", "CANCELLED"] = "PLANNED"


class RouteStatusData(BaseModel):
    status: Literal["PLANNED", "IN_PROGRESS", "COMPLETED", "CANCELLED"]


class RoutesService(IRoutesService, EntityManagement):
    entity_name = "Route"

    def __init__(
        self,
        repository: IRoutesRepository,
        drivers_repository: IDriversRepository,
        vehicles_repository: IVehiclesRepository,
    ):
        super().__init__(repository)
        self.drivers_repository = drivers_repository
        self.vehicles_repository = vehicles_repository

    async def _validate(self, data, id=None):
        if data.driver_id is not None and not await self.drivers_repository.get_by_id(
            data.driver_id
        ):
            raise EntityNotFoundError(f"Driver with ID {data.driver_id} not found")
        if (
            data.vehicle_id is not None
            and not await self.vehicles_repository.get_by_id(data.vehicle_id)
        ):
            raise EntityNotFoundError(f"Vehicle with ID {data.vehicle_id} not found")

    async def get_by_driver(self, driver_id):
        return await self.repository.get_by_driver(driver_id)

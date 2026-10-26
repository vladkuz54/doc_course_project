from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel

from ...dal.interfaces.drivers_interfaces import IDriversRepository
from ...dal.interfaces.routes_interfaces import IRoutesRepository
from ...dal.interfaces.vehicles_interfaces import IVehiclesRepository
from ..interfaces.routes_interface import IRoutesService
from .base_service import BaseService


class RouteData(BaseModel):
    driver_id: int | None = None
    vehicle_id: int | None = None
    distance: float
    departure_at: datetime
    started_at: datetime | None = None
    completed_at: datetime | None = None
    status: Literal["PLANNED", "IN_PROGRESS", "COMPLETED", "CANCELLED"] = "PLANNED"


class RoutesService(IRoutesService, BaseService):
    entity_name = "Route"

    def __init__(
        self,
        repository: IRoutesRepository,
        drivers_repository: IDriversRepository,
        vehicles_repository: IVehiclesRepository,
    ):
        super().__init__(
            repository,
            {
                "driver_id": (drivers_repository, "Driver"),
                "vehicle_id": (vehicles_repository, "Vehicle"),
            },
        )

from datetime import date
from typing import Literal

from pydantic import BaseModel, Field, field_validator

from ...dal.db_models import ACTIVE_ROUTE_STATUSES, LICENSE_CATEGORIES, MIN_VEHICLE_YEAR
from ...dal.interfaces.routes_interfaces import IRoutesRepository
from ...dal.interfaces.vehicles_interfaces import IVehiclesRepository
from ..exceptions import EntityAlreadyExistsError
from ..interfaces.vehicles_interface import IVehiclesService
from .entity_management import EntityManagement


class VehicleData(BaseModel):
    make: str
    year: int = Field(ge=MIN_VEHICLE_YEAR)
    vin: str = Field(pattern=r"^[A-HJ-NPR-Z0-9]{17}$")
    required_license_category: Literal[LICENSE_CATEGORIES]
    technical_state: str
    status: Literal["ACTIVE", "DECOMMISSIONED"] = "ACTIVE"

    @field_validator("year")
    @classmethod
    def year_not_in_future(cls, value):
        if value > date.today().year + 1:
            raise ValueError(f"year must be at most {date.today().year + 1}")
        return value


class VehicleStatusData(BaseModel):
    status: Literal["ACTIVE", "DECOMMISSIONED"]


class VehiclesService(IVehiclesService, EntityManagement):
    entity_name = "Vehicle"

    def __init__(
        self, repository: IVehiclesRepository, routes_repository: IRoutesRepository
    ):
        super().__init__(repository)
        self.routes_repository = routes_repository

    async def _validate(self, data, id=None):
        existing = await self.repository.get_by_vin(data.vin)
        if existing and existing.id != id:
            raise EntityAlreadyExistsError(
                f"Vehicle with VIN {data.vin} already exists"
            )

    async def _can_change_status(self, entity, status):
        if status != "DECOMMISSIONED":
            return True
        routes = await self.routes_repository.get_by_vehicle(entity.id)
        return not any(r.status in ACTIVE_ROUTE_STATUSES for r in routes)

    async def get_by_driver(self, driver_id):
        return await self.repository.get_by_driver(driver_id)

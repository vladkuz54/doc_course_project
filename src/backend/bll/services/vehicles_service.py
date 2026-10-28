from datetime import date
from typing import Literal

from pydantic import BaseModel, Field, field_validator

from ...dal.db_models import LICENSE_CATEGORIES, MIN_VEHICLE_YEAR
from ...dal.interfaces.vehicles_interfaces import IVehiclesRepository
from ..exceptions import EntityAlreadyExistsError
from ..interfaces.vehicles_interface import IVehiclesService
from .base_service import BaseService


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


class VehiclesService(IVehiclesService, BaseService):
    entity_name = "Vehicle"

    def __init__(self, repository: IVehiclesRepository):
        super().__init__(repository)

    async def _validate(self, data, id=None):
        existing = await self.repository.get_by_vin(data.vin)
        if existing and existing.id != id:
            raise EntityAlreadyExistsError(
                f"Vehicle with VIN {data.vin} already exists"
            )

    async def get_by_driver(self, driver_id):
        return await self.repository.get_by_driver(driver_id)

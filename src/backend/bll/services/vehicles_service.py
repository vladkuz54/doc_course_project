from typing import Literal

from pydantic import BaseModel

from ...dal.interfaces.vehicles_interfaces import IVehiclesRepository
from ..exceptions import EntityAlreadyExistsError
from ..interfaces.vehicles_interface import IVehiclesService
from .base_service import BaseService


class VehicleData(BaseModel):
    make: str
    year: int
    vin: str
    required_license_category: str
    technical_state: str
    status: Literal["ACTIVE", "DECOMMISSIONED"] = "ACTIVE"


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

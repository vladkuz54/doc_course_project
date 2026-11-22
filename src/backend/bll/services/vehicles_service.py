from datetime import date as Date
from typing import Annotated, Literal

from pydantic import BaseModel, Field, StringConstraints, field_validator

from ...dal.db_models import LICENSE_CATEGORIES, MIN_VEHICLE_YEAR
from ...dal.interfaces.routes_interfaces import IRoutesRepository
from ...dal.interfaces.vehicles_interfaces import IVehiclesRepository
from ..exceptions import BusinessRuleError, EntityAlreadyExistsError
from ..interfaces.vehicles_interface import IVehiclesService
from .entity_management_service import EntityManagement


class VehicleData(BaseModel):
    make: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]
    year: int = Field(ge=MIN_VEHICLE_YEAR)
    vin: str = Field(pattern=r"^[A-HJ-NPR-Z0-9]{17}$")
    required_license_category: Literal[LICENSE_CATEGORIES]
    status: Literal["ACTIVE", "DECOMMISSIONED"] = "ACTIVE"

    @field_validator("year")
    @classmethod
    def year_not_in_future(cls, value):
        if value > Date.today().year + 1:
            raise ValueError(f"не може бути пізніше {Date.today().year + 1}")
        return value


class VehicleUpdateData(VehicleData):
    status: Literal["ACTIVE", "DECOMMISSIONED"]


class VehicleStatusData(BaseModel):
    status: Literal["ACTIVE", "DECOMMISSIONED"]


class VehiclesService(IVehiclesService, EntityManagement):
    entity_name = "Транспорт"
    status_labels = {"ACTIVE": "Активний", "DECOMMISSIONED": "Списаний"}
    status_blocked_message = (
        "Транспорт не можна списати, поки на нього є заплановані маршрути "
        "або маршрути в дорозі. Спочатку завершіть, скасуйте або передайте "
        "ці маршрути іншому транспорту."
    )

    def __init__(
        self, repository: IVehiclesRepository, routes_repository: IRoutesRepository
    ):
        super().__init__(repository)
        self.routes_repository = routes_repository

    async def _validate(self, data, id=None):
        vehicle = await self.get_by_id(id)
        if vehicle.status == "DECOMMISSIONED":
            raise BusinessRuleError("Списаний автомобіль не можна оновлювати.")
        existing = await self.repository.get_by_vin(data.vin)
        if existing and existing.id != id:
            raise EntityAlreadyExistsError(
                f"Транспорт із VIN {data.vin} уже є ({existing.make}). "
                "Перевірте VIN."
            )

    async def _can_change_status(self, entity, status):
        if status != "DECOMMISSIONED":
            return True
        routes = await self.routes_repository.get_by_vehicle(entity.id)
        return not any(r.is_active() for r in routes)

    async def get_by_driver(self, driver_id):
        return await self.repository.get_by_driver(driver_id)

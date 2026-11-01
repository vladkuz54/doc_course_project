from datetime import date as Date
from typing import Literal

from pydantic import BaseModel, Field, field_validator

from ...dal.db_models import ACTIVE_ROUTE_STATUSES, LICENSE_CATEGORIES, MIN_VEHICLE_YEAR
from ...dal.interfaces.routes_interfaces import IRoutesRepository
from ...dal.interfaces.vehicles_interfaces import IVehiclesRepository
from ..exceptions import BusinessRuleError, EntityAlreadyExistsError
from ..interfaces.repair_records_interface import IRepairRecordsService
from ..interfaces.vehicles_interface import IVehiclesService
from .entity_management import EntityManagement
from .repair_records_service import RepairRecordData


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
        if value > Date.today().year + 1:
            raise ValueError(f"year must be at most {Date.today().year + 1}")
        return value


class VehicleStatusData(BaseModel):
    status: Literal["ACTIVE", "DECOMMISSIONED"]


class MaintenanceData(BaseModel):
    type: Literal["SERVICE_TO", "INSPECTION", "REPAIR"]
    date: Date


class TechnicalStateData(BaseModel):
    technical_state: str


class VehiclesService(IVehiclesService, EntityManagement):
    entity_name = "Vehicle"

    def __init__(
        self,
        repository: IVehiclesRepository,
        routes_repository: IRoutesRepository,
        repair_records_service: IRepairRecordsService,
    ):
        super().__init__(repository)
        self.routes_repository = routes_repository
        self.repair_records_service = repair_records_service

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

    async def schedule_maintenance(self, vehicle_id, type, date):
        await self.get_by_id(vehicle_id)
        if date < Date.today():
            raise BusinessRuleError("Maintenance date cannot be in the past")
        return await self.repair_records_service.create(
            RepairRecordData(
                vehicle_id=vehicle_id, date=date, type=type, status="PLANNED"
            )
        )

    async def update_technical_state(self, vehicle_id, state):
        vehicle = await self.get_by_id(vehicle_id)
        vehicle.technical_state = state
        return await self.repository.update(vehicle)

from datetime import date
from decimal import Decimal

from pydantic import BaseModel

from ...dal.interfaces.fuel_records_interfaces import IFuelRecordsRepository
from ...dal.interfaces.vehicles_interfaces import IVehiclesRepository
from ..interfaces.fuel_records_interface import IFuelRecordsService
from .base_service import BaseService


class FuelRecordData(BaseModel):
    vehicle_id: int
    date: date
    amount: Decimal
    liters: float


class FuelRecordsService(IFuelRecordsService, BaseService):
    entity_name = "Fuel record"

    def __init__(
        self,
        repository: IFuelRecordsRepository,
        vehicles_repository: IVehiclesRepository,
    ):
        super().__init__(repository, {"vehicle_id": (vehicles_repository, "Vehicle")})

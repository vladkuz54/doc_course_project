from datetime import date
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel

from ...dal.interfaces.repair_records_interfaces import IRepairRecordsRepository
from ...dal.interfaces.vehicles_interfaces import IVehiclesRepository
from ..interfaces.repair_records_interface import IRepairRecordsService
from .base_service import BaseService


class RepairRecordData(BaseModel):
    vehicle_id: int
    date: date
    amount: Decimal | None = None
    type: Literal["SERVICE_TO", "INSPECTION", "REPAIR"]
    description: str = ""
    status: Literal["PLANNED", "DONE"] = "PLANNED"


class RepairRecordsService(IRepairRecordsService, BaseService):
    entity_name = "Repair record"

    def __init__(
        self,
        repository: IRepairRecordsRepository,
        vehicles_repository: IVehiclesRepository,
    ):
        super().__init__(repository, {"vehicle_id": (vehicles_repository, "Vehicle")})

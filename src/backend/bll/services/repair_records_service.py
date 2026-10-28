from datetime import date
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel

from ...dal.interfaces.repair_records_interfaces import IRepairRecordsRepository
from ...dal.interfaces.vehicles_interfaces import IVehiclesRepository
from ..exceptions import EntityNotFoundError
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
        super().__init__(repository)
        self.vehicles_repository = vehicles_repository

    async def _validate(self, data, id=None):
        if not await self.vehicles_repository.get_by_id(data.vehicle_id):
            raise EntityNotFoundError(f"Vehicle with ID {data.vehicle_id} not found")

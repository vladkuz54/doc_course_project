from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel

from ...dal.db_models import ACTIVE_ROUTE_STATUSES, RepairRecords
from ...dal.interfaces.routes_interfaces import IRoutesRepository
from ..exceptions import BusinessRuleError
from ..interfaces.repair_records_interface import IRepairRecordsService
from .accounting_service import AccountingService

MAINTENANCE_TYPE_LABELS = {
    "SERVICE_TO": "ТО",
    "INSPECTION": "техогляд",
    "REPAIR": "ремонт",
}


class RepairRecordData(BaseModel):
    vehicle_id: int
    date: date
    amount: Decimal | None = None
    type: Literal["SERVICE_TO", "INSPECTION", "REPAIR"]
    description: str = ""
    status: Literal["PLANNED", "DONE"] = "PLANNED"


class RepairCostData(BaseModel):
    cost: Decimal


class RepairRecordsService(IRepairRecordsService, AccountingService):
    entity_name = "Repair record"

    def __init__(
        self, repository, vehicles_repository, routes_repository: IRoutesRepository
    ):
        super().__init__(repository, vehicles_repository)
        self.routes_repository = routes_repository

    async def _validate(self, data, id=None):
        await self._ensure_vehicle_exists(data.vehicle_id)
        if id is not None:
            existing = await self.get_by_id(id)
            if data.status != existing.status or (
                existing.status == "DONE" and data.amount != existing.amount
            ):
                raise BusinessRuleError(
                    "Repair status and cost change only through the cost route"
                )
        if data.status == "PLANNED" and data.amount is not None:
            raise BusinessRuleError("A planned repair cannot have an amount")
        if data.status == "DONE" and data.amount is None:
            raise BusinessRuleError("A done repair must have an amount")
        if data.amount is not None and data.amount < 0:
            raise BusinessRuleError("Repair amount cannot be negative")
        if data.status == "PLANNED":
            for route in await self.routes_repository.get_by_vehicle(data.vehicle_id):
                last_day = route.planned_return_at
                if route.status == "IN_PROGRESS":
                    last_day = max(last_day, datetime.now())
                if (
                    route.status in ACTIVE_ROUTE_STATUSES
                    and route.departure_at.date() <= data.date <= last_day.date()
                ):
                    raise BusinessRuleError(
                        f"The vehicle is on route {route.id} on {data.date}"
                    )

    def _create_record(self, data):
        return RepairRecords(**self.to_fields(data))

    async def record_repair_cost(self, id, cost):
        record = await self.get_by_id(id)
        if record.status != "PLANNED":
            raise BusinessRuleError(f"Repair record with ID {id} is not planned")
        if cost < 0:
            raise BusinessRuleError("Repair cost cannot be negative")
        record.amount = cost
        record.status = "DONE"
        return await self.repository.update(record)

    async def get_planned(self):
        return await self.repository.get_planned()

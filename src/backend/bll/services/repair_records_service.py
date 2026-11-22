from datetime import date
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel

from ...dal.db_models import RepairRecords
from ...dal.interfaces.routes_interfaces import IRoutesRepository
from ..exceptions import BusinessRuleError
from ..interfaces.repair_records_interface import IRepairRecordsService
from .accounting_service import AccountingService


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
    entity_name = "Запис про обслуговування"

    def __init__(
        self, repository, vehicles_repository, routes_repository: IRoutesRepository
    ):
        AccountingService.__init__(self, repository, vehicles_repository)
        self.routes_repository = routes_repository

    async def _validate(self, data, id=None):
        await self._ensure_vehicle_exists(data.vehicle_id)
        existing = await self.get_by_id(id) if id is not None else None
        if existing is not None:
            if existing.status == "DONE" and (
                data.status != existing.status or data.amount != existing.amount
            ):
                raise BusinessRuleError(
                    "Обслуговування вже виконане, тому його статус і вартість "
                    "змінити не можна."
                )
            if data.status != existing.status:
                raise BusinessRuleError(
                    "Щоб позначити обслуговування виконаним, внесіть його вартість."
                )
        if data.status == "PLANNED" and data.amount is not None:
            raise BusinessRuleError(
                "Для запланованого обслуговування вартість ще не вказують. "
                "Залиште її порожньою і внесіть, коли роботу буде виконано."
            )
        if data.status == "DONE" and data.amount is None:
            raise BusinessRuleError("Вкажіть вартість виконаного обслуговування.")
        if data.status == "DONE" and data.date > date.today():
            raise BusinessRuleError(
                f"Дата виконаного обслуговування ({data.date:%d/%m/%Y}) ще не "
                "настала. Вкажіть фактичну дату виконання."
            )
        if data.amount is not None and data.amount < 0:
            raise BusinessRuleError("Вартість обслуговування не може бути від'ємною.")
        if data.status == "PLANNED":
            if existing is None or data.vehicle_id != existing.vehicle_id:
                vehicle = await self.vehicles_repository.get_by_id(data.vehicle_id)
                if vehicle.status != "ACTIVE":
                    raise BusinessRuleError(
                        f"Транспорт {vehicle.make} ({vehicle.vin}) списаний, тому "
                        "для нього не можна запланувати обслуговування."
                    )
            if existing is None or data.date != existing.date:
                if data.date < date.today():
                    raise BusinessRuleError(
                        f"Дата обслуговування ({data.date:%d/%m/%Y}) уже минула. "
                        "Оберіть сьогоднішню або пізнішу дату."
                    )
            for route in await self.routes_repository.get_by_vehicle(data.vehicle_id):
                if (
                    route.is_active()
                    and route.departure_at.date()
                    <= data.date
                    <= route.occupied_until().date()
                ):
                    raise BusinessRuleError(
                        f"{data.date:%d/%m/%Y} транспорт буде на маршруті "
                        f"№{route.id}. Оберіть іншу дату або перенесіть маршрут."
                    )

    def _create_record(self, data):
        return RepairRecords(**self.to_fields(data))

    async def record_repair_cost(self, id, cost):
        record = await self.get_by_id(id)
        if record.status != "PLANNED":
            raise BusinessRuleError("Вартість цього обслуговування вже внесено.")
        if cost < 0:
            raise BusinessRuleError("Вартість обслуговування не може бути від'ємною.")
        if record.date > date.today():
            raise BusinessRuleError("Не можна внести вартість раніше терміну.")
        record.amount = cost
        record.status = "DONE"
        return await self.repository.update(record)

    async def get_planned(self):
        return await self.repository.get_planned()

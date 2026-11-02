from datetime import date
from decimal import Decimal

from pydantic import BaseModel

from ...dal.db_models import FuelRecords
from ..interfaces.fuel_records_interface import IFuelRecordsService
from .accounting_service import AccountingService


class FuelRecordData(BaseModel):
    vehicle_id: int
    date: date
    amount: Decimal
    liters: float


class FuelRecordsService(IFuelRecordsService, AccountingService):
    entity_name = "Fuel record"

    async def _validate(self, data, id=None):
        await self._ensure_vehicle_exists(data.vehicle_id)

    def _create_record(self, data):
        return FuelRecords(**self.to_fields(data))

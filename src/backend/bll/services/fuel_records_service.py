from datetime import date
from decimal import Decimal

from pydantic import BaseModel, Field

from ...dal.db_models import FuelRecords
from ..interfaces.fuel_records_interface import IFuelRecordsService
from .accounting_service import AccountingService


class FuelRecordData(BaseModel):
    vehicle_id: int
    date: date
    amount: Decimal = Field(ge=0)
    liters: float = Field(gt=0, allow_inf_nan=False)


class FuelRecordsService(IFuelRecordsService, AccountingService):
    entity_name = "Запис про пальне"

    async def _validate(self, data, id=None):
        await self._ensure_vehicle_exists(data.vehicle_id)

    def _create_record(self, data):
        return FuelRecords(**self.to_fields(data))

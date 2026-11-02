from sqlalchemy import select
from sqlalchemy.orm import selectinload

from ..db_models import RepairRecords, Vehicles
from ..interfaces.repair_records_interfaces import IRepairRecordsRepository
from .accounting_repository import AccountingRepository


class RepairRecordsRepository(IRepairRecordsRepository, AccountingRepository):
    def __init__(self, session):
        super().__init__(session, RepairRecords)

    async def get_planned(self):
        result = await self.session.execute(
            select(self.model)
            .join(Vehicles, Vehicles.id == self.model.vehicle_id)
            .where(self.model.status == "PLANNED", Vehicles.status == "ACTIVE")
            .options(selectinload(self.model.vehicle))
        )
        return result.scalars().all()

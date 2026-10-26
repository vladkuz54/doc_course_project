from ..db_models import RepairRecords
from ..interfaces.repair_records_interfaces import IRepairRecordsRepository
from .accounting_repository import AccountingRepository


class RepairRecordsRepository(IRepairRecordsRepository, AccountingRepository):
    def __init__(self, session):
        super().__init__(session, RepairRecords)

    async def get_planned(self):
        return await self._where(self.model.status == "PLANNED")

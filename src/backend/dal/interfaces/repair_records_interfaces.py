from abc import abstractmethod

from ..db_models import RepairRecords
from .accounting_interfaces import IAccountingRepository


class IRepairRecordsRepository(IAccountingRepository[RepairRecords]):

    @abstractmethod
    async def get_planned(self):
        pass

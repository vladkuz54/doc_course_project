from ..db_models import FuelRecords
from .accounting_interfaces import IAccountingRepository


class IFuelRecordsRepository(IAccountingRepository[FuelRecords]):
    pass

from ..db_models import FuelRecords
from ..interfaces.fuel_records_interfaces import IFuelRecordsRepository
from .accounting_repository import AccountingRepository


class FuelRecordsRepository(IFuelRecordsRepository, AccountingRepository):
    def __init__(self, session):
        super().__init__(session, FuelRecords)

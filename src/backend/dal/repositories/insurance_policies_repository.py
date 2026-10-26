from ..db_models import InsurancePolicies
from ..interfaces.insurance_policies_interfaces import IInsurancePoliciesRepository
from .accounting_repository import AccountingRepository


class InsurancePoliciesRepository(IInsurancePoliciesRepository, AccountingRepository):
    def __init__(self, session):
        super().__init__(session, InsurancePolicies)

    async def get_expiring(self, until):
        return await self._where(self.model.end_date <= until)

from abc import abstractmethod

from ..db_models import InsurancePolicies
from .accounting_interfaces import IAccountingRepository


class IInsurancePoliciesRepository(IAccountingRepository[InsurancePolicies]):

    @abstractmethod
    async def get_expiring(self, until):
        pass

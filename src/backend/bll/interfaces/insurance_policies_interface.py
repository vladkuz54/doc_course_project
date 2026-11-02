from abc import abstractmethod

from .accounting_interface import IAccountingService


class IInsurancePoliciesService(IAccountingService):

    @abstractmethod
    async def get_expiring(self, until):
        pass

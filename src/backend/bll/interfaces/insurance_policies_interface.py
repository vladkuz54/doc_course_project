from abc import abstractmethod

from .base_interface import IBaseService


class IInsurancePoliciesService(IBaseService):

    @abstractmethod
    async def get_expiring(self, until):
        pass

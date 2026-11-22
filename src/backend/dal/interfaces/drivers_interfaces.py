from abc import abstractmethod

from ..db_models import Drivers
from .base_interfaces import IBaseRepository


class IDriversRepository(IBaseRepository[Drivers]):

    @abstractmethod
    async def get_by_user_id(self, user_id):
        pass

    @abstractmethod
    async def get_license_expiring(self, until):
        pass

    @abstractmethod
    async def get_medical_check_due(self, until):
        pass

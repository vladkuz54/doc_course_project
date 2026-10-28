from abc import abstractmethod

from ..db_models import Users
from .base_interfaces import IBaseRepository


class IUsersRepository(IBaseRepository[Users]):

    @abstractmethod
    async def get_by_username(self, username):
        pass

    @abstractmethod
    async def get_by_driver(self, driver_id):
        pass

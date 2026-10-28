from abc import abstractmethod

from ..db_models import Notifications
from .base_interfaces import IBaseRepository


class INotificationsRepository(IBaseRepository[Notifications]):

    @abstractmethod
    async def get_unread(self):
        pass

    @abstractmethod
    async def get_for_driver(self, driver_id):
        pass

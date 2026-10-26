from ..db_models import Notifications
from ..interfaces.notifications_interfaces import INotificationsRepository
from .base_repository import BaseRepository


class NotificationsRepository(INotificationsRepository, BaseRepository):
    def __init__(self, session):
        super().__init__(session, Notifications)

    async def get_unread(self):
        return await self._where(self.model.is_read.is_(False))

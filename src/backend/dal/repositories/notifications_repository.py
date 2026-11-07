from sqlalchemy import or_, select

from ..db_models import Drivers, Notifications
from ..interfaces.notifications_interfaces import INotificationsRepository
from .base_repository import BaseRepository


class NotificationsRepository(INotificationsRepository, BaseRepository):
    def __init__(self, session):
        super().__init__(session, Notifications)

    async def get_unread_or_read_since(self, since):
        return await self._where(
            or_(self.model.is_read.is_(False), self.model.read_at >= since)
        )

    async def get_by_driver(self, driver_id):
        result = await self.session.execute(
            select(self.model)
            .join(Drivers, Drivers.user_id == self.model.recipient_id)
            .where(Drivers.id == driver_id)
            .order_by(self.model.created_at.desc())
        )
        return result.scalars().all()

    async def get_for_admins(self):
        result = await self.session.execute(
            select(self.model)
            .where(self.model.recipient_id.is_(None))
            .order_by(self.model.created_at.desc())
        )
        return result.scalars().all()

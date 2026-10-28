from sqlalchemy import and_, or_, select

from ..db_models import DriverRequests, Notifications, Routes
from ..interfaces.notifications_interfaces import INotificationsRepository
from .base_repository import BaseRepository


class NotificationsRepository(INotificationsRepository, BaseRepository):
    def __init__(self, session):
        super().__init__(session, Notifications)

    async def get_unread(self):
        return await self._where(self.model.is_read.is_(False))

    async def get_by_driver(self, driver_id):
        def related(entity, ids):
            return and_(
                self.model.related_entity == entity, self.model.related_id.in_(ids)
            )

        my_routes = select(Routes.id).where(Routes.driver_id == driver_id)
        my_requests = select(DriverRequests.id).where(
            DriverRequests.driver_id == driver_id
        )
        result = await self.session.execute(
            select(self.model)
            .where(
                or_(
                    related("drivers", [driver_id]),
                    related("routes", my_routes),
                    related("driver_requests", my_requests),
                )
            )
            .order_by(self.model.created_at.desc())
        )
        return result.scalars().all()

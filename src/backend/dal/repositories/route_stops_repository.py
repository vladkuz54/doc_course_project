from sqlalchemy import select

from ..db_models import Routes, RouteStops
from ..interfaces.route_stops_interfaces import IRouteStopsRepository
from .base_repository import BaseRepository


class RouteStopsRepository(IRouteStopsRepository, BaseRepository):
    def __init__(self, session):
        super().__init__(session, RouteStops)

    async def get_by_driver(self, driver_id):
        result = await self.session.execute(
            select(self.model)
            .join(Routes, Routes.id == self.model.route_id)
            .where(Routes.driver_id == driver_id)
            .order_by(self.model.route_id, self.model.order_no)
        )
        return result.scalars().all()

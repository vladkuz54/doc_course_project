from sqlalchemy import select

from ..db_models import RouteStops
from ..interfaces.route_stops_interfaces import IRouteStopsRepository
from .base_repository import BaseRepository


class RouteStopsRepository(IRouteStopsRepository, BaseRepository):
    def __init__(self, session):
        super().__init__(session, RouteStops)

    async def get_by_route(self, route_id):
        result = await self.session.execute(
            select(self.model)
            .where(self.model.route_id == route_id)
            .order_by(self.model.order_no)
        )
        return result.scalars().all()

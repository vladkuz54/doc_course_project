from abc import abstractmethod

from ..db_models import RouteStops
from .base_interfaces import IBaseRepository


class IRouteStopsRepository(IBaseRepository[RouteStops]):

    @abstractmethod
    async def get_by_driver(self, driver_id):
        pass

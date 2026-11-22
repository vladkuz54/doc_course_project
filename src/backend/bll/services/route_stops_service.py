from backend.bll.exceptions import BusinessRuleError
from backend.bll.services.base_service import BaseService

from ...dal.interfaces.route_stops_interfaces import IRouteStopsRepository
from ..interfaces.route_stops_interface import IRouteStopsService


class RouteStopsService(IRouteStopsService, BaseService):
    entity_name = "Зупинку"

    def __init__(self, repository: IRouteStopsRepository):
        super().__init__(repository)

    async def _validate(self, data, id=None):
        raise BusinessRuleError("Зупинки потрібно редагувати через маршрутин.")

    async def get_by_driver(self, driver_id):
        return await self.repository.get_by_driver(driver_id)

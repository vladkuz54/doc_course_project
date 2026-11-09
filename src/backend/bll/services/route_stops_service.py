from pydantic import BaseModel

from ...dal.interfaces.route_stops_interfaces import IRouteStopsRepository
from ..interfaces.route_stops_interface import IRouteStopsService
from .read_service import ReadService


class RouteStopData(BaseModel):
    route_id: int
    order_no: int
    address: str


class RouteStopsService(IRouteStopsService, ReadService):
    entity_name = "Зупинку"

    def __init__(self, repository: IRouteStopsRepository):
        super().__init__(repository)

    async def get_by_driver(self, driver_id):
        return await self.repository.get_by_driver(driver_id)

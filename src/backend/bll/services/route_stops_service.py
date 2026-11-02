from pydantic import BaseModel

from ...dal.interfaces.route_stops_interfaces import IRouteStopsRepository
from ..exceptions import EntityNotFoundError
from ..interfaces.route_stops_interface import IRouteStopsService


class RouteStopData(BaseModel):
    route_id: int
    order_no: int
    address: str


class RouteStopsService(IRouteStopsService):
    entity_name = "Route stop"

    def __init__(self, repository: IRouteStopsRepository):
        self.repository = repository

    async def get_all(self):
        return await self.repository.get_all()

    async def get_by_id(self, id):
        obj = await self.repository.get_by_id(id)
        if not obj:
            raise EntityNotFoundError(f"{self.entity_name} with ID {id} not found")
        return obj

    async def get_by_driver(self, driver_id):
        return await self.repository.get_by_driver(driver_id)

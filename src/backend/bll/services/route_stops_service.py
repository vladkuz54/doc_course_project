from pydantic import BaseModel

from ...dal.interfaces.route_stops_interfaces import IRouteStopsRepository
from ...dal.interfaces.routes_interfaces import IRoutesRepository
from ..exceptions import EntityAlreadyExistsError, EntityNotFoundError
from ..interfaces.route_stops_interface import IRouteStopsService
from .base_service import BaseService


class RouteStopData(BaseModel):
    route_id: int
    order_no: int
    address: str


class RouteStopsService(IRouteStopsService, BaseService):
    entity_name = "Route stop"

    def __init__(
        self, repository: IRouteStopsRepository, routes_repository: IRoutesRepository
    ):
        super().__init__(repository)
        self.routes_repository = routes_repository

    async def _validate(self, data, id=None):
        if not await self.routes_repository.get_by_id(data.route_id):
            raise EntityNotFoundError(f"Route with ID {data.route_id} not found")
        stops = await self.repository.get_by_route(data.route_id)
        if any(s.order_no == data.order_no and s.id != id for s in stops):
            raise EntityAlreadyExistsError(
                f"Route {data.route_id} already has a stop number {data.order_no}"
            )

    async def get_by_driver(self, driver_id):
        return await self.repository.get_by_driver(driver_id)

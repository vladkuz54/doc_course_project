from pydantic import BaseModel

from ...dal.interfaces.route_stops_interfaces import IRouteStopsRepository
from ...dal.interfaces.routes_interfaces import IRoutesRepository
from ..exceptions import EntityAlreadyExistsError
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
        super().__init__(repository, {"route_id": (routes_repository, "Route")})

    async def validate(self, data, id=None):
        await super().validate(data, id)
        stops = await self.repository.get_by_route(data.route_id)
        if any(s.order_no == data.order_no and s.id != id for s in stops):
            raise EntityAlreadyExistsError(
                f"Route {data.route_id} already has a stop number {data.order_no}"
            )

from abc import abstractmethod

from .base_interface import IBaseService


class IRoutesService(IBaseService):

    @abstractmethod
    async def list_by_driver(self, driver_id):
        pass

    @abstractmethod
    async def list(self, period_from, period_to, vehicle=None):
        pass

    @abstractmethod
    async def assign_driver(self, route_id, driver_id):
        pass

    @abstractmethod
    async def assign_vehicle(self, route_id, vehicle_id):
        pass

    @abstractmethod
    async def reschedule(self, route_id, departure_at):
        pass

    @abstractmethod
    async def edit_stops(self, route_id, addresses):
        pass

    @abstractmethod
    async def start(self, route_id, started_at=None):
        pass

    @abstractmethod
    async def arrive_at_stop(self, route_id, stop_id):
        pass

    @abstractmethod
    async def complete(self, route_id, returned_at=None):
        pass

    @abstractmethod
    async def cancel(self, route_id):
        pass

    @abstractmethod
    async def restore(self, route_id):
        pass

    @abstractmethod
    async def repeat(self, route_id, departure_at):
        pass

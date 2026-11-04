from abc import abstractmethod

from .base_interface import IBaseService


class IVehiclesService(IBaseService):

    @abstractmethod
    async def get_by_driver(self, driver_id):
        pass

    @abstractmethod
    async def update_technical_state(self, vehicle_id, state):
        pass

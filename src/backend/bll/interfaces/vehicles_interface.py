from abc import abstractmethod

from .entity_management_interface import IEntityManagement


class IVehiclesService(IEntityManagement):

    @abstractmethod
    async def get_by_driver(self, driver_id):
        pass

from abc import abstractmethod

from .entity_management_interface import IEntityManagement


class IDriversService(IEntityManagement):

    @abstractmethod
    async def get_by_user_id(self, user_id):
        pass

    @abstractmethod
    async def get_by_driver(self, driver_id):
        pass

    @abstractmethod
    async def get_license_expiring(self, until):
        pass

    @abstractmethod
    async def get_medical_check_due(self, until):
        pass

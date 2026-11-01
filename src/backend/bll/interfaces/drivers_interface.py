from abc import abstractmethod

from .base_interface import IBaseService


class IDriversService(IBaseService):

    @abstractmethod
    async def get_by_user_id(self, user_id):
        pass

    @abstractmethod
    async def get_by_driver(self, driver_id):
        pass

    @abstractmethod
    async def submit_request(self, data):
        pass

    @abstractmethod
    async def approve_license_update(self, request_id):
        pass

    @abstractmethod
    async def approve_medical_check(self, request_id, valid_until):
        pass

    @abstractmethod
    async def get_license_expiring(self, until):
        pass

    @abstractmethod
    async def get_medical_check_due(self, until):
        pass

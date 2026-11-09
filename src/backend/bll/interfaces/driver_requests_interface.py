from abc import ABC, abstractmethod


class IDriverRequestsService(ABC):

    @abstractmethod
    async def get_all(self):
        pass

    @abstractmethod
    async def get_by_id(self, id):
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
    async def approve_medical_check(self, request_id):
        pass

    @abstractmethod
    async def reject_request(self, request_id):
        pass

from datetime import date as Date
from decimal import Decimal

from pydantic import BaseModel

from ...dal.interfaces.insurance_policies_interfaces import IInsurancePoliciesRepository
from ...dal.interfaces.vehicles_interfaces import IVehiclesRepository
from ..exceptions import EntityNotFoundError
from ..interfaces.insurance_policies_interface import IInsurancePoliciesService
from .base_service import BaseService


class InsurancePolicyData(BaseModel):
    vehicle_id: int
    date: Date
    amount: Decimal
    start_date: Date
    end_date: Date


class InsurancePoliciesService(IInsurancePoliciesService, BaseService):
    entity_name = "Insurance policy"

    def __init__(
        self,
        repository: IInsurancePoliciesRepository,
        vehicles_repository: IVehiclesRepository,
    ):
        super().__init__(repository)
        self.vehicles_repository = vehicles_repository

    async def _validate(self, data, id=None):
        if not await self.vehicles_repository.get_by_id(data.vehicle_id):
            raise EntityNotFoundError(f"Vehicle with ID {data.vehicle_id} not found")

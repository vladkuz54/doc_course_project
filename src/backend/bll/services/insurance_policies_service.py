from datetime import date as Date
from decimal import Decimal

from pydantic import BaseModel

from ...dal.interfaces.insurance_policies_interfaces import IInsurancePoliciesRepository
from ...dal.interfaces.vehicles_interfaces import IVehiclesRepository
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
        super().__init__(repository, {"vehicle_id": (vehicles_repository, "Vehicle")})

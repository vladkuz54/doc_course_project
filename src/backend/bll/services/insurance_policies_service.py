from datetime import date as Date
from decimal import Decimal

from pydantic import BaseModel

from ...dal.db_models import InsurancePolicies
from ..exceptions import BusinessRuleError
from ..interfaces.insurance_policies_interface import IInsurancePoliciesService
from .accounting_service import AccountingService


class InsurancePolicyData(BaseModel):
    vehicle_id: int
    date: Date
    amount: Decimal
    start_date: Date
    end_date: Date


class InsurancePoliciesService(IInsurancePoliciesService, AccountingService):
    entity_name = "Insurance policy"

    async def _validate(self, data, id=None):
        await self._ensure_vehicle_exists(data.vehicle_id)
        if data.end_date < data.start_date:
            raise BusinessRuleError("end_date cannot be before start_date")

    def _create_record(self, data):
        return InsurancePolicies(**self.to_fields(data))

    async def get_expiring(self, until):
        return await self.repository.get_expiring(until)

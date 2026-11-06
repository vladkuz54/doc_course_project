from datetime import date as Date
from decimal import Decimal

from pydantic import BaseModel, Field

from ...dal.db_models import InsurancePolicies
from ..exceptions import BusinessRuleError
from ..interfaces.insurance_policies_interface import IInsurancePoliciesService
from .accounting_service import AccountingService


class InsurancePolicyData(BaseModel):
    vehicle_id: int
    date: Date
    amount: Decimal = Field(ge=0)
    start_date: Date
    end_date: Date


class InsurancePoliciesService(IInsurancePoliciesService, AccountingService):
    entity_name = "Страховий поліс"

    async def _validate(self, data, id=None):
        await self._ensure_vehicle_exists(data.vehicle_id)
        if data.end_date < data.start_date:
            raise BusinessRuleError(
                f"Кінець покриття ({data.end_date:%d/%m/%Y}) не може бути "
                f"раніше за його початок ({data.start_date:%d/%m/%Y})."
            )

    def _create_record(self, data):
        return InsurancePolicies(**self.to_fields(data))

    async def get_expiring(self, until):
        return await self.repository.get_expiring(until)

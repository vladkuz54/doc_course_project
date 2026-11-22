from datetime import date as Date
from decimal import Decimal

from pydantic import BaseModel, Field

from ...dal.db_models import InsurancePolicies
from ...dal.interfaces.routes_interfaces import IRoutesRepository
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

    def __init__(
        self, repository, vehicles_repository, routes_repository: IRoutesRepository
    ):
        AccountingService.__init__(self, repository, vehicles_repository)
        self.routes_repository = routes_repository

    async def _validate(self, data, id=None):
        await self._ensure_vehicle_exists(data.vehicle_id)
        if data.end_date < data.start_date:
            raise BusinessRuleError(
                f"Кінець покриття ({data.end_date:%d/%m/%Y}) не може бути "
                f"раніше за його початок ({data.start_date:%d/%m/%Y})."
            )
        if id is not None:
            old = await self.get_by_id(id)
            same_vehicle = data.vehicle_id == old.vehicle_id
            await self._ensure_routes_stay_covered(
                old.vehicle_id, id, data if same_vehicle else None
            )

    async def delete(self, id):
        policy = await self.get_by_id(id)
        await self._ensure_routes_stay_covered(policy.vehicle_id, id)
        return await super().delete(id)

    async def _ensure_routes_stay_covered(self, vehicle_id, policy_id, edited=None):
        policies = [
            p
            for p in await self.repository.get_by_vehicle(vehicle_id)
            if p.id != policy_id
        ]
        if edited is not None:
            policies.append(edited)
        for route in await self.routes_repository.get_by_vehicle(vehicle_id):
            departure = route.departure_at.date()
            if route.is_active() and not any(
                p.start_date <= departure <= p.end_date for p in policies
            ):
                raise BusinessRuleError(
                    f"Маршрут №{route.id} з виїздом {departure:%d/%m/%Y} залишиться "
                    "без страхового поліса. Спочатку додайте інший поліс, "
                    "змініть транспорт маршруту або скасуйте його."
                )

    def _create_record(self, data):
        return InsurancePolicies(**self.to_fields(data))

    async def get_expiring(self, until):
        return await self.repository.get_expiring(until)

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from ..db_models import InsurancePolicies, Vehicles
from ..interfaces.insurance_policies_interfaces import IInsurancePoliciesRepository
from .accounting_repository import AccountingRepository


class InsurancePoliciesRepository(IInsurancePoliciesRepository, AccountingRepository):
    def __init__(self, session):
        super().__init__(session, InsurancePolicies)

    async def get_expiring(self, until):
        result = await self.session.execute(
            select(self.model)
            .join(Vehicles, Vehicles.id == self.model.vehicle_id)
            .where(self.model.end_date <= until, Vehicles.status == "ACTIVE")
            .options(selectinload(self.model.vehicle))
        )
        return result.scalars().all()

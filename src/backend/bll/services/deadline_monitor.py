from datetime import date, timedelta

from ..observer import DomainEvent, Subject
from .repair_records_service import MAINTENANCE_TYPE_LABELS

WARNING_DAYS = 14


def _until():
    return date.today() + timedelta(days=WARNING_DAYS)


class DeadlineMonitor(Subject):
    def __init__(
        self, repair_records_service, insurance_policies_service, drivers_service
    ):
        super().__init__()
        self.repair_records_service = repair_records_service
        self.insurance_policies_service = insurance_policies_service
        self.drivers_service = drivers_service

    async def check_maintenance_due(self):
        until = _until()
        for repair in await self.repair_records_service.get_planned():
            if repair.date <= until:
                label = MAINTENANCE_TYPE_LABELS[repair.type]
                await self._notify(
                    DomainEvent(
                        "MAINTENANCE_DUE",
                        "vehicles",
                        repair.vehicle_id,
                        f"Планове обслуговування ({label}) для {repair.vehicle.make}: {repair.date:%d.%m.%Y}",
                    )
                )

    async def check_insurance_expiring(self):
        until = _until()
        latest = {}
        for policy in await self.insurance_policies_service.get_expiring(until):
            current = latest.get(policy.vehicle_id)
            if current is None or policy.end_date > current.end_date:
                latest[policy.vehicle_id] = policy
        for vehicle_id, policy in latest.items():
            policies = await self.insurance_policies_service.get_by_vehicle(vehicle_id)
            if any(p.end_date > until for p in policies):
                continue
            await self._notify(
                DomainEvent(
                    "INSURANCE_EXPIRING",
                    "vehicles",
                    vehicle_id,
                    f"Страховка {policy.vehicle.make} спливає {policy.end_date:%d.%m.%Y}",
                )
            )

    async def check_license_expiring(self):
        for driver in await self.drivers_service.get_license_expiring(_until()):
            await self._notify_driver_and_admins(
                "LICENSE_EXPIRING",
                driver,
                f"Посвідчення спливає: {driver.full_name}, {driver.license_expiry_date:%d.%m.%Y}",
            )

    async def check_medical_check_due(self):
        for driver in await self.drivers_service.get_medical_check_due(_until()):
            await self._notify_driver_and_admins(
                "MEDICAL_CHECK_DUE",
                driver,
                f"Медогляд спливає: {driver.full_name}, {driver.medical_valid_until:%d.%m.%Y}",
            )

    async def _notify_driver_and_admins(self, type, driver, text):
        for recipient_id in (driver.user_id, None):
            await self._notify(
                DomainEvent(type, "drivers", driver.id, text, recipient_id)
            )

from datetime import date, timedelta

from ...dal.db_models import WARNING_DAYS
from ..labels import MAINTENANCE_TYPE_LABELS
from ..observer import DomainEvent, Subject


def _until():
    return date.today() + timedelta(days=WARNING_DAYS)


def _cover_end(policies):
    policies = sorted(policies, key=lambda p: p.start_date)
    cover_end = policies[0].end_date
    for policy in policies[1:]:
        if policy.start_date > max(cover_end, date.today()) + timedelta(days=1):
            break
        cover_end = max(cover_end, policy.end_date)
    return cover_end


class DeadlineMonitor(Subject):
    def __init__(
        self, repair_records_service, insurance_policies_service, drivers_service
    ):
        super().__init__()
        self.repair_records_service = repair_records_service
        self.insurance_policies_service = insurance_policies_service
        self.drivers_service = drivers_service

    async def check_all(self):
        return [
            *await self.check_maintenance_due(),
            *await self.check_repair_cost_missing(),
            *await self.check_insurance_expiring(),
            *await self.check_license_expiring(),
            *await self.check_medical_check_due(),
        ]

    async def check_maintenance_due(self):
        until = _until()
        events = []
        for repair in await self.repair_records_service.get_planned():
            if date.today() <= repair.date <= until:
                label = MAINTENANCE_TYPE_LABELS[repair.type]
                events.append(
                    DomainEvent(
                        "MAINTENANCE_DUE",
                        "vehicles",
                        repair.vehicle_id,
                        f"Планове обслуговування ({label}) для {repair.vehicle.make}: {repair.date:%d.%m.%Y}",
                    )
                )
        return await self._publish(events)

    async def check_repair_cost_missing(self):
        events = []
        for repair in await self.repair_records_service.get_planned():
            if repair.date < date.today():
                label = MAINTENANCE_TYPE_LABELS[repair.type]
                events.append(
                    DomainEvent(
                        "REPAIR_COST_MISSING",
                        "vehicles",
                        repair.vehicle_id,
                        f"Не внесено вартість: {label} для {repair.vehicle.make} "
                        f"від {repair.date:%d.%m.%Y}",
                    )
                )
        return await self._publish(events)

    async def check_insurance_expiring(self):
        until = _until()
        expiring = await self.insurance_policies_service.get_expiring(until)
        vehicles = {p.vehicle_id: p.vehicle for p in expiring}
        events = []
        for vehicle_id, vehicle in vehicles.items():
            cover_end = _cover_end(
                await self.insurance_policies_service.get_by_vehicle(vehicle_id)
            )
            if cover_end <= until:
                events.append(
                    DomainEvent(
                        "INSURANCE_EXPIRING",
                        "vehicles",
                        vehicle_id,
                        f"Страховка {vehicle.make} спливає {cover_end:%d.%m.%Y}",
                    )
                )
        return await self._publish(events)

    async def check_license_expiring(self):
        events = []
        for driver in await self.drivers_service.get_license_expiring(_until()):
            events += self._driver_and_admin_events(
                "LICENSE_EXPIRING",
                driver,
                f"Посвідчення спливає: {driver.full_name}, {driver.license_expiry_date:%d.%m.%Y}",
            )
        return await self._publish(events)

    async def check_medical_check_due(self):
        events = []
        for driver in await self.drivers_service.get_medical_check_due(_until()):
            events += self._driver_and_admin_events(
                "MEDICAL_CHECK_DUE",
                driver,
                f"Медогляд спливає: {driver.full_name}, {driver.medical_valid_until:%d.%m.%Y}",
            )
        return await self._publish(events)

    def _driver_and_admin_events(self, type, driver, text):
        return [
            DomainEvent(type, "drivers", driver.id, text, recipient_id)
            for recipient_id in (driver.user_id, None)
        ]

    async def _publish(self, events):
        for event in events:
            await self._notify(event)
        return events

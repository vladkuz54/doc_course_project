from abc import ABC, abstractmethod
from datetime import date
from decimal import Decimal

from pydantic import BaseModel

from .exceptions import BusinessRuleError


class ReportData(BaseModel):
    title: str
    period_from: date
    period_to: date
    rows: list[dict]


async def _named_rows(rows_by_vehicle, vehicles_service):
    rows = []
    for id in sorted(rows_by_vehicle):
        vehicle = await vehicles_service.get_by_id(id)
        row = {k: v for k, v in rows_by_vehicle[id].items() if k != "vehicle_id"}
        rows.append({"vehicle": vehicle.make, **row})
    return rows


async def _vehicle_ids(vehicles_service, vehicle):
    if vehicle:
        return [vehicle.id]
    vehicles = await vehicles_service.get_all()
    return [v.id for v in vehicles if v.status == "ACTIVE"]


async def _completed_routes(routes_service, period_from, period_to, vehicle):
    routes = await routes_service.list(period_from, period_to, vehicle)
    return [r for r in routes if r.status == "COMPLETED" and r.vehicle_id is not None]


class ReportStrategy(ABC):
    @abstractmethod
    async def generate(self, period_from, period_to, vehicle=None):
        pass


class VehicleUtilizationReport(ReportStrategy):
    def __init__(self, routes_service, vehicles_service):
        self.routes_service = routes_service
        self.vehicles_service = vehicles_service

    async def generate(self, period_from, period_to, vehicle=None):
        def new_row(vehicle_id):
            return {
                "vehicle_id": vehicle_id,
                "completed_routes": 0,
                "total_distance": 0.0,
                "hours_on_route": 0.0,
                "utilization_percent": 0.0,
            }

        rows = {
            id: new_row(id) for id in await _vehicle_ids(self.vehicles_service, vehicle)
        }
        for route in await _completed_routes(
            self.routes_service, period_from, period_to, vehicle
        ):
            row = rows.setdefault(route.vehicle_id, new_row(route.vehicle_id))
            row["completed_routes"] += 1
            row["total_distance"] += route.distance
            started = route.started_at or route.departure_at
            row["hours_on_route"] += (
                route.completed_at - started
            ).total_seconds() / 3600
        period_hours = ((period_to - period_from).days + 1) * 24
        for row in rows.values():
            row["utilization_percent"] = round(
                row["hours_on_route"] / period_hours * 100, 1
            )
            row["hours_on_route"] = round(row["hours_on_route"], 1)
        return ReportData(
            title="Завантаженість автомобілів",
            period_from=period_from,
            period_to=period_to,
            rows=await _named_rows(rows, self.vehicles_service),
        )


class MaintenanceCostReport(ReportStrategy):
    def __init__(
        self,
        repair_records_service,
        fuel_records_service,
        insurance_policies_service,
        vehicles_service,
    ):
        self.repair_records_service = repair_records_service
        self.fuel_records_service = fuel_records_service
        self.insurance_policies_service = insurance_policies_service
        self.vehicles_service = vehicles_service

    async def generate(self, period_from, period_to, vehicle=None):
        def new_row(vehicle_id):
            return {
                "vehicle_id": vehicle_id,
                "fuel_cost": Decimal("0.00"),
                "repair_cost": Decimal("0.00"),
                "insurance_cost": Decimal("0.00"),
                "total_cost": Decimal("0.00"),
            }

        rows = {
            id: new_row(id) for id in await _vehicle_ids(self.vehicles_service, vehicle)
        }

        def add(record, column):
            row = rows.setdefault(record.vehicle_id, new_row(record.vehicle_id))
            row[column] += record.amount
            row["total_cost"] += record.amount

        for fuel in await self.fuel_records_service.list(
            period_from, period_to, vehicle
        ):
            add(fuel, "fuel_cost")
        for repair in await self.repair_records_service.list(
            period_from, period_to, vehicle
        ):
            if repair.status == "DONE":
                add(repair, "repair_cost")
        for policy in await self.insurance_policies_service.list(
            period_from, period_to, vehicle
        ):
            add(policy, "insurance_cost")
        return ReportData(
            title="Витрати на утримання автопарку",
            period_from=period_from,
            period_to=period_to,
            rows=await _named_rows(rows, self.vehicles_service),
        )


class UsageAnalyticsReport(ReportStrategy):
    def __init__(self, routes_service, fuel_records_service, vehicles_service):
        self.routes_service = routes_service
        self.fuel_records_service = fuel_records_service
        self.vehicles_service = vehicles_service

    async def generate(self, period_from, period_to, vehicle=None):
        rows = {}

        def row_for(vehicle_id):
            return rows.setdefault(
                vehicle_id,
                {
                    "vehicle_id": vehicle_id,
                    "total_distance": 0.0,
                    "liters": 0.0,
                    "fuel_cost": Decimal("0"),
                    "liters_per_100km": None,
                },
            )

        for route in await _completed_routes(
            self.routes_service, period_from, period_to, vehicle
        ):
            row_for(route.vehicle_id)["total_distance"] += route.distance
        for fuel in await self.fuel_records_service.list(
            period_from, period_to, vehicle
        ):
            row = row_for(fuel.vehicle_id)
            row["liters"] += fuel.liters
            row["fuel_cost"] += fuel.amount
        for row in rows.values():
            if row["total_distance"] > 0:
                row["liters_per_100km"] = round(
                    row["liters"] / row["total_distance"] * 100, 2
                )
        return ReportData(
            title="Аналітика використання транспорту за період",
            period_from=period_from,
            period_to=period_to,
            rows=await _named_rows(rows, self.vehicles_service),
        )


class ReportService:
    def __init__(self):
        self._strategy = None

    def set_strategy(self, strategy):
        self._strategy = strategy

    async def build(self, period_from, period_to, vehicle=None):
        if self._strategy is None:
            raise BusinessRuleError("Оберіть тип звіту.")
        if period_from > period_to:
            raise BusinessRuleError(
                f"Початкова дата ({period_from:%d/%m/%Y}) пізніша за кінцеву "
                f"({period_to:%d/%m/%Y}). Виправте період звіту."
            )
        return await self._strategy.generate(period_from, period_to, vehicle)

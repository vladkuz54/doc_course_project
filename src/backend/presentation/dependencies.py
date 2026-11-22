from datetime import timedelta
from typing import Literal

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from ..bll.assignment_checks import (
    DriverActiveHandler,
    InsuranceHandler,
    LicenseCategoryHandler,
    MedicalCheckHandler,
    ScheduleConflictHandler,
    VehicleActiveHandler,
    VehicleMaintenanceHandler,
)
from ..bll.live_notifications import live_notifications
from ..bll.services.deadline_monitor import DeadlineMonitor
from ..bll.services.driver_requests_service import DriverRequestsService
from ..bll.services.drivers_service import DriversService
from ..bll.services.fuel_records_service import FuelRecordsService
from ..bll.services.insurance_policies_service import InsurancePoliciesService
from ..bll.services.notifications_service import NotificationsService
from ..bll.services.repair_records_service import RepairRecordsService
from ..bll.services.reports_service import (
    ExpensesReport,
    ReportService,
    ReportStrategy,
    UsageAnalyticsReport,
    VehicleUtilizationReport,
)
from ..bll.services.route_stops_service import RouteStopsService
from ..bll.services.routes_service import RoutesService
from ..bll.services.users_service import UsersService
from ..bll.services.vehicles_service import VehiclesService
from ..dal import Session
from ..dal.repositories.driver_requests_repository import DriverRequestsRepository
from ..dal.repositories.drivers_repository import DriversRepository
from ..dal.repositories.fuel_records_repository import FuelRecordsRepository
from ..dal.repositories.insurance_policies_repository import InsurancePoliciesRepository
from ..dal.repositories.notifications_repository import NotificationsRepository
from ..dal.repositories.repair_records_repository import RepairRecordsRepository
from ..dal.repositories.route_stops_repository import RouteStopsRepository
from ..dal.repositories.routes_repository import RoutesRepository
from ..dal.repositories.users_repository import UsersRepository
from ..dal.repositories.vehicles_repository import VehiclesRepository
from .exports import ReportExporter


async def get_db_session():
    async with Session() as session:
        yield session


def get_users_service(
    session: AsyncSession = Depends(get_db_session),
) -> UsersService:
    return UsersService(UsersRepository(session), DriversRepository(session))


def get_notifications_service(
    session: AsyncSession = Depends(get_db_session),
) -> NotificationsService:
    service = NotificationsService(NotificationsRepository(session))
    service.attach(live_notifications)
    return service


def get_drivers_service(
    session: AsyncSession = Depends(get_db_session),
) -> DriversService:
    return DriversService(
        DriversRepository(session),
        UsersRepository(session),
        RoutesRepository(session),
        DriverRequestsRepository(session),
    )


def get_driver_requests_service(
    session: AsyncSession = Depends(get_db_session),
    notifications: NotificationsService = Depends(get_notifications_service),
) -> DriverRequestsService:
    service = DriverRequestsService(
        DriverRequestsRepository(session), DriversRepository(session)
    )
    service.attach(notifications)
    return service


def get_repair_records_service(
    session: AsyncSession = Depends(get_db_session),
) -> RepairRecordsService:
    return RepairRecordsService(
        RepairRecordsRepository(session),
        VehiclesRepository(session),
        RoutesRepository(session),
    )


def get_vehicles_service(
    session: AsyncSession = Depends(get_db_session),
) -> VehiclesService:
    return VehiclesService(VehiclesRepository(session), RoutesRepository(session))


def get_insurance_policies_service(
    session: AsyncSession = Depends(get_db_session),
) -> InsurancePoliciesService:
    return InsurancePoliciesService(
        InsurancePoliciesRepository(session), VehiclesRepository(session)
    )


def build_assignment_chain(repair_records_service, insurance_policies_service):
    chain = DriverActiveHandler()
    chain.set_next(LicenseCategoryHandler()).set_next(MedicalCheckHandler()).set_next(
        VehicleActiveHandler()
    ).set_next(VehicleMaintenanceHandler(repair_records_service)).set_next(
        InsuranceHandler(insurance_policies_service)
    ).set_next(
        ScheduleConflictHandler()
    )
    return chain


def get_routes_service(
    session: AsyncSession = Depends(get_db_session),
    repair_records_service: RepairRecordsService = Depends(get_repair_records_service),
    insurance_policies_service: InsurancePoliciesService = Depends(
        get_insurance_policies_service
    ),
    notifications: NotificationsService = Depends(get_notifications_service),
) -> RoutesService:
    service = RoutesService(
        RoutesRepository(session),
        DriversRepository(session),
        VehiclesRepository(session),
        RouteStopsRepository(session),
        build_assignment_chain(repair_records_service, insurance_policies_service),
    )
    service.attach(notifications)
    return service


def get_route_stops_service(
    session: AsyncSession = Depends(get_db_session),
) -> RouteStopsService:
    return RouteStopsService(RouteStopsRepository(session))


def get_fuel_records_service(
    session: AsyncSession = Depends(get_db_session),
) -> FuelRecordsService:
    return FuelRecordsService(
        FuelRecordsRepository(session), VehiclesRepository(session)
    )


def get_deadline_monitor(
    repair_records_service: RepairRecordsService = Depends(get_repair_records_service),
    insurance_policies_service: InsurancePoliciesService = Depends(
        get_insurance_policies_service
    ),
    drivers_service: DriversService = Depends(get_drivers_service),
    notifications: NotificationsService = Depends(get_notifications_service),
) -> DeadlineMonitor:
    monitor = DeadlineMonitor(
        repair_records_service, insurance_policies_service, drivers_service
    )
    monitor.attach(notifications)
    return monitor


def get_manual_deadline_monitor(
    repair_records_service: RepairRecordsService = Depends(get_repair_records_service),
    insurance_policies_service: InsurancePoliciesService = Depends(
        get_insurance_policies_service
    ),
    drivers_service: DriversService = Depends(get_drivers_service),
    notifications: NotificationsService = Depends(get_notifications_service),
) -> DeadlineMonitor:
    notifications.set_quiet_period(timedelta(0))
    return get_deadline_monitor(
        repair_records_service,
        insurance_policies_service,
        drivers_service,
        notifications,
    )


def get_report_service() -> ReportService:
    return ReportService()


def get_report_strategy(
    kind: Literal["utilization", "expenses", "usage"],
    routes_service: RoutesService = Depends(get_routes_service),
    repair_records_service: RepairRecordsService = Depends(get_repair_records_service),
    fuel_records_service: FuelRecordsService = Depends(get_fuel_records_service),
    insurance_policies_service: InsurancePoliciesService = Depends(
        get_insurance_policies_service
    ),
    vehicles_service: VehiclesService = Depends(get_vehicles_service),
) -> ReportStrategy:
    if kind == "utilization":
        return VehicleUtilizationReport(routes_service, vehicles_service)
    if kind == "expenses":
        return ExpensesReport(
            repair_records_service,
            fuel_records_service,
            insurance_policies_service,
            vehicles_service,
        )
    if kind == "usage":
        return UsageAnalyticsReport(
            routes_service, fuel_records_service, vehicles_service
        )


def get_report_exporter() -> ReportExporter:
    return ReportExporter()


async def run_deadline_checks():
    async with Session() as session:
        notifications = get_notifications_service(session)
        monitor = get_deadline_monitor(
            get_repair_records_service(session),
            get_insurance_policies_service(session),
            get_drivers_service(session),
            notifications,
        )
        await monitor.check_all()

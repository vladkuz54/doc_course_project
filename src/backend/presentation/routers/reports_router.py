from datetime import date
from typing import Literal

from fastapi import APIRouter, Depends, Response

from ...bll.exports import ExcelExport, PdfExport, ReportExporter
from ...bll.reports import (
    MaintenanceCostReport,
    ReportData,
    ReportService,
    UsageAnalyticsReport,
    VehicleUtilizationReport,
)
from ...bll.services.fuel_records_service import FuelRecordsService
from ...bll.services.repair_records_service import RepairRecordsService
from ...bll.services.routes_service import RoutesService
from ...bll.services.vehicles_service import VehiclesService
from ..dependencies import (
    get_fuel_records_service,
    get_repair_records_service,
    get_report_exporter,
    get_report_service,
    get_routes_service,
    get_vehicles_service,
)
from .auth import require_admin

router = APIRouter(
    prefix="/reports", tags=["reports"], dependencies=[Depends(require_admin)]
)


@router.get("/{kind}", response_model=ReportData)
async def get_report(
    kind: Literal["utilization", "maintenance", "usage"],
    period_from: date,
    period_to: date,
    vehicle_id: int | None = None,
    format: Literal["json", "pdf", "xlsx"] = "json",
    report_service: ReportService = Depends(get_report_service),
    report_exporter: ReportExporter = Depends(get_report_exporter),
    routes_service: RoutesService = Depends(get_routes_service),
    repair_records_service: RepairRecordsService = Depends(get_repair_records_service),
    fuel_records_service: FuelRecordsService = Depends(get_fuel_records_service),
    vehicles_service: VehiclesService = Depends(get_vehicles_service),
):
    report_service.set_strategy(
        {
            "utilization": VehicleUtilizationReport(routes_service, vehicles_service),
            "maintenance": MaintenanceCostReport(
                repair_records_service, vehicles_service
            ),
            "usage": UsageAnalyticsReport(
                routes_service, fuel_records_service, vehicles_service
            ),
        }[kind]
    )
    vehicle = None
    if vehicle_id is not None:
        vehicle = await vehicles_service.get_by_id(vehicle_id)
    report = await report_service.build(period_from, period_to, vehicle)
    if format == "json":
        return report
    report_exporter.set_strategy({"pdf": PdfExport(), "xlsx": ExcelExport()}[format])
    file = report_exporter.export(report)
    return Response(
        content=file.content,
        media_type=file.content_type,
        headers={"Content-Disposition": f'attachment; filename="{file.filename}"'},
    )

from datetime import date
from typing import Literal

from fastapi import APIRouter, Depends, Response

from ...bll.interfaces.fuel_records_interface import IFuelRecordsService
from ...bll.interfaces.insurance_policies_interface import IInsurancePoliciesService
from ...bll.interfaces.repair_records_interface import IRepairRecordsService
from ...bll.interfaces.routes_interface import IRoutesService
from ...bll.interfaces.vehicles_interface import IVehiclesService
from ...bll.reports import (
    MaintenanceCostReport,
    ReportData,
    ReportService,
    UsageAnalyticsReport,
    VehicleUtilizationReport,
)
from ..dependencies import (
    get_fuel_records_service,
    get_insurance_policies_service,
    get_repair_records_service,
    get_report_exporter,
    get_report_service,
    get_routes_service,
    get_vehicles_service,
)
from ..exports import ExcelExport, PdfExport, ReportExporter
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
    routes_service: IRoutesService = Depends(get_routes_service),
    repair_records_service: IRepairRecordsService = Depends(get_repair_records_service),
    fuel_records_service: IFuelRecordsService = Depends(get_fuel_records_service),
    insurance_policies_service: IInsurancePoliciesService = Depends(
        get_insurance_policies_service
    ),
    vehicles_service: IVehiclesService = Depends(get_vehicles_service),
):
    report_service.set_strategy(
        {
            "utilization": VehicleUtilizationReport(routes_service, vehicles_service),
            "maintenance": MaintenanceCostReport(
                repair_records_service,
                fuel_records_service,
                insurance_policies_service,
                vehicles_service,
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

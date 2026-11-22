from datetime import date
from typing import Literal

from fastapi import APIRouter, Depends, Response

from ...bll.interfaces.reports_interface import IReportService
from ...bll.interfaces.vehicles_interface import IVehiclesService
from ...bll.services.reports_service import ReportData, ReportStrategy
from ..dependencies import (
    get_report_exporter,
    get_report_service,
    get_report_strategy,
    get_vehicles_service,
)
from ..exports import ExcelExport, PdfExport, ReportExporter
from .auth import require_admin

router = APIRouter(
    prefix="/reports", tags=["reports"], dependencies=[Depends(require_admin)]
)


@router.get("/{kind}", response_model=ReportData)
async def get_report(
    kind: Literal["utilization", "expenses", "usage"],
    period_from: date,
    period_to: date,
    vehicle_id: int | None = None,
    format: Literal["json", "pdf", "xlsx"] = "json",
    report_service: IReportService = Depends(get_report_service),
    report_exporter: ReportExporter = Depends(get_report_exporter),
    strategy: ReportStrategy = Depends(get_report_strategy),
    vehicles_service: IVehiclesService = Depends(get_vehicles_service),
):
    report_service.set_strategy(strategy)
    vehicle = None
    if vehicle_id is not None:
        vehicle = await vehicles_service.get_by_id(vehicle_id)
    report = await report_service.generate(period_from, period_to, vehicle)
    if format == "json":
        return report
    report_exporter.set_strategy({"pdf": PdfExport(), "xlsx": ExcelExport()}[format])
    file = report_exporter.export(report)
    return Response(
        content=file.content,
        media_type=file.content_type,
        headers={"Content-Disposition": f'attachment; filename="{file.filename}"'},
    )

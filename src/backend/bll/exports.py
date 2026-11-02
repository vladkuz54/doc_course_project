from abc import ABC, abstractmethod
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path

from openpyxl import Workbook
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from .exceptions import BusinessRuleError

PDF_FONT = "DejaVuSans"
pdfmetrics.registerFont(
    TTFont(PDF_FONT, Path(__file__).parent / "fonts" / "DejaVuSans.ttf")
)


@dataclass
class File:
    filename: str
    content_type: str
    content: bytes


def _period(report):
    return f"{report.period_from:%d.%m.%Y} - {report.period_to:%d.%m.%Y}"


def _filename(report, extension):
    return f"report_{report.period_from}_{report.period_to}.{extension}"


def _columns(report):
    return list(report.rows[0]) if report.rows else []


class ExportStrategy(ABC):
    @abstractmethod
    def export(self, report):
        pass


class PdfExport(ExportStrategy):
    def export(self, report):
        styles = getSampleStyleSheet()
        title = ParagraphStyle("ReportTitle", styles["Title"], fontName=PDF_FONT)
        text = ParagraphStyle("ReportText", styles["Normal"], fontName=PDF_FONT)
        story = [Paragraph(report.title, title), Paragraph(_period(report), text)]
        columns = _columns(report)
        if columns:
            cells = [columns] + [
                ["" if row[c] is None else str(row[c]) for c in columns]
                for row in report.rows
            ]
            table = Table(cells)
            table.setStyle(
                TableStyle(
                    [
                        ("FONTNAME", (0, 0), (-1, -1), PDF_FONT),
                        ("FONTSIZE", (0, 0), (-1, -1), 9),
                        ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                    ]
                )
            )
            story += [Spacer(1, 12), table]
        buffer = BytesIO()
        SimpleDocTemplate(buffer, pagesize=A4, title=report.title).build(story)
        return File(_filename(report, "pdf"), "application/pdf", buffer.getvalue())


class ExcelExport(ExportStrategy):
    def export(self, report):
        workbook = Workbook()
        sheet = workbook.active
        sheet.append([report.title])
        sheet.append([_period(report)])
        columns = _columns(report)
        if columns:
            sheet.append([])
            sheet.append(columns)
            for row in report.rows:
                sheet.append([row[c] for c in columns])
        buffer = BytesIO()
        workbook.save(buffer)
        return File(
            _filename(report, "xlsx"),
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            buffer.getvalue(),
        )


class ReportExporter:
    def __init__(self):
        self._strategy = None

    def set_strategy(self, strategy):
        self._strategy = strategy

    def export(self, report):
        if self._strategy is None:
            raise BusinessRuleError("The export format is not set")
        return self._strategy.export(report)

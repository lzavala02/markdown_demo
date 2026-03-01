"""
Export scaffolding for report outputs.

`Exporter` defines APIs to export summary data to Excel and PDF (AC9).
This module contains only stubs and documentation comments describing
expected behavior and extension points.
"""

from pathlib import Path
from typing import Any


class Exporter:
    """
    Provide export capabilities for summary reports.

    Responsibilities:
    - `export_to_excel`: produce an XLSX file with sheets for each report.
    - `export_to_pdf`: render a printable PDF summary (layout defined by caller).

    Implementations should focus on creating clean, accessible outputs
    suitable for stakeholder distribution.
    """

    def export_to_excel(self, report_data: dict[str, Any], output_path: Path) -> Path:
        """
        Export `report_data` to an Excel workbook saved at `output_path`.

        `report_data` is expected to be a mapping of sheet names to
        serializable tabular structures (e.g., list-of-dicts).

        Returns the path to the written file.
        """
        raise NotImplementedError()

    def export_to_pdf(self, report_data: dict[str, Any], output_path: Path) -> Path:
        """
        Export `report_data` to a PDF file saved at `output_path`.

        PDF generation choices (library, templates) are left to
        implementation. This method should return the path to the PDF.
        """
        raise NotImplementedError()

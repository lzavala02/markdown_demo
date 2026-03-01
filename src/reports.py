"""
Reporting scaffolding.

`ReportGenerator` exposes methods needed by the acceptance criteria for
summary reports and trend calculations. Implementations should accept
consolidated data and produce structures suitable for visualization and
export (no rendering is done in this layer).
"""

from datetime import date
from typing import Any

from .models import ConsolidatedRecord


class ReportGenerator:
    """
    Generate summary data structures from consolidated records.

    Exposed APIs (stubs):
    - `summary_by_production_line` (AC4): counts/issues per line with date filters
    - `defect_trends` (AC5): grouped defect counts over time
    - `shipment_status_for_lot` (AC6): provide shipment status for a given lot id
    """

    def summary_by_production_line(
        self,
        records: list[ConsolidatedRecord],
        start_date: date = None,
        end_date: date = None,
    ) -> dict[str, Any]:
        """
        Return a summary mapping production line IDs to issue counts and
        other metrics. Date filtering should be applied when `start_date`
        and/or `end_date` are provided.
        """
        raise NotImplementedError()

    def defect_trends(
        self, records: list[ConsolidatedRecord], group_by: str = "week"
    ) -> dict[str, Any]:
        """
        Compute defect counts grouped by defect type and time bucket.

        `group_by` may be a time grain such as "day", "week", or "month".
        The return value should be structured for easy plotting by a
        frontend or reporting tool.
        """
        raise NotImplementedError()

    def shipment_status_for_lot(
        self, records: list[ConsolidatedRecord], lot_id: str
    ) -> dict[str, Any]:
        """
        Return a small structured report describing the shipment status of
        `lot_id` (AC6). Include provenance fields and any flags for review.
        """
        raise NotImplementedError()

"""
Data consistency checking scaffolding.

`ConsistencyChecker` identifies discrepancies across sources (AC8).
This module outlines the API used to find missing or inconsistent
records between quality, production, and shipping datasets.
"""
from typing import List, Dict, Any
from .models import ProductionRecord, QualityRecord, ShippingRecord, ConsolidatedRecord


class ConsistencyChecker:
    """
    Inspect consolidated or raw datasets and report inconsistencies.

    Example outputs:
    - list of lots present in quality but missing in shipping
    - ambiguous lot id collisions
    - basic data quality metrics (nulls, unexpected data types)
    """

    def find_discrepancies(self, consolidated: List[ConsolidatedRecord]) -> Dict[str, Any]:
        """
        Analyze `consolidated` records and return a dictionary describing
        discrepancies and suggested actions for review.

        The return structure should be easily serializable to JSON for
        front-end display or downstream processing.
        """
        raise NotImplementedError()

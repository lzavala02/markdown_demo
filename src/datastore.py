"""
In-memory data store scaffolding.

Provides a simple repository interface to hold consolidated records in
memory during processing. This is sufficient for unit testing and
prototyping; persistence/backing stores can be added later as needed.
"""
from typing import List, Optional
from .models import ConsolidatedRecord


class InMemoryDataStore:
    """
    Minimal in-memory store for consolidated records.

    API:
    - `save_records(records)`: replace or extend stored records
    - `query_by_lot(lot_id)`: return list of matching consolidated records
    - `query_by_date_range(start, end)`: return records produced within range
    """

    def __init__(self) -> None:
        # Internal list to keep consolidated records; treating this as
        # the single source of truth for the scope of the scaffolding.
        self._records: List[ConsolidatedRecord] = []

    def save_records(self, records: List[ConsolidatedRecord]) -> None:
        """Save or replace records in the in-memory store."""
        raise NotImplementedError()

    def query_by_lot(self, lot_id: str) -> List[ConsolidatedRecord]:
        """Return consolidated records matching `lot_id` (normalized)."""
        raise NotImplementedError()

    def query_by_date_range(self, start_date, end_date) -> List[ConsolidatedRecord]:
        """Return records whose production date falls inside the inclusive range."""
        raise NotImplementedError()

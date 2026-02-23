"""
Data consolidation scaffolding.

The `DataConsolidator` defines an API to combine production, quality,
and shipping records into `ConsolidatedRecord` instances. Matching
and normalization are delegated to `RecordMatcher` and `LotNormalizer`.
"""
from typing import Iterable, List
from .models import ProductionRecord, QualityRecord, ShippingRecord, ConsolidatedRecord


class DataConsolidator:
    """
    High-level orchestrator to produce a unified dataset per AC2.

    Responsibilities:
    - Accept lists of production, quality, and shipping records.
    - Rely on a `LotNormalizer` to canonicalize lot ids.
    - Use `RecordMatcher` to link records by lot id and/or production date.
    - Return a list of `ConsolidatedRecord` instances.
    """

    def consolidate(
        self,
        production: Iterable[ProductionRecord],
        quality: Iterable[QualityRecord],
        shipping: Iterable[ShippingRecord],
    ) -> List[ConsolidatedRecord]:
        """
        Consolidate the provided iterables into unified records.

        This is a stub method: implementations should call the
        normalizer and matcher components and populate `ConsolidatedRecord`.
        """
        raise NotImplementedError()

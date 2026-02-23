"""
Record matching scaffolding.

`RecordMatcher` provides the API for associating production, quality,
and shipping records using lot id and/or production date per AC2.
"""
from typing import List, Iterable, Tuple
from .models import ProductionRecord, QualityRecord, ShippingRecord


class RecordMatcher:
    """
    Provides methods to match records across sources.

    Matching policies (intent, not implemented here):
    - Primary match by normalized `lot_id`.
    - Secondary match by `production_date` window when lot id is missing.
    - Should expose methods that return matched groups and unmatched items
      so unmatched/ambiguous items can be flagged (AC3).
    """

    def match_by_lot(
        self,
        production: Iterable[ProductionRecord],
        quality: Iterable[QualityRecord],
        shipping: Iterable[ShippingRecord],
    ) -> Tuple[List[Tuple[ProductionRecord, List[QualityRecord], List[ShippingRecord]]], dict]:
        """
        Match records using lot identifier.

        Returns a tuple `(matches, diagnostics)` where `matches` is a list
        of tuples mapping a production record to associated quality and
        shipping records, and `diagnostics` is a dictionary describing
        unmatched or ambiguous items for review.
        """
        raise NotImplementedError()

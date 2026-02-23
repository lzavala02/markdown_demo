"""
Lot ID normalization scaffolding.

This module outlines `LotNormalizer` responsible for detecting and
standardizing inconsistent lot ID formatting and flagging ambiguous
or unmatched identifiers for review (per AC3).
"""
from typing import Tuple, Optional


class LotNormalizer:
    """
    Encapsulates rules for normalizing lot identifiers.

    Responsibilities (scaffolded):
    - Normalize casing, trim whitespace, and remove common punctuation.
    - Detect ambiguous or malformed lot IDs and return markers for
      manual review.
    - Provide a deterministic `normalize` API used by consolidator/matcher.
    """

    def normalize(self, raw_lot_id: str) -> str:
        """
        Convert `raw_lot_id` into a canonical representation.

        Examples of expected behavior (not implemented here):
        - " Lot-123 " -> "LOT-123" or "lot-123" depending on chosen convention
        - remove leading/trailing whitespace and normalize internal spacing

        Returns the normalized lot identifier.
        """
        raise NotImplementedError()

    def is_ambiguous(self, raw_lot_id: str) -> Tuple[bool, Optional[str]]:
        """
        Quick check to determine whether the provided `raw_lot_id` is
        ambiguous (e.g., multiple candidate normalizations or missing parts).

        Returns a tuple `(is_ambiguous, reason)` where `reason` is a
        short human-readable explanation suitable for review workflows.
        """
        raise NotImplementedError()

"""
Domain models for data consolidation scaffolding.

This module defines lightweight dataclass-based models used across the
scaffolded services. These are intentionally minimal: only fields required
to describe the acceptance criteria in the user story are included.

Do not add business logic here — these are plain data holders with
clear field-level comments to help you understand expected shapes.
"""
from dataclasses import dataclass
from datetime import date, datetime
from enum import Enum
from typing import Optional, Dict, Any


class ShipmentStatus(Enum):
    """
    Minimal enum describing shipment lifecycle for a lot.

    - SHIPPED: The lot has completed shipment.
    - PENDING: The lot is scheduled / pending shipping.
    - NOT_SHIPPED: No shipping record exists for the lot.
    """

    SHIPPED = "shipped"
    PENDING = "pending"
    NOT_SHIPPED = "not_shipped"


@dataclass
class ProductionRecord:
    """
    Represents a single row/entry from a production log.

    Fields:
    - `lot_id`: raw lot identifier (may need normalization).
    - `production_date`: when the batch was produced.
    - `line_id`: production line identifier (for line-level summaries).
    - `metadata`: optional free-form map for additional fields present in logs.
    """

    lot_id: str
    production_date: date
    line_id: Optional[str]
    metadata: Dict[str, Any]


@dataclass
class QualityRecord:
    """
    Represents an inspection or quality record.

    Fields:
    - `lot_id`: raw lot identifier present on the inspection file.
    - `inspection_date`: date of inspection.
    - `defect_type`: classification of defect (string in scaffolding).
    - `defect_count`: numeric count of defects found.
    - `metadata`: additional fields from the quality spreadsheet.
    """

    lot_id: str
    inspection_date: date
    defect_type: Optional[str]
    defect_count: Optional[int]
    metadata: Dict[str, Any]


@dataclass
class ShippingRecord:
    """
    Represents a shipping spreadsheet entry.

    Fields:
    - `lot_id`: raw lot identifier listed in shipping file.
    - `ship_date`: date shipped or scheduled.
    - `status`: textual shipping status as found in source file.
    - `metadata`: carrier, tracking number, etc.
    """

    lot_id: str
    ship_date: Optional[date]
    status: Optional[str]
    metadata: Dict[str, Any]


@dataclass
class ConsolidatedRecord:
    """
    Single unified record that combines production, quality, and shipping
    information for a lot. Fields are optional because not every source will
    contain data for each lot.

    Consumers (reports, exporters) should rely on documented fields below.
    """

    lot_id_normalized: str
    production: Optional[ProductionRecord]
    quality: Optional[QualityRecord]
    shipping: Optional[ShippingRecord]
    # computed or derived fields
    shipment_status: ShipmentStatus
    # place to keep provenance info such as source filenames or row numbers
    provenance: Dict[str, Any]

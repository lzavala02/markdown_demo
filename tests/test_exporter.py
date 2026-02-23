"""
Unit test stubs for `src.exporter`.

Verify the export API surface exists; concrete file creation tests should
be added once implementation libraries are chosen.
"""
from pathlib import Path
from src.exporter import Exporter


def test_exporter_api():
    ex = Exporter()
    assert hasattr(ex, "export_to_excel")
    assert hasattr(ex, "export_to_pdf")

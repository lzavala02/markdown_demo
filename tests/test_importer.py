"""
Unit test stubs for `src.importer`.

These tests outline the expected importer behavior: accept file paths
and return typed records. Actual parsing logic is not implemented in
the scaffolding — tests should be implemented alongside concrete
parsing code later.
"""

from src.importer import DataImporter


def test_import_production_logs_csv(tmp_path):
    """
    Create a small CSV file and verify `import_production_logs` parses
    rows into `ProductionRecord` objects with expected fields.
    """
    csv_content = """lot_id,production_date,line_id,notes
LOT-001,2024-02-01,L1,first batch
LOT-002,02/15/2024,L2,second batch
"""

    file_path = tmp_path / "prod_logs.csv"
    file_path.write_text(csv_content, encoding="utf-8")

    di = DataImporter()
    records = di.import_production_logs([file_path])

    assert len(records) == 2
    assert records[0].lot_id == "LOT-001"
    assert str(records[0].production_date) == "2024-02-01"
    assert records[1].lot_id == "LOT-002"
    assert str(records[1].production_date) == "2024-02-15"

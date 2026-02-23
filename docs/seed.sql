ROLLBACK;
BEGIN;

-- 1. Reset all tables
TRUNCATE production_lines, defect_types, lots, production_records, quality_records, shipping_records, lot_id_normalizations, data_discrepancies RESTART IDENTITY CASCADE;

-- 2. Insert Reference Data
INSERT INTO production_lines (line_name) VALUES ('Line 1'), ('Line 2'), ('Line 3'), ('Line 4');
INSERT INTO defect_types (defect_name) VALUES ('Surface Scratch'), ('Dimensional Variance'), ('Missing Component'), ('Material Flaw'), ('Packaging Damage');

-- 3. Insert Lots (Central Registry)
-- Example entry using subquery for the line_id
INSERT INTO lots (business_lot_number, production_date, production_line_id, is_normalized) 
VALUES ('LOT-20260112-001', '2026-01-12', (SELECT production_line_id FROM production_lines WHERE line_name = 'Line 1'), TRUE);

-- 4. Insert Production Records (Includes mandatory record_timestamp)
INSERT INTO production_records (lot_id, production_line_id, production_date, record_timestamp, quantity_produced, status, issue_description) 
VALUES (
    (SELECT lot_id FROM lots WHERE business_lot_number = 'LOT-20260112-001'), 
    (SELECT production_line_id FROM production_lines WHERE line_name = 'Line 1'), 
    '2026-01-12', 
    '2026-01-12 16:00:00', -- Derived timestamp (Swing shift)
    382, 
    'Completed', 
    NULL
);

-- 5. Insert Shipping Records
INSERT INTO shipping_records (lot_id, shipment_date, shipment_status, carrier_info, destination) 
VALUES (
    (SELECT lot_id FROM lots WHERE business_lot_number = 'LOT-20260112-001'), 
    '2026-01-29', 
    'Shipped', 
    'XPO - PRO-812238', 
    'MI'
);

-- 6. Insert Normalization Audit Trail (AC3)
INSERT INTO lot_id_normalizations (original_lot_number, normalized_lot_number, validation_status) 
VALUES ('LOT 20260112 001 ', 'LOT-20260112-001', 'Normalized');

COMMIT;

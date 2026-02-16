-- Reference Table for Production Lines
CREATE TABLE production_lines (
    production_line_id SERIAL PRIMARY KEY,
    line_name VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- Reference Table for Defect Categories
CREATE TABLE defect_types (
    defect_type_id SERIAL PRIMARY KEY,
    defect_name VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- Central Hub for Lot Master Data
CREATE TABLE lots (
    lot_id SERIAL PRIMARY KEY,
    business_lot_number VARCHAR(50) NOT NULL UNIQUE, -- Standardized/Cleaned ID
    production_date DATE NOT NULL,
    production_line_id INTEGER NOT NULL REFERENCES production_lines(production_line_id) ON DELETE CASCADE,
    is_normalized BOOLEAN DEFAULT FALSE NOT NULL,
    data_flag VARCHAR(50), 
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- Indexing for performance (AC10)
CREATE INDEX idx_lots_business_number ON lots(business_lot_number);
CREATE INDEX idx_lots_production_line ON lots(production_line_id);

-- Production Logs (AC1)
CREATE TABLE production_records (
    production_record_id SERIAL PRIMARY KEY,
    lot_id INTEGER NOT NULL REFERENCES lots(lot_id) ON DELETE CASCADE,
    production_line_id INTEGER NOT NULL REFERENCES production_lines(production_line_id) ON DELETE CASCADE,
    production_date DATE NOT NULL,
    record_timestamp TIMESTAMP NOT NULL,
    quantity_produced INTEGER NOT NULL CHECK (quantity_produced >= 0),
    status VARCHAR(50) NOT NULL,
    issue_description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- Quality Inspection Records (AC1)
CREATE TABLE quality_records (
    quality_record_id SERIAL PRIMARY KEY,
    lot_id INTEGER NOT NULL REFERENCES lots(lot_id) ON DELETE CASCADE,
    inspection_date DATE NOT NULL,
    defect_type_id INTEGER NOT NULL REFERENCES defect_types(defect_type_id) ON DELETE CASCADE,
    defect_count INTEGER NOT NULL CHECK (defect_count >= 0),
    inspection_status VARCHAR(20) NOT NULL,
    inspector VARCHAR(100),
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- Shipping Spreadsheets (AC1)
CREATE TABLE shipping_records (
    shipping_record_id SERIAL PRIMARY KEY,
    lot_id INTEGER NOT NULL REFERENCES lots(lot_id) ON DELETE CASCADE,
    shipment_date DATE,
    shipment_status VARCHAR(50) NOT NULL, -- e.g., 'Shipped', 'Pending'
    carrier_info VARCHAR(100),
    destination VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- File Tracking (AC1)
CREATE TABLE data_imports (
    data_import_id SERIAL PRIMARY KEY,
    source_type VARCHAR(50) NOT NULL, -- 'Production', 'Quality', 'Shipping'
    file_name VARCHAR(255) NOT NULL,
    file_format VARCHAR(10) NOT NULL, 
    import_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    import_status VARCHAR(20) NOT NULL -- 'Success', 'Failed'
);

-- Standardization Audit (AC3)
CREATE TABLE lot_id_normalizations (
    lot_id_normalization_id SERIAL PRIMARY KEY,
    original_lot_number VARCHAR(100) NOT NULL,
    normalized_lot_number VARCHAR(50) NOT NULL,
    validation_status VARCHAR(20) NOT NULL, 
    flag_reason TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- Data Discrepancy Tracking (AC8)
CREATE TABLE data_discrepancies (
    data_discrepancy_id SERIAL PRIMARY KEY,
    lot_id INTEGER NOT NULL REFERENCES lots(lot_id) ON DELETE CASCADE,
    missing_in_source VARCHAR(50) NOT NULL,
    description TEXT NOT NULL,
    resolution_status VARCHAR(20) DEFAULT 'Open' NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
);

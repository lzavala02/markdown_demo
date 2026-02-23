"""
Database Module
===============
Handles database connections, schema initialization, and core CRUD operations.

This module manages:
- Database connection pooling and lifecycle
- Schema creation and initialization (AC1, AC2)
- Transaction management with proper resource cleanup
- Index creation for performance (AC10)

Time Complexity: Schema creation is O(n) where n is table count
Space Complexity: O(m) where m is connection pool size (typically constant)

Resource Management:
- All connections are properly closed via context managers or explicit cleanup
- Transactions are committed or rolled back to prevent resource leaks
"""

import psycopg2
from psycopg2 import sql, pool, Error
from contextlib import contextmanager
import logging
from config import Config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Database:
    """
    Database management class handling connections and schema initialization.
    
    This class implements connection pooling to efficiently manage database
    connections across the application. All connections are properly closed
    to prevent resource leaks.
    
    Attributes:
        _connection_pool (psycopg2.pool.SimpleConnectionPool): Pool of DB connections
        _initialized (bool): Flag indicating if schema has been initialized
    """
    
    _connection_pool = None
    _initialized = False
    
    @classmethod
    def initialize(cls):
        """
        Initialize database connection pool and create schema.
        
        Creates a connection pool for efficient connection management.
        If schema doesn't exist, creates all tables and indexes.
        
        Time Complexity: O(n) where n is number of schema statements
        Space Complexity: O(m) where m is pool size (constant)
        
        Raises:
            Error: If database connection or schema creation fails
        """
        if cls._initialized:
            logger.info("Database already initialized")
            return
        
        try:
            # Create connection pool (5-20 connections)
            cls._connection_pool = pool.SimpleConnectionPool(
                minconn=5,
                maxconn=20,
                host=Config.DB_HOST,
                port=Config.DB_PORT,
                database=Config.DB_NAME,
                user=Config.DB_USER,
                password=Config.DB_PASSWORD
            )
            logger.info("Connection pool created successfully")
            
            # Initialize schema
            cls._create_schema()
            cls._initialized = True
            logger.info("Database schema initialized")
            
        except Error as e:
            logger.error(f"Database initialization error: {e}")
            raise
    
    @classmethod
    def _create_schema(cls):
        """
        Creates all database tables, indexes, and constraints.
        
        This method is idempotent - it will safely handle cases where
        tables already exist.
        
        Tables created (addressing AC1-AC3, AC8):
        1. production_lines - Reference table for production lines
        2. defect_types - Reference table for defect categories
        3. lots - Central hub for normalized lot IDs (AC3)
        4. production_records - Production logs (AC1)
        5. quality_records - Quality inspection data (AC1)
        6. shipping_records - Shipping data (AC1)
        7. data_imports - File import tracking (AC1)
        8. lot_id_normalizations - Lot ID sanitization audit (AC3)
        9. data_discrepancies - Data consistency flags (AC8)
        
        Time Complexity: O(n) where n = number of SQL statements
        Space Complexity: O(1) - Single connection used
        
        Raises:
            Error: If schema creation fails
        """
        schema_sql = """
        -- Reference Table for Production Lines (AC4 - filterable by line)
        CREATE TABLE IF NOT EXISTS production_lines (
            production_line_id SERIAL PRIMARY KEY,
            line_name VARCHAR(100) NOT NULL UNIQUE,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
        );

        -- Reference Table for Defect Categories (AC5 - groupable by defect type)
        CREATE TABLE IF NOT EXISTS defect_types (
            defect_type_id SERIAL PRIMARY KEY,
            defect_name VARCHAR(100) NOT NULL UNIQUE,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
        );

        -- Central Hub for Lot Master Data (AC2 - consolidation point)
        CREATE TABLE IF NOT EXISTS lots (
            lot_id SERIAL PRIMARY KEY,
            business_lot_number VARCHAR(50) NOT NULL UNIQUE,
            production_date DATE NOT NULL,
            production_line_id INTEGER NOT NULL REFERENCES production_lines(production_line_id) ON DELETE CASCADE,
            is_normalized BOOLEAN DEFAULT FALSE NOT NULL,
            data_flag VARCHAR(50),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
        );

        -- Indexes for performance optimization (AC10 - response time < 5 seconds)
        CREATE INDEX IF NOT EXISTS idx_lots_business_number ON lots(business_lot_number);
        CREATE INDEX IF NOT EXISTS idx_lots_production_line ON lots(production_line_id);
        CREATE INDEX IF NOT EXISTS idx_lots_production_date ON lots(production_date);

        -- Production Logs (AC1 - multi-source import)
        CREATE TABLE IF NOT EXISTS production_records (
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

        -- Quality Inspection Records (AC1 - multi-source import)
        CREATE TABLE IF NOT EXISTS quality_records (
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

        -- Shipping Spreadsheets (AC1 - multi-source import)
        CREATE TABLE IF NOT EXISTS shipping_records (
            shipping_record_id SERIAL PRIMARY KEY,
            lot_id INTEGER NOT NULL REFERENCES lots(lot_id) ON DELETE CASCADE,
            shipment_date DATE,
            shipment_status VARCHAR(50) NOT NULL,
            carrier_info VARCHAR(100),
            destination VARCHAR(255),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
        );

        -- File Tracking (AC1)
        CREATE TABLE IF NOT EXISTS data_imports (
            data_import_id SERIAL PRIMARY KEY,
            source_type VARCHAR(50) NOT NULL,
            file_name VARCHAR(255) NOT NULL,
            file_format VARCHAR(10) NOT NULL,
            import_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
            import_status VARCHAR(20) NOT NULL
        );

        -- Lot ID Normalization Audit (AC3 - standardization tracking)
        CREATE TABLE IF NOT EXISTS lot_id_normalizations (
            lot_id_normalization_id SERIAL PRIMARY KEY,
            original_lot_number VARCHAR(100) NOT NULL,
            normalized_lot_number VARCHAR(50) NOT NULL,
            validation_status VARCHAR(20) NOT NULL,
            flag_reason TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
        );

        -- Data Discrepancy Tracking (AC8 - consistency checks)
        CREATE TABLE IF NOT EXISTS data_discrepancies (
            data_discrepancy_id SERIAL PRIMARY KEY,
            lot_id INTEGER NOT NULL REFERENCES lots(lot_id) ON DELETE CASCADE,
            missing_in_source VARCHAR(50) NOT NULL,
            description TEXT NOT NULL,
            resolution_status VARCHAR(20) DEFAULT 'Open' NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
        );
        """
        
        conn = None
        try:
            conn = cls._connection_pool.getconn()
            cursor = conn.cursor()
            cursor.execute(schema_sql)
            conn.commit()
            logger.info("Schema created/verified successfully")
        except Error as e:
            if conn:
                conn.rollback()
            logger.error(f"Schema creation error: {e}")
            raise
        finally:
            if conn:
                cursor.close()
                cls._connection_pool.putconn(conn)
    
    @classmethod
    @contextmanager
    def get_connection(cls):
        """
        Context manager for obtaining a database connection from the pool.
        
        Automatically handles connection return to pool and error handling.
        This ensures proper resource cleanup even if exceptions occur.
        
        Usage:
            with Database.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query)
                conn.commit()
        
        Time Complexity: O(1)
        Space Complexity: O(1)
        
        Yields:
            psycopg2.connection: Database connection from pool
        """
        conn = None
        try:
            conn = cls._connection_pool.getconn()
            yield conn
        except Error as e:
            if conn:
                conn.rollback()
            logger.error(f"Database error: {e}")
            raise
        finally:
            if conn:
                cls._connection_pool.putconn(conn)
    
    @classmethod
    def close_all(cls):
        """
        Closes all connections in the pool.
        
        This should be called when shutting down the application
        to properly release all database resources.
        
        Time Complexity: O(n) where n = number of connections in pool
        Space Complexity: O(1)
        """
        if cls._connection_pool:
            cls._connection_pool.closeall()
            logger.info("All database connections closed")
    
    @classmethod
    def execute_query(cls, query_sql, params=None):
        """
        Executes a SELECT query and returns results.
        
        Time Complexity: O(n) where n = result set size
        Space Complexity: O(n) for storing results
        
        Args:
            query_sql (str): SQL SELECT query
            params (tuple): Query parameters for parameterized queries
        
        Returns:
            list: List of tuples representing rows
        
        Raises:
            Error: If query execution fails
        """
        with cls.get_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute(query_sql, params)
                results = cursor.fetchall()
                return results
            finally:
                cursor.close()
    
    @classmethod
    def execute_update(cls, update_sql, params=None):
        """
        Executes an INSERT, UPDATE, or DELETE query.
        
        Automatically commits changes. Returns number of affected rows.
        
        Time Complexity: O(n) where n = rows affected
        Space Complexity: O(1)
        
        Args:
            update_sql (str): SQL INSERT/UPDATE/DELETE query
            params (tuple): Query parameters for parameterized queries
        
        Returns:
            int: Number of rows affected
        
        Raises:
            Error: If query execution fails
        """
        with cls.get_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute(update_sql, params)
                affected_rows = cursor.rowcount
                conn.commit()
                return affected_rows
            finally:
                cursor.close()


if __name__ == '__main__':
    # Test database connection and schema
    try:
        Database.initialize()
        print("✓ Database initialized successfully")
    except Exception as e:
        print(f"✗ Database initialization failed: {e}")
    finally:
        Database.close_all()

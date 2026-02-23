"""
Reporter Module
===============
Generates summary reports and insights from consolidated data.

Implements:
- AC4: Production Line Issues summary with date filtering
- AC5: Defect Type Trends visualization data
- AC6: Batch Shipment Status lookup by lot ID
- AC9: Report export to PDF/Excel

Time Complexity: 
- Query execution: O(n log n) for grouped aggregations
- Report generation: O(n) for iterating results

Space Complexity: O(n) for result sets
"""

import logging
from datetime import datetime, timedelta
from database import Database
from psycopg2 import Error
import json

logger = logging.getLogger(__name__)


class Reporter:
    """
    Generates reports and summary statistics from operational data.
    
    Supports:
    1. Production Line Issues (AC4)
    2. Defect Trends (AC5)
    3. Shipment Status by Lot (AC6)
    4. Export to multiple formats (AC9)
    """
    
    # ===== AC4: Production Line Issues Report =====
    
    @staticmethod
    def get_production_line_issues(date_from, date_to=None):
        """
        Gets summary of issues by production line for given date range.
        
        AC4 - Production Line Issues:
        - Display summary of issues by production line
        - Allow filtering by date range (weekly view)
        
        Time Complexity: O(n log n) for grouping operations
        Space Complexity: O(m) where m = distinct production lines
        
        Args:
            date_from (date): Start of date range
            date_to (date): End of date range (defaults to date_from if not specified)
        
        Returns:
            list: Production line issue summaries
            [
                {
                    'production_line': str,
                    'issue_count': int,
                    'affected_lots': int,
                    'total_quantity': int
                },
                ...
            ]
        """
        if date_to is None:
            date_to = date_from
        
        try:
            query = """
            SELECT 
                pl.line_name,
                COUNT(DISTINCT pr.production_record_id) as total_records,
                COUNT(DISTINCT CASE WHEN pr.issue_description IS NOT NULL THEN pr.production_record_id END) as issue_count,
                COUNT(DISTINCT pr.lot_id) as affected_lots,
                COALESCE(SUM(pr.quantity_produced), 0) as total_quantity
            FROM production_lines pl
            LEFT JOIN lots l ON pl.production_line_id = l.production_line_id
            LEFT JOIN production_records pr ON l.lot_id = pr.lot_id
            WHERE pr.production_date BETWEEN %s AND %s
            GROUP BY pl.line_name
            ORDER BY issue_count DESC
            """
            
            results = Database.execute_query(query, (date_from, date_to))
            
            return [
                {
                    'production_line': r[0],
                    'total_records': r[1],
                    'issue_count': r[2],
                    'affected_lots': r[3],
                    'total_quantity': r[4]
                }
                for r in results
            ]
            
        except Error as e:
            logger.error(f"Failed to get production line issues: {e}")
            return []
    
    # ===== AC5: Defect Type Trends Report =====
    
    @staticmethod
    def get_defect_trends(days_back=30, groupby='day'):
        """
        Gets defect trends over time grouped by defect type.
        
        AC5 - Defect Type Trends:
        - Show defect counts grouped by defect type
        - Support trend visualization over time
        
        Time Complexity: O(n log n) for date-based grouping
        Space Complexity: O(n) for results
        
        Args:
            days_back (int): Number of days to look back (default 30)
            groupby (str): Grouping granularity ('day', 'week', 'month')
        
        Returns:
            list: Defect trends over time
            [
                {
                    'defect_type': str,
                    'date': date,
                    'defect_count': int,
                    'inspection_events': int
                },
                ...
            ]
        """
        try:
            # Determine date grouping function
            if groupby == 'week':
                date_group = "DATE_TRUNC('week', qr.inspection_date)"
            elif groupby == 'month':
                date_group = "DATE_TRUNC('month', qr.inspection_date)"
            else:  # day
                date_group = "qr.inspection_date"
            
            start_date = datetime.now().date() - timedelta(days=days_back)
            
            query = f"""
            SELECT 
                dt.defect_name,
                {date_group}::DATE as period_date,
                SUM(qr.defect_count) as total_defects,
                COUNT(qr.quality_record_id) as inspection_count
            FROM defect_types dt
            JOIN quality_records qr ON dt.defect_type_id = qr.defect_type_id
            WHERE qr.inspection_date >= %s
            GROUP BY dt.defect_name, period_date
            ORDER BY period_date DESC, total_defects DESC
            """
            
            results = Database.execute_query(query, (start_date,))
            
            return [
                {
                    'defect_type': r[0],
                    'date': r[1],
                    'defect_count': r[2],
                    'inspection_events': r[3]
                }
                for r in results
            ]
            
        except Error as e:
            logger.error(f"Failed to get defect trends: {e}")
            return []
    
    @staticmethod
    def get_defect_summary():
        """
        Gets overall defect type summary (counts by type).
        
        Complements AC5 with overall statistics.
        
        Time Complexity: O(n) for aggregation
        Space Complexity: O(m) where m = distinct defect types
        
        Returns:
            list: Defect type summaries
            [
                {
                    'defect_type': str,
                    'total_count': int,
                    'affected_lots': int
                },
                ...
            ]
        """
        try:
            query = """
            SELECT 
                dt.defect_name,
                SUM(qr.defect_count) as total_count,
                COUNT(DISTINCT qr.lot_id) as affected_lots
            FROM defect_types dt
            LEFT JOIN quality_records qr ON dt.defect_type_id = qr.defect_type_id
            GROUP BY dt.defect_name
            ORDER BY total_count DESC
            """
            
            results = Database.execute_query(query, None)
            
            return [
                {
                    'defect_type': r[0],
                    'total_count': r[1] if r[1] else 0,
                    'affected_lots': r[2] if r[2] else 0
                }
                for r in results
            ]
            
        except Error as e:
            logger.error(f"Failed to get defect summary: {e}")
            return []
    
    # ===== AC6: Batch/Lot Shipment Status Report =====
    
    @staticmethod
    def get_shipment_status(lot_id=None, lot_number=None):
        """
        Gets shipment status for a specific lot.
        
        AC6 - Batch Shipment Status:
        - Search by lot ID
        - Display shipment status (Shipped, Pending, Not Shipped)
        
        Time Complexity: O(1) for index lookup + O(n) for detail retrieval
        Space Complexity: O(1)
        
        Args:
            lot_id (int): Database lot ID
            lot_number (str): Business lot number (normalized or raw)
        
        Returns:
            dict: Shipment status or None
            {
                'lot_id': int,
                'lot_number': str,
                'production_date': date,
                'production_line': str,
                'shipment_status': str,
                'shipment_date': date,
                'carrier_info': str,
                'destination': str,
                'has_record': bool
            }
        """
        from data_normalizer import LotIDNormalizer
        
        try:
            # Determine which lookup to use
            if lot_id:
                lot_query = "SELECT lot_id, business_lot_number, production_date, production_line_id FROM lots WHERE lot_id = %s"
                params = (lot_id,)
            elif lot_number:
                normalized = LotIDNormalizer.normalize(lot_number)
                lot_query = "SELECT lot_id, business_lot_number, production_date, production_line_id FROM lots WHERE business_lot_number = %s"
                params = (normalized,)
            else:
                return None
            
            lot_results = Database.execute_query(lot_query, params)
            if not lot_results:
                return None
            
            lot_id, lot_number, prod_date, line_id = lot_results[0]
            
            # Get production line name
            line_query = "SELECT line_name FROM production_lines WHERE production_line_id = %s"
            line_results = Database.execute_query(line_query, (line_id,))
            production_line = line_results[0][0] if line_results else "Unknown"
            
            # Get shipping record
            ship_query = """
            SELECT shipment_status, shipment_date, carrier_info, destination
            FROM shipping_records
            WHERE lot_id = %s
            LIMIT 1
            """
            
            ship_results = Database.execute_query(ship_query, (lot_id,))
            
            if ship_results:
                status, ship_date, carrier, destination = ship_results[0]
                return {
                    'lot_id': lot_id,
                    'lot_number': lot_number,
                    'production_date': prod_date,
                    'production_line': production_line,
                    'shipment_status': status,
                    'shipment_date': ship_date,
                    'carrier_info': carrier,
                    'destination': destination,
                    'has_record': True
                }
            else:
                return {
                    'lot_id': lot_id,
                    'lot_number': lot_number,
                    'production_date': prod_date,
                    'production_line': production_line,
                    'shipment_status': 'Not Shipped',
                    'shipment_date': None,
                    'carrier_info': None,
                    'destination': None,
                    'has_record': False
                }
            
        except Error as e:
            logger.error(f"Failed to get shipment status: {e}")
            return None
    
    @staticmethod
    def get_shipment_status_summary(status_filter=None):
        """
        Gets summary of all shipment statuses with flagged lots.
        
        Complements AC6 with batch shipment overview.
        
        Time Complexity: O(n) for query execution
        Space Complexity: O(n) for results
        
        Args:
            status_filter (str): Optional filter by status
                ('Shipped', 'Pending', 'Not Shipped', None)
        
        Returns:
            dict: Summary statistics
            {
                'shipped': int,
                'pending': int,
                'not_shipped': int,
                'flagged_lots': [list of lot info with flags]
            }
        """
        try:
            # Get shipment status breakdown
            query = """
            SELECT 
                sr.shipment_status,
                COUNT(DISTINCT sr.lot_id) as lot_count
            FROM shipping_records sr
            GROUP BY sr.shipment_status
            """
            
            results = Database.execute_query(query, None)
            
            summary = {
                'shipped': 0,
                'pending': 0,
                'not_shipped': 0,
                'flagged_lots': []
            }
            
            for status, count in results:
                if status == 'Shipped':
                    summary['shipped'] = count
                elif status == 'Pending':
                    summary['pending'] = count
                elif status == 'Not Shipped':
                    summary['not_shipped'] = count
            
            # Also count lots with no shipping record
            no_ship_query = "SELECT COUNT(DISTINCT l.lot_id) FROM lots l WHERE NOT EXISTS (SELECT 1 FROM shipping_records sr WHERE sr.lot_id = l.lot_id)"
            no_ship_results = Database.execute_query(no_ship_query, None)
            if no_ship_results:
                summary['not_shipped'] = (summary.get('not_shipped', 0) or 0) + no_ship_results[0][0]
            
            return summary
            
        except Error as e:
            logger.error(f"Failed to get shipment status summary: {e}")
            return {}
    
    # ===== AC9: Report Export Functions =====
    
    @staticmethod
    def export_production_line_report(date_from, date_to=None, format='json'):
        """
        Exports Production Line Issues report.
        
        AC9 - Report Generation:
        - Generate reports automatically from consolidated data
        - Include production line issue counts
        
        Time Complexity: O(n) for data serialization
        Space Complexity: O(n)
        
        Args:
            date_from (date): Report start date
            date_to (date): Report end date
            format (str): Export format ('json', 'csv')
        
        Returns:
            str: Report data as string
        """
        try:
            issues = Reporter.get_production_line_issues(date_from, date_to)
            
            if format.lower() == 'json':
                # Convert dates to strings for JSON serialization
                report_data = {
                    'report_type': 'Production Line Issues',
                    'date_range': {
                        'from': str(date_from),
                        'to': str(date_to or date_from)
                    },
                    'generated_at': str(datetime.now()),
                    'data': issues
                }
                return json.dumps(report_data, indent=2)
            
            elif format.lower() == 'csv':
                csv_lines = ['Production Line,Issue Count,Affected Lots,Total Quantity Produced']
                for issue in issues:
                    csv_lines.append(
                        f"{issue['production_line']},{issue['issue_count']},"+
                        f"{issue['affected_lots']},{issue['total_quantity']}"
                    )
                return '\n'.join(csv_lines)
            
        except Exception as e:
            logger.error(f"Failed to export production line report: {e}")
            return None
    
    @staticmethod
    def export_defect_trends_report(days_back=30, format='json'):
        """
        Exports Defect Trends report.
        
        AC9 - Report Generation:
        - Include defect trends
        
        Time Complexity: O(n)
        Space Complexity: O(n)
        
        Args:
            days_back (int): Number of days to include
            format (str): Export format ('json', 'csv')
        
        Returns:
            str: Report data as string
        """
        try:
            trends = Reporter.get_defect_trends(days_back)
            summary = Reporter.get_defect_summary()
            
            if format.lower() == 'json':
                report_data = {
                    'report_type': 'Defect Trends',
                    'period_days': days_back,
                    'generated_at': str(datetime.now()),
                    'summary': summary,
                    'trends': [
                        {
                            'defect_type': t['defect_type'],
                            'date': str(t['date']),
                            'defect_count': t['defect_count'],
                            'inspection_events': t['inspection_events']
                        }
                        for t in trends
                    ]
                }
                return json.dumps(report_data, indent=2)
            
            elif format.lower() == 'csv':
                csv_lines = ['Date,Defect Type,Defect Count,Inspection Events']
                for trend in trends:
                    csv_lines.append(
                        f"{trend['date']},{trend['defect_type']},"+
                        f"{trend['defect_count']},{trend['inspection_events']}"
                    )
                return '\n'.join(csv_lines)
        
        except Exception as e:
            logger.error(f"Failed to export defect trends report: {e}")
            return None
    
    @staticmethod
    def export_shipment_status_report(format='json'):
        """
        Exports Shipment Status report for flagged lots.
        
        AC9 - Report Generation:
        - Include shipment status of flagged lots
        
        Time Complexity: O(n)
        Space Complexity: O(n)
        
        Args:
            format (str): Export format ('json', 'csv')
        
        Returns:
            str: Report data as string
        """
        try:
            summary = Reporter.get_shipment_status_summary()
            
            if format.lower() == 'json':
                report_data = {
                    'report_type': 'Shipment Status Summary',
                    'generated_at': str(datetime.now()),
                    'summary': summary
                }
                return json.dumps(report_data, indent=2)
            
            elif format.lower() == 'csv':
                csv_lines = ['Status,Count']
                csv_lines.append(f"Shipped,{summary.get('shipped', 0)}")
                csv_lines.append(f"Pending,{summary.get('pending', 0)}")
                csv_lines.append(f"Not Shipped,{summary.get('not_shipped', 0)}")
                return '\n'.join(csv_lines)
        
        except Exception as e:
            logger.error(f"Failed to export shipment status report: {e}")
            return None


if __name__ == '__main__':
    print("Reporter Module - Generates operational reports and insights")

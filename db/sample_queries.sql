SELECT 
    pl.line_name,
    COUNT(pr.production_record_id) AS total_logs,
    COUNT(pr.issue_description) FILTER (WHERE pr.issue_description IS NOT NULL) AS issue_count,
    COALESCE(SUM(pr.quantity_produced), 0) AS total_qty_produced
FROM production_lines pl
JOIN lots l ON pl.production_line_id = l.production_line_id
LEFT JOIN production_records pr ON l.lot_id = pr.lot_id
WHERE pr.production_date BETWEEN '2026-02-01' AND '2026-02-07' -- Weekly Filter
GROUP BY pl.line_name
ORDER BY issue_count DESC;

SELECT 
    dt.defect_name,
    qr.inspection_date,
    SUM(qr.defect_count) AS daily_defect_total,
    COUNT(qr.quality_record_id) AS inspection_event_count
FROM defect_types dt
JOIN quality_records qr ON dt.defect_type_id = qr.defect_type_id
WHERE qr.inspection_date >= CURRENT_DATE - INTERVAL '30 days' -- Last 30 days
GROUP BY dt.defect_name, qr.inspection_date
ORDER BY qr.inspection_date DESC, daily_defect_total DESC;

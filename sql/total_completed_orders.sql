-- Number of completed orders.
SELECT COUNT(DISTINCT order_id) AS total_completed_orders
FROM fact_orders
WHERE order_status = 'Completed';

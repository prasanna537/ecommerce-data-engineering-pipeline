-- Average order value = completed revenue / completed orders.
SELECT ROUND(COALESCE(SUM(revenue) * 1.0 / NULLIF(COUNT(DISTINCT order_id), 0), 0), 2) AS average_order_value
FROM fact_orders
WHERE order_status = 'Completed';

-- Total revenue from completed orders.
SELECT ROUND(COALESCE(SUM(revenue), 0), 2) AS total_revenue
FROM fact_orders
WHERE order_status = 'Completed';

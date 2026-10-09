-- Revenue and completed orders per calendar month.
SELECT
    d.year_month,
    d.year,
    d.month,
    ROUND(SUM(f.revenue), 2)      AS monthly_revenue,
    COUNT(DISTINCT f.order_id)    AS completed_orders
FROM fact_orders AS f
JOIN dim_date AS d ON d.date_key = f.order_date
WHERE f.order_status = 'Completed'
GROUP BY d.year_month, d.year, d.month
ORDER BY d.year_month;

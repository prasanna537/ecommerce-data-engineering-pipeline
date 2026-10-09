-- Revenue per product category (completed orders).
SELECT
    p.category,
    ROUND(SUM(f.revenue), 2)    AS category_revenue,
    SUM(f.quantity)             AS units_sold,
    COUNT(DISTINCT f.order_id)  AS completed_orders
FROM fact_orders AS f
JOIN dim_product AS p ON p.product_id = f.product_id
WHERE f.order_status = 'Completed'
GROUP BY p.category
ORDER BY category_revenue DESC, p.category;

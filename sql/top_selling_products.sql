-- Top 10 products by units sold (completed orders); revenue breaks ties.
SELECT
    p.product_id,
    p.product_name,
    p.category,
    SUM(f.quantity)          AS units_sold,
    ROUND(SUM(f.revenue), 2) AS product_revenue
FROM fact_orders AS f
JOIN dim_product AS p ON p.product_id = f.product_id
WHERE f.order_status = 'Completed'
GROUP BY p.product_id, p.product_name, p.category
ORDER BY units_sold DESC, product_revenue DESC, p.product_id
LIMIT 10;

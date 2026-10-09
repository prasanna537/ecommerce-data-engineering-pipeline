# Power BI Setup Guide

Power BI Desktop is the main reporting interface of this project. The ETL produces
the CSV files; you build the dashboard from them. This repository does **not** contain a
`.pbix` file, so follow the steps below to create it (about 20 minutes).

## 0. Prerequisites

1. Install [Power BI Desktop](https://powerbi.microsoft.com/desktop/) (free, Windows).
2. From the project root run the pipeline so the CSV files exist:

   ```powershell
   python -m src.etl
   ```

3. Check that `data\exports\` contains the 8 CSV files listed below.

## 1. Files to import

| File (in `data\exports\`) | Role | Rows (default data) |
|---|---|---|
| `fact_orders.csv` | Fact table, one row per order | 518 |
| `dim_customer.csv` | Customer dimension | 146 |
| `dim_product.csv` | Product dimension | 20 |
| `dim_date.csv` | Date dimension | 276 (only dates that have orders) |
| `monthly_revenue.csv`, `category_revenue.csv`, `top_selling_products.csv`, `kpi_summary.csv` | Pre-aggregated SQL results (optional; handy for checking your DAX) | small |

The visuals should use the four model tables plus DAX measures. Use the aggregate files
only to cross-check your numbers.

## 2. Import the data

1. Open Power BI Desktop, then **Home > Get data > Text/CSV**.
2. Select `fact_orders.csv` and click **Transform Data** (not Load).
3. In Power Query confirm the data types:
   - `order_date`: **Date**
   - `quantity`: **Whole number**
   - `unit_price`, `revenue`: **Fixed decimal number**
   - everything else: **Text**
4. Repeat for `dim_customer.csv`, `dim_product.csv`, `dim_date.csv`.
   In `dim_date`, set `date_key` to **Date**, and `year`, `quarter`, `month` to **Whole number**.
5. Click **Close & Apply**.

> **Tip - make the folder path portable:** in Power Query choose **Manage Parameters > New**,
> create a text parameter `DataFolder` = `C:\...\Ecommerce analyst\data\exports\`, and edit each
> query's Source step to use `DataFolder & "fact_orders.csv"`. If the project moves, change one value.

## 3. Build the data model (star schema)

Open **Model view** and create these relationships (drag the column from the fact table to the dimension):

| From (many) | To (one) | Cardinality | Cross-filter |
|---|---|---|---|
| `fact_orders[order_date]` | `dim_date[date_key]` | Many to one (*:1) | Single |
| `fact_orders[customer_id]` | `dim_customer[customer_id]` | Many to one (*:1) | Single |
| `fact_orders[product_id]` | `dim_product[product_id]` | Many to one (*:1) | Single |

```
dim_customer ──┐
dim_product  ──┼──< fact_orders >── dim_date
```

Then tidy the model:

- Select `dim_date[month_name]`, then **Column tools > Sort by column > `month`**.
- Hide `fact_orders[customer_id]`, `[product_id]` and `[order_date]` from report view
  (users should slice by the dimension columns).
- Do not mark `dim_date` as a date table for time-intelligence functions; it only holds dates that
  have orders, and the measures here do not need it.

## 4. Add the DAX measures

1. **Home > Enter data**, create an empty table named `_Measures`, then load it.
2. Right-click `_Measures` > **New measure** and paste each measure from
   [`measures.dax`](measures.dax): **Total Revenue**, **Total Orders**, **Average Order Value**,
   **Monthly Revenue** (plus the optional **Units Sold** and **Order Completion Rate**).
3. Format: Total Revenue / Average Order Value / Monthly Revenue as **Currency**; Total Orders as **Whole number**.

Revenue and orders count `Completed` orders only. This matches the SQL queries.

## 5. Build the dashboard

Suggested single page, "Sales Overview":

| Visual | Fields |
|---|---|
| Card | `Total Revenue` |
| Card | `Total Orders` |
| Card | `Average Order Value` |
| Line chart | X: `dim_date[year_month]`, Y: `Monthly Revenue` |
| Bar chart | Y: `dim_product[category]`, X: `Total Revenue` |
| Bar chart (Top N filter = 10 on `product_name`, by `Units Sold`) | Y: `dim_product[product_name]`, X: `Units Sold` |
| Donut or stacked bar | Legend: `fact_orders[order_status]`, Values: count of `order_id` (uses all statuses, so do not use the completed-only measure here) |
| Slicers | `dim_date[year_month]`, `dim_product[category]` |

## 6. Validate against SQL

With no slicers selected, the cards must equal `data\exports\kpi_summary.csv`
(for the default data: revenue 52,976.19, 381 orders, average order value 139.05).
If they differ, check the data types in step 2 and the relationships in step 3.

## 7. Refresh after re-running the ETL

Run `python -m src.etl`, then click **Home > Refresh** in Power BI Desktop. Close the CSV files
in Excel first, because an open file can block the refresh.

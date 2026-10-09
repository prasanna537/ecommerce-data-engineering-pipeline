# E-Commerce Analytics Platform

A beginner-friendly analytics pipeline: **Python + pandas** generate and clean synthetic order data,
**SQLite + SQL** store and analyse it, and **Microsoft Power BI Desktop** is the dashboard.

## Architecture

```
generate_data.py      extract.py        transform.py            load.py            analytics.py / export.py
synthetic orders  ->  read raw CSV  ->  validate + clean   ->   upsert into   ->    SQL queries -> CSV files
(data/raw)            (as text)         + revenue calc          SQLite (star)      (data/exports)  -> Power BI
                                            |
                                            +--> data/processed/rejected_records.csv (with reasons)
```

| Folder / file | Purpose |
|---|---|
| `src/` | Python modules: `config`, `generate_data`, `extract`, `transform`, `load`, `analytics`, `export`, `etl` (entry point) |
| `sql/` | `schema.sql` (tables) and one `.sql` file per analytics query |
| `data/` | Generated at run time: `raw/`, `processed/`, `exports/`, and `ecommerce.db` (git-ignored) |
| `powerbi/` | `SETUP_GUIDE.md` (step-by-step) and `measures.dax` |
| `reports/` | `etl_run_summary.json` written by each ETL run |
| `tests/` | pytest suite (50 tests) |

**Database model (star schema):** `fact_orders` (one row per order) with `dim_customer`, `dim_product`
and `dim_date`. `fact_orders.order_id` is the primary key.

## Setup (Windows PowerShell)

Requires Python 3.10+ (developed on 3.11).

```powershell
cd "D:\Ecommerce analyst"
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

If activation is blocked, run once: `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`.

## Run the pipeline

```powershell
python -m src.generate_data      # optional: (re)create data\raw\orders_raw.csv (565 rows)
python -m src.etl                # run the full ETL (generates data first if missing)
```

Options for the generator: `python -m src.generate_data --orders 800 --seed 7`.

Outputs:

| File | Content |
|---|---|
| `data\processed\clean_orders.csv` | Valid orders with computed `revenue` |
| `data\processed\rejected_records.csv` | Rejected rows, original values, `source_row`, `rejection_reasons` |
| `data\ecommerce.db` | SQLite database |
| `data\exports\*.csv` | Power BI import files (model tables and SQL analytics results) |
| `reports\etl_run_summary.json` | Row counts and rejection counts per reason |

With the default seed: 565 raw rows, 518 clean, 47 rejected.

## Data quality rules

A row is rejected if it breaks any rule. All reasons are listed, separated by `;`.

| Reason code | Rule |
|---|---|
| `missing_<column>` | A required column is blank or whitespace (all 9 columns are required) |
| `invalid_order_date` | Not a real date in `YYYY-MM-DD` format |
| `invalid_quantity` | Not a whole number greater than 0 (rejects 0, negatives, text, 2.5, NaN, inf) |
| `invalid_unit_price` | Not a finite number greater than 0 |
| `invalid_order_status` | Not one of Completed, Cancelled, Returned, Pending |
| `duplicate_order_id` | `order_id` already seen on an earlier valid row. The first valid row is kept |

Cleaning: text is trimmed; IDs are upper-cased; status is title-cased (so ` ord-9 ` / `completed` become `ORD-9` / `Completed`).

**Revenue:** `revenue = quantity * unit_price`, rounded to cents, for every clean row.
All headline metrics (total revenue, orders, average order value, monthly and category revenue, top products)
count **only `Completed` orders**. Cancelled, Returned and Pending orders stay in the database for analysis.

## Idempotent loading

`fact_orders` uses `order_id` as primary key and loads with `INSERT ... ON CONFLICT DO UPDATE`;
dimensions use upserts or `INSERT OR IGNORE`. Rerunning `python -m src.etl` on the same file leaves
the database identical, and if an order's values change in the raw file, that order is updated, not duplicated.
Loading runs in a single transaction. Orders removed from the raw file are not deleted from the database.

## SQL analytics

Queries live in `sql/`: `total_revenue`, `total_completed_orders`, `monthly_revenue`, `category_revenue`,
`top_selling_products` (top 10 by units), `average_order_value`. Run them from Python with
`src.analytics.run_query(conn, "monthly_revenue")`, or open `data\ecommerce.db` in any SQLite tool.

## Tests

```powershell
python -m pytest -q
```

Tests use temporary folders and never touch your real `data\` folder. They cover data generation,
data-quality rules, revenue calculation, duplicate handling, idempotency and SQL analytics (against a small dataset with hand-calculated answers).

## Power BI dashboard

Power BI Desktop is the main reporting interface. After `python -m src.etl`, follow
[`powerbi/SETUP_GUIDE.md`](powerbi/SETUP_GUIDE.md): import the CSVs from `data\exports\`, create the relationships
(`fact_orders` to `dim_date`, `dim_customer`, `dim_product`, many-to-one), add the measures from
[`powerbi/measures.dax`](powerbi/measures.dax) (Total Revenue, Total Orders, Average Order Value, Monthly Revenue),
and build the visuals. The guide includes a check against `kpi_summary.csv`.

No `.pbix` file is included, and the Power BI steps have not been run in Power BI Desktop by the project author.

## Limitations

- Data is synthetic; each record holds one product, so one order equals one line.
- Batch ETL only (no streaming, Kafka or Airflow).
- `dim_customer` contains only the customer ID, because the source has no customer attributes.

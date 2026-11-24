# Bluestock Mutual Fund Data Dictionary – Day 2

Definitions below are based on the supplied CSV headers and observed values. Source references are the corresponding original CSVs in `data/raw/`. Dates are stored as ISO `YYYY-MM-DD` text in cleaned files.

## fund_master

Source: `data/raw/01_fund_master.csv`; cleaned output: `data/processed/01_fund_master.csv`.

| Column | Data type | Business definition |
|---|---|---|
| `amfi_code` | INTEGER | AMFI scheme identifier |
| `fund_house` | TEXT | Asset management company / fund house |
| `scheme_name` | TEXT | Published mutual fund scheme name |
| `category` | TEXT | Broad scheme category |
| `sub_category` | TEXT | More specific investment category |
| `plan` | TEXT | Regular or Direct plan |
| `launch_date` | TEXT | Launch date (as supplied in source data) |
| `benchmark` | TEXT | Benchmark (as supplied in source data) |
| `expense_ratio_pct` | REAL | Annual expense ratio in percent |
| `exit_load_pct` | REAL | Exit load pct (as supplied in source data) |
| `min_sip_amount` | INTEGER | Min sip amount (as supplied in source data) |
| `min_lumpsum_amount` | INTEGER | Min lumpsum amount (as supplied in source data) |
| `fund_manager` | TEXT | Fund manager (as supplied in source data) |
| `risk_category` | TEXT | Risk category (as supplied in source data) |
| `sebi_category_code` | TEXT | Sebi category code (as supplied in source data) |

## nav_history

Source: `data/raw/02_nav_history.csv`; cleaned output: `data/processed/02_nav_history.csv`.

| Column | Data type | Business definition |
|---|---|---|
| `date` | TEXT | Observation date |
| `nav` | REAL | Net asset value per unit; must be positive |
| `scheme_name` | TEXT | Published mutual fund scheme name |
| `fund_house` | TEXT | Asset management company / fund house |
| `scheme_code` | INTEGER | Scheme code (as supplied in source data) |
| `amfi_code` | INTEGER | AMFI scheme identifier |

## aum_by_fund_house

Source: `data/raw/03_aum_by_fund_house.csv`; cleaned output: `data/processed/03_aum_by_fund_house.csv`.

| Column | Data type | Business definition |
|---|---|---|
| `date` | TEXT | Observation date |
| `fund_house` | TEXT | Asset management company / fund house |
| `aum_lakh_crore` | REAL | Aum lakh crore (as supplied in source data) |
| `aum_crore` | INTEGER | Assets under management in crore rupees |
| `num_schemes` | INTEGER | Num schemes (as supplied in source data) |

## monthly_sip_inflows

Source: `data/raw/04_monthly_sip_inflows.csv`; cleaned output: `data/processed/04_monthly_sip_inflows.csv`.

| Column | Data type | Business definition |
|---|---|---|
| `month` | TEXT | Reporting month in YYYY-MM format |
| `sip_inflow_crore` | INTEGER | Sip inflow crore (as supplied in source data) |
| `active_sip_accounts_crore` | REAL | Active sip accounts crore (as supplied in source data) |
| `new_sip_accounts_lakh` | REAL | New sip accounts lakh (as supplied in source data) |
| `sip_aum_lakh_crore` | REAL | Sip aum lakh crore (as supplied in source data) |
| `yoy_growth_pct` | REAL | Yoy growth pct (as supplied in source data) |

## category_inflows

Source: `data/raw/05_category_inflows.csv`; cleaned output: `data/processed/05_category_inflows.csv`.

| Column | Data type | Business definition |
|---|---|---|
| `month` | TEXT | Reporting month in YYYY-MM format |
| `category` | TEXT | Broad scheme category |
| `net_inflow_crore` | REAL | Net inflow crore (as supplied in source data) |

## industry_folio_count

Source: `data/raw/06_industry_folio_count.csv`; cleaned output: `data/processed/06_industry_folio_count.csv`.

| Column | Data type | Business definition |
|---|---|---|
| `month` | TEXT | Reporting month in YYYY-MM format |
| `total_folios_crore` | REAL | Total folios crore (as supplied in source data) |
| `equity_folios_crore` | REAL | Equity folios crore (as supplied in source data) |
| `debt_folios_crore` | REAL | Debt folios crore (as supplied in source data) |
| `hybrid_folios_crore` | REAL | Hybrid folios crore (as supplied in source data) |
| `others_folios_crore` | REAL | Others folios crore (as supplied in source data) |

## scheme_performance

Source: `data/raw/07_scheme_performance.csv`; cleaned output: `data/processed/07_scheme_performance.csv`.

| Column | Data type | Business definition |
|---|---|---|
| `amfi_code` | INTEGER | AMFI scheme identifier |
| `scheme_name` | TEXT | Published mutual fund scheme name |
| `fund_house` | TEXT | Asset management company / fund house |
| `category` | TEXT | Broad scheme category |
| `plan` | TEXT | Regular or Direct plan |
| `return_1yr_pct` | REAL | One-year return percentage |
| `return_3yr_pct` | REAL | Three-year return percentage |
| `return_5yr_pct` | REAL | Five-year return percentage |
| `benchmark_3yr_pct` | REAL | Benchmark 3yr pct (as supplied in source data) |
| `alpha` | REAL | Alpha (as supplied in source data) |
| `beta` | REAL | Beta (as supplied in source data) |
| `sharpe_ratio` | REAL | Sharpe ratio (as supplied in source data) |
| `sortino_ratio` | REAL | Sortino ratio (as supplied in source data) |
| `std_dev_ann_pct` | REAL | Std dev ann pct (as supplied in source data) |
| `max_drawdown_pct` | REAL | Max drawdown pct (as supplied in source data) |
| `aum_crore` | INTEGER | Assets under management in crore rupees |
| `expense_ratio_pct` | REAL | Annual expense ratio in percent |
| `morningstar_rating` | INTEGER | Morningstar rating (as supplied in source data) |
| `risk_grade` | TEXT | Risk grade (as supplied in source data) |
| `expense_ratio_in_expected_range` | TEXT | Expense ratio in expected range (as supplied in source data) |
| `return_values_numeric_valid` | TEXT | Return values numeric valid (as supplied in source data) |
| `return_anomaly_flag` | TEXT | Return anomaly flag (as supplied in source data) |

## investor_transactions

Source: `data/raw/08_investor_transactions.csv`; cleaned output: `data/processed/08_investor_transactions.csv`.

| Column | Data type | Business definition |
|---|---|---|
| `investor_id` | TEXT | Investor id (as supplied in source data) |
| `transaction_date` | TEXT | Date on which investor transaction occurred |
| `amfi_code` | INTEGER | AMFI scheme identifier |
| `transaction_type` | TEXT | Normalized transaction class: SIP, Lumpsum, or Redemption |
| `amount_inr` | INTEGER | Transaction amount in Indian rupees; must be positive |
| `state` | TEXT | Investor state |
| `city` | TEXT | Investor city |
| `city_tier` | TEXT | City tier (as supplied in source data) |
| `age_group` | TEXT | Age group (as supplied in source data) |
| `gender` | TEXT | Gender (as supplied in source data) |
| `annual_income_lakh` | REAL | Annual income lakh (as supplied in source data) |
| `payment_mode` | TEXT | Payment mode (as supplied in source data) |
| `kyc_status` | TEXT | Know-your-customer verification status; unexpected enum values are flagged |
| `kyc_status_valid` | TEXT | Kyc status valid (as supplied in source data) |
| `transaction_type_valid` | TEXT | Transaction type valid (as supplied in source data) |
| `amount_valid` | TEXT | Amount valid (as supplied in source data) |

## portfolio_holdings

Source: `data/raw/09_portfolio_holdings.csv`; cleaned output: `data/processed/09_portfolio_holdings.csv`.

| Column | Data type | Business definition |
|---|---|---|
| `amfi_code` | INTEGER | AMFI scheme identifier |
| `stock_symbol` | TEXT | Stock symbol (as supplied in source data) |
| `stock_name` | TEXT | Stock name (as supplied in source data) |
| `sector` | TEXT | Sector (as supplied in source data) |
| `weight_pct` | REAL | Portfolio holding weight as a percentage |
| `market_value_cr` | REAL | Market value cr (as supplied in source data) |
| `current_price_inr` | REAL | Current price inr (as supplied in source data) |
| `portfolio_date` | TEXT | Portfolio date (as supplied in source data) |

## benchmark_indices

Source: `data/raw/10_benchmark_indices.csv`; cleaned output: `data/processed/10_benchmark_indices.csv`.

| Column | Data type | Business definition |
|---|---|---|
| `date` | TEXT | Observation date |
| `index_name` | TEXT | Index name (as supplied in source data) |
| `close_value` | REAL | Benchmark index closing level |

## Star-schema tables

- `dim_fund`: one row per AMFI code; primary key `fund_id`, unique business key `amfi_code`.
- `dim_date`: one row per calendar date present in date-bearing source data; primary key `date_id` (YYYYMMDD).
- `fact_nav`: one NAV observation per fund/date; foreign keys to `dim_fund` and `dim_date`.
- `fact_transactions`: one investor transaction; foreign keys to `dim_fund` (nullable when source AMFI code has no master match) and `dim_date`.
- `fact_performance`: one performance snapshot per fund; foreign key to `dim_fund`.
- `fact_aum`: one fund-house AUM observation per date; foreign key to `dim_date`; fund house is retained as a descriptive attribute because source grain is fund-house/date.

All ten cleaned datasets are also loaded as `stg_*` tables in SQLite so the supplied source rows remain queryable even when a row cannot be linked to a star-schema dimension.

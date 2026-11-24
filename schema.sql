PRAGMA foreign_keys = ON;
CREATE TABLE IF NOT EXISTS dim_fund (
  fund_id INTEGER PRIMARY KEY AUTOINCREMENT,
  amfi_code INTEGER NOT NULL UNIQUE,
  scheme_name TEXT NOT NULL,
  fund_house TEXT,
  category TEXT,
  sub_category TEXT,
  plan TEXT,
  benchmark TEXT,
  expense_ratio_pct REAL,
  risk_category TEXT
);
CREATE TABLE IF NOT EXISTS dim_date (
  date_id INTEGER PRIMARY KEY,
  full_date TEXT NOT NULL UNIQUE,
  year INTEGER NOT NULL,
  quarter INTEGER NOT NULL,
  month INTEGER NOT NULL,
  month_name TEXT NOT NULL,
  day INTEGER NOT NULL,
  day_of_week TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS fact_nav (
  nav_id INTEGER PRIMARY KEY AUTOINCREMENT,
  fund_id INTEGER NOT NULL,
  date_id INTEGER NOT NULL,
  nav REAL NOT NULL CHECK(nav > 0),
  FOREIGN KEY(fund_id) REFERENCES dim_fund(fund_id),
  FOREIGN KEY(date_id) REFERENCES dim_date(date_id),
  UNIQUE(fund_id,date_id)
);
CREATE TABLE IF NOT EXISTS fact_transactions (
  transaction_id INTEGER PRIMARY KEY AUTOINCREMENT,
  investor_id TEXT,
  fund_id INTEGER,
  date_id INTEGER NOT NULL,
  transaction_type TEXT NOT NULL CHECK(transaction_type IN ('SIP','Lumpsum','Redemption')),
  amount_inr REAL NOT NULL CHECK(amount_inr > 0),
  state TEXT,
  city TEXT,
  city_tier TEXT,
  age_group TEXT,
  gender TEXT,
  payment_mode TEXT,
  kyc_status TEXT,
  FOREIGN KEY(fund_id) REFERENCES dim_fund(fund_id),
  FOREIGN KEY(date_id) REFERENCES dim_date(date_id)
);
CREATE TABLE IF NOT EXISTS fact_performance (
  performance_id INTEGER PRIMARY KEY AUTOINCREMENT,
  fund_id INTEGER NOT NULL,
  return_1yr_pct REAL, return_3yr_pct REAL, return_5yr_pct REAL,
  benchmark_3yr_pct REAL, alpha REAL, beta REAL, sharpe_ratio REAL,
  sortino_ratio REAL, std_dev_ann_pct REAL, max_drawdown_pct REAL,
  aum_crore REAL, expense_ratio_pct REAL,
  FOREIGN KEY(fund_id) REFERENCES dim_fund(fund_id), UNIQUE(fund_id)
);
CREATE TABLE IF NOT EXISTS fact_aum (
  aum_id INTEGER PRIMARY KEY AUTOINCREMENT,
  date_id INTEGER NOT NULL,
  fund_house TEXT NOT NULL,
  aum_lakh_crore REAL,
  aum_crore REAL,
  num_schemes INTEGER,
  FOREIGN KEY(date_id) REFERENCES dim_date(date_id), UNIQUE(date_id,fund_house)
);

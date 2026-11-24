from pathlib import Path
import pandas as pd, numpy as np, sqlite3, json, re
from sqlalchemy import create_engine, text

ROOT = Path(__file__).resolve().parent
RAW = ROOT / 'data' / 'raw'
OUT = ROOT / 'data' / 'processed'
OUT.mkdir(parents=True, exist_ok=True)
DB = ROOT / 'bluestock_mf.db'

FILES = {
 'fund_master':'01_fund_master.csv', 'aum_by_fund_house':'03_aum_by_fund_house.csv',
 'monthly_sip_inflows':'04_monthly_sip_inflows.csv', 'category_inflows':'05_category_inflows.csv',
 'industry_folio_count':'06_industry_folio_count.csv', 'scheme_performance':'07_scheme_performance.csv',
 'investor_transactions':'08_investor_transactions.csv', 'portfolio_holdings':'09_portfolio_holdings.csv',
 'benchmark_indices':'10_benchmark_indices.csv', 'nav_history':'02_nav_history.csv'
}

# Locate source files by their normalized suffixes; source copies remain unchanged.
def source_path(key):
    p = RAW / FILES[key]
    if p.exists(): return p
    candidates = list(RAW.glob('*' + FILES[key].split('_',1)[-1]))
    if candidates: return candidates[0]
    raise FileNotFoundError(f'Missing source CSV for {key}: expected {FILES[key]} in {RAW}')

def read(key):
    return pd.read_csv(source_path(key), low_memory=False)

def parse_dates(s):
    # Parse ISO dates explicitly; parse remaining formats as day-first.
    raw = s.astype('string').str.strip()
    out = pd.Series(pd.NaT, index=s.index, dtype='datetime64[ns]')
    iso = raw.str.match(r'^\d{4}-\d{2}-\d{2}$', na=False)
    out.loc[iso] = pd.to_datetime(raw.loc[iso], format='%Y-%m-%d', errors='coerce')
    out.loc[~iso] = pd.to_datetime(raw.loc[~iso], errors='coerce', dayfirst=True, format='mixed')
    return out

def write(df, name):
    df.to_csv(OUT / name, index=False)
    return len(df)

log = {}
# 1. Fund master: preserve all source fields, normalize key/date/numeric fields.
fund = read('fund_master')
fund['amfi_code'] = pd.to_numeric(fund['amfi_code'], errors='coerce').astype('Int64')
if 'launch_date' in fund: fund['launch_date'] = parse_dates(fund['launch_date']).dt.strftime('%Y-%m-%d')
for c in ['expense_ratio_pct','exit_load_pct','min_sip_amount','min_lumpsum_amount']:
    if c in fund: fund[c] = pd.to_numeric(fund[c], errors='coerce')
fund = fund.drop_duplicates(subset=['amfi_code'], keep='first')
log['fund_master'] = {'rows':len(fund),'duplicate_amfi_codes_removed':int(read('fund_master').shape[0]-len(fund))}

# 2. NAV: date, numeric NAV, key validation, dedupe, forward fill within scheme.
nav = read('nav_history')
code_col = 'amfi_code' if 'amfi_code' in nav.columns else 'scheme_code'
nav['amfi_code'] = pd.to_numeric(nav[code_col], errors='coerce').astype('Int64')
nav['date'] = parse_dates(nav['date'])
nav['nav'] = pd.to_numeric(nav['nav'], errors='coerce')
nav = nav.sort_values(['amfi_code','date'])
nav = nav.drop_duplicates(subset=['amfi_code','date'], keep='last')
invalid_nav = int((nav['nav'].notna() & (nav['nav'] <= 0)).sum())
nav.loc[nav['nav'] <= 0, 'nav'] = np.nan
nav['nav'] = nav.groupby('amfi_code', dropna=False)['nav'].ffill()
nav = nav[nav['date'].notna() & nav['amfi_code'].notna() & nav['nav'].notna()]
nav['date'] = nav['date'].dt.strftime('%Y-%m-%d')
log['nav_history'] = {'rows':len(nav),'invalid_nonpositive_nav_set_missing':invalid_nav,'note':'Forward-fill applies to missing NAV values on existing scheme/date rows; no synthetic weekend/holiday dates are invented.'}

# 3. Investor transactions.
tx = read('investor_transactions')
tx['transaction_date'] = parse_dates(tx['transaction_date'])
tx['amfi_code'] = pd.to_numeric(tx['amfi_code'], errors='coerce').astype('Int64')
tx['amount_inr'] = pd.to_numeric(tx['amount_inr'], errors='coerce')
raw_types = tx['transaction_type'].astype(str).str.strip().str.lower()
map_types = {'sip':'SIP','systematic investment plan':'SIP','lumpsum':'Lumpsum','lump sum':'Lumpsum','lump-sum':'Lumpsum','redemption':'Redemption'}
tx['transaction_type'] = raw_types.map(map_types)
valid_kyc = {'Verified','Pending'}
tx['kyc_status'] = tx['kyc_status'].astype(str).str.strip().str.title()
# Keep source values but flag unexpected statuses for review.
tx['kyc_status_valid'] = tx['kyc_status'].isin(valid_kyc)
tx['transaction_type_valid'] = tx['transaction_type'].notna()
tx['amount_valid'] = tx['amount_inr'].gt(0)
tx = tx[tx['transaction_date'].notna() & tx['amount_valid'] & tx['transaction_type_valid']].copy()
tx['transaction_date'] = tx['transaction_date'].dt.strftime('%Y-%m-%d')
log['investor_transactions'] = {'rows':len(tx),'invalid_or_unmapped_transaction_types_removed':int((~raw_types.isin(map_types)).sum()),'nonpositive_or_missing_amounts_removed':int((~pd.to_numeric(read('investor_transactions')['amount_inr'],errors='coerce').gt(0)).sum()),'unexpected_kyc_status_rows_retained_and_flagged':int((~tx['kyc_status_valid']).sum()),'accepted_kyc_enum':sorted(valid_kyc)}

# 4. Scheme performance.
perf = read('scheme_performance')
perf['amfi_code'] = pd.to_numeric(perf['amfi_code'], errors='coerce').astype('Int64')
return_cols = [c for c in perf.columns if re.match(r'return_.*_pct$',c) or c in ['benchmark_3yr_pct','alpha','beta','sharpe_ratio','sortino_ratio','std_dev_ann_pct','max_drawdown_pct']]
for c in return_cols: perf[c] = pd.to_numeric(perf[c], errors='coerce')
perf['expense_ratio_pct'] = pd.to_numeric(perf['expense_ratio_pct'], errors='coerce')
perf['expense_ratio_in_expected_range'] = perf['expense_ratio_pct'].between(0.1,2.5,inclusive='both')
perf['return_values_numeric_valid'] = perf[return_cols].notna().all(axis=1) if return_cols else True
# Flag statistical outliers using broad absolute-return threshold; never silently delete them.
retcols=[c for c in return_cols if c.startswith('return_')]
perf['return_anomaly_flag'] = perf[retcols].abs().gt(100).any(axis=1) if retcols else False
log['scheme_performance']={'rows':len(perf),'non_numeric_return_or_risk_values':int((~perf['return_values_numeric_valid']).sum()),'expense_ratio_out_of_0_1_to_2_5_pct_range':int((~perf['expense_ratio_in_expected_range']).sum()),'return_anomaly_rows_abs_return_over_100_pct':int(perf['return_anomaly_flag'].sum())}

# Remaining six datasets: consistent date/numeric cleanup and duplicate removal.
aum=read('aum_by_fund_house'); aum['date']=parse_dates(aum['date']).dt.strftime('%Y-%m-%d')
for c in ['aum_lakh_crore','aum_crore','num_schemes']: aum[c]=pd.to_numeric(aum[c],errors='coerce')
aum=aum.drop_duplicates()
sip=read('monthly_sip_inflows'); sip['month']=sip['month'].astype(str).str.strip()
for c in sip.columns:
 if c!='month': sip[c]=pd.to_numeric(sip[c],errors='coerce')
sip=sip.drop_duplicates(subset=['month'],keep='last')
cat=read('category_inflows'); cat['month']=cat['month'].astype(str).str.strip(); cat['net_inflow_crore']=pd.to_numeric(cat['net_inflow_crore'],errors='coerce'); cat=cat.drop_duplicates()
folio=read('industry_folio_count'); folio['month']=folio['month'].astype(str).str.strip()
for c in folio.columns:
 if c!='month': folio[c]=pd.to_numeric(folio[c],errors='coerce')
folio=folio.drop_duplicates(subset=['month'],keep='last')
hold=read('portfolio_holdings'); hold['amfi_code']=pd.to_numeric(hold['amfi_code'],errors='coerce').astype('Int64'); hold['portfolio_date']=parse_dates(hold['portfolio_date']).dt.strftime('%Y-%m-%d')
for c in ['weight_pct','market_value_cr','current_price_inr']: hold[c]=pd.to_numeric(hold[c],errors='coerce')
hold=hold.drop_duplicates(subset=['amfi_code','stock_symbol','portfolio_date'],keep='last')
bench=read('benchmark_indices'); bench['date']=parse_dates(bench['date']).dt.strftime('%Y-%m-%d'); bench['close_value']=pd.to_numeric(bench['close_value'],errors='coerce'); bench=bench.drop_duplicates(subset=['date','index_name'],keep='last')

cleaned={'fund_master':fund,'nav_history':nav,'aum_by_fund_house':aum,'monthly_sip_inflows':sip,'category_inflows':cat,'industry_folio_count':folio,'scheme_performance':perf,'investor_transactions':tx,'portfolio_holdings':hold,'benchmark_indices':bench}
for k,df in cleaned.items(): log.setdefault(k,{})['output_rows']=write(df,FILES[k])

# SQL schema is stored separately and also used to create relational star tables.
schema = r'''PRAGMA foreign_keys = ON;
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
'''
(ROOT/'schema.sql').write_text(schema,encoding='utf-8')

# Analytical queries: requested six + four useful additional analyses.
queries = r'''-- 1. Top 5 funds by AUM (scheme-level performance snapshot)
SELECT f.amfi_code, f.scheme_name, p.aum_crore
FROM fact_performance p JOIN dim_fund f USING(fund_id)
ORDER BY p.aum_crore DESC LIMIT 5;

-- 2. Average NAV per month
SELECT substr(d.full_date,1,7) AS month, ROUND(AVG(n.nav),4) AS avg_nav
FROM fact_nav n JOIN dim_date d USING(date_id)
GROUP BY month ORDER BY month;

-- 3. SIP year-on-year growth from the monthly SIP dataset
SELECT month, sip_inflow_crore, yoy_growth_pct
FROM stg_monthly_sip_inflows ORDER BY month;

-- 4. Transactions by state
SELECT state, COUNT(*) AS transaction_count, ROUND(SUM(amount_inr),2) AS total_amount_inr
FROM fact_transactions GROUP BY state ORDER BY total_amount_inr DESC;

-- 5. Funds with expense ratio below 1 percent
SELECT amfi_code, scheme_name, expense_ratio_pct
FROM dim_fund WHERE expense_ratio_pct < 1 ORDER BY expense_ratio_pct;

-- 6. Monthly transaction volume and value by transaction type
SELECT substr(d.full_date,1,7) AS month, t.transaction_type, COUNT(*) AS txn_count, SUM(t.amount_inr) AS amount_inr
FROM fact_transactions t JOIN dim_date d USING(date_id)
GROUP BY month,t.transaction_type ORDER BY month,t.transaction_type;

-- 7. Top 10 states by SIP amount
SELECT state, SUM(amount_inr) AS sip_amount_inr
FROM fact_transactions WHERE transaction_type='SIP'
GROUP BY state ORDER BY sip_amount_inr DESC LIMIT 10;

-- 8. Fund performance versus benchmark (3-year excess return)
SELECT f.scheme_name, p.return_3yr_pct, p.benchmark_3yr_pct,
       ROUND(p.return_3yr_pct-p.benchmark_3yr_pct,2) AS excess_return_pct
FROM fact_performance p JOIN dim_fund f USING(fund_id)
WHERE p.return_3yr_pct IS NOT NULL AND p.benchmark_3yr_pct IS NOT NULL
ORDER BY excess_return_pct DESC;

-- 9. Portfolio sector exposure by scheme
SELECT h.amfi_code, f.scheme_name, h.sector, ROUND(SUM(h.weight_pct),2) AS sector_weight_pct
FROM stg_portfolio_holdings h LEFT JOIN dim_fund f ON f.amfi_code=h.amfi_code
GROUP BY h.amfi_code,f.scheme_name,h.sector ORDER BY h.amfi_code,sector_weight_pct DESC;

-- 10. Latest AUM by fund house
SELECT a.fund_house, a.aum_crore, d.full_date
FROM fact_aum a JOIN dim_date d USING(date_id)
WHERE d.full_date=(SELECT MAX(full_date) FROM dim_date)
ORDER BY a.aum_crore DESC;
'''
(ROOT/'queries.sql').write_text(queries,encoding='utf-8')

# Create database, retain all 10 cleaned files as staging tables, then load star schema.
if DB.exists(): DB.unlink()
engine=create_engine(f'sqlite:///{DB}')
with engine.begin() as conn:
    for stmt in [s.strip() for s in schema.split(';') if s.strip()]: conn.exec_driver_sql(stmt)
for k,df in cleaned.items(): df.to_sql('stg_'+k,engine,if_exists='replace',index=False)
# Populate dimensions from the cleaned source data.
fund.to_sql('_fund_tmp',engine,if_exists='replace',index=False)
with engine.begin() as c:
    for r in fund.to_dict('records'):
        c.execute(text('''INSERT OR IGNORE INTO dim_fund(amfi_code,scheme_name,fund_house,category,sub_category,plan,benchmark,expense_ratio_pct,risk_category)
        VALUES(:amfi_code,:scheme_name,:fund_house,:category,:sub_category,:plan,:benchmark,:expense_ratio_pct,:risk_category)'''),r)
# Collect all usable dates across date-bearing datasets.
dates=set()
for df,col in [(nav,'date'),(tx,'transaction_date'),(aum,'date'),(bench,'date')]: dates.update(x for x in df[col].dropna().astype(str) if re.match(r'^\d{4}-\d{2}-\d{2}$',x))
for r in sorted(dates):
    dt=pd.Timestamp(r); date_id=int(dt.strftime('%Y%m%d'))
    with engine.begin() as c:
        c.execute(text('''INSERT OR IGNORE INTO dim_date(date_id,full_date,year,quarter,month,month_name,day,day_of_week)
        VALUES(:id,:date,:year,:quarter,:month,:month_name,:day,:dow)'''),{'id':date_id,'date':r,'year':dt.year,'quarter':dt.quarter,'month':dt.month,'month_name':dt.strftime('%B'),'day':dt.day,'dow':dt.strftime('%A')})
with engine.begin() as c:
    # NAV rows only for AMFI codes represented in dim_fund.
    c.exec_driver_sql('''INSERT OR IGNORE INTO fact_nav(fund_id,date_id,nav)
      SELECT f.fund_id, CAST(REPLACE(n.date,'-','') AS INTEGER), n.nav
      FROM stg_nav_history n JOIN dim_fund f ON f.amfi_code=n.amfi_code
      WHERE n.nav>0''')
    c.exec_driver_sql('''INSERT INTO fact_transactions(investor_id,fund_id,date_id,transaction_type,amount_inr,state,city,city_tier,age_group,gender,payment_mode,kyc_status)
      SELECT t.investor_id,f.fund_id,CAST(REPLACE(t.transaction_date,'-','') AS INTEGER),t.transaction_type,t.amount_inr,t.state,t.city,t.city_tier,t.age_group,t.gender,t.payment_mode,t.kyc_status
      FROM stg_investor_transactions t LEFT JOIN dim_fund f ON f.amfi_code=t.amfi_code
      WHERE t.amount_inr>0 AND t.transaction_type IN ('SIP','Lumpsum','Redemption')''')
    c.exec_driver_sql('''INSERT OR IGNORE INTO fact_performance(fund_id,return_1yr_pct,return_3yr_pct,return_5yr_pct,benchmark_3yr_pct,alpha,beta,sharpe_ratio,sortino_ratio,std_dev_ann_pct,max_drawdown_pct,aum_crore,expense_ratio_pct)
      SELECT f.fund_id,p.return_1yr_pct,p.return_3yr_pct,p.return_5yr_pct,p.benchmark_3yr_pct,p.alpha,p.beta,p.sharpe_ratio,p.sortino_ratio,p.std_dev_ann_pct,p.max_drawdown_pct,p.aum_crore,p.expense_ratio_pct
      FROM stg_scheme_performance p JOIN dim_fund f ON f.amfi_code=p.amfi_code''')
    c.exec_driver_sql('''INSERT OR IGNORE INTO fact_aum(date_id,fund_house,aum_lakh_crore,aum_crore,num_schemes)
      SELECT CAST(REPLACE(date,'-','') AS INTEGER),fund_house,aum_lakh_crore,aum_crore,num_schemes FROM stg_aum_by_fund_house''')
# Remove helper table.
with engine.begin() as c: c.exec_driver_sql('DROP TABLE IF EXISTS _fund_tmp')

# Counts: source, processed and loaded staging/fact.
counts={}
with engine.connect() as c:
    for k,df in cleaned.items():
        counts[k]={'cleaned_csv_rows':len(df),'sqlite_staging_rows':c.exec_driver_sql(f'SELECT COUNT(*) FROM stg_{k}').scalar_one()}
    for t in ['dim_fund','dim_date','fact_nav','fact_transactions','fact_performance','fact_aum']:
        counts[t]={'rows':c.exec_driver_sql(f'SELECT COUNT(*) FROM {t}').scalar_one()}
    counts['fact_nav']['source_clean_rows']=len(nav)
    counts['fact_transactions']['source_clean_rows']=len(tx)
    counts['fact_performance']['source_clean_rows']=len(perf)
    counts['fact_aum']['source_clean_rows']=len(aum)
(ROOT/'reports'/'day2_validation_summary.json').write_text(json.dumps({'cleaning':log,'database_counts':counts},indent=2,default=str),encoding='utf-8')

# Data dictionary generated from actual cleaned columns and inferred dtypes.
def dtype(s):
    if pd.api.types.is_integer_dtype(s): return 'INTEGER'
    if pd.api.types.is_float_dtype(s): return 'REAL'
    return 'TEXT'
with open(ROOT/'data_dictionary.md','w',encoding='utf-8') as f:
    f.write('# Bluestock Mutual Fund Data Dictionary – Day 2\n\n')
    f.write('Definitions below are based on the supplied CSV headers and observed values. Source references are the corresponding original CSVs in `data/raw/`. Dates are stored as ISO `YYYY-MM-DD` text in cleaned files.\n\n')
    descriptions={
      'amfi_code':'AMFI scheme identifier','scheme_name':'Published mutual fund scheme name','fund_house':'Asset management company / fund house','category':'Broad scheme category','sub_category':'More specific investment category','plan':'Regular or Direct plan','date':'Observation date','nav':'Net asset value per unit; must be positive','transaction_date':'Date on which investor transaction occurred','transaction_type':'Normalized transaction class: SIP, Lumpsum, or Redemption','amount_inr':'Transaction amount in Indian rupees; must be positive','kyc_status':'Know-your-customer verification status; unexpected enum values are flagged','expense_ratio_pct':'Annual expense ratio in percent','return_1yr_pct':'One-year return percentage','return_3yr_pct':'Three-year return percentage','return_5yr_pct':'Five-year return percentage','aum_crore':'Assets under management in crore rupees','month':'Reporting month in YYYY-MM format','state':'Investor state','city':'Investor city','weight_pct':'Portfolio holding weight as a percentage','close_value':'Benchmark index closing level'
    }
    for k,df in cleaned.items():
      f.write(f'## {k}\n\nSource: `data/raw/{FILES[k]}`; cleaned output: `data/processed/{FILES[k]}`.\n\n| Column | Data type | Business definition |\n|---|---|---|\n')
      for col in df.columns:
        f.write(f'| `{col}` | {dtype(df[col])} | {descriptions.get(col, col.replace("_"," ").capitalize()+" (as supplied in source data)")} |\n')
      f.write('\n')
    f.write('## Star-schema tables\n\n- `dim_fund`: one row per AMFI code; primary key `fund_id`, unique business key `amfi_code`.\n- `dim_date`: one row per calendar date present in date-bearing source data; primary key `date_id` (YYYYMMDD).\n- `fact_nav`: one NAV observation per fund/date; foreign keys to `dim_fund` and `dim_date`.\n- `fact_transactions`: one investor transaction; foreign keys to `dim_fund` (nullable when source AMFI code has no master match) and `dim_date`.\n- `fact_performance`: one performance snapshot per fund; foreign key to `dim_fund`.\n- `fact_aum`: one fund-house AUM observation per date; foreign key to `dim_date`; fund house is retained as a descriptive attribute because source grain is fund-house/date.\n\nAll ten cleaned datasets are also loaded as `stg_*` tables in SQLite so the supplied source rows remain queryable even when a row cannot be linked to a star-schema dimension.\n')

print(json.dumps({'cleaned_files':{k:len(v) for k,v in cleaned.items()},'counts':counts},indent=2))

# Bluestock Mutual Fund Analytics – Week 2 Day 2

## Deliverables
- `data/processed/`: 10 cleaned CSV datasets
- `bluestock_mf.db`: SQLite database containing the six requested star-schema tables plus ten `stg_*` tables preserving each cleaned dataset
- `schema.sql`: table definitions, primary keys, foreign keys and integrity constraints
- `queries.sql`: 10 analytical SQL queries
- `data_dictionary.md`: column-level definitions and source references
- `day2_pipeline.py`: reproducible cleaning, validation and database-loading pipeline
- `reports/day2_validation_summary.json`: row counts and quality checks

## Setup (Windows PowerShell)
```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python day2_pipeline.py
```

The pipeline reads the ten original files from `data/raw/`, writes cleaned outputs to `data/processed/`, recreates `bluestock_mf.db`, and writes a validation summary. It uses `pandas`, `SQLAlchemy`, and SQLite.

## Data-quality decisions
- NAV rows are sorted by AMFI code and date, deduplicated by scheme/date, non-positive NAV values are set missing, and remaining missing NAV values are forward-filled within each scheme. It does not invent weekend/holiday dates that are absent from the source.
- Transaction types are normalized to `SIP`, `Lumpsum`, and `Redemption`. Invalid dates, unknown transaction types, and non-positive amounts are excluded. KYC statuses outside the source dataset's observed enum (`Verified`, `Pending`) are retained with a `kyc_status_valid` flag.
- Performance return and risk metrics are converted to numeric. Values outside a broad ±100% return threshold and expense ratios outside 0.1–2.5% are flagged, not deleted.
- All ten cleaned CSVs are loaded into SQLite staging tables (`stg_*`). Fact tables contain records that can be joined to the required dimensions; nullable `fund_id` in transactions preserves transactions whose AMFI code is absent from the master dimension.

## Git
```powershell
git add data/processed bluestock_mf.db schema.sql queries.sql data_dictionary.md day2_pipeline.py requirements.txt reports README.md
git commit -m "Day 2: Cleaned data + SQLite DB loaded"
git push origin main
```

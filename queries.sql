-- 1. Top 5 funds by AUM (scheme-level performance snapshot)
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
WHERE d.full_date=(SELECT MAX(d2.full_date) FROM fact_aum a2 JOIN dim_date d2 USING(date_id))
ORDER BY a.aum_crore DESC;

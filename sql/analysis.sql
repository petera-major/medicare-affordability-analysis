-- Most expensive states 
SELECT state_name, allowed_charges_per_person
FROM cms_charges
ORDER BY allowed_charges_per_person DESC
LIMIT 5;

-- Cheapest states 
SELECT state_name, allowed_charges_per_person
FROM cms_charges
ORDER BY allowed_charges_per_person ASC
LIMIT 5;

-- Top 5 richest states for single moms (2024)
SELECT state_name, median_income
FROM acs_incomes
WHERE year = 2024 AND income_group = 'Female_no_spouse_kids'
ORDER BY median_income DESC
LIMIT 5;

-- Bottom 5 poorest states for single moms (2024)
SELECT state_name, median_income
FROM acs_incomes
WHERE year = 2024 AND income_group = 'Female_no_spouse_kids'
ORDER BY median_income ASC
LIMIT 5;

-- all groups 2024 incomes
SELECT 
  c.state_name,
  a.income_group,
  c.allowed_charges_per_person,
  a.median_income,
  ROUND((c.allowed_charges_per_person / a.median_income) * 100, 2) AS affordability_index
FROM cms_charges c
JOIN acs_incomes a
  ON c.state_code = a.state_code
WHERE a.year = 2024
ORDER BY affordability_index DESC;

-- Most burdensome states for single moms
SELECT 
  c.state_name, 
  c.allowed_charges_per_person, 
  a.median_income, 
  ROUND((c.allowed_charges_per_person / a.median_income) * 100, 2) AS affordability_index
FROM cms_charges c
JOIN acs_incomes a
  ON c.state_code = a.state_code
WHERE a.year = 2024
  AND a.income_group = 'Female_no_spouse_kids'
ORDER BY affordability_index DESC
LIMIT 5;

-- Least burdensome
SELECT 
  c.state_name, 
  c.allowed_charges_per_person, 
  a.median_income, 
  ROUND((c.allowed_charges_per_person / a.median_income) * 100, 2) AS affordability_index
FROM cms_charges c
JOIN acs_incomes a
  ON c.state_code = a.state_code
WHERE a.year = 2024
  AND a.income_group = 'Female_no_spouse_kids'
ORDER BY affordability_index ASC
LIMIT 5;

-- Senior (65+) income change, and 2021 CMS cost context
SELECT 
  a21.state_name,
  a21.median_income AS median_income_2021,
  a24.median_income AS median_income_2024,
  ROUND(((a24.median_income - a21.median_income) / a21.median_income) * 100, 2) AS pct_change_income,
  c.allowed_charges_per_person AS medicare_cost_per_utilizer_2021
FROM acs_incomes a21
JOIN acs_incomes a24
  ON a21.state_code = a24.state_code
 AND a21.income_group = '65plus'
 AND a24.income_group = '65plus'
 AND a21.year = 2021
 AND a24.year = 2024
JOIN cms_charges c
  ON c.state_code = a21.state_code
ORDER BY pct_change_income ASC;


-- seniors household income 2021 vs 2024
CREATE OR REPLACE VIEW vw_senior_income_change AS
SELECT 
  a21.state_code,
  a21.state_name,
  a21.median_income AS median_income_2021,
  a24.median_income AS median_income_2024,
  ROUND(((a24.median_income - a21.median_income) / NULLIF(a21.median_income,0)) * 100, 2) AS pct_change_income_21_24,
  c.allowed_charges_per_utilizer AS cms_cost_2021
FROM acs_incomes a21
JOIN acs_incomes a24 
  ON a21.state_code = a24.state_code
 AND a21.income_group = '65plus'
 AND a24.income_group = '65plus'
 AND a21.year = 2021
 AND a24.year = 2024
JOIN cms_charges c 
  ON c.state_code = a21.state_code;


-- affordability ranking by group/year 
CREATE OR REPLACE VIEW vw_affordability_rank_2024 AS
SELECT
  state_code, state_name, income_group,
  ROUND((cms_cost_per_utilizer / median_income) * 100, 2) AS affordability_index_pct,
  DENSE_RANK() OVER (PARTITION BY income_group ORDER BY (cms_cost_per_utilizer/median_income)) AS rank_more_affordable,
  DENSE_RANK() OVER (PARTITION BY income_group ORDER BY (cms_cost_per_utilizer/median_income) DESC) AS rank_less_affordable
FROM vw_affordability_long
WHERE year=2024;
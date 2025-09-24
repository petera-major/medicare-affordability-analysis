SELECT 'cms_rows' AS check_name, COUNT(*) AS value
FROM cms_charges
UNION ALL
SELECT 'acs_rows_2021', COUNT(*) FROM acs_incomes WHERE year=2021
UNION ALL
SELECT 'acs_rows_2024', COUNT(*) FROM acs_incomes WHERE year=2024
;

SELECT 'cms_at_least_50_states' AS check_name,
       CASE WHEN COUNT(*) >= 50 THEN 'PASS' ELSE 'FAIL' END AS result
FROM cms_charges
;

SELECT 'acs_has_2021' AS check_name,
       CASE WHEN EXISTS(SELECT 1 FROM acs_incomes WHERE year=2021) THEN 'PASS' ELSE 'FAIL' END AS result
UNION ALL
SELECT 'acs_has_2024',
       CASE WHEN EXISTS(SELECT 1 FROM acs_incomes WHERE year=2024) THEN 'PASS' ELSE 'FAIL' END
;

SELECT 'cms_missing_in_acs_2024' AS check_name,
       COUNT(*) AS missing_states
FROM cms_charges c
LEFT JOIN acs_incomes a
  ON a.state_code = c.state_code AND a.year = 2024
WHERE a.state_code IS NULL
;

WITH g AS (
  SELECT state_code, COUNT(*) AS groups_2024
  FROM acs_incomes
  WHERE year=2024
  GROUP BY state_code
)
SELECT 'states_with_fewer_than_5_groups_2024' AS check_name,
       COUNT(*) AS states_flagged
FROM g
WHERE groups_2024 < 5
;

SELECT 'bad_cms_costs' AS check_name,
       COUNT(*) AS rows_flagged
FROM cms_charges
WHERE allowed_charges_per_person IS NULL OR allowed_charges_per_person <= 0
UNION ALL
SELECT 'bad_acs_income',
       COUNT(*)
FROM acs_incomes
WHERE median_income IS NULL OR median_income <= 0
;

SELECT 'cms_cost_min' AS metric, MIN(allowed_charges_per_person) AS value FROM cms_charges
UNION ALL
SELECT 'cms_cost_max', MAX(allowed_charges_per_person) FROM cms_charges
UNION ALL
SELECT 'acs_2024_income_min', MIN(median_income) FROM acs_incomes WHERE year=2024
UNION ALL
SELECT 'acs_2024_income_max', MAX(median_income) FROM acs_incomes WHERE year=2024
;

SELECT 'join_rows_cms_x_acs_2024' AS check_name,
       COUNT(*) AS joined_rows
FROM cms_charges c
JOIN acs_incomes a USING(state_code)
WHERE a.year=2024
;

SELECT 'sample_FL_rows' AS check_name,
       COUNT(*) AS rows
FROM acs_incomes a
JOIN cms_charges c USING(state_code)
WHERE a.year IN (2021, 2024) AND c.state_code='FL'
UNION ALL
SELECT 'sample_FL_affordability_2024', NULL
UNION ALL
SELECT CONCAT(a.income_group, ' -> ',
              ROUND((c.allowed_charges_per_person / a.median_income)*100,2), '%') AS detail,
       NULL
FROM acs_incomes a
JOIN cms_charges c USING(state_code)
WHERE a.year=2024 AND c.state_code='FL'
ORDER BY 1
;

import pandas as pd
import mysql.connector

conn = mysql.connector.connect(
    host="localhost", user="root", password="", database="healthcare_affordability"
)

exports = {
  "cms_top5_expensive.csv": """
    SELECT state_name, allowed_charges_per_person
    FROM cms_charges
    ORDER BY allowed_charges_per_person DESC
    LIMIT 5
  """,
  "cms_top5_cheap.csv": """
    SELECT state_name, allowed_charges_per_person
    FROM cms_charges
    ORDER BY allowed_charges_per_person ASC
    LIMIT 5
  """,
  "affordability_all_groups_2024.csv": """
    SELECT c.state_name, a.income_group,
           c.allowed_charges_per_person, a.median_income,
           ROUND((c.allowed_charges_per_person/a.median_income)*100,2) AS affordability_index
    FROM cms_charges c
    JOIN acs_incomes a ON a.state_code=c.state_code
    WHERE a.year=2024
    ORDER BY affordability_index DESC
  """,
  "senior_change_21_24.csv": """
    SELECT a21.state_name,
           a21.median_income AS median_income_2021,
           a24.median_income AS median_income_2024,
           ROUND(((a24.median_income - a21.median_income)/a21.median_income)*100, 2) AS pct_change_income,
           c.allowed_charges_per_person AS medicare_cost_per_utilizer_2021
    FROM acs_incomes a21
    JOIN acs_incomes a24 ON a21.state_code=a24.state_code
      AND a21.income_group='65plus' AND a24.income_group='65plus'
      AND a21.year=2021 AND a24.year=2024
    JOIN cms_charges c ON c.state_code=a21.state_code
    ORDER BY pct_change_income ASC
  """
}

empty = []
for fname, sql in exports.items():
    df = pd.read_sql(sql, conn)
    if df.empty:
        print(f"[WARN] Query for {fname} returned 0 rows. Check joins/filters.")
        empty.append(fname)
    else:
        df.to_csv(fname, index=False)
        print("Wrote", fname)

conn.close()

if empty:
    print("\nThese were empty:", ", ".join(empty))


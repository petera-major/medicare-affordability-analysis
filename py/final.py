from pathlib import Path
import pandas as pd
from sqlalchemy import create_engine, text

DB_USER = "root"
DB_PASS = ""        
DB_HOST = "localhost"
DB_NAME = "healthcare_affordability"
OUTDIR  = Path("power-bi-exports")
OUTDIR.mkdir(exist_ok=True)

ENGINE = create_engine(f"mysql+mysqlconnector://{DB_USER}:{DB_PASS}@{DB_HOST}/{DB_NAME}")

SQL_CREATE_VIEW = """
CREATE OR REPLACE VIEW vw_affordability_fact AS
SELECT
  c.state_code,
  c.state_name,
  a.year,
  a.income_group,
  c.beneficiaries,
  c.allowed_charges_per_person AS cms_cost_per_utilizer,
  a.median_income,
  ROUND(c.allowed_charges_per_person / NULLIF(a.median_income,0) * 100, 2) AS affordability_index_pct
FROM acs_incomes a
JOIN cms_charges c USING (state_code);
"""

SQL_FACT_ALL      = "SELECT * FROM vw_affordability_fact"
SQL_FACT_2024     = "SELECT * FROM vw_affordability_fact WHERE year=2024"
SQL_CMS_RANK      = """
SELECT state_code, state_name, allowed_charges_per_person AS cms_cost_per_utilizer
FROM cms_charges
ORDER BY cms_cost_per_utilizer DESC
"""
SQL_SENIORS_CHANGE = """
SELECT 
  a21.state_code, a21.state_name,
  a21.median_income AS median_income_2021,
  a24.median_income AS median_income_2024,
  ROUND(((a24.median_income - a21.median_income)/NULLIF(a21.median_income,0))*100, 2) AS pct_change_income_21_24,
  c.allowed_charges_per_person AS cms_cost_per_utilizer_2021
FROM acs_incomes a21
JOIN acs_incomes a24 USING(state_code)
JOIN cms_charges c     USING(state_code)
WHERE a21.income_group='65plus' AND a21.year=2021
  AND a24.income_group='65plus' AND a24.year=2024
ORDER BY pct_change_income_21_24 ASC
"""

def top_bottom_by_group(df_fact_2024: pd.DataFrame, k=5):
    """
    Return two DataFrames with top/bottom k states per income_group by affordability_index_pct.
    Top = most burdensome (higher %). Bottom = least burdensome.
    """
    cols = ["state_code","state_name","income_group","cms_cost_per_utilizer","median_income","affordability_index_pct"]
    top_rows = []
    bot_rows = []
    for grp, dfg in df_fact_2024.groupby("income_group", dropna=True):
        dfg = dfg.sort_values("affordability_index_pct", ascending=False)
        top_rows.append(dfg.head(k)[cols].assign(rank=range(1, min(k, len(dfg))+1)))
        bot_rows.append(dfg.tail(k).sort_values("affordability_index_pct", ascending=True)[cols].assign(rank=range(1, min(k, len(dfg))+1)))
    top = pd.concat(top_rows, ignore_index=True) if top_rows else pd.DataFrame(columns=cols+["rank"])
    bot = pd.concat(bot_rows, ignore_index=True) if bot_rows else pd.DataFrame(columns=cols+["rank"])
    return top, bot

def fmt_money(n):
    try:
        return "${:,.0f}".format(float(n))
    except Exception:
        return str(n)

def fmt_pct(n):
    try:
        return "{:,.1f}%".format(float(n))
    except Exception:
        return str(n)

def main():
    with ENGINE.begin() as conn:
        conn.execute(text(SQL_CREATE_VIEW))

        fact_all  = pd.read_sql(SQL_FACT_ALL, ENGINE)
        fact_2024 = pd.read_sql(SQL_FACT_2024, ENGINE)
        cms_rank  = pd.read_sql(SQL_CMS_RANK, ENGINE)
        seniors   = pd.read_sql(SQL_SENIORS_CHANGE, ENGINE)

    num_cols = ["cms_cost_per_utilizer", "median_income", "affordability_index_pct"]
    for c in num_cols:
        if c in fact_all.columns:
            fact_all[c] = pd.to_numeric(fact_all[c], errors="coerce")
        if c in fact_2024.columns:
            fact_2024[c] = pd.to_numeric(fact_2024[c], errors="coerce")

    top5, bottom5 = top_bottom_by_group(fact_2024, k=5)

    fact_all.to_csv(OUTDIR / "affordability_fact.csv", index=False)
    fact_2024.to_csv(OUTDIR / "affordability_fact_2024.csv", index=False)
    cms_rank.to_csv(OUTDIR / "cms_cost.csv", index=False)
    top5.to_csv(OUTDIR / "affordability_by_group_top5_2024.csv", index=False)
    bottom5.to_csv(OUTDIR / "affordability_by_group_bottom5_2024.csv", index=False)
    seniors.to_csv(OUTDIR / "senior_income_change_21_24.csv", index=False)

    lines = []
    lines.append("Healthcare Affordability — Key Findings\n")
    lines.append("Data: CMS 2021 (per utilizer cost) + ACS 2021 & 2024 (median incomes by household type)\n")

    if not cms_rank.empty:
        most_exp = cms_rank.head(5).copy()
        least_exp = cms_rank.tail(5).copy().sort_values("cms_cost_per_utilizer")
        lines.append("• Highest Medicare cost per utilizer (CMS 2021):")
        for _, r in most_exp.iterrows():
            lines.append(f"    - {r.state_name}: {fmt_money(r.cms_cost_per_utilizer)}")
        lines.append("• Lowest Medicare cost per utilizer (CMS 2021):")
        for _, r in least_exp.iterrows():
            lines.append(f"    - {r.state_name}: {fmt_money(r.cms_cost_per_utilizer)}")
        lines.append("")

    if not top5.empty:
        lines.append("• 2024 Affordability index (higher % = more burden):")
        for grp in sorted(top5.income_group.unique()):
            tg = top5[top5.income_group == grp].sort_values("rank")
            bg = bottom5[bottom5.income_group == grp].sort_values("rank")
            if tg.empty or bg.empty: 
                continue
            lines.append(f"   – Group: {grp}")
            lines.append("     Most burdensome (Top 3):")
            for _, r in tg.head(3).iterrows():
                lines.append(f"       * {r.state_name}: {fmt_pct(r.affordability_index_pct)} "
                             f"(CMS {fmt_money(r.cms_cost_per_utilizer)} vs Income {fmt_money(r.median_income)})")
            lines.append("     Least burdensome (Bottom 3):")
            for _, r in bg.head(3).iterrows():
                lines.append(f"       * {r.state_name}: {fmt_pct(r.affordability_index_pct)} "
                             f"(CMS {fmt_money(r.cms_cost_per_utilizer)} vs Income {fmt_money(r.median_income)})")
        lines.append("")

    if not seniors.empty:
        best = seniors.tail(3).sort_values("pct_change_income_21_24", ascending=False)
        worst = seniors.head(3)
        lines.append("• Seniors (65+) income change 2021→2024:")
        lines.append("   Best improvements:")
        for _, r in best.iterrows():
            lines.append(f"     - {r.state_name}: {fmt_pct(r.pct_change_income_21_24)} "
                         f"(2021 {fmt_money(r.median_income_2021)} → 2024 {fmt_money(r.median_income_2024)}; "
                         f"CMS {fmt_money(r.cms_cost_per_utilizer_2021)})")
        lines.append("   Weakest growth:")
        for _, r in worst.iterrows():
            lines.append(f"     - {r.state_name}: {fmt_pct(r.pct_change_income_21_24)} "
                         f"(2021 {fmt_money(r.median_income_2021)} → 2024 {fmt_money(r.median_income_2024)}; "
                         f"CMS {fmt_money(r.cms_cost_per_utilizer_2021)})")

    summary = "\n".join(lines).strip() + "\n"
    (OUTDIR / "insights.txt").write_text(summary, encoding="utf-8")
    print(f"\nWrote:\n  - {OUTDIR/'affordability_fact.csv'}\n  - {OUTDIR/'affordability_fact_2024.csv'}"
          f"\n  - {OUTDIR/'cms_cost_rank.csv'}\n  - {OUTDIR/'affordability_by_group_top5_2024.csv'}"
          f"\n  - {OUTDIR/'affordability_by_group_bottom5_2024.csv'}\n  - {OUTDIR/'senior_income_change_21_24.csv'}"
          f"\n  - {OUTDIR/'insights.txt'}\n")

    print("----- INSIGHTS PREVIEW -----")
    print(summary)

if __name__ == "__main__":
    main()

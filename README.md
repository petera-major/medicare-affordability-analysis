# Medicare Affordability vs Household Income (2021–2024)

**SQL | Python | Power BI**

This project analyzes how Medicare costs compare to household incomes across U.S. states, using **CMS Medicare data (2021)** and **U.S. Census ACS data (2021 & 2024)**.  
The goal was to measure **affordability** for different household groups (seniors, single parents, families of four, etc.) and visualize disparities across states.

---

## Key Insights
- In **D.C.**, male-headed households with children face the *highest burden* (over **340% of median income** goes toward Medicare costs).  
- Seniors’ incomes grew ~15% in states like **Connecticut**, making Medicare relatively more affordable.  
- States like **Wisconsin** and **New Mexico** saw income growth of only ~2%, so Medicare costs take a larger share of seniors’ resources.  
- **Alaska, Vermont, and North Dakota** are among the most affordable states for households, while **California, Florida, and New York** show higher burdens across groups.  

---

## Tech Stack
- **SQL**: Designed schema, loaded CMS & Census datasets, built affordability index queries.  
- **Python (pandas)**: Cleaned raw CSV files, reshaped ACS data into SQL-ready long format.  
- **MySQL**: Created tables and joins for Medicare costs vs. income groups.  
- **Power BI**: Developed interactive dashboards (line charts, bar charts, maps) to compare affordability across states and demographics.  

---

## Why This Project Matters

Healthcare affordability is one of the most pressing policy challenges.
This project demonstrates how data engineering + analytics + visualization can highlight income gaps, cost burdens, and policy tradeoffs.

---

## Dashboards
Screenshots and interactive analysis:  

Dashboard: ![Dashboard](visuals/dashboard.png)

1. **Distribution of Affordability (Table)** – Household income groups vs CMS cost share.
  [Afforability](visuals/affordability.png)
  
2. **Seniors Income vs Medicare Costs (Line Chart)** – 2021 vs 2024 trend by state.
  [Seniors](visuals/senior.png)
   
3. **Least Affordable States** – Bar + line chart of households facing the heaviest burden.
  [Least](visuals/least.png)
     
4. **Most Affordable States** – Bar + line chart of households with lowest burden.
   [Most](visuals/most.png)

---

##  Project Files
- `schema.sql` – Database schema design.  
- `schema.py` – Python cleaning + CSV transformer for SQL inserts.  
- `analysis.sql` – SQL queries for affordability metrics.  
- `final.py` – Exports query results to CSV for Power BI.  
- `power-bi-exports/` – CSV files imported into Power BI.  
- `dashboards/` – Screenshots of Power BI dashboards.  



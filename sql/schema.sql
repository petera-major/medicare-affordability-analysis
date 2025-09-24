-- States (optional but recommended)
CREATE TABLE IF NOT EXISTS states (
  state_code CHAR(2) PRIMARY KEY,
  state_name VARCHAR(64) UNIQUE
);

-- CMS 2021
CREATE TABLE IF NOT EXISTS cms_charges (
  state_code CHAR(2) PRIMARY KEY,
  state_name VARCHAR(64),
  beneficiaries INT,
  allowed_charges_per_person DECIMAL(12,2) NOT NULL
);

-- ACS incomes (store 2021 and 2024 together)
CREATE TABLE IF NOT EXISTS acs_incomes (
  state_code CHAR(2),
  state_name VARCHAR(64),
  year INT,                -- 2021 or 2024
  income_group VARCHAR(70),
  median_income DECIMAL(12,2) NOT NULL,
  PRIMARY KEY (state_code, year, income_group)
);


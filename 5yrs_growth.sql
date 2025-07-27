WITH CompanyYears AS (
    -- Step 1: Find companies with at least 5 years of data and get their min/max years
    SELECT
        cik,
        MIN(fiscal_year) as start_year,
        MAX(fiscal_year) as end_year,
        (MAX(fiscal_year) - MIN(fiscal_year)) as num_years
    FROM
        sec_financial_reports
    GROUP BY
        cik
    HAVING
        COUNT(fiscal_year) >= 5 AND (MAX(fiscal_year) - MIN(fiscal_year)) > 0
),
Financials AS (
    -- Step 2: Get the financial data for the start and end years
    SELECT
        cy.cik,
        cy.num_years,
        start_report.revenue AS start_revenue,
        end_report.revenue AS end_revenue,
        start_report.operating_income AS start_operating_income,
        end_report.operating_income AS end_operating_income
    FROM
        CompanyYears cy
    JOIN
        sec_financial_reports start_report ON cy.cik = start_report.cik AND cy.start_year = start_report.fiscal_year
    JOIN
        sec_financial_reports end_report ON cy.cik = end_report.cik AND cy.end_year = end_report.fiscal_year
),
FilteredFinancials AS (
    -- Step 3: Filter out rows that would cause calculation errors before calculation
    SELECT
        *
    FROM
        Financials
    WHERE
        start_revenue IS NOT NULL AND start_revenue > 0
        AND end_revenue IS NOT NULL AND end_revenue > 0
        AND start_operating_income IS NOT NULL AND start_operating_income > 0
        AND end_operating_income IS NOT NULL AND end_operating_income > 0
)
-- Step 4 & 5: Calculate CAGR on clean data and filter for companies meeting the growth criteria
SELECT
    c.ticker,
    c.title,
    f.num_years,
    f.start_revenue,
    f.end_revenue,
    (POWER(GREATEST(CAST(f.end_revenue AS DOUBLE) / CAST(f.start_revenue AS DOUBLE), 0.000000001), 1.0 / f.num_years) - 1) * 100 AS revenue_cagr_percent,
    f.start_operating_income,
    f.end_operating_income,
    (POWER(GREATEST(CAST(f.end_operating_income AS DOUBLE) / CAST(f.start_operating_income AS DOUBLE), 0.000000001), 1.0 / f.num_years) - 1) * 100 AS operating_income_cagr_percent
FROM
    FilteredFinancials f
JOIN
    sec_companies c ON f.cik = LPAD(c.cik, 10, '0') -- Pad CIK for correct join
WHERE
    (POWER(GREATEST(CAST(f.end_revenue AS DOUBLE) / CAST(f.start_revenue AS DOUBLE), 0.000000001), 1.0 / f.num_years) - 1) >= 0.20
    AND (POWER(GREATEST(CAST(f.end_operating_income AS DOUBLE) / CAST(f.start_operating_income AS DOUBLE), 0.000000001), 1.0 / f.num_years) - 1) >= 0.20
ORDER BY
    c.ticker;
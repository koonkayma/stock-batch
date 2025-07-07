CREATE TABLE sec_companies (
    cik VARCHAR(10) NOT NULL,
    ticker VARCHAR(20),
    title VARCHAR(255),
    PRIMARY KEY (cik)
);




CREATE TABLE sec_financial_reports (
    -- Identifiers
    cik VARCHAR(10) NOT NULL,
    fiscal_year INT NOT NULL,
    filing_date DATE,
    form VARCHAR(20),

    -- (All the financial metric columns from the previous design remain here...)
    revenue DECIMAL(19, 4),
    cost_of_revenue DECIMAL(19, 4),
    gross_profit DECIMAL(19, 4),
    research_and_development DECIMAL(19, 4),
    selling_general_and_admin DECIMAL(19, 4),
    operating_expenses DECIMAL(19, 4),
    operating_income DECIMAL(19, 4),
    interest_expense DECIMAL(19, 4),
    interest_and_investment_income DECIMAL(19, 4),
    pretax_income DECIMAL(19, 4),
    income_tax_expense DECIMAL(19, 4),
    net_income DECIMAL(19, 4),
    shares_outstanding BIGINT,
    eps DECIMAL(10, 4),
    dividend_per_share DECIMAL(10, 4),
    gross_margin DECIMAL(10, 4),
    operating_margin DECIMAL(10, 4),
    profit_margin DECIMAL(10, 4),
    cash_and_equivalents DECIMAL(19, 4),
    short_term_investments DECIMAL(19, 4),
    cash_and_short_term_investments DECIMAL(19, 4),
    receivables DECIMAL(19, 4),
    inventory DECIMAL(19, 4),
    total_current_assets DECIMAL(19, 4),
    property_plant_and_equipment DECIMAL(19, 4),
    long_term_investments DECIMAL(19, 4),
    goodwill DECIMAL(19, 4),
    other_intangible_assets DECIMAL(19, 4),
    total_assets DECIMAL(19, 4),
    accounts_payable DECIMAL(19, 4),
    accrued_expenses DECIMAL(19, 4),
    current_portion_of_long_term_debt DECIMAL(19, 4),
    total_current_liabilities DECIMAL(19, 4),
    long_term_debt DECIMAL(19, 4),
    total_liabilities DECIMAL(19, 4),
    shareholders_equity DECIMAL(19, 4),
    total_liabilities_and_equity DECIMAL(19, 4),
    depreciation_and_amortization DECIMAL(19, 4),
    stock_based_compensation DECIMAL(19, 4),
    operating_cash_flow DECIMAL(19, 4),
    capital_expenditures DECIMAL(19, 4),
    investing_cash_flow DECIMAL(19, 4),
    financing_cash_flow DECIMAL(19, 4),
    net_cash_flow DECIMAL(19, 4),
    free_cash_flow DECIMAL(19, 4),
    working_capital DECIMAL(19, 4),
    book_value_per_share DECIMAL(10, 4),
    PaymentsOfDividends DECIMAL(19, 4),

    -- Record Keeping
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    -- Keys
    PRIMARY KEY (cik, fiscal_year),
    INDEX (cik) -- Added an index for faster joins
);

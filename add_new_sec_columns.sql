-- Migration script to add new columns to sec_financial_reports locally

ALTER TABLE `sec_financial_reports`
ADD COLUMN `public_float` DECIMAL(19,4) DEFAULT NULL,
ADD COLUMN `short_term_borrowings` DECIMAL(19,4) DEFAULT NULL,
ADD COLUMN `retained_earnings` DECIMAL(19,4) DEFAULT NULL,
ADD COLUMN `treasury_stock` DECIMAL(19,4) DEFAULT NULL,
ADD COLUMN `additional_paid_in_capital` DECIMAL(19,4) DEFAULT NULL,
ADD COLUMN `entity_shares_outstanding` BIGINT(20) DEFAULT NULL,
ADD COLUMN `filer_category` VARCHAR(100) DEFAULT NULL,
ADD COLUMN `auditor_attestation_flag` BOOLEAN DEFAULT NULL,
ADD COLUMN `shell_company_flag` BOOLEAN DEFAULT NULL;

-- Verify changes
DESCRIBE `sec_financial_reports`;

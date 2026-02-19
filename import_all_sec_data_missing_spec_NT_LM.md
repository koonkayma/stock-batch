Below is an updated view of the specific rows in your table that would benefit from these additions:

| Database Column                       | SEC XBRL Tag(s) / API Field (Additions in Bold)                                                                                               |
| ------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------- |
| **revenue**                           | `RevenueFromContractWithCustomerExcludingAssessedTax`, `Revenues`, **SalesRevenueNet**, **SalesRevenueGoodsNet**, **SalesRevenueServicesNet** |
| **cost_of_revenue**                   | `CostOfGoodsAndServicesSold`, `CostOfRevenue`, **CostOfGoodsSold**, **CostOfServices**                                                        |
| **gross_profit**                      | **GrossProfit**, or Calculated (`revenue` - `cost_of_revenue`)                                                                                |
| **shares_outstanding**                | `CommonStockSharesOutstanding`, **EntityCommonStockSharesOutstanding**, `WeightedAverage...`                                                  |
| **current_portion_of_long_term_debt** | `LongTermDebtAndCapitalLeaseObligationsCurrent`, **LongTermDebtCurrent**, **ShortTermBorrowings**                                             |
| **long_term_debt**                    | `LongTermDebtNoncurrent`, **LongTermDebt**                                                                                                    |
| **cash_and_equivalents**              | `CashAndCashEquivalentsAtCarryingValue`, **Cash**                                                                                             |

As noted in Source, there is no single enforced list of tags for financial reports, so you may still encounter edge cases (like "Ceco Environmental Corp" missing `ShortTermBorrowings` tags entirely, as seen in Source). Using this expanded list will significantly improve your coverage.

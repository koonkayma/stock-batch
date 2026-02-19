Technical Specification and Quantitative Framework for the Antigravity Financial Intelligence System

The evolution of algorithmic trading and quantitative investment analysis has necessitated a shift away from legacy, high-latency data ingestion models toward dynamic, API-centric architectures. The Antigravity system represents a paradigm shift in financial data engineering, specifically designed to interface directly with the Securities and Exchange Commission (SEC) Electronic Data Gathering, Analysis, and Retrieval (EDGAR) system through its modernized RESTful services. By eschewing static database tables such as `sec_companies` or `sec_financial_reports` and legacy import scripts like `import_all_sec_data.py`, Antigravity establishes a real-time, stateful pipeline that converts raw, unstructured eXtensible Business Reporting Language (XBRL) data into high-conviction investment signals. This report provides an exhaustive technical specification for the Antigravity system, detailing its data ingestion mechanisms, quantitative picking algorithms, and robust production-ready infrastructure.

The Architecture of Direct SEC Data Ingestion

The foundation of the Antigravity system is a stateless ingestion engine that operates on the principle of minimal data persistence and maximal source fidelity. The system initiates its workflow by querying the official SEC ticker mapping file, which serves as the universal directory for all publicly traded entities in the United States. Unlike proprietary data providers that may introduce mapping errors or latency, the official `company_tickers.json` file provides the authoritative link between human-readable stock tickers and the SEC’s internal Central Index Key (CIK).[1]

Authority Mapping and CIK Normalization

The ingestion process begins with a standardized request to `https://www.sec.gov/files/company_tickers.json`. This endpoint returns a structured JSON payload containing entries for over 10,000 tickers, including the CIK, the ticker symbol, and the conformed company name.[1, 2, 3] A critical engineering requirement for the Antigravity engine is the transformation of the CIK from its integer representation in the mapping file to the 10-digit, zero-padded string format required by the SEC’s financial data APIs.[4]

For example, a company like Apple Inc. is represented with a CIK of 320193. The ingestion engine must apply a string padding function to generate the conformed CIK string `0000320193`.[3, 5, 6] This normalization is non-trivial; it ensures that the subsequent construction of URIs for the Company Facts API is valid. The construction logic for the data request follows a strict template:

URLFact​=[https://data.sec.gov/api/xbrl/companyfacts/CIK](https://data.sec.gov/api/xbrl/companyfacts/CIK){CIKpadded​}.json

This endpoint provides a comprehensive historical record of every XBRL-tagged fact reported by the entity, categorized by taxonomy (e.g., `us-gaap` or `ifrs-full`) and concept (e.g., `NetIncomeLoss`).[6, 7]

| SEC API Endpoint                | Logical Purpose            | Payload Format       | Authorization |
| ------------------------------- | -------------------------- | -------------------- | ------------- |
| `company_tickers.json`          | Universal Entity Directory | JSON (Nested Object) | Public        |
| `companyfacts/CIK{cik}.json`    | XBRL Fact History          | JSON (Hierarchical)  | User-Agent    |
| `submissions/CIK{cik}.json`     | Filing Metadata/Forms      | JSON (Columnar)      | User-Agent    |
| `company_tickers_exchange.json` | Extended Mapping           | JSON (Nested Object) | Public        |

Compliance with Fair Access Protocols

Accessing the SEC’s data infrastructure requires strict adherence to its Fair Access policy to prevent service degradation for other users. The Antigravity system must implement a middleware layer that manages two critical compliance components: the User-Agent header and the request rate limiter.[1]

The User-Agent header is a mandatory string that identifies the application and provides a point of contact for the SEC’s webmasters. It must follow the format `Company Name admin@example.com`.[1, 6] In conjunction with this identification, the system must enforce a global rate limit of 10 requests per second across all threads or distributed instances.[1, 8, 9] The Antigravity scheduler uses a token bucket algorithm to ensure that the request frequency never exceeds this threshold, utilizing a standard 0.1-second delay between iterative calls.[5, 6] Failure to maintain these standards results in a `429 Too Many Requests` status or temporary IP-level blacklisting.[6, 10]

Quantitative Signal Engineering for the Growth Strategy

The Growth picking strategy in Antigravity is built upon the premise that sustainable enterprise value is derived from the consistent generation of cash flow, which is less susceptible to accounting manipulation than net income.[11, 12, 13] The strategy employs a 5-year longitudinal analysis with a resilience threshold of at least three years of positive free cash flow.

Hierarchical Mapping of XBRL Concepts

Because companies have significant latitude in their choice of XBRL tags, the system must use a hierarchical mapping to extract the components of Free Cash Flow (FCF). This is particularly critical for the "Growth" picker, which relies on the relationship between operating cash and capital reinvestment.

The system defines FCF as:

FCF=Net Cash Provided by Operating Activities−Capital Expenditures

The engine searches for "Net Cash Provided by Operating Activities" using a prioritized list of tags, beginning with `us-gaap:NetCashProvidedByUsedInOperatingActivities`.[14] If this tag is absent, the engine attempts to resolve the value via `us-gaap:NetCashProvidedByUsedInOperatingActivitiesContinuingOperations`. For "Capital Expenditures," the system checks `us-gaap:PaymentsToAcquirePropertyPlantAndEquipment`, `us-gaap:CapitalExpenditures`, or `us-gaap:PaymentsToAcquireProductiveAssets`.[15, 16, 17]

| Quantitative Component | Primary XBRL Tag                             | Priority 2 Alias                                          | Type     |
| ---------------------- | -------------------------------------------- | --------------------------------------------------------- | -------- |
| Operating Cash Flow    | `NetCashProvidedByUsedInOperatingActivities` | `CashProvidedByOperatingActivities`                       | Duration |
| CapEx                  | `PaymentsToAcquirePropertyPlantAndEquipment` | `CapitalExpenditures`                                     | Duration |
| Gross Profit           | `GrossProfit`                                | `Revenue` - `CostOfGoodsSold`                             | Duration |
| Research & Dev         | `ResearchAndDevelopmentExpense`              | `ResearchAndDevelopmentExpenseExcludingAcquiredInProcess` | Duration |

Longitudinal Persistence Logic

The Growth picker iterates through the `units` dictionary of the JSON response, filtering for facts where the `form` attribute is `10-K`.[3, 6] This ensures that only audited annual results are used for long-term trend analysis. The algorithm constructs a time-series of FCF for the most recent five fiscal years. A "Positive Signal" is generated if the count of years with FCF>0 is greater than or equal to 3.

This 3/5 rule serves as a fundamental filter against cyclical anomalies or aggressive expansion phases that may temporarily depress cash flow. By requiring persistence, Antigravity identifies companies with established, cash-generative business models that have demonstrated the ability to self-fund their operations through at least one minor economic or industry cycle.[12, 13, 18]

Solvency and Sustainability: The Dividend Strategy Picker

The Dividend picking logic within Antigravity focuses on high-quality income generation, targeting companies that exhibit low financial leverage and sustainable capital return policies.[19, 20] The strategy utilizes two primary financial hurdles: the Debt-to-Equity (D/E) ratio and the Dividend Payout Ratio.

Calculating the Debt-to-Equity Threshold

The D/E ratio is the primary indicator of a company’s financial stability during market downturns. The system extracts `TotalLiabilities` and `StockholdersEquity` from the most recent balance sheet reporting frame (formally identified as an "Instant" period type in the XBRL taxonomy).[21, 22]

D/E=Shareholders′ EquityTotal Liabilities​

While the general benchmark for a "low debt" profile is D/E<1.0, the Antigravity system incorporates industry-specific adjustments derived from Standard Industrial Classification (SIC) codes found in the entity metadata.[23, 24] For example, tech companies are held to a stricter 0.5 standard, while utilities and banking entities—which naturally operate with higher leverage—may pass with ratios as high as 2.0.[22, 25]

Payout Ratio and Yield Sustainability

The Dividend Payout Ratio measures the proportion of earnings returned to shareholders. A ratio that is too high suggests that the company is failing to reinvest in its future or is potentially funding its dividend through debt.[19, 26] The system calculates this by dividing the sum of `PaymentsOfDividendsCommonStock` by `NetIncomeLoss` for the Trailing Twelve Months (TTM).[27, 28, 29]

Payout Ratio=∑TTM Net Income∑TTM Dividends​

The algorithm categorizes the results into sustainability bands:

1. **Healthy:** 35%−55%. This indicates a well-established company that balances shareholder rewards with growth reinvestment.[19]

2. **Growth-Focused:** 0%−35%. Typical of "Value" stocks or companies that have recently initiated a dividend.[19]

3. **High/Risky:** 55%−95%. Borderline sustainability; these entities are flagged for a secondary Free Cash Flow check to ensure the dividend is covered by actual cash rather than accounting profits.[19, 26, 30]

4. **Unsustainable:** >95%. These entities are immediately disqualified as "Dividend Traps".[19, 29]

| Payout Ratio Range | Sustainability Classification | Action Signal    |
| ------------------ | ----------------------------- | ---------------- |
| 0%−35%             | Good / Value                  | Neutral-Positive |
| 35%−55%            | Healthy / Leader              | Strong Buy       |
| 55%−75%            | High                          | Caution          |
| 75%−95%            | Very High                     | Warning          |
| >95%               | Unsustainable                 | Disqualify       |

Detecting Fundamental Reversals: The Turnaround Picker

The Turnaround strategy is designed to identify "wounded" companies that have begun a verifiable recovery process. Unlike value strategies that buy "cheap" stocks regardless of momentum, the Antigravity turnaround picker requires quantitative proof of an operational inflection point.[31, 32]

Operating Margin Inflection

The primary signal for a turnaround is the recovery of operating margins. Operating income, or Earnings Before Interest and Taxes (EBIT), provides a cleaner view of core business performance than net income, which may be obscured by tax credits or debt restructuring costs.[33, 34]

EBIT Margin=RevenuesOperatingIncomeLoss​

The picker requires a "Sequential Improvement" pattern. This is defined as a sequence where the EBIT margin in the current quarter Q0​ is higher than the margin in Q−1​, which in turn must be higher than Q−2​. This two-quarter expansion suggests that cost-cutting measures or product-mix shifts are consistently impacting the bottom line.[11, 35]

Management and Credit Signals

Academic research suggests that turnarounds are often accompanied by specific corporate events. The Antigravity engine searches the `submissions` history for specific form filings that correlate with recovery:

1. **Management Changes:** Detection of Form 8-K filings containing items related to the replacement of the CEO or CFO.[36]

2. **Credit Stabilization:** Improvement in the interest coverage ratio, calculated as EBIT/InterestExpense. A rise from a distressed level (e.g., <1.5x) toward a safer threshold (>3.0x) is a high-conviction turnaround signal.[31, 36]

3. **Dividend Resumption:** If a company that previously omitted its dividend (detected by a change from positive `PaymentsOfDividends` to zero) suddenly reports a new payment, it is scored as a high-confidence turnaround candidate.[31, 36]

Sequential Recovery: Trend from Loss to Earn

The "Loss to Earn" picker is a specialized sub-type of the turnaround strategy that focuses exclusively on the transition of the bottom line. It targets companies that have emerged from a period of chronic unprofitability to report their first positive earnings.[11, 37, 38]

The Trough-and-Pivot Analysis

This strategy requires a granular analysis of the `NetIncomeLoss` time-series, specifically targeting the last eight quarters of data. The picker applies a "Trough-and-Pivot" filter:

1. **The Distressed Phase:** At least four of the previous six quarters must have reported a negative `NetIncomeLoss`.[35, 39, 40]

2. **The Pivot Point:** The most recent quarter must report a positive value.[34, 39, 41]

3. **The Clean Profit Check:** To ensure the profit is not an accounting artifact, the system verifies that `NetIncomeLoss` is closely correlated with `NetCashProvidedByUsedInOperatingActivities`. If the cash flow remains negative while the earnings go positive, the signal is flagged as a "Low Quality" or "Non-Cash" pivot and is generally discarded.[11, 13]

Acceleration and Momentum Confirmation

Once a loss-to-earn pivot is detected, the system calculates the "Earnings Line" acceleration. A stock is preferred if the positive earning in the current quarter represents an acceleration in the rate of change.

Acceleration=(EarningsQ0​−EarningsQ−1​)−(EarningsQ−1​−EarningsQ−2​)

A positive acceleration value, combined with the first positive earnings report in several years, often precedes a major institutional re-rating of the stock, as fund managers typically wait for verified profitability before initiating positions.[11, 35, 40]

##Supplemental Data Enrichment via Finnhub and yFinance

While the SEC Company Facts API provides the authoritative fundamental record, it does not provide real-time pricing, trading volume, or consensus analyst estimates. The Antigravity program integrates with the Finnhub Stock API and the yFinance library to enrich fundamental picks with market-aware metadata.[2, 42, 43]

Real-Time Valuation and Price Proximity

Fundamental data is often trailing by several weeks (the "filing lag"). To prevent picking "value traps" that have already seen their stock price collapse beyond fundamental recovery, the system queries current price data to calculate:

1. **Forward P/E Multiples:** Dividing the latest market price by the projected earnings per share (EPS) provided by Finnhub’s consensus estimate endpoints.[23, 44, 45]

2. **Price Momentum:** Confirming that the stock is trading above its 200-day Moving Average (MA). For turnaround and loss-to-earn picks, an upward-sloping 200-day MA is a mandatory technical confirmation that the market has begun to recognize the fundamental improvement.[35]

3. **Relative Strength Index (RSI):** Avoiding overbought entities by ensuring the RSI (typically 14-day) is between 40 and 70 at the time of the pick.[35]

Liquidity and Market Cap Filtering

To ensure that the generated picks are tradeable for professional investors, the system applies liquidity filters. Using yFinance or Finnhub volume data, the program calculates the 30-day Average Daily Trading Volume (ADTV). Entities with an ADTV<$1 Million are excluded to avoid the volatility and bid-ask spread risks associated with penny stocks.[31, 46]

| Enrichment Factor | Purpose                         | Provider |
| ----------------- | ------------------------------- | -------- |
| Latest Quote      | Real-time valuation checks      | Finnhub  |
| ADTV              | Liquidity verification          | yFinance |
| Consensus EPS     | Forward-looking growth analysis | Finnhub  |
| 200-Day MA        | Trend confirmation              | Finnhub  |
| RSI               | Entry timing optimization       | Finnhub  |

Software Design: Resumability and State Management

The Antigravity system is designed as a mission-critical pipeline that must handle thousands of API requests and potential network failures without data loss or redundant processing. The program moves away from single-execution scripts toward a state-machine architecture managed by a local relational database.[47, 48, 49]

The State Management Database

The system utilizes an SQLite or PostgreSQL database (configured via environment variables) to track the lifecycle of every CIK in the SEC ticker list. This database serves as the "source of truth" for the pipeline's progress, enabling the program to resume immediately after a crash, network timeout, or scheduled pause.[50, 51, 52]

The `processing_registry` table schema is defined as follows:

```
CREATE TABLE processing_registry (
    cik TEXT PRIMARY KEY,
    ticker TEXT,
    last_attempt_timestamp DATETIME,
    status TEXT, -- 'PENDING', 'FETCHING', 'ANALYZING', 'COMPLETED', 'FAILED_404', 'FAILED_PARSE'
    error_message TEXT,
    retry_count INTEGER DEFAULT 0,
    strategy_matches TEXT -- Serialized JSON (e.g., '')
);
```

When the Antigravity engine initializes, it performs a "Delta Sync." It fetches the latest `company_tickers.json` and performs an upsert into the `processing_registry`. It then selects all rows where `status` is not `COMPLETED` and `status` is not `FAILED_404`.[53, 54, 55] This allows for efficient multi-day processing runs, where the system only works on new or previously failed tickers.[6, 55, 56]

Environment and Configuration Management

The system leverages a strict separation of code and configuration. Sensitive credentials and environmental parameters are stored in a `.env` file, which is loaded into the program’s memory at runtime.[57, 58]

• `DB_CONNECTION_STRING`: The URI for the state database (e.g., `postgresql://user:pass@localhost:5432/antigravity`).

• `FINNHUB_API_KEY`: The authorization token for supplemental market data.

• `SEC_USER_AGENT`: The identity string required for EDGAR API headers.

• `LOG_DESTINATION`: The file path for the system logs (e.g., `/var/log/antigravity/engine.log`).

• `CSV_OUTPUT_PATH`: The location for the final picks report.

Logging, Monitoring, and Resilience Strategy

Production-grade scraping and analysis require a sophisticated error-handling and logging infrastructure. The Antigravity system implements a layered approach to monitor pipeline health and ensure data integrity.[6, 58, 59]

Specific Handling for ERROR 404 and 429

The SEC APIs are not perfectly synchronized; a ticker may exist in the mapping file before its XBRL facts are available in the Facts API. The Antigravity engine implements a specific `404 Not Found` handler:

1. **Warning Level Logging:** A 404 error is logged as a `WARNING`, not an `ERROR`. This reflects that the data is missing from the source, rather than a failure of the program logic.[6, 60, 61]

2. **State Marking:** The CIK is marked as `FAILED_404` in the database, preventing the system from repeatedly wasting API calls on that entity in future runs.[62, 63, 64]

For `429 Too Many Requests`, the program implements exponential backoff. If a rate limit is hit, the system pauses for 2retry_count seconds before re-attempting, ensuring that the SEC’s automated tools do not identify the scraper as a malicious botnet.[1, 6]

The CSV Picking Audit Trail

Every company that passes one or more quantitative screens is appended to the `picks.csv` file. This file is the primary output of the system and is structured for direct import into visualization tools or spreadsheets.[43, 52, 65]

| CSV Header              | Logic Source           | Data Format             |
| ----------------------- | ---------------------- | ----------------------- |
| `timestamp`             | `datetime.now()`       | ISO-8601                |
| `ticker`                | `company_tickers.json` | String (Upper)          |
| `cik`                   | `company_tickers.json` | 10-Digit String         |
| `matching_strategies`   | Internal Logic         | JSON Array              |
| `fcf_count`             | Growth Logic           | Integer (0-5)           |
| `payout_ratio`          | Dividend Logic         | Float (Percentage)      |
| `ebit_margin_trend`     | Turnaround Logic       | String (e.g., 'UPWARD') |
| `price_momentum_signal` | Finnhub Logic          | Boolean                 |

Production Orchestration and Scheduling

The Antigravity system is designed to be fully automated, running as a background service with minimal manual intervention.

Scheduled Execution via Cron

The program is optimized for a weekly or daily execution schedule, depending on the user's investment horizon. For a weekly swing-trading strategy, a `cron` job is configured to run at 2:00 AM on Saturdays.[62, 63, 66] This ensures that all filings from the previous business week have been disseminated and the TTM calculations are using the most current data.

```
# Antigravity Weekly Production Run
0 2 * * 6 /usr/bin/python3 /opt/antigravity/main.py >> /var/log/antigravity/production.log 2>&1
```

Resource Management and Batch Processing

To optimize performance and database I/O, the program processes tickers in batches of 25. After each batch, the system performs a database commit, updating the `processing_registry` and appending any new picks to the CSV.[6, 57] This batch-and-commit approach minimizes the impact of a process crash, ensuring that no more than 25 tickers of work are ever lost in a single failure event.

Strategic Integration: Multi-Factor Scoring

While the four picking strategies can operate independently, the Antigravity engine provides a "Synergy Score" for entities that pass multiple screens. A company that meets the Dividend criteria (low debt, sustainable payout) while simultaneously passing the Turnaround criteria (sequential EBIT margin improvement) is considered a "High Conviction" pick.[12, 18, 67]

This multi-factor approach allows the user to filter the broad equity market into a manageable watchlist of 30 to 100 high-quality stocks that warrant deeper qualitative analysis.[13, 68] By automating the heavy lifting of XBRL data extraction and financial ratio calculation, Antigravity empowers quantitative researchers to focus on high-level strategy and risk management rather than data plumbing.

Conclusion and Future Operational Roadmap

The Antigravity system establishes a robust, state-of-the-art framework for fundamental stock screening using structured SEC data. By moving away from legacy monolithic scripts and static table imports, it provides a dynamic, resilient, and highly efficient pipeline for quantitative asset selection. The integration of stateful processing, robust logging, and external market data enrichment ensures that the system is not only accurate but also production-ready for professional investment environments. As the SEC continues to modernize its data delivery through initiatives like "EDGAR Next," the Antigravity architecture is well-positioned to adapt, providing a long-term competitive advantage in the systematic identification of growth, dividend, and turnaround opportunities.

--------------------------------------------------------------------------------

1. Accessing EDGAR Data - SEC.gov, [https://www.sec.gov/search-filings/edgar-search-assistance/accessing-edgar-data](https://www.google.com/url?sa=E&q=https%3A%2F%2Fwww.sec.gov%2Fsearch-filings%2Fedgar-search-assistance%2Faccessing-edgar-data)

2. Extracting data from SEC EDGAR RESTful APIs - Kaggle, [https://www.kaggle.com/code/svendaj/extracting-data-from-sec-edgar-restful-apis](https://www.google.com/url?sa=E&q=https%3A%2F%2Fwww.kaggle.com%2Fcode%2Fsvendaj%2Fextracting-data-from-sec-edgar-restful-apis)

3. How I retrieve company financials for free via SEC data | by Rohit Salunke | Medium, [https://medium.com/@vincirohit/how-i-retrieve-company-financials-for-free-via-sec-data-3afe3f8566a9](https://www.google.com/url?sa=E&q=https%3A%2F%2Fmedium.com%2F%40vincirohit%2Fhow-i-retrieve-company-financials-for-free-via-sec-data-3afe3f8566a9)

4. So you want to integrate with the SEC API - GreenFlux Blog, [https://blog.greenflux.us/so-you-want-to-integrate-with-the-sec-api/](https://www.google.com/url?sa=E&q=https%3A%2F%2Fblog.greenflux.us%2Fso-you-want-to-integrate-with-the-sec-api%2F)

5. sec-edgar-pipeline skill by bobmatnyc/claude-mpm-skills - playbooks, [https://playbooks.com/skills/bobmatnyc/claude-mpm-skills/sec-edgar-pipeline](https://www.google.com/url?sa=E&q=https%3A%2F%2Fplaybooks.com%2Fskills%2Fbobmatnyc%2Fclaude-mpm-skills%2Fsec-edgar-pipeline)

6. SEC EDGAR Scraper - Apify, [https://apify.com/labrat011/sec-edgar-scraper](https://www.google.com/url?sa=E&q=https%3A%2F%2Fapify.com%2Flabrat011%2Fsec-edgar-scraper)

7. EDGAR Application Programming Interfaces (APIs) - SEC.gov, [https://www.sec.gov/search-filings/edgar-application-programming-interfaces](https://www.google.com/url?sa=E&q=https%3A%2F%2Fwww.sec.gov%2Fsearch-filings%2Fedgar-application-programming-interfaces)

8. sec-edgar-api - Read the Docs, [https://sec-edgar-api.readthedocs.io/](https://www.google.com/url?sa=E&q=https%3A%2F%2Fsec-edgar-api.readthedocs.io%2F)

9. Developer Resources - SEC.gov, [https://www.sec.gov/about/developer-resources](https://www.google.com/url?sa=E&q=https%3A%2F%2Fwww.sec.gov%2Fabout%2Fdeveloper-resources)

10. SEC to apply new rate control limits to EDGAR websites, [https://www.sec.gov/filergroup/announcements-old/new-rate-control-limits](https://www.google.com/url?sa=E&q=https%3A%2F%2Fwww.sec.gov%2Ffilergroup%2Fannouncements-old%2Fnew-rate-control-limits)

11. How to Spot Earnings Trends Before They Show Up in the Headlines | TIKR.com, [https://www.tikr.com/blog/how-to-spot-earnings-trends-before-they-show-up-in-the-headlines](https://www.google.com/url?sa=E&q=https%3A%2F%2Fwww.tikr.com%2Fblog%2Fhow-to-spot-earnings-trends-before-they-show-up-in-the-headlines)

12. Stock Screeners: Profitability and Efficiency Metrics - Investing.com, [https://www.investing.com/academy/stocks/stock-screener-profitability-and-efficiency-metrics/](https://www.google.com/url?sa=E&q=https%3A%2F%2Fwww.investing.com%2Facademy%2Fstocks%2Fstock-screener-profitability-and-efficiency-metrics%2F)

13. How to Screen for High-Quality Stocks | TIKR.com, [https://www.tikr.com/blog/how-to-screen-for-high-quality-stocks](https://www.google.com/url?sa=E&q=https%3A%2F%2Fwww.tikr.com%2Fblog%2Fhow-to-screen-for-high-quality-stocks)

14. Element: us-gaap:NetCashProvidedByUsedInOperatingActivities - XBRL Site, [https://xbrlsite.azurewebsites.net/2019/Prototype/references/us-gaap/Element-10473.html](https://www.google.com/url?sa=E&q=https%3A%2F%2Fxbrlsite.azurewebsites.net%2F2019%2FPrototype%2Freferences%2Fus-gaap%2FElement-10473.html)

15. XBRL US GAAP Taxonomy Preparers Guide, [https://xbrl.us/wp-content/uploads/2015/03/PreparersGuide.pdf](https://www.google.com/url?sa=E&q=https%3A%2F%2Fxbrl.us%2Fwp-content%2Fuploads%2F2015%2F03%2FPreparersGuide.pdf)

16. Free Cash Flow Reconciliation - SEC.gov, [https://www.sec.gov/Archives/edgar/data/70033/000119312505163969/dex994.htm](https://www.google.com/url?sa=E&q=https%3A%2F%2Fwww.sec.gov%2FArchives%2Fedgar%2Fdata%2F70033%2F000119312505163969%2Fdex994.htm)

17. Query XBRL Facts - EdgarTools - Python Library for SEC Data Analysis, [https://edgartools.readthedocs.io/en/latest/xbrl-querying/](https://www.google.com/url?sa=E&q=https%3A%2F%2Fedgartools.readthedocs.io%2Fen%2Flatest%2Fxbrl-querying%2F)

18. Key Financial Metrics Investors Value Most for Funding Decisions - Qubit Capital, [https://qubit.capital/blog/showcase-financial-metrics-for-investors](https://www.google.com/url?sa=E&q=https%3A%2F%2Fqubit.capital%2Fblog%2Fshowcase-financial-metrics-for-investors)

19. What Is an Ideal Payout Ratio? - Dividend.com, [https://www.dividend.com/dividend-education/what-is-an-ideal-payout-ratio/](https://www.google.com/url?sa=E&q=https%3A%2F%2Fwww.dividend.com%2Fdividend-education%2Fwhat-is-an-ideal-payout-ratio%2F)

20. Dividend Payout Ratio Explained for Quality Investing - NJ Mutual Fund, [https://www.njmutualfund.com/mfblog/blog/what-is-dividend-payout-ratio](https://www.google.com/url?sa=E&q=https%3A%2F%2Fwww.njmutualfund.com%2Fmfblog%2Fblog%2Fwhat-is-dividend-payout-ratio)

21. XBRL Glossary of Terms - SEC.gov, [https://www.sec.gov/data-research/structured-data/inline-xbrl/xbrl-glossary-terms](https://www.google.com/url?sa=E&q=https%3A%2F%2Fwww.sec.gov%2Fdata-research%2Fstructured-data%2Finline-xbrl%2Fxbrl-glossary-terms)

22. Debt to equity ratios for healthy businesses - British Business Bank, [https://www.british-business-bank.co.uk/business-guidance/guidance-articles/finance/what-level-of-debt-is-healthy-for-business](https://www.google.com/url?sa=E&q=https%3A%2F%2Fwww.british-business-bank.co.uk%2Fbusiness-guidance%2Fguidance-articles%2Ffinance%2Fwhat-level-of-debt-is-healthy-for-business)

23. Five Key Financial Ratios for Stock Analysis | Charles Schwab, [https://www.schwab.com/learn/story/five-key-financial-ratios-stock-analysis](https://www.google.com/url?sa=E&q=https%3A%2F%2Fwww.schwab.com%2Flearn%2Fstory%2Ffive-key-financial-ratios-stock-analysis)

24. Debt-to-Equity Ratio Basics for Growth Companies - Phoenix Strategy Group, [https://www.phoenixstrategy.group/blog/debt-to-equity-ratio-basics-for-growth-companies](https://www.google.com/url?sa=E&q=https%3A%2F%2Fwww.phoenixstrategy.group%2Fblog%2Fdebt-to-equity-ratio-basics-for-growth-companies)

25. What Is a Good Debt to Equity Ratio? A 2025 Guide to Leverage, Risk, and Financial Health, [https://towerpointwealth.com/what-is-a-good-debt-to-equity-ratio/](https://www.google.com/url?sa=E&q=https%3A%2F%2Ftowerpointwealth.com%2Fwhat-is-a-good-debt-to-equity-ratio%2F)

26. How to Screen for High Dividend Stocks: Your Guide to Income Investing, [https://www.investing.com/academy/trading/high-dividend-stock-screener-guide/](https://www.google.com/url?sa=E&q=https%3A%2F%2Fwww.investing.com%2Facademy%2Ftrading%2Fhigh-dividend-stock-screener-guide%2F)

27. How to calculate dividends effortlessly: A detailed guide - Saxo, [https://www.home.saxo/learn/guides/financial-literacy/how-to-calculate-dividends-effortlessly-a-detailed-guide](https://www.google.com/url?sa=E&q=https%3A%2F%2Fwww.home.saxo%2Flearn%2Fguides%2Ffinancial-literacy%2Fhow-to-calculate-dividends-effortlessly-a-detailed-guide)

28. Dividend Payout Ratio | Formula + Calculator - Wall Street Prep, [https://www.wallstreetprep.com/knowledge/dividend-payout-ratio/](https://www.google.com/url?sa=E&q=https%3A%2F%2Fwww.wallstreetprep.com%2Fknowledge%2Fdividend-payout-ratio%2F)

29. What is Dividend Payout ratio? | TD Direct Investing, [https://www.td.com/ca/en/investing/direct-investing/articles/dividend-payout-ratio](https://www.google.com/url?sa=E&q=https%3A%2F%2Fwww.td.com%2Fca%2Fen%2Finvesting%2Fdirect-investing%2Farticles%2Fdividend-payout-ratio)

30. Potentially highest paying dividend stocks in 2025 - Fidelity Investments, [https://www.fidelity.com/learning-center/trading-investing/high-dividend-stocks](https://www.google.com/url?sa=E&q=https%3A%2F%2Fwww.fidelity.com%2Flearning-center%2Ftrading-investing%2Fhigh-dividend-stocks)

31. Wounded Wolves: Turnaround Stocks Quant Screening Backtesting, [https://bs-uploads.toptal.io/blackfish-uploads/portfolio_item_attachment/896482/image/original/SSRN-id2915958-35060a3a4d8ec851aa339ba6de086d2d.pdf](https://www.google.com/url?sa=E&q=https%3A%2F%2Fbs-uploads.toptal.io%2Fblackfish-uploads%2Fportfolio_item_attachment%2F896482%2Fimage%2Foriginal%2FSSRN-id2915958-35060a3a4d8ec851aa339ba6de086d2d.pdf)

32. Wounded Wolves: Turnaround Stocks Quantitative Screening Backtesting - SSRN, [https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2915958](https://www.google.com/url?sa=E&q=https%3A%2F%2Fpapers.ssrn.com%2Fsol3%2Fpapers.cfm%3Fabstract_id%3D2915958)

33. EBIT (Operating Income): Meaning and Example Calculations, Exciting or No?, [https://breakingintowallstreet.com/kb/accounting/ebit-operating-income/](https://www.google.com/url?sa=E&q=https%3A%2F%2Fbreakingintowallstreet.com%2Fkb%2Faccounting%2Febit-operating-income%2F)

34. EBIT | Formula + Calculator - Wall Street Prep, [https://www.wallstreetprep.com/knowledge/ebit/](https://www.google.com/url?sa=E&q=https%3A%2F%2Fwww.wallstreetprep.com%2Fknowledge%2Febit%2F)

35. Mark Minervini's Stock Screener: What Indicators and Criteria Does He Use?, [https://www.finermarketpoints.com/post/mark-minervini-s-stock-screener-what-indicators-and-criteria-does-he-use](https://www.google.com/url?sa=E&q=https%3A%2F%2Fwww.finermarketpoints.com%2Fpost%2Fmark-minervini-s-stock-screener-what-indicators-and-criteria-does-he-use)

36. Quant Screening Backtesting: Turnaround Stocks - R-bloggers, [https://www.r-bloggers.com/2017/02/quant-screening-backtesting-turnaround-stocks/](https://www.google.com/url?sa=E&q=https%3A%2F%2Fwww.r-bloggers.com%2F2017%2F02%2Fquant-screening-backtesting-turnaround-stocks%2F)

37. Understanding the Difference Between Monthly, Quarterly, and Annual Financial Reports, [https://reachreporting.com/blog/understanding-the-difference-between-monthly-quarterly-and-annual-financial-reports](https://www.google.com/url?sa=E&q=https%3A%2F%2Freachreporting.com%2Fblog%2Funderstanding-the-difference-between-monthly-quarterly-and-annual-financial-reports)

38. Extracting Financial Statements from SEC Filings - XBRL-To-JSON | by Dr J - Medium, [https://medium.com/@jan_5421/extracting-financial-statements-from-sec-filings-xbrl-to-json-f83542ade90](https://www.google.com/url?sa=E&q=https%3A%2F%2Fmedium.com%2F%40jan_5421%2Fextracting-financial-statements-from-sec-filings-xbrl-to-json-f83542ade90)

39. How can extract an income statement from all company concepts? - Stack Overflow, [https://stackoverflow.com/questions/70767270/how-can-extract-an-income-statement-from-all-company-concepts](https://www.google.com/url?sa=E&q=https%3A%2F%2Fstackoverflow.com%2Fquestions%2F70767270%2Fhow-can-extract-an-income-statement-from-all-company-concepts)

40. Track Profitability With The Earnings Line - Deepvue, [https://deepvue.com/fundamentals/track-profitability-with-the-earnings-line/](https://www.google.com/url?sa=E&q=https%3A%2F%2Fdeepvue.com%2Ffundamentals%2Ftrack-profitability-with-the-earnings-line%2F)

41. EPS Explained with a Simple Example: The Most Important Stock Metric, [https://www.stocktitan.net/articles/eps-explained-simple-example](https://www.google.com/url?sa=E&q=https%3A%2F%2Fwww.stocktitan.net%2Farticles%2Feps-explained-simple-example)

42. How to extract financial fundamentals from SEC "companyfacts" json? - Reddit, [https://www.reddit.com/r/algotrading/comments/wctt2c/how_to_extract_financial_fundamentals_from_sec/](https://www.google.com/url?sa=E&q=https%3A%2F%2Fwww.reddit.com%2Fr%2Falgotrading%2Fcomments%2Fwctt2c%2Fhow_to_extract_financial_fundamentals_from_sec%2F)

43. Web Scraping for Stock Prices in Python - GeeksforGeeks, [https://www.geeksforgeeks.org/python/web-scraping-for-stock-prices-in-python/](https://www.google.com/url?sa=E&q=https%3A%2F%2Fwww.geeksforgeeks.org%2Fpython%2Fweb-scraping-for-stock-prices-in-python%2F)

44. Stock Research: How to Analyze Stocks in 5 Steps (With Video Examples) - NerdWallet, [https://www.nerdwallet.com/investing/learn/how-to-research-stocks](https://www.google.com/url?sa=E&q=https%3A%2F%2Fwww.nerdwallet.com%2Finvesting%2Flearn%2Fhow-to-research-stocks)

45. Stock Screeners: How To Use Important Financial Metrics - Investing.com, [https://www.investing.com/academy/stocks/stock-screener-important-financial-metrics/](https://www.google.com/url?sa=E&q=https%3A%2F%2Fwww.investing.com%2Facademy%2Fstocks%2Fstock-screener-important-financial-metrics%2F)

46. Trend-following Effect in Stocks - Quantpedia, [https://quantpedia.com/strategies/trend-following-effect-in-stocks](https://www.google.com/url?sa=E&q=https%3A%2F%2Fquantpedia.com%2Fstrategies%2Ftrend-following-effect-in-stocks)

47. Inventory Management with JSON in Python - GeeksforGeeks, [https://www.geeksforgeeks.org/python/inventory-management-with-json-in-python/](https://www.google.com/url?sa=E&q=https%3A%2F%2Fwww.geeksforgeeks.org%2Fpython%2Finventory-management-with-json-in-python%2F)

48. sql - Best table structure for tracking state changes - Stack Overflow, [https://stackoverflow.com/questions/21475816/best-table-structure-for-tracking-state-changes](https://www.google.com/url?sa=E&q=https%3A%2F%2Fstackoverflow.com%2Fquestions%2F21475816%2Fbest-table-structure-for-tracking-state-changes)

49. Creating a Python logic file for process apps - IBM, [https://www.ibm.com/docs/en/process-mining/2.1.0?topic=apps-creating-python-logic-files-process](https://www.google.com/url?sa=E&q=https%3A%2F%2Fwww.ibm.com%2Fdocs%2Fen%2Fprocess-mining%2F2.1.0%3Ftopic%3Dapps-creating-python-logic-files-process)

50. Effective Web Scraping with Python: Building a Robust Data Pipeline for Price Monitoring, [https://dev.to/dowerdev/effective-web-scraping-with-python-building-a-robust-data-pipeline-for-price-monitoring-5g6d](https://www.google.com/url?sa=E&q=https%3A%2F%2Fdev.to%2Fdowerdev%2Feffective-web-scraping-with-python-building-a-robust-data-pipeline-for-price-monitoring-5g6d)

51. Python Web Scraping: Full Tutorial With Examples (2026) - ScrapingBee, [https://www.scrapingbee.com/blog/web-scraping-101-with-python/](https://www.google.com/url?sa=E&q=https%3A%2F%2Fwww.scrapingbee.com%2Fblog%2Fweb-scraping-101-with-python%2F)

52. A Guide to Storing Scraped Data with Python | by Otávio Simões Silveira | Level Up Coding, [https://levelup.gitconnected.com/a-guide-to-storing-scraped-data-with-python-a275d849463e](https://www.google.com/url?sa=E&q=https%3A%2F%2Flevelup.gitconnected.com%2Fa-guide-to-storing-scraped-data-with-python-a275d849463e)

53. Automated data scraping using CRON - Stack Overflow, [https://stackoverflow.com/questions/5161921/automated-data-scraping-using-cron](https://www.google.com/url?sa=E&q=https%3A%2F%2Fstackoverflow.com%2Fquestions%2F5161921%2Fautomated-data-scraping-using-cron)

54. Database design for tracking progress over time - Stack Overflow, [https://stackoverflow.com/questions/10038393/database-design-for-tracking-progress-over-time](https://www.google.com/url?sa=E&q=https%3A%2F%2Fstackoverflow.com%2Fquestions%2F10038393%2Fdatabase-design-for-tracking-progress-over-time)

55. How to "stop" and "resume" long time running Python script? - Stack Overflow, [https://stackoverflow.com/questions/6299349/how-to-stop-and-resume-long-time-running-python-script](https://www.google.com/url?sa=E&q=https%3A%2F%2Fstackoverflow.com%2Fquestions%2F6299349%2Fhow-to-stop-and-resume-long-time-running-python-script)

56. python - Saving the state of a program to allow it to be resumed - Stack Overflow, [https://stackoverflow.com/questions/5568904/saving-the-state-of-a-program-to-allow-it-to-be-resumed](https://www.google.com/url?sa=E&q=https%3A%2F%2Fstackoverflow.com%2Fquestions%2F5568904%2Fsaving-the-state-of-a-program-to-allow-it-to-be-resumed)

57. Beginner project for SQL. This is a simple python script to scrape stock prices off NASDAQ API and feed it to MySQL. : r/datascience - Reddit, [https://www.reddit.com/r/datascience/comments/fnh8zm/beginner_project_for_sql_this_is_a_simple_python/](https://www.google.com/url?sa=E&q=https%3A%2F%2Fwww.reddit.com%2Fr%2Fdatascience%2Fcomments%2Ffnh8zm%2Fbeginner_project_for_sql_this_is_a_simple_python%2F)

58. 22 Python Web Scraping Projects: From Beginner to Advanced - Firecrawl, [https://www.firecrawl.dev/blog/python-web-scraping-projects](https://www.google.com/url?sa=E&q=https%3A%2F%2Fwww.firecrawl.dev%2Fblog%2Fpython-web-scraping-projects)

59. Staff Interpretations and FAQs Related to Interactive Data Disclosure | DART, [https://dart.deloitte.com/USDART/home/accounting/sec/sec-material-supplement/staff-interpretations-faqs-related-interactive-data](https://www.google.com/url?sa=E&q=https%3A%2F%2Fdart.deloitte.com%2FUSDART%2Fhome%2Faccounting%2Fsec%2Fsec-material-supplement%2Fstaff-interpretations-faqs-related-interactive-data)

60. How I Automated My Tech Job Applications Using Python, Apify, and AI - Reddit, [https://www.reddit.com/r/Python/comments/1h5cajf/how_i_automated_my_tech_job_applications_using/](https://www.google.com/url?sa=E&q=https%3A%2F%2Fwww.reddit.com%2Fr%2FPython%2Fcomments%2F1h5cajf%2Fhow_i_automated_my_tech_job_applications_using%2F)

61. continuous log file processing and extract required data using python - Stack Overflow, [https://stackoverflow.com/questions/60314765/continuous-log-file-processing-and-extract-required-data-using-python](https://www.google.com/url?sa=E&q=https%3A%2F%2Fstackoverflow.com%2Fquestions%2F60314765%2Fcontinuous-log-file-processing-and-extract-required-data-using-python)

62. Python script to get job status at specific intervals - Lucidworks Support, [https://support.lucidworks.com/hc/en-us/articles/19536006741655-Python-script-to-get-job-status-at-specific-intervals](https://www.google.com/url?sa=E&q=https%3A%2F%2Fsupport.lucidworks.com%2Fhc%2Fen-us%2Farticles%2F19536006741655-Python-script-to-get-job-status-at-specific-intervals)

63. Web Scraping Automation: How to Run Scrapers on a Schedule - Firecrawl, [https://www.firecrawl.dev/blog/automated-web-scraping-free-2025](https://www.google.com/url?sa=E&q=https%3A%2F%2Fwww.firecrawl.dev%2Fblog%2Fautomated-web-scraping-free-2025)

64. Scrapy state between job runs. Base class for recreating spider's… | by alex_ber - Medium, [https://alex-ber.medium.com/scrapy-state-between-job-runs-b880c7b34a9d](https://www.google.com/url?sa=E&q=https%3A%2F%2Falex-ber.medium.com%2Fscrapy-state-between-job-runs-b880c7b34a9d)

65. Building a Custom Stock Monitoring Solution using Web Scraping - AskPython, [https://www.askpython.com/python/building-custom-stock-monitoring-solution-web-scraping](https://www.google.com/url?sa=E&q=https%3A%2F%2Fwww.askpython.com%2Fpython%2Fbuilding-custom-stock-monitoring-solution-web-scraping)

66. Automating Data Processing for Web Scraping Workflows - ScrapeHero, [https://www.scrapehero.com/automating-data-processing-for-web-scraping/](https://www.google.com/url?sa=E&q=https%3A%2F%2Fwww.scrapehero.com%2Fautomating-data-processing-for-web-scraping%2F)

67. Key Metrics to Consider When Investing - Simply Ethical, [https://simplyethical.com/blog/key-metrics-to-consider-when-investing/](https://www.google.com/url?sa=E&q=https%3A%2F%2Fsimplyethical.com%2Fblog%2Fkey-metrics-to-consider-when-investing%2F)

68. How to back test your investment strategy - Real world example, [https://www.quant-investing.com/blog/how-to-back-test-your-investment-strategy-real-world-example](https://www.google.com/url?sa=E&q=https%3A%2F%2Fwww.quant-investing.com%2Fblog%2Fhow-to-back-test-your-investment-strategy-real-world-example)

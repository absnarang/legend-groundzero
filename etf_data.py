"""
ETF/Legend model constants — model source, seed SQL, and example NLQ questions.
Extracted from playground.py so both playground and nlq_eval can import cleanly.

DISCLAIMER: All data is ENTIRELY FICTIONAL and for ILLUSTRATIVE/EDUCATIONAL PURPOSES ONLY.
"""

ETF_MODEL = """\
// Profile with both stereotypes (labels) and tags (key=value annotations)
Profile nlq::NlqProfile
{
    stereotypes: [core, junction, timeseries, calculated, sensitive];
    tags: [description, synonyms, businessDomain, importance, exampleQuestions, sampleValues, unit];
}

// ── Enumerations ──────────────────────────────────────────────────────────────

Enum etf::FundType
{
    ETF,          // Exchange-Traded Fund: trades intraday on exchange
    MUTUAL_FUND,  // Traditional mutual fund: priced once per day at NAV
    INDEX_FUND,   // Passively tracks an index (can be ETF or mutual fund)
    ACTIVE_FUND   // Actively managed; higher expense ratios typical
}

Enum etf::AssetClass
{
    EQUITY,        // Stocks / equities
    FIXED_INCOME,  // Bonds, treasuries, credit
    COMMODITY,     // Gold, oil, agricultural products
    REAL_ESTATE,   // REITs and property-related securities
    MULTI_ASSET    // Blend of multiple asset classes
}

Enum etf::Sector
{
    TECHNOLOGY,
    HEALTHCARE,
    FINANCIALS,
    ENERGY,
    CONSUMER_DISCRETIONARY,
    CONSUMER_STAPLES,
    INDUSTRIALS,
    MATERIALS,
    UTILITIES,
    COMMUNICATION_SERVICES,
    REAL_ESTATE,
    BROAD_MARKET   // Diversified / no single sector
}

// ── Core domain classes ───────────────────────────────────────────────────────

Class <<nlq::NlqProfile.core>>
      {nlq::NlqProfile.description = 'An investment fund (ETF or mutual fund) traded on an exchange or sold directly',
       nlq::NlqProfile.synonyms = 'fund, etf, mutual fund, ticker, vehicle, product, basket',
       nlq::NlqProfile.businessDomain = 'Asset Management, ETF, Mutual Fund, Index Fund',
       nlq::NlqProfile.importance = 'high',
       nlq::NlqProfile.sampleValues = 'ticker: SPY, QQQ, VTI, AGG, GLD; fundType: ETF, INDEX_FUND; assetClass: EQUITY, FIXED_INCOME; aum: 503000 (SPY), 263000 (QQQ)',
       nlq::NlqProfile.unit = 'aum: USD millions; expenseRatio: decimal fraction (0.0003 = 0.03% = 3 basis points)',
       nlq::NlqProfile.exampleQuestions = 'Which EQUITY ETFs have expense ratio below 0.1%? Show INDEX_FUND funds sorted by AUM. What is the benchmarkIndex of SPY?'} etf::Fund
[
    positiveAum:          $this.aum > 0,
    validExpenseRatio:    $this.expenseRatio >= 0 && $this.expenseRatio < 1
]
{
    fundId:        Integer[1];
    ticker:        String[1];
    fundName:      String[1];
    fundType:      String[1];   // etf::FundType enum value stored as string
    assetClass:    String[1];   // etf::AssetClass enum value stored as string
    sector:        String[1];   // etf::Sector enum value (primary sector focus)
    aum:           Float[1];    // Assets Under Management, USD millions
    expenseRatio:  Float[1];    // Annual fee as decimal: 0.0003 = 3 bps = 0.03%
    inceptionDate: String[1];   // ISO-8601 date, e.g. '1993-01-22'
    benchmarkIndex: String[1];  // e.g. 'S&P 500 Index', 'Bloomberg US Aggregate'
}

Class <<nlq::NlqProfile.core>>
      {nlq::NlqProfile.description = 'An individual equity security (stock) held inside one or more funds',
       nlq::NlqProfile.synonyms = 'stock, equity, share, security, company, issuer, name',
       nlq::NlqProfile.businessDomain = 'Equities, Securities, Stocks, Constituents',
       nlq::NlqProfile.importance = 'high',
       nlq::NlqProfile.sampleValues = 'ticker: AAPL, MSFT, NVDA, AMZN, GOOGL; sector: TECHNOLOGY, HEALTHCARE; country: US; marketCap: 3000000 (AAPL = $3T)',
       nlq::NlqProfile.unit = 'marketCap: USD millions',
       nlq::NlqProfile.exampleQuestions = 'Which US TECHNOLOGY stocks have market cap above 2 trillion? Show all securities in the FINANCIALS sector. Which securities appear in multiple funds?'} etf::Security
[
    positiveMarketCap: $this.marketCap > 0
]
{
    securityId:  Integer[1];
    ticker:      String[1];
    companyName: String[1];
    sector:      String[1];    // etf::Sector enum value
    country:     String[1];    // ISO country code, e.g. 'US', 'GB'
    marketCap:   Float[1];     // Market capitalisation, USD millions
}

Class <<nlq::NlqProfile.junction>>
      {nlq::NlqProfile.description = 'A fund holding: the percentage weight of one security inside one fund at a point in time',
       nlq::NlqProfile.synonyms = 'holding, position, weight, allocation, constituent, component, exposure',
       nlq::NlqProfile.businessDomain = 'Portfolio Construction, Holdings, Weights, Allocations',
       nlq::NlqProfile.importance = 'high',
       nlq::NlqProfile.sampleValues = 'weight: 7.12 (AAPL in SPY = 7.12%); shares: 180000000; marketValue: 3400 (USD millions)',
       nlq::NlqProfile.unit = 'weight: percentage (7.12 = 7.12%); shares: number of shares; marketValue: USD millions',
       nlq::NlqProfile.exampleQuestions = 'What are the top 5 holdings of SPY by weight? Which holdings have weight above 5%? What is total market value of AAPL positions across all ETFs?'} etf::Holding
[
    validWeight:        $this.weight > 0 && $this.weight <= 100,
    positiveShares:     $this.shares > 0,
    positiveMarketValue: $this.marketValue > 0
]
{
    holdingId:   Integer[1];
    weight:      Float[1];      // Percentage weight, e.g. 7.12 means 7.12%
    shares:      Float[1];      // Number of shares held by the fund
    marketValue: Float[1];      // Market value of the position, USD millions
}

Class <<nlq::NlqProfile.timeseries>>
      {nlq::NlqProfile.description = 'Daily Net Asset Value (NAV) snapshot for a fund — one record per fund per business day',
       nlq::NlqProfile.synonyms = 'nav, net asset value, price, daily price, close price, valuation, unit price',
       nlq::NlqProfile.businessDomain = 'Fund Valuation, Pricing, Performance',
       nlq::NlqProfile.importance = 'medium',
       nlq::NlqProfile.sampleValues = 'navDate: 2024-01-15, 2024-02-15; nav: 476.31 (SPY Jan-2024); volume: 51000000',
       nlq::NlqProfile.unit = 'nav: USD per share; volume: number of shares traded',
       nlq::NlqProfile.exampleQuestions = 'Show NAV history for SPY from January to March 2024. Which fund had the highest NAV on 2024-03-15? What was the volume-weighted average NAV of QQQ?'} etf::NAVRecord
[
    positiveNav:    $this.nav > 0,
    positiveVolume: $this.volume > 0
]
{
    navId:   Integer[1];
    navDate: String[1];   // ISO-8601 date, e.g. '2024-01-15'
    nav:     Float[1];    // Net Asset Value per share in USD
    volume:  Float[1];    // Daily trading volume in shares
}

Association etf::Fund_Holdings
{
    fund:    etf::Fund[1];
    holdings: etf::Holding[*];
}

Association etf::Security_Holdings
{
    security: etf::Security[1];
    holdings: etf::Holding[*];
}

Association etf::Fund_NAV
{
    fund:       etf::Fund[1];
    navRecords: etf::NAVRecord[*];
}

Database store::EtfDB
(
    Table T_FUND
    (
        FUND_ID        INTEGER PRIMARY KEY,
        TICKER         VARCHAR(20),
        FUND_NAME      VARCHAR(200),
        FUND_TYPE      VARCHAR(50),
        ASSET_CLASS    VARCHAR(50),
        SECTOR         VARCHAR(50),
        AUM            DOUBLE,
        EXPENSE_RATIO  DOUBLE,
        INCEPTION_DATE VARCHAR(20),
        BENCHMARK      VARCHAR(100)
    )
    Table T_SECURITY
    (
        SECURITY_ID  INTEGER PRIMARY KEY,
        TICKER       VARCHAR(20),
        COMPANY_NAME VARCHAR(200),
        SECTOR       VARCHAR(50),
        COUNTRY      VARCHAR(50),
        MARKET_CAP   DOUBLE
    )
    Table T_HOLDING
    (
        HOLDING_ID   INTEGER PRIMARY KEY,
        FUND_ID      INTEGER,
        SECURITY_ID  INTEGER,
        WEIGHT       DOUBLE,
        SHARES       DOUBLE,
        MARKET_VALUE DOUBLE
    )
    Table T_NAV
    (
        NAV_ID   INTEGER PRIMARY KEY,
        FUND_ID  INTEGER,
        NAV_DATE VARCHAR(20),
        NAV      DOUBLE,
        VOLUME   DOUBLE
    )
    Join Fund_Holdings(T_HOLDING.FUND_ID = T_FUND.FUND_ID)
    Join Security_Holdings(T_HOLDING.SECURITY_ID = T_SECURITY.SECURITY_ID)
    Join Fund_NAV(T_NAV.FUND_ID = T_FUND.FUND_ID)
)

Mapping etf::EtfMapping
(
    etf::Fund: Relational
    {
        ~mainTable [EtfDB] T_FUND
        fundId:        [EtfDB] T_FUND.FUND_ID,
        ticker:        [EtfDB] T_FUND.TICKER,
        fundName:      [EtfDB] T_FUND.FUND_NAME,
        fundType:      [EtfDB] T_FUND.FUND_TYPE,
        assetClass:    [EtfDB] T_FUND.ASSET_CLASS,
        sector:        [EtfDB] T_FUND.SECTOR,
        aum:           [EtfDB] T_FUND.AUM,
        expenseRatio:  [EtfDB] T_FUND.EXPENSE_RATIO,
        inceptionDate: [EtfDB] T_FUND.INCEPTION_DATE,
        benchmarkIndex: [EtfDB] T_FUND.BENCHMARK
    }
    etf::Security: Relational
    {
        ~mainTable [EtfDB] T_SECURITY
        securityId:  [EtfDB] T_SECURITY.SECURITY_ID,
        ticker:      [EtfDB] T_SECURITY.TICKER,
        companyName: [EtfDB] T_SECURITY.COMPANY_NAME,
        sector:      [EtfDB] T_SECURITY.SECTOR,
        country:     [EtfDB] T_SECURITY.COUNTRY,
        marketCap:   [EtfDB] T_SECURITY.MARKET_CAP
    }
    etf::Holding: Relational
    {
        ~mainTable [EtfDB] T_HOLDING
        holdingId:   [EtfDB] T_HOLDING.HOLDING_ID,
        weight:      [EtfDB] T_HOLDING.WEIGHT,
        shares:      [EtfDB] T_HOLDING.SHARES,
        marketValue: [EtfDB] T_HOLDING.MARKET_VALUE
    }
    etf::NAVRecord: Relational
    {
        ~mainTable [EtfDB] T_NAV
        navId:   [EtfDB] T_NAV.NAV_ID,
        navDate: [EtfDB] T_NAV.NAV_DATE,
        nav:     [EtfDB] T_NAV.NAV,
        volume:  [EtfDB] T_NAV.VOLUME
    }
)

RelationalDatabaseConnection store::EtfConn
{
    type: DuckDB;
    specification: InMemory { };
    auth: NoAuth { };
}

Runtime etf::EtfRuntime
{
    mappings:
    [
        etf::EtfMapping
    ];
    connections:
    [
        store::EtfDB:
        [
            environment: store::EtfConn
        ]
    ];
}"""

ETF_SEED_SQL = """\
CREATE TABLE IF NOT EXISTS T_FUND (
    FUND_ID INTEGER PRIMARY KEY, TICKER VARCHAR(20), FUND_NAME VARCHAR(200),
    FUND_TYPE VARCHAR(50), ASSET_CLASS VARCHAR(50), SECTOR VARCHAR(50),
    AUM DOUBLE, EXPENSE_RATIO DOUBLE, INCEPTION_DATE VARCHAR(20), BENCHMARK VARCHAR(100)
);
CREATE TABLE IF NOT EXISTS T_SECURITY (
    SECURITY_ID INTEGER PRIMARY KEY, TICKER VARCHAR(20), COMPANY_NAME VARCHAR(200),
    SECTOR VARCHAR(50), COUNTRY VARCHAR(50), MARKET_CAP DOUBLE
);
CREATE TABLE IF NOT EXISTS T_HOLDING (
    HOLDING_ID INTEGER PRIMARY KEY, FUND_ID INTEGER, SECURITY_ID INTEGER,
    WEIGHT DOUBLE, SHARES DOUBLE, MARKET_VALUE DOUBLE
);
CREATE TABLE IF NOT EXISTS T_NAV (
    NAV_ID INTEGER PRIMARY KEY, FUND_ID INTEGER, NAV_DATE VARCHAR(20),
    NAV DOUBLE, VOLUME DOUBLE
);
INSERT OR IGNORE INTO T_FUND VALUES
    (1, 'SPY',  'SPDR S&P 500 ETF Trust',          'ETF',         'EQUITY',       'BROAD_MARKET',           503000, 0.0945, '1993-01-22', 'S&P 500'),
    (2, 'QQQ',  'Invesco QQQ Trust',                'ETF',         'EQUITY',       'TECHNOLOGY',             263000, 0.20,   '1999-03-10', 'NASDAQ-100'),
    (3, 'VTI',  'Vanguard Total Stock Market ETF',  'INDEX_FUND',  'EQUITY',       'BROAD_MARKET',           420000, 0.03,   '2001-05-24', 'CRSP US Total Market'),
    (4, 'AGG',  'iShares Core US Aggregate Bond',   'ETF',         'FIXED_INCOME', 'BROAD_MARKET',           108000, 0.03,   '2003-09-22', 'Bloomberg US Aggregate'),
    (5, 'GLD',  'SPDR Gold Shares',                 'ETF',         'COMMODITY',    'BROAD_MARKET',            58000, 0.40,   '2004-11-18', 'Gold Spot Price');
INSERT OR IGNORE INTO T_SECURITY VALUES
    (1,  'AAPL', 'Apple Inc.',          'TECHNOLOGY',             'US', 2950000),
    (2,  'MSFT', 'Microsoft Corp.',     'TECHNOLOGY',             'US', 3100000),
    (3,  'NVDA', 'NVIDIA Corp.',        'TECHNOLOGY',             'US', 2200000),
    (4,  'AMZN', 'Amazon.com Inc.',     'CONSUMER_DISCRETIONARY', 'US', 1900000),
    (5,  'GOOGL','Alphabet Inc.',       'COMMUNICATION_SERVICES', 'US', 2000000),
    (6,  'META', 'Meta Platforms Inc.', 'COMMUNICATION_SERVICES', 'US', 1300000),
    (7,  'BRK',  'Berkshire Hathaway',  'FINANCIALS',             'US',  900000),
    (8,  'JPM',  'JPMorgan Chase',      'FINANCIALS',             'US',  580000),
    (9,  'JNJ',  'Johnson & Johnson',   'HEALTHCARE',             'US',  400000),
    (10, 'XOM',  'Exxon Mobil Corp.',   'ENERGY',                 'US',  450000);
INSERT OR IGNORE INTO T_HOLDING VALUES
    -- SPY holdings (fund 1)
    (1,  1, 1,  7.12, 18500000, 35760),
    (2,  1, 2,  6.89, 14200000, 34600),
    (3,  1, 3,  5.24,  8700000, 26300),
    (4,  1, 4,  3.92,  7300000, 19660),
    (5,  1, 5,  3.78,  8900000, 18980),
    (6,  1, 6,  2.41,  3800000, 12090),
    (7,  1, 7,  1.85,  1200000,  9280),
    (8,  1, 8,  1.71,  2600000,  8580),
    (9,  1, 9,  1.24,  2900000,  6220),
    (10, 1, 10, 1.18,  3100000,  5920),
    -- QQQ holdings (fund 2)
    (11, 2, 1,  8.94, 22000000, 23510),
    (12, 2, 2,  8.61, 17500000, 22640),
    (13, 2, 3,  7.48, 12400000, 19680),
    (14, 2, 4,  5.12,  9500000, 13470),
    (15, 2, 5,  5.01, 11800000, 13190),
    (16, 2, 6,  3.89,  6100000, 10220),
    -- VTI holdings (fund 3) — similar to SPY but broader
    (17, 3, 1,  5.80, 15000000, 24370),
    (18, 3, 2,  5.61, 11500000, 23570),
    (19, 3, 3,  4.12,  6800000, 17290),
    (20, 3, 8,  1.52,  2300000,  6380),
    (21, 3, 9,  1.10,  2600000,  4620),
    (22, 3, 10, 1.05,  2800000,  4410);
INSERT OR IGNORE INTO T_NAV VALUES
    -- SPY daily NAV (fund 1)
    (1,  1, '2024-01-15', 474.25, 82400000),
    (2,  1, '2024-01-16', 476.18, 79100000),
    (3,  1, '2024-01-17', 472.90, 91200000),
    (4,  1, '2024-02-15', 499.48, 88600000),
    (5,  1, '2024-03-15', 518.12, 95000000),
    -- QQQ daily NAV (fund 2)
    (6,  2, '2024-01-15', 412.33, 42100000),
    (7,  2, '2024-01-16', 415.80, 38700000),
    (8,  2, '2024-01-17', 410.20, 48200000),
    (9,  2, '2024-02-15', 438.92, 44500000),
    (10, 2, '2024-03-15', 455.61, 51200000),
    -- VTI (fund 3)
    (11, 3, '2024-01-15', 230.14, 31200000),
    (12, 3, '2024-02-15', 242.88, 28900000),
    (13, 3, '2024-03-15', 251.43, 33100000),
    -- AGG (fund 4)
    (14, 4, '2024-01-15',  95.42, 18400000),
    (15, 4, '2024-02-15',  94.18, 17200000),
    (16, 4, '2024-03-15',  95.81, 19100000),
    -- GLD (fund 5)
    (17, 5, '2024-01-15', 184.32, 12800000),
    (18, 5, '2024-02-15', 189.45,  9200000),
    (19, 5, '2024-03-15', 198.73, 14300000);"""

ETF_EXAMPLE_QUESTIONS = [
    # Enum filtering — FundType + AssetClass
    "Show all EQUITY assetClass funds sorted by aum descending",
    "Which INDEX_FUND type funds have expenseRatio below 0.0005?",
    # Association traversal — Fund → Holding → Security
    "What are the top 5 holdings of SPY by weight?",
    "Which securities appear in both SPY and QQQ holdings?",
    # Enum + constraint — Sector + weight threshold
    "List all TECHNOLOGY sector holdings with weight above 3 percent",
    # Timeseries — NAVRecord
    "Show the NAV history for QQQ across all available dates",
    # Units and numeric constraints — marketCap in USD millions
    "Show US-listed securities with marketCap above 2000000 USD millions",
    # Aggregation across association
    "What is the total marketValue of AAPL positions across all ETFs?",
    # Multi-property richness — uses benchmarkIndex and inceptionDate
    "Which funds track the S&P 500 index and what is their expense ratio?",
]

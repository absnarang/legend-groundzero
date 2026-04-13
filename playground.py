"""
Legend Ground Zero — bidirectional Pure ↔ SQL sync + NLQ playground

DISCLAIMER
----------
All company names, fund names, ticker symbols (e.g. SPY, QQQ, VTI, AAPL, MSFT, NVDA),
financial metrics (AUM, market capitalisation, NAV, expense ratio, weights, volumes),
asset classes (EQUITY, FIXED_INCOME, COMMODITY), sectors (TECHNOLOGY, HEALTHCARE,
FINANCIALS), benchmark indices, and any other data appearing in this application are
ENTIRELY FICTIONAL and used for ILLUSTRATIVE AND EDUCATIONAL PURPOSES ONLY.

- Numbers do not represent real market data, valuations, or performance figures.
- Any resemblance to actual funds, securities, companies, or financial instruments —
  whether currently existing or historical — is purely coincidental.
- Enum values, sector labels, and asset-class names are generic examples generated
  by frontier AI models and carry no endorsement of, or affiliation with, any real
  financial product, index provider, or institution.
- This application does not constitute financial advice, investment recommendations,
  or solicitation of any kind.
- No trademark or copyright of any company, fund manager, or index provider is
  claimed or implied.

This software is provided for technical demonstration of the Pure language engine
and LLM-powered Natural Language Query pipeline only.
"""

import json
import os
import re
import subprocess
import urllib.request
import urllib.error
from typing import Optional, Tuple, List, Dict
import streamlit as st

ENGINE_URL = "http://localhost:8080"

# ── Financial ETF/MF model with NlqProfile semantic annotations ───────────────

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

from northwind_data import NORTHWIND_MODEL, NORTHWIND_SEED_SQL, CHEAT_SHEET

DEFAULT_MODEL = """\
Class model::Department
{
    deptId:   Integer[1];
    deptName: String[1];
    budget:   Float[1];
}

Class model::Person
{
    firstName: String[1];
    lastName:  String[1];
    age:       Integer[1];
    salary:    Float[1];
}

Association model::Person_Department
{
    department: model::Department[1];
    employees:  model::Person[*];
}

Database store::CompanyDB
(
    Table T_DEPARTMENT
    (
        DEPT_ID   INTEGER PRIMARY KEY,
        DEPT_NAME VARCHAR(100),
        BUDGET    DOUBLE
    )
    Table T_PERSON
    (
        ID         INTEGER PRIMARY KEY,
        FIRST_NAME VARCHAR(100),
        LAST_NAME  VARCHAR(100),
        AGE        INTEGER,
        SALARY     DOUBLE,
        DEPT_ID    INTEGER
    )
    Join Person_Department(T_PERSON.DEPT_ID = T_DEPARTMENT.DEPT_ID)
)

Mapping model::CompanyMapping
(
    model::Department: Relational
    {
        ~mainTable [CompanyDB] T_DEPARTMENT
        deptId:   [CompanyDB] T_DEPARTMENT.DEPT_ID,
        deptName: [CompanyDB] T_DEPARTMENT.DEPT_NAME,
        budget:   [CompanyDB] T_DEPARTMENT.BUDGET
    }
    model::Person: Relational
    {
        ~mainTable [CompanyDB] T_PERSON
        firstName: [CompanyDB] T_PERSON.FIRST_NAME,
        lastName:  [CompanyDB] T_PERSON.LAST_NAME,
        age:       [CompanyDB] T_PERSON.AGE,
        salary:    [CompanyDB] T_PERSON.SALARY
    }
)

RelationalDatabaseConnection store::CompanyConn
{
    type: DuckDB;
    specification: InMemory { };
    auth: NoAuth { };
}

Runtime model::CompanyRuntime
{
    mappings:
    [
        model::CompanyMapping
    ];
    connections:
    [
        store::CompanyDB:
        [
            environment: store::CompanyConn
        ]
    ];
}"""

SEED_SQL = """\
CREATE TABLE IF NOT EXISTS T_DEPARTMENT (
    DEPT_ID   INTEGER PRIMARY KEY,
    DEPT_NAME VARCHAR(100),
    BUDGET    DOUBLE
);
CREATE TABLE IF NOT EXISTS T_PERSON (
    ID         INTEGER PRIMARY KEY,
    FIRST_NAME VARCHAR(100),
    LAST_NAME  VARCHAR(100),
    AGE        INTEGER,
    SALARY     DOUBLE,
    DEPT_ID    INTEGER
);
INSERT OR IGNORE INTO T_DEPARTMENT VALUES
    (1, 'Engineering', 5000000),
    (2, 'Sales',       2000000),
    (3, 'Finance',     3000000);
INSERT OR IGNORE INTO T_PERSON VALUES
    (1, 'Alice', 'Smith',  34, 120000, 1),
    (2, 'Bob',   'Jones',  28,  85000, 2),
    (3, 'Carol', 'Wang',   45, 175000, 3),
    (4, 'Dave',  'Patel',  31,  95000, 1),
    (5, 'Eve',   'Smith',  29, 110000, 2),
    (6, 'Frank', 'Lee',    38, 145000, 1),
    (7, 'Grace', 'Kim',    42, 190000, 3);"""

# Default query — simple JOIN: Person → Department
DEFAULT_QUERY = (
    "model::Person.all()"
    "->project([p|$p.firstName, p|$p.lastName, p|$p.salary, p|$p.department.deptName],"
    " ['firstName','lastName','salary','deptName'])"
    "->sort('salary', 'DESC')"
)

EXAMPLES = {
    # ── Scalar (no joins) ─────────────────────────────────────────────────────
    "Scalar — All people, salary DESC": (
        "model::Person.all()"
        "->project([p|$p.firstName, p|$p.lastName, p|$p.age, p|$p.salary],"
        " ['firstName','lastName','age','salary'])"
        "->sort('salary', 'DESC')"
    ),
    "Scalar — Filter age > 30": (
        "model::Person.all()"
        "->filter(p|$p.age > 30)"
        "->project([p|$p.firstName, p|$p.lastName, p|$p.age, p|$p.salary],"
        " ['firstName','lastName','age','salary'])"
        "->sort('salary', 'DESC')"
    ),
    "Scalar — Top 3 earners": (
        "model::Person.all()"
        "->project([p|$p.firstName, p|$p.lastName, p|$p.salary],"
        " ['firstName','lastName','salary'])"
        "->sort('salary', 'DESC')->take(3)"
    ),
    # ── JOIN: navigate Association → generates LEFT OUTER JOIN SQL ────────────
    "JOIN — People + dept name": (
        "model::Person.all()"
        "->project([p|$p.firstName, p|$p.lastName, p|$p.salary, p|$p.department.deptName],"
        " ['firstName','lastName','salary','deptName'])"
        "->sort('salary', 'DESC')"
    ),
    "JOIN — Filter by dept (Engineering)": (
        "model::Person.all()"
        "->filter(p|$p.department.deptName == 'Engineering')"
        "->project([p|$p.firstName, p|$p.lastName, p|$p.salary, p|$p.department.deptName],"
        " ['firstName','lastName','salary','deptName'])"
        "->sort('salary', 'DESC')"
    ),
    "JOIN — High earners + dept budget": (
        "model::Person.all()"
        "->filter(p|$p.salary > 100000)"
        "->project([p|$p.firstName, p|$p.salary,"
        "           p|$p.department.deptName, p|$p.department.budget],"
        " ['firstName','salary','deptName','deptBudget'])"
        "->sort('salary', 'DESC')"
    ),
    # ── Window functions (TDS literal — inline data, no DB tables needed) ─────
    "Window — RANK salary within dept": """\
#TDS
    name, dept, salary
    Alice, Engineering, 120000
    Bob, Sales, 85000
    Carol, Finance, 175000
    Dave, Engineering, 95000
    Eve, Sales, 110000
    Frank, Engineering, 145000
    Grace, Finance, 190000
#->extend(over(~dept, ~salary->descending()), ~rank:{p,w,r|$p->rank($w,$r)})""",

    "Window — LAG: salary vs previous year": """\
#TDS
    name, year, salary
    Alice, 2022, 110000
    Alice, 2023, 120000
    Alice, 2024, 135000
    Bob, 2022, 80000
    Bob, 2023, 85000
    Bob, 2024, 92000
    Carol, 2022, 160000
    Carol, 2023, 175000
    Carol, 2024, 190000
#->extend(over(~name, ~year->ascending()), ~prevSalary:{p,w,r|$p->lag($r).salary})""",

    "Window — LEAD: peek next year salary": """\
#TDS
    name, year, salary
    Alice, 2022, 110000
    Alice, 2023, 120000
    Alice, 2024, 135000
    Bob, 2022, 80000
    Bob, 2023, 85000
    Bob, 2024, 92000
#->extend(over(~name, ~year->ascending()), ~nextSalary:{p,w,r|$p->lead($r).salary})""",

    "Window — Running total salary per dept": """\
#TDS
    name, dept, salary
    Alice, Engineering, 120000
    Dave, Engineering, 95000
    Frank, Engineering, 145000
    Bob, Sales, 85000
    Eve, Sales, 110000
    Carol, Finance, 175000
    Grace, Finance, 190000
#->extend(over(~dept, ~salary->ascending()), ~runTotal:{p,w,r|$r.salary}:y|$y->plus())""",

    # ── ASOF join (time-series: match each trade to latest quote before it) ───
    "ASOF — Latest quote per trade (by time)": """\
#TDS
    trade_id, trade_time
    1, %2024-01-15T10:30:00
    2, %2024-01-15T11:30:00
    3, %2024-01-15T12:30:00
#->asOfJoin(
    #TDS
        quote_id, quote_time, price
        A, %2024-01-15T10:15:00, 100
        B, %2024-01-15T10:45:00, 102
        C, %2024-01-15T11:15:00, 105
        D, %2024-01-15T12:00:00, 108
        E, %2024-01-15T12:45:00, 110
    #,
    {t, q | $t.trade_time > $q.quote_time}
)""",

    "ASOF — Latest quote per trade + symbol": """\
#TDS
    trade_id, symbol, trade_time
    1, AAPL, %2024-01-15T10:30:00
    2, MSFT, %2024-01-15T10:30:00
    3, AAPL, %2024-01-15T11:30:00
    4, MSFT, %2024-01-15T11:45:00
#->asOfJoin(
    #TDS
        quote_symbol, quote_time, price
        AAPL, %2024-01-15T10:00:00, 180
        MSFT, %2024-01-15T10:00:00, 350
        AAPL, %2024-01-15T11:00:00, 182
        MSFT, %2024-01-15T11:15:00, 353
    #,
    {t, q | $t.trade_time > $q.quote_time},
    {t, q | $t.symbol == $q.quote_symbol}
)""",
}

# ── Helpers ──────────────────────────────────────────────────────────────────

def post_json(url: str, payload: dict) -> dict:
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read())
    except urllib.error.URLError as e:
        return {"success": False, "error": str(e)}


def check_health() -> bool:
    try:
        with urllib.request.urlopen(f"{ENGINE_URL}/health", timeout=3) as resp:
            return json.loads(resp.read()).get("status") == "ok"
    except Exception:
        return False


def pure_to_sql(model_src: str, query_expr: str) -> Tuple[str, Optional[str]]:
    """Compile Pure → SQL via /engine/plan. Returns (sql, error)."""
    full_code = model_src.strip() + "\n\n" + query_expr.strip()
    result = post_json(f"{ENGINE_URL}/engine/plan", {"code": full_code})
    if result.get("success"):
        return result["sql"], None
    return "", result.get("error") or "Unknown compile error"


def _parse_model(model_src: str) -> Tuple[str, Dict[str, str]]:
    """
    Extract (class_name, {SQL_COL -> pure_prop}) from the Pure model source.
    Also maps quoted alias -> pure_prop for ORDER BY lookups.
    """
    class_name = "Unknown"
    m = re.search(r'\bClass\s+([\w:]+)', model_src)
    if m:
        class_name = m.group(1)

    col_to_prop: Dict[str, str] = {}
    # Match lines like:   firstName: [PersonDB] T_PERSON.FIRST_NAME
    for match in re.finditer(r'(\w+)\s*:\s*\[\w+\]\s*\w+\.(\w+)', model_src):
        prop = match.group(1)
        col  = match.group(2).upper()
        col_to_prop[col] = prop
        # Also map the quoted alias (same as prop name) used in ORDER BY
        col_to_prop[prop.lower()] = prop
        col_to_prop[prop] = prop

    return class_name, col_to_prop


def _unwrap_subqueries(sql: str) -> Tuple[str, List[Tuple[str,str]], Optional[int]]:
    """
    Peel off the outer ORDER BY and LIMIT wrappers that the SQLGenerator adds.
    Returns (inner_sql, order_by_cols, limit).
    order_by_cols is a list of (col_alias, 'ASC'|'DESC').
    """
    sql = sql.strip().rstrip(';')
    order_by: List[Tuple[str, str]] = []
    limit: Optional[int] = None

    # Keep unwrapping: SELECT * FROM (...) AS alias  [ORDER BY ...] [LIMIT n]
    while True:
        changed = False

        # Strip LIMIT n from outermost
        lm = re.search(r'\bLIMIT\s+(\d+)\s*$', sql, re.IGNORECASE)
        if lm and limit is None:
            limit = int(lm.group(1))
            sql = sql[:lm.start()].strip()
            changed = True

        # Strip ORDER BY ... from outermost (before LIMIT was removed)
        om = re.search(r'\bORDER\s+BY\s+(.*?)\s*$', sql, re.IGNORECASE | re.DOTALL)
        if om and not order_by:
            for part in re.split(r',\s*', om.group(1).strip()):
                part = part.strip()
                tokens = part.rsplit(None, 1)
                raw_col = tokens[0].strip().strip('"').strip("'")
                direction = tokens[1].upper() if len(tokens) > 1 and tokens[1].upper() in ('ASC','DESC') else 'ASC'
                order_by.append((raw_col, direction))
            sql = sql[:om.start()].strip()
            changed = True

        # Unwrap: SELECT * FROM ( ... ) AS alias
        wm = re.match(r'SELECT\s+\*\s+FROM\s+\((.+)\)\s+AS\s+\w+\s*$', sql, re.IGNORECASE | re.DOTALL)
        if wm:
            sql = wm.group(1).strip()
            changed = True

        if not changed:
            break

    return sql, order_by, limit


def _translate_condition(cond: str, col_to_prop: Dict[str, str]) -> str:
    """
    Convert a SQL WHERE condition to a Pure filter condition.
    Replaces "t0"."COL" or "COL" with $p.property and AND/OR with &&/||.
    """
    # "t0"."COLUMN" → $p.property
    def replace_qualified(m: re.Match) -> str:
        col = m.group(1).upper()
        return f"$p.{col_to_prop.get(col, col)}"

    result = re.sub(r'"t\d+"\."(\w+)"', replace_qualified, cond)

    # Bare "COLUMN" that maps to a known property
    def replace_bare(m: re.Match) -> str:
        col = m.group(1).upper()
        if col.upper() in col_to_prop:
            return f"$p.{col_to_prop[col.upper()]}"
        return m.group(0)

    result = re.sub(r'"(\w+)"', replace_bare, result)

    # SQL AND / OR → Pure && / ||
    result = re.sub(r'\bAND\b', '&&', result, flags=re.IGNORECASE)
    result = re.sub(r'\bOR\b',  '||', result, flags=re.IGNORECASE)

    # Wrap compound conditions (containing && or ||) in parens if not already wrapped
    if ('&&' in result or '||' in result) and not result.startswith('('):
        # Split on && / || and wrap each atomic condition
        parts = re.split(r'(\s*&&\s*|\s*\|\|\s*)', result)
        wrapped = []
        for p in parts:
            stripped = p.strip()
            if stripped in ('&&', '||'):
                wrapped.append(f' {stripped} ')
            else:
                wrapped.append(f'({stripped})')
        result = ''.join(wrapped)

    return result


def _rule_based_sql_to_pure(model_src: str, sql: str) -> Tuple[str, Optional[str]]:
    """
    Rule-based SQL → Pure reverse translation (fallback).
    Handles SELECT/WHERE/ORDER BY/LIMIT including the nested-subquery structure
    that the Legend SQLGenerator produces.
    """
    try:
        class_name, col_to_prop = _parse_model(model_src)
        inner_sql, order_by, limit = _unwrap_subqueries(sql)

        # Parse the innermost SELECT
        # Expected: SELECT col_expr AS "alias", ... FROM "TABLE" AS "t0" [WHERE ...]
        where_clause: Optional[str] = None
        where_m = re.search(r'\bWHERE\s+(.+)$', inner_sql, re.IGNORECASE | re.DOTALL)
        if where_m:
            where_clause = where_m.group(1).strip()
            inner_sql = inner_sql[:where_m.start()].strip()

        col_match = re.search(r'SELECT\s+(.+?)\s+FROM\b', inner_sql, re.IGNORECASE | re.DOTALL)
        if not col_match:
            return "", "Could not parse SELECT columns from SQL"

        col_str = col_match.group(1).strip()

        # Parse projected columns → derive property names and aliases
        aliases: List[str] = []
        if col_str.strip() == '*':
            aliases = list(dict.fromkeys(col_to_prop.values()))
        else:
            for col_part in re.split(r',(?![^()]*\))', col_str):
                col_part = col_part.strip()
                alias_m = re.search(r'\bAS\s+"?(\w+)"?\s*$', col_part, re.IGNORECASE)
                if alias_m:
                    aliases.append(alias_m.group(1))
                else:
                    bare = col_part.strip('"').strip("'")
                    aliases.append(col_to_prop.get(bare.upper(), bare))

        # Build Pure chain
        parts = [f"{class_name}.all()"]

        if where_clause:
            cond = _translate_condition(where_clause, col_to_prop)
            parts.append(f"->filter(p|{cond})")

        lambdas = ", ".join(f"p|$p.{a}" for a in aliases)
        quoted  = ", ".join(f"'{a}'" for a in aliases)
        parts.append(f"->project([{lambdas}], [{quoted}])")

        for col_alias, direction in order_by:
            prop = col_to_prop.get(col_alias, col_alias)
            if direction == 'DESC':
                parts.append(f"->sort('{prop}', 'DESC')")
            else:
                parts.append(f"->sort('{prop}')")

        if limit is not None:
            parts.append(f"->take({limit})")

        return "".join(parts), None

    except Exception as e:
        return "", f"Parse error: {e}"


def sql_to_pure(model_src: str, sql: str) -> Tuple[str, Optional[str]]:
    """
    Translate SQL → Pure using Claude Sonnet 4.6 via the claude CLI
    (uses your Claude Pro subscription — no API key needed).
    Falls back to rule-based translation if the CLI is unavailable.
    """
    prompt = f"""\
You are a Legend/Pure language expert. Reverse-engineer the SQL below back into \
the exact Pure query expression that produced it.

Pure Model:
{model_src}

SQL Query:
{sql}

Return ONLY the Pure expression — no explanation, no markdown, no code fences.

════════════════════════════════════════════════════════
PATTERN REFERENCE — use EXACTLY these forms:
════════════════════════════════════════════════════════

── 1. TDS LITERAL (inline data) ─────────────────────────
SQL:  SELECT * FROM (VALUES ('Alice', 2022, 110000), ('Bob', 2023, 85000))
        AS _tds("name", "year", "salary")
Pure: #TDS
    name, year, salary
    Alice, 2022, 110000
    Bob, 2023, 85000
#
Rules:
  • Reconstruct every row from the VALUES list.
  • Date strings '%2024-01-15T10:30:00' → %2024-01-15T10:30:00  (drop quotes, keep %)
  • All other values keep their types (strings quoted in SQL → unquoted in TDS)

── 2. LEAD window ────────────────────────────────────────
SQL:  SELECT *, LEAD("salary", 1) OVER (PARTITION BY "name" ORDER BY "year" ASC ...) AS "nextSalary"
        FROM (...TDS source...) AS window_src
Pure: <tds_literal>->extend(over(~name, ~year->ascending()), ~nextSalary:{{p,w,r|$p->lead($r).salary}})

── 3. LAG window ─────────────────────────────────────────
SQL:  SELECT *, LAG("salary", 1) OVER (PARTITION BY "name" ORDER BY "year" ASC ...) AS "prevSalary"
        FROM (...TDS source...) AS window_src
Pure: <tds_literal>->extend(over(~name, ~year->ascending()), ~prevSalary:{{p,w,r|$p->lag($r).salary}})

── 4. RANK window ────────────────────────────────────────
SQL:  SELECT *, RANK() OVER (PARTITION BY "dept" ORDER BY "salary" DESC ...) AS "rank"
        FROM (...TDS source...) AS window_src
Pure: <tds_literal>->extend(over(~dept, ~salary->descending()), ~rank:{{p,w,r|$p->rank($w,$r)}})

── 5. Running aggregation (SUM window) ───────────────────
SQL:  SELECT *, SUM("salary") OVER (PARTITION BY "dept" ORDER BY "salary" ASC ...) AS "runTotal"
        FROM (...TDS source...) AS window_src
Pure: <tds_literal>->extend(over(~dept, ~salary->ascending()), ~runTotal:{{p,w,r|$r.salary}}:y|$y->plus())

── 6. ASOF JOIN ──────────────────────────────────────────
SQL:  SELECT * FROM (...left TDS...) AS "left_src"
        ASOF LEFT JOIN (...right TDS...) AS "right_src"
        ON "left_src"."trade_time" > "right_src"."quote_time"
Pure: <left_tds_literal>->asOfJoin(
    <right_tds_literal>,
    {{t, q | $t.trade_time > $q.quote_time}}
)

SQL (with key match):
        ON "left_src"."trade_time" > "right_src"."quote_time" AND "left_src"."symbol" = "right_src"."quote_symbol"
Pure: <left_tds_literal>->asOfJoin(
    <right_tds_literal>,
    {{t, q | $t.trade_time > $q.quote_time}},
    {{t, q | $t.symbol == $q.quote_symbol}}
)

── 7. CLASS query (DB tables, no TDS) ────────────────────
SQL:  SELECT "t0"."FIRST_NAME" AS "firstName", "t0"."SALARY" AS "salary",
             "j1"."DEPT_NAME" AS "deptName"
        FROM "T_PERSON" AS "t0"
        LEFT OUTER JOIN "T_DEPARTMENT" AS "j1" ON "t0"."DEPT_ID" = "j1"."DEPT_ID"
Pure: model::Person.all()
      ->project([p|$p.firstName, p|$p.salary, p|$p.department.deptName],
                ['firstName','salary','deptName'])

SQL (with WHERE):  ... FROM "T_PERSON" AS "t0" WHERE "t0"."AGE" > 30
Pure: model::Person.all()->filter(p|$p.age > 30)->project(...)

SQL (with ASOF-EXISTS):
  WHERE EXISTS (SELECT 1 FROM "T_DEPARTMENT" sub0
                WHERE sub0."DEPT_ID" = "t0"."DEPT_ID"
                  AND sub0."DEPT_NAME" = 'Engineering')
Pure: model::Person.all()->filter(p|$p.department.deptName == 'Engineering')->project(...)

SQL (ORDER BY): ... ORDER BY "salary" DESC
Pure: ...->sort('salary', 'DESC')

SQL (LIMIT): ... FETCH FIRST 3 ROWS ONLY  or  LIMIT 3
Pure: ...->take(3)

════════════════════════════════════════════════════════
ORDERING DIRECTION:
  ASC  / ASC NULLS LAST   → ->ascending()
  DESC / DESC NULLS FIRST → ->descending()

WINDOW FUNCTION LAMBDA FORMS (use exactly):
  LEAD  → {{p,w,r|$p->lead($r).colName}}
  LAG   → {{p,w,r|$p->lag($r).colName}}
  RANK  → {{p,w,r|$p->rank($w,$r)}}
  SUM   → {{p,w,r|$r.colName}}:y|$y->plus()
════════════════════════════════════════════════════════
"""
    try:
        # Unset CLAUDECODE so the CLI doesn't reject us as a "nested session"
        env = os.environ.copy()
        env.pop("CLAUDECODE", None)
        result = subprocess.run(
            ["claude", "--model", "claude-sonnet-4-6", "-p", prompt],
            capture_output=True, text=True, timeout=60, env=env,
        )
        if result.returncode == 0:
            output = result.stdout.strip()
            # Strip any accidental markdown code fences
            output = re.sub(r'^```\w*\n?', '', output).rstrip('`').strip()
            if output:
                return output, None
        # CLI ran but returned empty or error — fall back
        return _rule_based_sql_to_pure(model_src, sql)
    except FileNotFoundError:
        # claude CLI not on PATH — fall back silently
        return _rule_based_sql_to_pure(model_src, sql)
    except subprocess.TimeoutExpired:
        return _rule_based_sql_to_pure(model_src, sql)


def run_query(model_src: str, query_expr: str) -> dict:
    """Execute Pure query and return the server response."""
    full_code = model_src.strip() + "\n\n" + query_expr.strip()
    return post_json(f"{ENGINE_URL}/engine/execute", {"code": full_code})


def nlq_ask(model_src: str, question: str, domain: str = "", llm_model: str = "") -> dict:
    """Send natural language question to /engine/nlq. Returns NlqResult JSON."""
    payload = {"code": model_src, "question": question}
    if domain:
        payload["domain"] = domain
    if llm_model:
        payload["model"] = llm_model
    try:
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            f"{ENGINE_URL}/engine/nlq", data=data,
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=180) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        return {"success": False, "error": f"HTTP {e.code}: {body[:500]}"}
    except Exception as e:
        return {"success": False, "error": str(e)}


# ── Session state init ────────────────────────────────────────────────────────

def _init():
    defaults = {
        # widget keys — Streamlit owns these once the widgets are rendered
        "pure_input_area":  DEFAULT_QUERY,
        "sql_input_area":   "",
        # staging keys — we write here AFTER widgets render, applied on next rerun
        "_stage_pure":      None,
        "_stage_sql":       None,
        # other state
        "sync_error":       "",
        "result":           None,
        "_last_choice":     "(custom)",
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

_init()

# ── Apply any staged updates BEFORE widgets are rendered this run ─────────────
if st.session_state["_stage_sql"] is not None:
    st.session_state["sql_input_area"] = st.session_state["_stage_sql"]
    st.session_state["_stage_sql"] = None

if st.session_state["_stage_pure"] is not None:
    st.session_state["pure_input_area"] = st.session_state["_stage_pure"]
    st.session_state["_stage_pure"] = None


# ── Page ──────────────────────────────────────────────────────────────────────
st.set_page_config(page_title="Legend Lite Playground", layout="wide", page_icon="⚡")
st.title("⚡ Legend Lite Playground")
st.caption("Pure ↔ SQL bidirectional sync  •  Edit either side and sync the other")

if not check_health():
    st.error(f"🔴 Legend engine not reachable at {ENGINE_URL}")
    st.stop()
else:
    st.success(f"🟢 Engine at {ENGINE_URL}", icon=None)

# ── Disclaimer banner ─────────────────────────────────────────────────────────
with st.expander("⚠️ Disclaimer — all data is fictional and for illustration only", expanded=False):
    st.warning(
        """
**All data in this application is entirely fictional and for educational/illustrative purposes only.**

- **Company & fund names** (e.g. SPY, QQQ, AAPL, MSFT, NVDA) are used as recognisable
  placeholders only. They do not represent real funds or securities and all associated
  numbers are made up.
- **Financial metrics** — AUM, market capitalisation, NAV, expense ratio, weights,
  volumes, prices — are randomly chosen dummy values and bear no relation to any
  real market data, past or present.
- **Asset classes, sectors, enums** (EQUITY, FIXED\\_INCOME, TECHNOLOGY, HEALTHCARE …)
  are generic illustrative labels generated by frontier AI models. No affiliation with
  or endorsement of any real index provider, fund manager, or financial institution
  is claimed or implied.
- This application does **not** constitute financial advice, investment recommendations,
  or solicitation of any kind.
- No trademark, copyright, or intellectual property of any third party is claimed.

*This tool demonstrates the Pure language engine and LLM-powered NLQ pipeline only.*
        """,
        icon="⚠️",
    )

# ── Tabs ──────────────────────────────────────────────────────────────────────
tab_main, tab_sql_raw, tab_seed, tab_nlq, tab_cheat, tab_about = st.tabs(
    ["⇄ Pure ↔ SQL", "🗄️ Raw SQL", "🌱 Seed Data", "🔍 NLQ", "📚 Cheat Sheet", "📖 About"]
)

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 1 — Bidirectional Pure ↔ SQL
# ═══════════════════════════════════════════════════════════════════════════════
with tab_main:

    # ── Model editor (collapsible) ────────────────────────────────────────────
    with st.expander("📐 Pure Model (Class / Database / Mapping / Runtime)", expanded=False):
        model_src = st.text_area(
            "Model source",
            value=DEFAULT_MODEL,
            height=420,
            label_visibility="collapsed",
            key="model_editor",
        )
    # Fall back to default if somehow empty
    model_src = model_src or DEFAULT_MODEL

    # ── Example picker ────────────────────────────────────────────────────────
    choice = st.selectbox("Load example:", ["(custom)"] + list(EXAMPLES.keys()), key="example_pick")
    if choice != "(custom)" and st.session_state.get("_last_choice") != choice:
        # Stage the updates — they'll be applied before widgets render on next run
        st.session_state["_stage_pure"] = EXAMPLES[choice]
        st.session_state["_stage_sql"]  = ""
        st.session_state["sync_error"]  = ""
        st.session_state["result"]      = None
        st.session_state["_last_choice"] = choice
        st.rerun()
    st.session_state["_last_choice"] = choice

    # ── Two columns: Pure | SQL ───────────────────────────────────────────────
    col_pure, col_mid, col_sql = st.columns([10, 1, 10])

    with col_pure:
        st.markdown("#### Pure Query")
        # No value= needed — session state key drives the content
        pure_input = st.text_area(
            "Pure expression",
            height=160,
            label_visibility="collapsed",
            key="pure_input_area",
        )
        btn_pure_to_sql = st.button(
            "→  Compile to SQL",
            use_container_width=True,
            type="primary",
            key="btn_p2s",
            help="Compile Pure → show generated SQL in the right panel",
        )

    with col_mid:
        st.markdown("<br><br><br><br><br><br><br>", unsafe_allow_html=True)
        st.markdown("⇄")

    with col_sql:
        st.markdown("#### SQL (generated / editable)")
        sql_input = st.text_area(
            "SQL expression",
            height=160,
            label_visibility="collapsed",
            key="sql_input_area",
        )
        btn_sql_to_pure = st.button(
            "←  Translate to Pure",
            use_container_width=True,
            key="btn_s2p",
            help="Use Claude to reverse-translate SQL → Pure query",
        )

    # ── Error banner ──────────────────────────────────────────────────────────
    if st.session_state.sync_error:
        st.error(st.session_state.sync_error)

    # ── Pure → SQL ───────────────────────────────────────────────────────────
    if btn_pure_to_sql:
        st.session_state["sync_error"] = ""
        st.session_state["result"]     = None
        with st.spinner("Compiling Pure → SQL…"):
            sql, err = pure_to_sql(model_src, pure_input)
        if err:
            st.session_state["sync_error"] = f"Compile error: {err}"
        else:
            # Stage the SQL — it will be written to the widget key before next render
            st.session_state["_stage_sql"] = sql
        st.rerun()

    # ── SQL → Pure ───────────────────────────────────────────────────────────
    if btn_sql_to_pure:
        st.session_state["sync_error"] = ""
        st.session_state["result"]     = None
        with st.spinner("Translating SQL → Pure via Claude Sonnet 4.6…"):
            pure, err = sql_to_pure(model_src, sql_input)
        if err:
            st.session_state["sync_error"] = f"Translation error: {err}"
        else:
            # Stage the Pure — it will be written to the widget key before next render
            st.session_state["_stage_pure"] = pure
        st.rerun()

    st.divider()

    # ── Execute ───────────────────────────────────────────────────────────────
    exec_col, _ = st.columns([4, 8])
    with exec_col:
        btn_exec = st.button("▶  Execute Pure Query", type="primary", use_container_width=True)

    if btn_exec:
        q = st.session_state["pure_input_area"]
        with st.spinner("Executing…"):
            res = run_query(model_src, q)
        st.session_state.result = res

    if st.session_state.result:
        res = st.session_state.result
        if res.get("success"):
            import pandas as pd
            data = json.loads(res["data"])
            cols = res["columns"]
            st.success(f"✅ {res['rowCount']} row(s)")
            if data:
                st.dataframe(pd.DataFrame(data, columns=cols), use_container_width=True)
            else:
                st.info("Query returned 0 rows.")
        else:
            st.error(f"❌ {res.get('error') or 'Unknown error'}")


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 2 — Raw SQL runner
# ═══════════════════════════════════════════════════════════════════════════════
with tab_sql_raw:
    st.subheader("Execute Raw SQL")
    col_m, col_q = st.columns([1, 1])
    with col_m:
        sql_model = st.text_area("Pure model (for Runtime lookup):", value=DEFAULT_MODEL, height=340, key="raw_model")
    with col_q:
        raw_sql  = st.text_area("SQL:", value="SELECT * FROM T_PERSON ORDER BY SALARY DESC", height=120, key="raw_sql")
        raw_rt   = st.text_input("Runtime:", value="model::CompanyRuntime", key="raw_rt")
        if st.button("▶ Execute SQL", type="primary", use_container_width=True):
            r = post_json(f"{ENGINE_URL}/engine/sql", {"code": sql_model, "sql": raw_sql, "runtime": raw_rt})
            if r.get("success"):
                if "data" in r:
                    import pandas as pd
                    st.success(f"✅ {r['rowCount']} row(s)")
                    st.dataframe(pd.DataFrame(json.loads(r["data"]), columns=r["columns"]), use_container_width=True)
                else:
                    st.success(r.get("message", "Done"))
            else:
                st.error(r.get("error") or "Unknown error")


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 3 — Seed Data
# ═══════════════════════════════════════════════════════════════════════════════
with tab_seed:
    st.subheader("Seed Test Data")
    seed_sql = st.text_area("Seed SQL:", value=SEED_SQL, height=200, key="seed_sql")
    if st.button("🌱 Run Seed SQL", type="primary"):
        r = post_json(f"{ENGINE_URL}/engine/sql", {"code": DEFAULT_MODEL, "sql": seed_sql, "runtime": "model::CompanyRuntime"})
        st.success("✅ Seeded") if r.get("success") else st.error(r.get("error"))


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 4 — NLQ: Natural Language → Pure
# ═══════════════════════════════════════════════════════════════════════════════
with tab_nlq:
    st.subheader("🔍 Natural Language → Pure Query")
    st.caption("Powered by Claude via your Pro/Max subscription  •  Uses semantic metadata from NlqProfile annotations")

    # ── Two config rows ────────────────────────────────────────────────────────
    cfg_col1, cfg_col2 = st.columns([2, 1])

    with cfg_col1:
        nlq_model_choice = st.radio(
            "Domain model:",
            ["ETF / Mutual Fund (financial)", "Company / Person (default)"],
            horizontal=True,
            key="nlq_model_choice",
        )
    nlq_model_src = ETF_MODEL if "ETF" in nlq_model_choice else DEFAULT_MODEL

    with cfg_col2:
        nlq_llm_model = st.selectbox(
            "Claude model:",
            ["claude-haiku-4-5", "claude-sonnet-4-6", "claude-opus-4-6"],
            index=0,
            key="nlq_llm_model",
            help="Haiku is fastest; Opus is most capable. All use your Claude Pro/Max subscription via CLI.",
        )

    with st.expander("📐 Pure Model (view/edit)", expanded=False):
        nlq_model_src = st.text_area(
            "NLQ model source",
            value=nlq_model_src,
            height=350,
            label_visibility="collapsed",
            key="nlq_model_editor",
        )

    # ── Seed data helper for ETF ───────────────────────────────────────────────
    if "ETF" in nlq_model_choice:
        with st.expander("🌱 Seed ETF Data (run once before asking questions)", expanded=False):
            st.code(ETF_SEED_SQL[:500] + "\n...(truncated)", language="sql")
            if st.button("🌱 Seed ETF Data", key="nlq_seed_etf"):
                r = post_json(f"{ENGINE_URL}/engine/sql", {
                    "code": ETF_MODEL,
                    "sql": ETF_SEED_SQL,
                    "runtime": "etf::EtfRuntime",
                })
                if r.get("success"):
                    st.success("✅ ETF data seeded")
                else:
                    st.error(r.get("error", "Seed failed"))

    st.divider()

    # ── Question input ────────────────────────────────────────────────────────
    example_qs = ETF_EXAMPLE_QUESTIONS if "ETF" in nlq_model_choice else [
        "Show me all people in Engineering sorted by salary",
        "Who are the top 3 earners?",
        "Filter employees older than 35",
        "What departments have a budget over 3 million?",
    ]

    st.markdown("**Example questions** — click to load:")
    # Render example questions as buttons in a grid (3 per row)
    btn_cols = st.columns(3)
    for idx, eq in enumerate(example_qs):
        col = btn_cols[idx % 3]
        with col:
            if st.button(f"💬 {eq}", key=f"nlq_eq_{idx}", use_container_width=True):
                st.session_state["nlq_question_input"] = eq
                st.rerun()

    nlq_question = st.text_input(
        "Your question:",
        placeholder="e.g. What are the top 5 holdings of SPY by weight?",
        key="nlq_question_input",
    )

    nlq_domain = st.text_input(
        "Domain hint (optional):",
        placeholder="e.g. Holdings, NAV, Fund",
        key="nlq_domain",
    )

    btn_ask = st.button("🔍 Ask", type="primary", key="nlq_ask_btn", use_container_width=False)

    # ── NLQ session state ─────────────────────────────────────────────────────
    if "nlq_result" not in st.session_state:
        st.session_state["nlq_result"] = None

    if btn_ask and nlq_question and nlq_question.strip():
        selected_model = st.session_state.get("nlq_llm_model", "claude-haiku-4-5")
        with st.spinner(f"Asking {selected_model} via NLQ pipeline…"):
            result = nlq_ask(nlq_model_src, nlq_question.strip(), nlq_domain.strip(), selected_model)
        st.session_state["nlq_result"] = result

    # ── Display results ───────────────────────────────────────────────────────
    nlq_res = st.session_state.get("nlq_result")
    if nlq_res:
        st.divider()

        col_info, col_query = st.columns([1, 2])

        with col_info:
            st.markdown("**Pipeline info**")
            if nlq_res.get("rootClass"):
                st.info(f"Root class: `{nlq_res['rootClass']}`")
            if nlq_res.get("retrievedClasses"):
                retrieved = nlq_res["retrievedClasses"]
                if isinstance(retrieved, list):
                    st.caption(f"Retrieved classes: {', '.join(str(c) for c in retrieved[:8])}")
            latency = nlq_res.get("latencyMs", 0)
            if latency:
                st.caption(f"Latency: {latency:,} ms")
            if nlq_res.get("queryPlan"):
                with st.expander("Query plan"):
                    st.text(nlq_res["queryPlan"])
            if nlq_res.get("explanation"):
                with st.expander("Explanation"):
                    st.text(nlq_res["explanation"])

        with col_query:
            st.markdown("**Generated Pure query**")
            if nlq_res.get("success") and nlq_res.get("pureQuery"):
                pure_q = nlq_res["pureQuery"]
                st.code(pure_q, language="text")
                if nlq_res.get("error"):
                    st.warning(f"Validation warning: {nlq_res['error']}")

                # Execute the generated query
                if st.button("▶ Execute generated query", key="nlq_exec_btn"):
                    with st.spinner("Executing…"):
                        exec_res = run_query(nlq_model_src, pure_q)
                    if exec_res.get("success"):
                        import pandas as pd
                        data = json.loads(exec_res["data"])
                        cols = exec_res["columns"]
                        st.success(f"✅ {exec_res['rowCount']} row(s)")
                        if data:
                            st.dataframe(pd.DataFrame(data, columns=cols), use_container_width=True)
                        else:
                            st.info("Query returned 0 rows.")
                    else:
                        st.error(f"❌ {exec_res.get('error') or 'Unknown error'}")
            else:
                st.error(f"❌ {nlq_res.get('error') or 'NLQ failed'}")


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 5 — Cheat Sheet: TDS operations on Northwind model
# ═══════════════════════════════════════════════════════════════════════════════
with tab_cheat:
    st.subheader("📚 Pure TDS Cheat Sheet — Northwind Model")
    st.caption(
        "Every TDS relation function the Legend engine supports — one runnable example each. "
        "Pick an operation, read the explanation, then hit ▶ Execute to see live results."
    )

    # ── group filter ──────────────────────────────────────────────────────────
    all_groups = sorted({v[0] for v in CHEAT_SHEET.values()})
    cheat_group = st.radio(
        "Category:",
        ["All"] + all_groups,
        horizontal=True,
        key="cheat_group",
    )

    visible = {
        k: v for k, v in CHEAT_SHEET.items()
        if cheat_group == "All" or v[0] == cheat_group
    }

    cheat_choice = st.selectbox(
        "Operation:",
        list(visible.keys()),
        key="cheat_choice",
    )

    entry = visible[cheat_choice]
    group, description, query, explanation, uses_db = entry[:5]

    # ── info row ──────────────────────────────────────────────────────────────
    info_col, badge_col = st.columns([5, 1])
    with info_col:
        st.markdown(f"**{description}**")
    with badge_col:
        if uses_db:
            st.info("🗄️ DB")
            st.caption("requires seed")
        else:
            st.success("⚡ Inline")
            st.caption("no seed needed")

    # ── code block ────────────────────────────────────────────────────────────
    st.code(query, language="text")

    # ── explanation ───────────────────────────────────────────────────────────
    with st.expander("💡 How it works", expanded=False):
        st.markdown(explanation)

    st.divider()

    # ── action row ────────────────────────────────────────────────────────────
    seed_col, exec_col, _ = st.columns([2, 2, 4])

    with seed_col:
        if uses_db:
            if st.button("🌱 Seed Northwind Data", key="cheat_seed_btn"):
                with st.spinner("Seeding…"):
                    r = post_json(f"{ENGINE_URL}/engine/sql", {
                        "code": NORTHWIND_MODEL,
                        "sql": NORTHWIND_SEED_SQL,
                        "runtime": "northwind::runtime::NorthwindRuntime",
                    })
                if r.get("success"):
                    st.success("✅ Northwind data seeded")
                else:
                    st.error(r.get("error", "Seed failed"))
        else:
            st.caption("No seeding required — data is inline.")

    with exec_col:
        cheat_exec = st.button("▶ Execute", type="primary", key="cheat_exec_btn")

    # ── execute ───────────────────────────────────────────────────────────────
    if "cheat_result" not in st.session_state:
        st.session_state["cheat_result"] = None
    if "cheat_last_op" not in st.session_state:
        st.session_state["cheat_last_op"] = None

    if cheat_exec:
        model_src = NORTHWIND_MODEL  # always — TDS literals need the Runtime too
        with st.spinner("Running query…"):
            result = run_query(model_src, query)
        st.session_state["cheat_result"] = result
        st.session_state["cheat_last_op"] = cheat_choice

    cheat_res = st.session_state.get("cheat_result")
    if cheat_res and st.session_state.get("cheat_last_op") == cheat_choice:
        if cheat_res.get("success"):
            import pandas as pd
            data = json.loads(cheat_res["data"])
            cols = cheat_res["columns"]
            n = cheat_res["rowCount"]
            st.success(f"✅ {n} row(s) returned")
            if data:
                st.dataframe(pd.DataFrame(data, columns=cols), use_container_width=True)
            else:
                st.info("Query executed successfully — 0 rows returned.")
        else:
            st.error(f"❌ {cheat_res.get('error') or 'Unknown error'}")


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 6 — About
# ═══════════════════════════════════════════════════════════════════════════════
with tab_about:
    st.subheader("How the sync works")
    st.markdown("""
### Pure → SQL  (`→ Compile to SQL`)
Calls the Legend engine's `/engine/plan` endpoint which:
1. Parses and compiles the Pure expression into a **RelationNode IR tree**
2. Walks the IR tree with `SQLGenerator` (DuckDB dialect)
3. Returns the exact SQL that would be executed — no guessing, it's the real thing

### SQL → Pure  (`← Translate to Pure`)
Uses **Claude Sonnet 4.6** (via your Claude Pro subscription — no API key needed) to reverse-engineer the SQL back to a Pure expression that respects:
- Fully-qualified class names (`model::Person.all()`)
- Pure property names (camelCase, from model) not SQL column names
- Correct `->filter()`, `->project()`, `->sort()`, `->take()` chaining

Falls back to a local rule-based parser automatically if the `claude` CLI is unavailable.

### Pure syntax quick ref
| Operation | Syntax |
|-----------|--------|
| All records | `model::Person.all()` |
| Filter (AND) | `->filter(p\\|($p.age > 30) && ($p.salary > 100000))` |
| Project + JOIN | `->project([p\\|$p.firstName, p\\|$p.department.deptName], ['firstName','deptName'])` |
| Sort ASC | `->sort('colAlias')` |
| Sort DESC | `->sort('colAlias', 'DESC')` |
| Top N | `->take(N)` |
| Window RANK | `#TDS...#->extend(over(~dept, ~salary->descending()), ~rank:{p,w,r\\|$p->rank($w,$r)})` |
| Window LAG | `->extend(over(~name, ~year->ascending()), ~prev:{p,w,r\\|$p->lag($r).salary})` |
| Window LEAD | `->extend(over(~name, ~year->ascending()), ~next:{p,w,r\\|$p->lead($r).salary})` |
| ASOF join | `#TDS t...#->asOfJoin(#TDS q...#, {t,q\\|$t.time > $q.time})` |

### Association model (how JOINs are declared)
```
Association model::Person_Department { department: Department[1]; employees: Person[*]; }
Database store::CompanyDB ( ... Join Person_Department(T_PERSON.DEPT_ID = T_DEPARTMENT.DEPT_ID) )
```
Navigation `$p.department.deptName` → `LEFT OUTER JOIN T_DEPARTMENT ON T_PERSON.DEPT_ID = T_DEPARTMENT.DEPT_ID`
Filter through association → `EXISTS (SELECT 1 FROM T_DEPARTMENT WHERE ...)`
""")

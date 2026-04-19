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
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # python-dotenv not installed; rely on env vars directly

ENGINE_URL = "http://localhost:8080"

from etf_data import ETF_MODEL, ETF_SEED_SQL, ETF_EXAMPLE_QUESTIONS
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
st.set_page_config(page_title="Legend Workbench", layout="wide", page_icon="⚡")
st.title("⚡ Legend Workbench")
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
tab_main, tab_sql_raw, tab_seed, tab_nlq, tab_cheat, tab_eval, tab_about = st.tabs(
    ["⇄ Pure ↔ SQL", "🗄️ Raw SQL", "🌱 Seed Data", "🔍 NLQ", "📚 Cheat Sheet", "📊 Eval", "📖 About"]
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
            if nlq_res.get("cannotAnswer"):
                st.markdown("**System declined to generate a query**")
                st.warning("The system determined it cannot answer this question with the available data model.")
                follow_up = nlq_res.get("followUpQuestion", "")
                if follow_up:
                    st.info(f"**Follow-up question:** {follow_up}")
            elif nlq_res.get("success") and nlq_res.get("pureQuery"):
                st.markdown("**Generated Pure query**")
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
# TAB 6 — Eval: NLQ Quality Evaluation
# ═══════════════════════════════════════════════════════════════════════════════
with tab_eval:
    import nlq_eval

    st.subheader("📊 NLQ Evaluation Framework")
    st.caption(
        "Measure NLQ pipeline quality across retrieval, routing, answer accuracy, "
        "and LLM-as-judge dimensions."
    )

    # ── Controls ──────────────────────────────────────────────────────────────
    eval_c1, eval_c2, eval_c3 = st.columns([1, 1, 2])

    with eval_c1:
        eval_domain = st.selectbox(
            "Domain filter:",
            ["All", "Northwind", "ETF"],
            key="eval_domain",
        )
    with eval_c2:
        eval_llm = st.selectbox(
            "NLQ generation model:",
            ["claude-opus-4-6", "claude-sonnet-4-6", "claude-haiku-4-5"],
            index=0,
            key="eval_llm_model",
        )
    with eval_c3:
        eval_api_key = st.text_input(
            "Anthropic API key (for LLM judge):",
            type="password",
            key="eval_api_key",
            value=os.getenv("ANTHROPIC_API_KEY", ""),
            help="Auto-loaded from .env if available. Claude Sonnet will score completeness/faithfulness/relevance.",
        )

    btn_eval = st.button("🚀 Run Eval", type="primary", key="eval_run_btn")

    # ── Session state ─────────────────────────────────────────────────────────
    if "eval_results" not in st.session_state:
        st.session_state["eval_results"] = None
    if "eval_stats" not in st.session_state:
        st.session_state["eval_stats"] = None

    # ── Run eval ──────────────────────────────────────────────────────────────
    if btn_eval:
        eval_cases_path = os.path.join(os.path.dirname(__file__), "eval_cases.json")
        cases = nlq_eval.load_cases(eval_cases_path)

        # Select model source based on domain
        if eval_domain == "Northwind":
            eval_model_src = NORTHWIND_MODEL
        elif eval_domain == "ETF":
            eval_model_src = ETF_MODEL
        else:
            # For "All", we need to run each case with its own model
            eval_model_src = None

        # Auto-seed databases so answer accuracy can execute queries
        seed_status = st.empty()
        seed_status.info("Seeding databases for answer accuracy scoring...")
        _seed_ok = True
        if eval_domain in ("Northwind", "All"):
            r = post_json(f"{ENGINE_URL}/engine/sql", {
                "code": NORTHWIND_MODEL, "sql": NORTHWIND_SEED_SQL,
                "runtime": "northwind::runtime::NorthwindRuntime",
            })
            if not r.get("success"):
                seed_status.warning(f"Northwind seed failed: {r.get('error', 'unknown')}")
                _seed_ok = False
        if eval_domain in ("ETF", "All"):
            r = post_json(f"{ENGINE_URL}/engine/sql", {
                "code": ETF_MODEL, "sql": ETF_SEED_SQL,
                "runtime": "etf::EtfRuntime",
            })
            if not r.get("success"):
                seed_status.warning(f"ETF seed failed: {r.get('error', 'unknown')}")
                _seed_ok = False
        if _seed_ok:
            seed_status.success("Databases seeded successfully.")

        progress_bar = st.progress(0, text="Starting eval...")

        def update_progress(i, total, case_id):
            progress_bar.progress(i / total, text=f"Evaluating {case_id}… ({i}/{total})")

        if eval_model_src is not None:
            # Single domain
            eval_results = nlq_eval.run_eval(
                cases,
                eval_model_src,
                ENGINE_URL,
                llm_model=eval_llm,
                api_key=eval_api_key,
                domain_filter=eval_domain,
                progress_callback=update_progress,
            )
        else:
            # All domains — run each case with the correct model
            eval_results = []
            filtered = cases
            for i, case in enumerate(filtered):
                msrc = ETF_MODEL if case.domain == "ETF" else NORTHWIND_MODEL
                batch = nlq_eval.run_eval(
                    [case], msrc, ENGINE_URL,
                    llm_model=eval_llm,
                    api_key=eval_api_key,
                    domain_filter="All",
                )
                eval_results.extend(batch)
                update_progress(i + 1, len(filtered), case.id)

        progress_bar.progress(1.0, text="Eval complete!")
        st.session_state["eval_results"] = eval_results
        st.session_state["eval_cases"] = cases
        st.session_state["eval_stats"] = nlq_eval.summary_stats(eval_results, cases)

    # ── Display results ───────────────────────────────────────────────────────
    eval_stats = st.session_state.get("eval_stats")
    eval_results = st.session_state.get("eval_results")

    if eval_stats and eval_results:
        st.divider()

        # ── Summary metrics ───────────────────────────────────────────────────
        st.markdown("### Summary Metrics")
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Overall Score", f"{eval_stats['avg_overall_score']:.2f}",
                  help="Weighted composite (0-1). Combines recall (20%), query precision (10%), "
                       "answer accuracy (20%), ops coverage (10%), completeness (15%), "
                       "faithfulness (10%), relevance (15%).")
        m2.metric("Recall", f"{eval_stats['avg_recall']:.2f}",
                  help="Retrieval recall (0-1). Fraction of expected classes that the NLQ pipeline "
                       "actually retrieved. 1.0 = all required classes were found.")
        m3.metric("Query Precision", f"{eval_stats['avg_query_precision']:.2f}",
                  help="Query precision (0-1). Fraction of classes referenced in the generated Pure "
                       "query that are actually needed. 1.0 = no unnecessary class references.")
        m4.metric("Answer Acc.", f"{eval_stats['avg_answer_accuracy']:.2f}",
                  help="Answer accuracy (0-1). Compares the generated query's results against the "
                       "reference query: 60% normalized column name overlap (with fuzzy matching) "
                       "+ 40% row count similarity.")

        j1, j2, j3 = st.columns(3)
        j1.metric("Completeness", f"{eval_stats['avg_completeness']:.1f}/5",
                  help="LLM judge (1-5). Does the generated query capture all the data elements "
                       "and operations requested? 5 = perfectly complete, 1 = missing most elements.")
        j2.metric("Faithfulness", f"{eval_stats['avg_faithfulness']:.1f}/5",
                  help="LLM judge (1-5). Is the query accurate — no wrong filters, incorrect classes, "
                       "or hallucinated operations? 5 = fully faithful, 1 = significantly wrong.")
        j3.metric("Relevance", f"{eval_stats['avg_relevance']:.1f}/5",
                  help="LLM judge (1-5). Would the results actually answer the user's question? "
                       "5 = perfectly relevant, 1 = irrelevant results.")

        pass_col, succ_col, cnt_col = st.columns(3)
        pass_col.metric("Pass Rate", f"{eval_stats['pass_rate']:.0%}",
                        help="Percentage of cases with overall score > 0.6 (the passing threshold).")
        succ_col.metric("NLQ Success Rate", f"{eval_stats['success_rate']:.0%}",
                        help="Percentage of cases where the NLQ pipeline returned a valid Pure query "
                             "without errors.")
        cnt_col.metric("Cases Evaluated", eval_stats["count"])

        # Follow-up metrics (only show if decline cases exist)
        if eval_stats.get("follow_up_rate", 0) > 0 or any(
            r.follow_up_triggered for r in eval_results
        ):
            fu1, fu2 = st.columns(2)
            fu1.metric("Follow-up Rate", f"{eval_stats.get('follow_up_rate', 0):.0%}",
                       help="Among cases marked expectDecline, what fraction did the system actually decline? Target: 85%.")
            fu2.metric("Follow-up Usefulness", f"{eval_stats.get('follow_up_usefulness', 0):.2f}/5",
                       help="Among correct declines, how useful was the follow-up question? (LLM judge, 1-5 scale). Target: 4.25/5.")

        # ── Explain section — diagnostic commentary ──────────────────────────
        with st.expander("📖 Explain these metrics", expanded=False):
            _s = eval_stats

            # --- Overall Score ---
            overall = _s["avg_overall_score"]
            if overall >= 0.90:
                st.success(f"**Overall Score ({overall:.2f}):** Excellent — the NLQ pipeline is performing well across all dimensions.")
            elif overall >= 0.75:
                st.info(f"**Overall Score ({overall:.2f}):** Good, but room for improvement. Check the weaker metrics below for specific guidance.")
            else:
                st.warning(f"**Overall Score ({overall:.2f}):** Needs attention. One or more metrics are dragging down the composite score significantly.")
            st.caption("Weighted composite: Recall (20%) + Query Precision (10%) + Answer Accuracy (20%) + Ops Coverage (10%) + Completeness (15%) + Faithfulness (10%) + Relevance (15%)")

            st.markdown("---")

            # --- Recall ---
            recall = _s["avg_recall"]
            if recall >= 0.95:
                st.markdown(f"**Recall ({recall:.2f}):** All required classes are being retrieved. No action needed.")
            elif recall >= 0.80:
                st.markdown(f"**Recall ({recall:.2f}):** Most classes retrieved, but some are being missed. Consider adding more synonyms/descriptions to NlqProfile annotations or increasing association expansion hops.")
            else:
                st.markdown(f"**Recall ({recall:.2f}):** Many required classes are not being retrieved. Check that the semantic index has sufficient NlqProfile annotations (descriptions, synonyms, exampleQuestions) for the missing classes.")

            # --- Query Precision ---
            qprec = _s["avg_query_precision"]
            if qprec >= 0.90:
                st.markdown(f"**Query Precision ({qprec:.2f}):** The generated queries reference only the classes they need. Excellent targeting.")
            elif qprec >= 0.70:
                st.markdown(f"**Query Precision ({qprec:.2f}):** Most class references in generated queries are necessary, but some queries reference extra classes. Check for unnecessary association navigation in the generated Pure expressions.")
            else:
                st.markdown(f"**Query Precision ({qprec:.2f}):** Generated queries frequently reference classes they don't need. The LLM may be over-navigating associations or using wrong root classes.")

            # --- Retrieval Precision (diagnostic) ---
            precision = _s["avg_precision"]
            st.markdown(f"**Retrieval Precision ({precision:.2f}):** *(diagnostic — not in overall score)* Measures how targeted TF-IDF class retrieval was. On small models this is structurally capped (~0.33–0.50).")

            # --- Answer Accuracy ---
            ans_acc = _s["avg_answer_accuracy"]
            # Count cases with 0.0 answer accuracy
            zero_acc_cases = [r for r in eval_results if r.answer_accuracy == 0.0 and r.success]
            low_acc_cases = [r for r in eval_results if 0.0 < r.answer_accuracy < 0.5 and r.success]
            if ans_acc >= 0.90:
                st.markdown(f"**Answer Accuracy ({ans_acc:.2f}):** Excellent — generated queries produce results very close to the reference.")
            elif ans_acc >= 0.70:
                reasons = []
                if zero_acc_cases:
                    zero_ids = ", ".join(r.case_id for r in zero_acc_cases[:5])
                    reasons.append(f"**{len(zero_acc_cases)} case(s) scored 0.0** (query execution failed — likely Pure syntax errors): {zero_ids}")
                if low_acc_cases:
                    low_ids = ", ".join(r.case_id for r in low_acc_cases[:5])
                    reasons.append(f"**{len(low_acc_cases)} case(s) scored below 0.5** (column alias mismatches or different row counts): {low_ids}")
                st.markdown(f"**Answer Accuracy ({ans_acc:.2f}):** Good but not great. This metric executes both generated and reference queries, then compares column names (60%) and row counts (40%).")
                if reasons:
                    st.markdown("Improvement opportunities:")
                    for r in reasons:
                        st.markdown(f"- {r}")
                st.markdown("Common causes: wrong sort syntax (`descending('col')` vs `~col->descending()`), column alias mismatches (`productName` vs `product`), filter placement errors (post-project filter on non-projected column).")
            else:
                st.markdown(f"**Answer Accuracy ({ans_acc:.2f}):** Low — many generated queries fail to execute or produce very different results than reference. Check that the database is seeded and that Pure syntax in the system prompt matches the engine's parser.")
                if zero_acc_cases:
                    zero_ids = ", ".join(r.case_id for r in zero_acc_cases[:8])
                    st.markdown(f"- Cases with 0.0 (execution failures): {zero_ids}")

            # --- Completeness ---
            comp = _s["avg_completeness"]
            if comp >= 4.5:
                st.markdown(f"**Completeness ({comp:.1f}/5):** The LLM captures nearly all requested data elements and operations.")
            elif comp >= 3.5:
                st.markdown(f"**Completeness ({comp:.1f}/5):** Some requested columns or operations are being omitted. Common issue: LLM projects fewer columns than the question implies. Adding more exampleQuestions to NlqProfile can help.")
            else:
                st.markdown(f"**Completeness ({comp:.1f}/5):** Significant elements are missing from generated queries. Review system prompt examples and ensure they demonstrate the expected level of detail.")

            # --- Faithfulness ---
            faith = _s["avg_faithfulness"]
            if faith >= 4.5:
                st.markdown(f"**Faithfulness ({faith:.1f}/5):** Queries are logically accurate with correct filters, classes, and operations.")
            elif faith >= 3.5:
                st.markdown(f"**Faithfulness ({faith:.1f}/5):** Minor logical errors in some queries — wrong filter values, incorrect root class, or misapplied operations. Check ROOT CLASS SELECTION rules in system prompt.")
            else:
                st.markdown(f"**Faithfulness ({faith:.1f}/5):** Frequent logical errors. The LLM may be hallucinating operations or using wrong classes.")

            # --- Relevance ---
            rel = _s["avg_relevance"]
            if rel >= 4.5:
                st.markdown(f"**Relevance ({rel:.1f}/5):** Generated queries consistently answer the user's question.")
            else:
                st.markdown(f"**Relevance ({rel:.1f}/5):** Some queries don't address the actual question. This suggests the LLM is misinterpreting the intent.")

            # --- Follow-up Rate ---
            fu_rate = _s.get("follow_up_rate", 0)
            fu_useful = _s.get("follow_up_usefulness", 0)
            if fu_rate > 0 or any(r.follow_up_triggered for r in eval_results):
                st.markdown("---")
                if fu_rate >= 0.85:
                    st.markdown(f"**Follow-up Rate ({fu_rate:.0%}):** Excellent — the system correctly declines unanswerable questions at or above the 85% target.")
                elif fu_rate >= 0.60:
                    st.markdown(f"**Follow-up Rate ({fu_rate:.0%}):** The system declines most unanswerable questions but misses some. Review the decline prompt instructions — the LLM may be generating queries for questions it should refuse.")
                else:
                    st.markdown(f"**Follow-up Rate ({fu_rate:.0%}):** Low — the system is generating queries for many unanswerable questions instead of declining. Check that the WHEN TO DECLINE instructions in the system prompt are clear enough.")

                if fu_useful >= 4.25:
                    st.markdown(f"**Follow-up Usefulness ({fu_useful:.2f}/5):** Excellent — follow-up questions are specific and actionable, meeting the 4.25/5 target.")
                elif fu_useful >= 3.0:
                    st.markdown(f"**Follow-up Usefulness ({fu_useful:.2f}/5):** Adequate but could be more specific. The LLM should generate follow-up questions that precisely identify what information is missing or why the question can't be answered.")
                else:
                    st.markdown(f"**Follow-up Usefulness ({fu_useful:.2f}/5):** Low — follow-up questions are too generic. Consider adding examples of good follow-up questions to the system prompt.")


        # Per-domain breakdown
        by_diff = eval_stats.get("by_difficulty", {})
        if by_diff:
            st.markdown("#### Per-Domain Breakdown")
            for domain_name, domain_stats in by_diff.items():
                st.caption(
                    f"**{domain_name}**: {domain_stats['count']} cases, "
                    f"avg score={domain_stats['avg_overall_score']:.2f}, "
                    f"avg recall={domain_stats['avg_recall']:.2f}, "
                    f"pass rate={domain_stats['pass_rate']:.0%}"
                )

        st.divider()

        # ── Per-case table ────────────────────────────────────────────────────
        st.markdown("### Per-Case Results")
        import pandas as pd

        table_data = []
        for r in eval_results:
            table_data.append({
                "ID": r.case_id,
                "Score": round(r.overall_score, 3),
                "Decline": "✓" if r.follow_up_triggered else "",
                "Recall": round(r.retrieval_recall, 2),
                "Q.Prec": round(r.query_precision, 2),
                "Ret.P": round(r.retrieval_precision, 2),
                "Ans. Acc.": round(r.answer_accuracy, 2),
                "Compl.": round(r.judge_completeness, 1),
                "Faith.": round(r.judge_faithfulness, 1),
                "Relev.": round(r.judge_relevance, 1),
                "Ops Cov.": round(r.ops_coverage, 2),
                "Root OK": "✓" if r.root_class_match else "✗",
                "Pass": "✅" if r.overall_score > 0.6 else "❌",
                "Latency": f"{r.latency_ms}ms",
                "Error": r.error or "",
            })

        st.dataframe(pd.DataFrame(table_data), use_container_width=True, hide_index=True)

        # ── Expandable details ────────────────────────────────────────────────
        st.markdown("### Case Details")
        for r in eval_results:
            status = "✅" if r.overall_score > 0.6 else "❌"
            with st.expander(f"{status} {r.case_id} — score={r.overall_score:.3f}", expanded=False):
                if r.error:
                    st.error(f"Error: {r.error}")
                if r.generated_query:
                    st.markdown("**Generated Query:**")
                    st.code(r.generated_query, language="text")
                # Find the matching case for reference query
                eval_cases_path = os.path.join(os.path.dirname(__file__), "eval_cases.json")
                all_cases = nlq_eval.load_cases(eval_cases_path)
                matching = [c for c in all_cases if c.id == r.case_id]
                if matching:
                    ref_q = matching[0].expected.get("referenceQuery", "")
                    if ref_q:
                        st.markdown("**Reference Query:**")
                        st.code(ref_q, language="text")
                    st.caption(f"Question: {matching[0].question}")
                    st.caption(f"Difficulty: {matching[0].difficulty}")
                if r.judge_rationale:
                    st.markdown(f"**Judge rationale:** {r.judge_rationale}")
                st.caption(
                    f"Recall={r.retrieval_recall:.2f} | Q.Prec={r.query_precision:.2f} | "
                    f"Ret.P={r.retrieval_precision:.2f} | "
                    f"Ops={r.ops_coverage:.2f} | Root={'✓' if r.root_class_match else '✗'} | "
                    f"Latency={r.latency_ms}ms"
                )


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 7 — About
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

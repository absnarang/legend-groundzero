# Legend Ground Zero

> **The definitive starting point for grounding AI agents in institutional data logic with zero friction**

An interactive Streamlit playground that brings together the full Legend Intelligence engine — Pure language queries, real-time SQL compilation, and LLM-powered natural language querying — in a single zero-friction UI.

---

## What It Is

Ground Zero is the **front door** to the Legend stack. Point it at a running [legend-intelligence](https://github.com/absnarang/legend-intelligence) backend and you get:

- **Pure ↔ SQL bidirectional editor** — write Pure, see the exact generated SQL; edit SQL, get it translated back to Pure
- **Query executor** — run Pure queries against in-memory DuckDB, see results as a table
- **NLQ tab** — type a question in plain English, get a runnable Pure query (Claude haiku/sonnet/opus via your Pro/Max subscription)
- **Pre-built financial data model** — ETF/Mutual Fund model with Fund, Security, Holding, NAVRecord classes + realistic seed data
- **Clickable example questions** — 7 sample NLQ questions for the ETF domain, 4 for Company/Person

---

## Quick Start

```bash
# 1. Install dependencies
pip install streamlit requests pandas

# 2. Start the legend-intelligence backend (port 8080)
#    See: https://github.com/absnarang/legend-intelligence

# 3. Run the playground
streamlit run playground.py
```

Open **http://localhost:8501** in your browser.

---

## Tabs

| Tab | Description |
|-----|-------------|
| **⇄ Pure ↔ SQL** | Bidirectional editor: Pure → SQL via engine compiler; SQL → Pure via Claude |
| **🗄️ Raw SQL** | Execute raw SQL directly against the DuckDB store |
| **🌱 Seed Data** | View and run the SQL seed scripts to populate in-memory tables |
| **🔍 NLQ** | Natural language → Pure query via the NLQ pipeline |
| **📖 About** | Pure syntax quick reference + how the engine works |

---

## NLQ Tab

The NLQ tab connects to the `/engine/nlq` endpoint on the legend-intelligence backend.

**Supported LLM models** (all via your Claude Pro/Max subscription — no API key needed):
- `claude-haiku-4-5` — fastest, default
- `claude-sonnet-4-6` — more capable
- `claude-opus-4-6` — most capable

**Domain models:**
- ETF / Mutual Fund (financial) — Fund, Security, Holding, NAVRecord with full NlqProfile annotations
- Company / Person (default) — Person, Department with association-based JOINs

---

## Example NLQ Questions

```
What are the top 5 holdings of SPY by weight?
Which EQUITY ETFs have expense ratio below 0.1%?
Show me all TECHNOLOGY stocks with market cap above 2 trillion
What was the average NAV of QQQ in January 2024?
Which funds hold AAPL and what is its total weight across all ETFs?
```

---

## Architecture

```
playground.py (Streamlit)
    │
    ├── POST /engine/plan      → Pure → SQL (compile only)
    ├── POST /engine/execute   → Pure → results
    ├── POST /engine/sql       → raw SQL → results
    └── POST /engine/nlq       → English → Pure query
         │
         └── legend-intelligence backend (Java, port 8080)
```

---

## Related

- [legend-intelligence](https://github.com/absnarang/legend-intelligence) — the Pure language engine and NLQ pipeline (Java backend)

# LucasAgent — Persistent Memory

> This file mirrors what the agent's persistent memory should contain.
> Load this into the agent via the `memory` tool after migration.

---

## CRITICAL_PROTOCOL

1️⃣ Analyze → 2️⃣ Execute & Test → 3️⃣ Fact‑Check → 4️⃣ Self‑Correct → 5️⃣ Output

Rules: use live Supabase data, no hallucinations, no extra commentary, only what asked. Silent failures are retried.

---

## User Profile

- **Name:** Maria (Flak)
- **Role:** M&E Fresh Eggs PM (Cebu, Philippines, PHT/UTC+8)
- **Supervisor pattern:** OWL = orchestrator, delegates to GC agents
- **Budget:** flash default, pro for complex tasks
- **Preferences:** Concise, direct, emoji-friendly. Self-corrects, no hallucinations.
- **Platform:** Telegram (group: M&E Fresh Eggs)

---

## Sales Input Rule

Only execute sales when message starts with `-sale`. Do NOT process sales from plain messages.

---

## Model Budget

- **Default:** openrouter/free or deepseek/deepseek-v4-flash
- **Complex tasks:** deepseek-v4-pro via OpenRouter
- **Never waste pro on simple queries**

---

## M&E Supabase

- **Project ref:** npohyeqnaltpqzmmlmej
- **Source of truth:** Supabase DB
- **GC1 scope:** M&E Fresh Eggs ONLY ("nothing else")
- **Read:** REST API with anon key
- **Write:** MCP SQL tool (`mcp_M_E_Fresh_Eggs_execute_sql`)
- **cost_per_egg in deliveries = cost PER TRAY** (mislabeled column)

---

## MCP SQL Timezone (CRITICAL)

`CURRENT_DATE` in MCP SQL returns **UTC date**, which is WRONG for PHT between midnight–8AM.

**Fix:** Always compute PHT date via:
```sql
SELECT (CURRENT_DATE + INTERVAL '8 hours')::date::text as pht_today
```
Then pass as explicit string. **NEVER use `CURRENT_DATE` alone in INSERT/UPDATE.**

Affected tables: sales, deliveries, expenses, spoilage, operational_funds.

---

## Egg Size IDs

| ID | Name |
|----|------|
| 1 | Peewee |
| 2 | Pullet |
| 3 | Small |
| 4 | Medium |
| 5 | Large |
| 6 | Extra Large |
| 7 | Jumbo |

**TRAY_SIZE = 30**

---

## Suppliers

| ID | Name | Phone | Notes |
|----|------|-------|-------|
| 1 | Lilanie Fernandez-Robert | 09668791926 | 2 times per week delivery |
| 2 | renren | +639762489371 | monday and friday - Pardo |

---

## Agentic Harness

- **GC1** = M&E Fresh Eggs operator (this agent)
- **OWL** = supervisor/orchestrator
- **Escalation:** retry → circuit breaker → self-correct → alert OWL → DM user
- **Two-tier auth:** REST anon = read, MCP SQL = write
- **Idempotency:** hash key prevents duplicate actions
- **Scope lock:** M&E ONLY

---

## Cron Jobs

| Job | Schedule | Job ID |
|-----|----------|--------|
| 1% Daily Revenue Cut | `0 21 * * *` | 02aa52a89e5d |
| Daily Sales Report | `0 8 * * *` | de60bc545060 |
| Health Check | `0 */2 * * *` | c2b0812e16f5 |
| Weekly Trend Report | `0 9 * * 1` | ebb091eaad88 |
| Data Sync | `*/5 * * * *` | 21edf0586dca |

---

## Key Dates

| Value | Meaning |
|-------|---------|
| `EXPENSE_TRACKING_START = '2026-06-19'` | Only expenses on/after this date reduce operational_funds balance |

---

## Known Pitfalls

1. Do NOT manually update inventory on sale insert — trigger handles it
2. ALWAYS restore inventory on delete — no DELETE trigger exists
3. TRAY_SIZE is always 30
4. Check stock BEFORE insert — prevent negative inventory
5. cost_per_egg column in deliveries stores cost PER TRAY
6. Anon key is masked in config.yaml — use MCP SQL for all writes
7. MCP SQL time syntax: use `NOW()::time`, never `AT TIME ZONE`
8. NO HALLUCINATED SALES — only insert what user explicitly states
9. NO DUPLICATES — check within conversation before inserting
10. tray_size NULL for piece sales

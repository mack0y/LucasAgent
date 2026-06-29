# LucasAgent — Persistent Memory

> This file mirrors what the agent's persistent memory should contain.
> Load this into the agent via the `memory` tool after migration.
> Last Supabase sync: 2026-06-29 ~07:00 PHT. Last verification loop: per-task subagent verification active since 2026-06-28 20:00 PHT. Agent identity restores as-is with this repo as self-backup.

---

## CRITICAL_PROTOCOL

1️⃣ Analyze → 2️⃣ Execute & Test → 3️⃣ Fact‑Check → 4️⃣ Self‑Correct → 5️⃣ Output

Rules: use live Supabase data, no hallucinations, no extra commentary, only what asked. Silent failures are retried.

---

## User Profile

- **Name:** Maria (Flak)
- **Role:** M&E Fresh Eggs PM (Cebu, Philippines, PHT/UTC+8)
- **Supervisor pattern:** OWL = orchestrator, delegates to GC agents
- **Preferences:** Concise, direct, emoji-friendly. Self-corrects, no hallucinations.
- **Platform:** Telegram (group: M&E Fresh Eggs)

---

## Sales Input Rule

Only execute sales when message starts with `-sale`. Do NOT process sales from plain messages.

---

## Model Config

- **Provider:** nous
- **Default:** stepfun/step-3.7-flash:free

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

## Egg Size IDs (Sales lookup base)
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

## Prices (from price_settings — source of truth)

| Size | per piece | per tray |
|------|-----------|----------|
| Peewee | 5.00 | 110.00 |
| Pullet | 6.50 | 185.00 |
| Small | 7.00 | 190.00 |
| Medium | 7.50 | 210.00 |
| Large | 8.50 | 245.00 |
| Extra Large | 9.00 | 260.00 |
| Jumbo | 9.50 | 275.00 |

---

## Suppliers

| ID | Name | Phone | Notes |
|----|------|-------|-------|
| 1 | Lilanie Fernandez-Robert | 09668791926 | 2 times per week delivery |
| 2 | renren | +639****9371 | monday and friday - Pardo |

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
| 1% Daily Revenue Cut | `0 21 * * *` | 542d5b031dee |
| Daily Sales Report | `0 8 * * *` | 0c0abb5d30b4 |
| Weekly Trend Report | `0 9 * * 1` | 0ed98d59c714 |
| Daily Self-Audit Report | `0 22 * * *` | 8bfa5438241c |

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
11. **Verification loop:** After every action, spawn backend verifier subagent; no report to user until verification passes
12. **Model drift:** Default provider is `nous`, model is `stepfun/step-3.7-flash:free`; do not use openrouter defaults in verifier/cron configs

---
name: me-fresh-eggs-harness
description: Agentic harness for M&E Fresh Eggs GC — wraps the delegated agent with reliability, QA, circuit breaker, and observability layers. Isolated memory, full autonomy, Telegram platform.
---

# M&E Fresh Eggs — Agentic Harness

## 🎯 Purpose

This harness wraps the delegated agent operating in the **M&E Fresh Eggs** Telegram group chat (GC). It provides:

| Layer | What It Does |
|-------|-------------|
| **Reliability Wrapper** | Retry + idempotency on every tool call |
| **QA Verification** | Validates outputs before acting (5-step protocol) |
| **Circuit Breaker** | Stops calling failing tools after threshold |
| **Observability** | Logs, traces, alerts on anomalies |
| **Escalation** | Auto-retry → self-correct → alert main agent |

## 🏗️ Architecture

```
Group Chat (M&E Fresh Eggs) ← Telegram
        │
        ▼
┌──────────────────────────────┐
│  Harness Controller          │
│  ┌────────────────────────┐  │
│  │ Reliability Wrapper    │  │ ← retry, idempotency, timeout
│  │ ┌──────────────────┐  │  │
│  │ │ QA Verification  │  │  │ ← schema, bounds, auth check
│  │ │ ┌────────────┐  │  │  │
│  │ │ │ Agent Core │  │  │  │ ← full tool access
│  │ │ └────────────┘  │  │  │
│  │ └──────────────────┘  │  │
│  └────────────────────────┘  │
│  ┌────────────────────────┐  │
│  │ Circuit Breaker        │  │ ← fail-open after threshold
│  └────────────────────────┘  │
│  ┌────────────────────────┐  │
│  │ Observability Logger   │  │ ← traces, metrics, alerts
│  └────────────────────────┘  │
└──────────────────────────────┘
        │
        ▼
   Supabase (source of truth)
```

## 🔧 Configuration

### Agent Identity
- **GC Name:** M&E Fresh Eggs
- **Platform:** Telegram
- **Autonomy:** Full (no approval gates for read/write within project scope)
- **Memory:** Isolated (separate from other GCs)
- **Source of Truth:** Supabase (npohyeqnaltpqzmmlmej)

### Failure Behavior (Escalation Ladder)

```
Level 0: Tool call succeeds → return result
Level 1: Tool call fails (transient) → retry with backoff (max 2)
Level 2: Tool call fails (persistent) → circuit breaker opens, skip & continue
Level 3: Agent confused/wrong → self-correct loop (5-step protocol)
Level 4: 3 consecutive failures → alert main agent (OWL)
Level 5: Agent crashed/stuck → main agent spawns replacement
Level 6: All recovery fails → DM user (Flak) as final fallback
```

### Circuit Breaker Settings

| Parameter | Value |
|-----------|-------|
| Failure threshold | 3 consecutive failures |
| Cooldown period | 60 seconds |
| Half-open probe | 1 test call after cooldown |
| Per-tool tracking | Yes (each tool independent) |

### QA Verification Rules

Before any **write** action (Supabase INSERT/UPDATE, send message, execute command):

1. **Schema Check** — Does data match expected format?
2. **Bounds Check** — Is value within acceptable range? (e.g., qty > 0, amount > 0)
3. **Auth Check** — Is this agent allowed this operation? (full autonomy = all project ops allowed)
4. **Idempotency Check** — Has this exact action already succeeded?
5. **Self-Correct** — If check fails, can agent fix? (max 2 correction attempts)

### Idempotency Keys

```
idempotency_key = hash(agent_id + tool_name + normalized_params + session_date)
```

If same key already in idempotency log → return cached result, skip execution.

### Observability

Every tool call through the harness logs:
- Timestamp
- Agent ID
- Tool name + params (sanitized)
- Result status (success/failure/retry)
- Duration
- Idempotency key

**Alert conditions:**
- Circuit breaker opens → log WARN
- 3+ retries in 5 min → log WARN
- QA rejection → log ERROR
- Agent crash → alert main agent

## 📋 Operational Procedures

### Daily Startup (automatic via cron)
1. Check Supabase connectivity (REST API health)
2. Load today's context (pricing, inventory snapshot)
3. Verify idempotency log is clean
4. Report ready to main agent

### On Every Incoming Message
1. Parse message → identify intent
2. Route to appropriate tool(s)
3. Wrap each tool call in reliability layer
4. Execute with QA verification
5. Return response to group chat
6. Log to observability

### End of Day (automatic via cron)
1. Generate daily sales summary
2. Update inventory snapshots
3. Log any anomalies detected
4. Archive idempotency keys (keep 7 days)

## 🛡️ Guardrails

- **Scope lock:** This GC = M&E Fresh Eggs ONLY. No other projects, no TrendWire, no side quests. All skills under this harness serve one business.
- **Supabase access:** READ via anon key (reporting) + WRITE via MCP SQL or dedicated scripts (sales input, inventory adjustments).
- **No cross-GC access:** This agent cannot read/write data for other GCs.
- **Secret redaction:** API keys never logged or outputted.
- **Context compression:** Auto-compress when approaching token limit.
- **Budget awareness:** Prefer deepseek-v4-flash for simple queries. Zero-token scripts for routine reports.
- **🚨 PHT timezone for ALL date columns:** Supabase runs on UTC. Between 12AM–8AM PHT, `CURRENT_DATE` returns the previous day. For ANY insert/update involving a date column (`sale_date`, `delivery_date`, `expense_date`, `spoilage_date`, `fund_date`), you MUST first run `SELECT (CURRENT_DATE + INTERVAL '8 hours')::date::text as pht_today` and use the returned string. NEVER use `CURRENT_DATE` directly in INSERT/UPDATE. See `me-sales-input` pitfall 8a and `references/timezone-fix-and-cron-patterns.md` for full details and real failure example (sale #1066).

## ⚠️ CRITICAL: Write Operations Require Different Auth

This harness has **two tiers** of Supabase access:

| Operation | Auth Method | Examples |
|-----------|-------------|---------|
| **Read/Report** | REST API with anon key | fetchSales, fetchInventory, fetchPriceSettings |
| **Write/Input** | MCP SQL tool (supports INSERT/UPDATE/DELETE) OR dedicated Python scripts | recordSale, updateInventory, recordDelivery, recordExpense, recordSpoilage |

The `daily_report.py` script uses REST API (anon, read-only). Write operations go through the MCP SQL tool (`mcp_M_E_Fresh_Eggs_execute_sql`) or through dedicated Python scripts like `record_sale.py`.

**Never attempt INSERT/UPDATE/DELETE via the anon key REST API — it will be blocked by RLS.**

## 🔗 Source of Truth: GitHub Repo

The **authoritative business logic** for M&E Fresh Eggs lives in:
- **Live app:** https://mack0y.github.io/M-EFresheggs/
- **Source code:** https://github.com/mack0y/M-EFresheggs

When building or updating skills for this GC, **always reference the app repo first**:
- `src/lib/api.js` — all 38+ Supabase API functions (the canonical implementation)
- `src/components/` — UI components that encode business rules (stock checks, calculations, undo logic)
- `database_schema.sql` — table definitions + triggers (auto-deduct inventory on sale/spoilage INSERT)

**This GC = M&E Fresh Eggs only.** No other projects, no TrendWire, no side quests. All skills under this harness serve one business: M&E Fresh Eggs egg sales + operations.

## ⚠️ Known Pitfalls

| Pitfall | Impact | Fix |
|---------|--------|-----|
| **OpenRouter credit wall (402)** | `delegate_task` fails immediately when credits exhausted | Add credits at `openrouter.ai/settings/credits`. Workaround: use `no_agent: true` scripts |
| **Key rotation** | New API key not reflected in all scripts | Update hex in `daily_report.py`, `me_health_check.py`, and `.env` simultaneously |
| **SSL timeout (transient)** | Health check reports false failure | Retry with backoff; single table timeout ≠ systemic issue |
| **Isolated memory drift** | GC agent loses context after session restart | Re-load from Supabase (source of truth) on startup |

## 📊 Reports Available

| Report | Trigger | Output | Status |
|--------|---------|--------|--------|
| Daily Sales | End of day / on-demand | Sales by size, total revenue, txns | ✅ `daily-reporting` skill |
| Inventory Snapshot | On-demand | Stock levels, alerts for low/out | ✅ `daily-reporting` skill |
| Anomaly Report | On-demand | Unusual patterns, failures, circuit opens | ✅ Via health check cron |
| Weekly Trend | Weekly | WoW comparison, trend direction | ✅ `daily-reporting` skill |
| 1% Revenue Cut | Daily 21:00 PHT (cron `02aa52a89e5d`) | Computes 1% of day's revenue → operational_funds | ✅ Cron job |

### Write Operations

| Operation | Description | Status |
|-----------|-------------|--------|
| Record Sale | INSERT sale + auto-calc total + trigger deducts inventory | ✅ `me-sales-input` skill |
| Delete Sale | DELETE sale + restore inventory manually | ✅ `me-sales-input` skill |
| List Recent | Paginated sales with egg size joined | ✅ `me-sales-input` script |
| Record Spoilage | Log damaged eggs + trigger deducts inventory | ❌ Skill needed |
| Record Delivery | Batch receive stock from supplier | ❌ Skill needed |
| Update Payment | Mark delivery paid/unpaid | ❌ Skill needed |
| Record Expense | Log operating expense | ✅ `me-sales-input` skill (shared) |
| Add Operational Fund | Log capital injection | ❌ Skill needed |
| Daily Revenue Cut (1%) | Auto-compute & record at 21:00 PHT | ✅ Cron job `02aa52a89e5d` |
| Add Customer/Supplier | Master data CRUD | ❌ Skill needed |
| Manual Inventory | Stock count adjustments | ❌ Skill needed |

**All write operations go through MCP SQL (INSERT/UPDATE/DELETE) or dedicated Python scripts (record_sale.py). REST API is read-only.**

**All write operations should replicate the exact logic from the app repo.**

## 🧪 Health Checks & Supabase REST API Syntax

```bash
# Supabase connectivity
curl -s "https://npohyeqnaltpqzmmlmej.supabase.co/rest/v1/egg_sizes?select=*&limit=1&apikey=<key>" | head -1

# Check recent sales (last 24h)
curl -s "https://npohyeqnaltpqzmmlmej.supabase.co/rest/v1/sales?select=total_amount&sale_date=gte.$(date -d '-1 day' +%F)&apikey=<key>" | jq '[.[]|.total_amount]|add'
```

### Supabase REST API Filter Syntax (learned from memory sync)

```
# Equality (single field)
?id=eq.{uuid}

# OR clause (multiple values) — use dot notation, commas separate
?or=(id.eq.uuid1,id.eq.uuid2,id.eq.uuid3)

# Combined filters (AND)
?select=*&sale_date=gte.2026-06-01&sale_date=lte.2026-06-30

# Upsert (insert or update on conflict)
POST /rest/v1/table
Headers: Prefer: resolution=merge-duplicates,return=minimal
Body: { "col": "val" }

# Delete by ID
DELETE /rest/v1/table?id=eq.{id}
```

**Common mistakes:**
- `id=eq.{id}` is WRONG — use `id.eq.{uuid}` (dot notation)
- `or=(id=eq.a,id=eq.b)` is WRONG — use `or=(id.eq.a,id.eq.b)`
- Batch deletes with `or=()` work for up to 10 IDs per request

## 📝 Notes

- This GC handles ALL M&E Fresh Eggs business operations
- Peewee/Pullet/Small/Medium/Large/Extra Large/Jumbo egg sizes
- Sales, inventory, deliveries, spoilage, expenses, customers, suppliers
- Pricing per piece and per tray
- Currency: PHP (₱)
- Timezone: PHT (UTC+8) — see `references/timezone-fix-and-cron-patterns.md` for MCP SQL procedure
- See `references/owl-gc-delegation.md` for the OWL/GC delegation pattern and escalation ladder
- See `references/app-business-rules.md` for the condensed business logic from the app repo
- See `references/supabase-rest-api-syntax.md` for Supabase REST API filter/mutation syntax (learned from memory sync)

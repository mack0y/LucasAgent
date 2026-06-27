# MCP SQL Timezone Fix & Cron Patterns

## Timezone Bug — Root Cause

Supabase Postgres runs on UTC. The Philippines is UTC+8. Between 12:00 AM and 8:00 AM PHT, `CURRENT_DATE` in SQL returns the **previous day's date**.

**Example:** At 6:00 AM PHT on June 27, `CURRENT_DATE` returns `2026-06-26`.

This causes:
- Sales inserted with wrong date → invisible in web UI "Today" filter
- Deliveries tagged wrong day → Reports show wrong period
- Expenses/funds misdated → balance calculations off

## The Fix — Always Use This Pattern

```sql
-- STEP 1: Get PHT date (run this FIRST, always)
SELECT (CURRENT_DATE + INTERVAL '8 hours')::date::text as pht_today;

-- STEP 2: Use the returned string in INSERT/UPDATE
-- Example: pht_today = '2026-06-27'
INSERT INTO sales (egg_size_id, quantity, unit, tray_size, total_amount, sale_date, sale_time)
VALUES (2, 9, 'piece', NULL, 58.50, '2026-06-27', NOW()::time);
```

**NEVER:**
- Use `CURRENT_DATE` in INSERT/UPDATE
- Hardcode a date without querying first
- Trust your own date calculation (agent may run in different timezone context)

**Affected tables with DATE columns:**
- `sales.sale_date`
- `deliveries.delivery_date`
- `expenses.expense_date`
- `spoilage.spoilage_date`
- `operational_funds.fund_date`

## Real Failure — Sale #1066

- **What happened:** Agent inserted 9 pcs Pullet sale at 6AM PHT using `CURRENT_DATE`
- **Result:** Stored as `2026-06-26` instead of `2026-06-27`
- **Symptom:** Sale invisible in web UI "Today" filter
- **Fix:** `UPDATE sales SET sale_date = '2026-06-27', sale_time = '06:05:00' WHERE id = 1066;`

## Cron Job Pattern — 1% Daily Revenue Cut

A daily cron at 21:00 PHT computes 1% of day's revenue and records it as an operational fund.

### Guardrails (all required):
1. **PHT date** — compute via `(CURRENT_DATE + INTERVAL '8 hours')::date::text`
2. **Duplicate check** — query `operational_funds` for today's cut before inserting
3. **Zero check** — if no sales today, skip (don't insert ₱0)
4. **Sequential operations** — check first, then insert (not atomic) for idempotency

### SQL Flow:
```sql
-- 1. Get PHT date
SELECT (CURRENT_DATE + INTERVAL '8 hours')::date::text as pht_today;

-- 2. Get today's revenue
SELECT SUM(total_amount) FROM sales WHERE sale_date = '{pht_today}';

-- 3. Check if already recorded
SELECT id FROM operational_funds 
WHERE fund_date = '{pht_today}' AND description = '1% Daily Revenue Cut';

-- 4. Insert only if new AND revenue > 0
INSERT INTO operational_funds (amount, description, fund_date)
VALUES ({cutAmount}, '1% Daily Revenue Cut', '{pht_today}');
```

### Web App Equivalent:
- `getLocalDate()` → `toLocaleDateString('en-CA', {timeZone: 'Asia/Manila'})`
- `recordDailyRevenueCut()` in `src/lib/api.js`
- UI button in `ExpensesFunds.jsx` — green "Daily Cut" button

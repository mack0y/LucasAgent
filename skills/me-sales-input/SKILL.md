---
name: me-sales-input
description: Record, delete, and undo sales for M&E Fresh Eggs. Mirrors the web app (mack0y/M-EFresheggs) logic - stock check, auto-price calc, inventory auto-deduct via Supabase trigger, stock restore on delete.
---

# M&E Fresh Eggs - Sales Input Skill

## Scope

**This skill serves M&E Fresh Eggs ONLY.** No other projects, no side quests. All operations are scoped to the M&E Fresh Eggs Supabase project (npohyeqnaltpqzmmlmej).

## Purpose

Replicates the SalesLog.jsx logic from https://mack0y.github.io/M-EFresheggs/ as a chat-accessible skill. Record sales via conversation with the same business rules as the web app.

## Business Rules

1. **Stock check before sale** - reject if totalEggs > stock_on_hand
2. **Auto-price from price_settings** - total_amount = qty x price_per_piece or qty x price_per_tray
3. **Auto-deduct inventory** - Supabase trigger `after_sale_insert` handles this on INSERT. Do NOT manually update inventory on insert.
4. **Stock restore on delete** - NO DELETE trigger exists. Must manually add back eggCount to inventory.quantity_on_hand.
5. **Tray size** = 30 eggs (constant TRAY_SIZE = 30)
6. **Egg size IDs:** Peewee=1, Pullet=2, Small=3, Medium=4, Large=5, Extra Large=6, Jumbo=7
7. **Timezone:** PHT (UTC+8) for date/time stamping

## Command: `-sale`

**IMPORTANT `/sale` is intercepted by Hermes as "unknown command". Use the **dash-prefix** instead:**

```
-sale 3 pcs Large
-sale 1 tray Small
-sale 2 trays Medium, 5 pcs Jumbo
-sale 1 tray Medium
```

When the message starts with `-sale`, skip straight to parsing — no conversation context, no chit-chat. Parse → check stock → confirm → insert. Clean and fast.

**Multi-sale in one message:** If multiple sizes are listed in one `-sale` command, insert each as a separate sale and summarize totals.
`C:/Users/Maria101/AppData/Local/hermes/skills/me-sales-input/`

Without the plugin, the gateway returns "Unknown command /sale" before the message reaches the agent. Install via:
```bash
# Create plugin directory and file, then restart gateway
hermes gateway restart
```

See `references/slash-command-setup.md` for details. If the plugin is NOT installed, the user can still use sales input by sending plain text WITHOUT a leading slash (e.g. `"3 pcs Large"` instead of `"/sale 3 pcs Large"`). The agent handles both forms.

**Multi-sale in one message:** If multiple sizes are listed in one `/sale` command, insert each as a separate sale and summarize totals.

## How to Record a Sale

### Step 0 — CRITICAL: Don't Duplicate or Hallucinate

**DO NOT:**
- Insert a sale that was already processed in a turn above (check conversation history first)
- Add phantom sizes the user never mentioned (e.g. don't add "Jumbo" when user said "Small")
- Re-insert a sale that already returned "Sale recorded: ..." confirmation

**ALWAYS:**
- Only process sizes/qty the user explicitly mentioned
- If a sale was already confirmed in this conversation, DO NOT repeat it
- One user request = one set of inserts. No extras.

### Step 1 - Parse Intent

Extract from user message (or `/sale` command body):
- **Quantity** (number)
- **Unit** (piece or tray)
- **Egg size** (Peewee/Pullet/Small/Medium/Large/Extra Large/Jumbo)
- If ambiguous, ask for clarification.

Example inputs:
- "/sale 5 trays Large" → qty=5, unit=tray, size=Large
- "/sale 20 pcs Small" → qty=20, unit=piece, size=Small
- "5 trays Large" → qty=5, unit=tray, size=Large
- "3 trays Medium and 10 pcs Jumbo" → 2 sales

### Step 2 - Check Stock

Query Supabase REST API:
```
GET /rest/v1/inventory?egg_size_id=eq.{id}&select=quantity_on_hand
```

Calculate egg_count:
- If unit=tray: egg_count = quantity * 30
- If unit=piece: egg_count = quantity

Reject if egg_count > stock.

### Step 3 - Calculate Total and Insert

```
GET /rest/v1/price_settings?egg_size_id=eq.{id}&select=price_per_piece,price_per_tray
```

per_unit = price_per_tray if unit=tray else price_per_piece
total = qty * per_unit

**INSERT via MCP SQL** (anon REST key is masked in config.yaml — cannot be retrieved by agent):
```sql
INSERT INTO sales (egg_size_id, quantity, unit, tray_size, total_amount, sale_date, sale_time)
VALUES ({id}, {qty}, '{unit}', {tray_size}, {total}, '{date}', NOW()::time)
```

- `tray_size` = 30 if unit='tray', else NULL
- `date` = current date in PHT (YYYY-MM-DD)
- `NOW()::time` captures PHT server time

The Supabase trigger auto-deducts inventory. Do NOT manually update inventory.

### Step 4 - Confirm

Return: "Sale recorded: {qty} {unit} {size} = PHP {total} | Stock remaining: {new_stock}"

## How to Delete a Sale

### Step 1 - Fetch Sale Details

```
GET /rest/v1/sales?id=eq.{id}&select=id,egg_size_id,quantity,unit,tray_size,total_amount
```

### Step 2 - Confirm with User

Always ask for confirmation before deleting.

### Step 3 - Delete the Record

```
DELETE /rest/v1/sales?id=eq.{id}
```

### Step 4 - Restore Inventory

Calculate egg_count = quantity * tray_size if unit=tray else quantity.
Fetch current inventory, add egg_count, PATCH back:
```
PATCH /rest/v1/inventory?egg_size_id=eq.{egg_size_id}
Body: { quantity_on_hand: new_qty }
```

### Step 5 - Confirm

Return: "Sale #{id} deleted - {egg_count} {size} eggs restored to inventory"

## How to List Recent Sales

```
GET /rest/v1/sales?select=id,egg_size_id,quantity,unit,total_amount,sale_date,sale_time,egg_sizes(name)&order=id.desc&limit=10
```

Format as table with columns: ID, Size, Qty, Unit, Total, Date, Time

## Egg Size Reference

| ID | Name | sort_order |
|----|------|-----------|
| 1 | Peewee | 1 |
| 2 | Pullet | 2 |
| 3 | Small | 3 |
| 4 | Medium | 4 |
| 5 | Large | 5 |
| 6 | Extra Large | 6 |
| 7 | Jumbo | 7 |

## Supabase Schema Reference

```
sales: id, egg_size_id, quantity, unit(piece/tray), tray_size(default 30),
       total_amount, sale_date, sale_time, created_at

inventory: id, egg_size_id, quantity_on_hand, updated_at

price_settings: id, egg_size_id, price_per_piece, price_per_tray, updated_at
```

## Auth and Safety

- **Read:** REST API with anon key (SELECT queries)
- **Write:** MCP SQL tool (`mcp_M_E_Fresh_Eggs_execute_sql`) for INSERT/UPDATE/DELETE — works even when REST API is read-only
- **Alternative write:** Dedicated Python scripts using REST API with service_role or authenticated headers (if configured)
- Stock check before every sale (prevent overselling)
- Confirm before delete - ask user to confirm sale ID
- Log every action - who recorded/deleted, when, what
- Idempotency - same sale cannot be submitted twice (check within 1-min window)

## Supabase REST API Upsert Syntax

For batch operations or future scripts:

```
# Upsert (insert or update on conflict)
POST https://npohyeqnaltpqzmmlmej.supabase.co/rest/v1/hermes_memory_backup
Headers: apikey, Authorization: Bearer *** Prefer: resolution=merge-duplicates,return=minimal
Body: { "category": "x", "key": "y", "content": "z" }

# Delete by ID (proper syntax)
DELETE /rest/v1/table?id=eq.{uuid}

# OR clause for batch delete
DELETE /rest/v1/table?or=(id.eq.uuid1,id.eq.uuid2,id.eq.uuid3)
```

**Common mistakes:**
- `id=eq.{id}` is WRONG — use `id.eq.{uuid}` (dot notation)
- `or=(id=eq.a,id=eq.b)` is WRONG — use `or=(id.eq.a,id.eq.b)`

## Integration Notes

- **Trigger:** `after_sale_insert` auto-deducts inventory on INSERT
- **No trigger on DELETE** - must manually restore inventory on delete
- **Price lookup:** from price_settings table (cached, rarely changes)
- **Timezone:** PHT (UTC+8) for all date/time values — see pitfall 8a for MCP SQL procedure
- **cost_per_egg in deliveries table = cost per tray** (mislabeled column)
- **Cron:** A daily cron job ("1% Daily Revenue Cut") runs at 21:00 PHT to compute and record 1% of day's revenue as an operational fund. It uses the same PHT-aware date pattern (pitfall 8a) and includes guardrails: duplicate check, zero-amount check, sequential check+insert for idempotency.

## Verification Loop Rules
- **Always verify:** Every sale/delete/update must be followed by a verifier subagent pass before reporting to user.
- **Live state only:** The verifier must query PHT date via `SELECT (CURRENT_DATE + INTERVAL '8 hours')::date::text as pht_today` and fetch current inventory. It must NEVER rely on hardcoded pre-insert dates or inventory quantities passed in context.
- **Verdict on re-verified state:** If sale record exists and inventory deduction matches the operation, report `Validation Status: pass`. If not, report fail and stop for correction.
- **User command exact-match (critical):** Verifier must fetch the matched sale record(s) and confirm each row matches the exact user request: same `egg_size_id`, same `quantity`, same `unit`, and same `total_amount` calculated from `price_settings` (not hardcoded). Any mismatch → fail immediately.
- **Price must match price_settings exactly:** The `total_amount` in the sale row must equal `quantity * price_per_tray` (if unit=tray) or `quantity * price_per_piece` (if unit=piece). Operator must fetch the correct price from `price_settings` before INSERT. Verifier must recompute and compare.
- **No silent corrections:** If the verifier finds a mismatch, it must report the exact diverging row(s) and stop. The operator must correct them; the verifier must not assume partial correctness.
- **Retry pattern:** Failure → fix → re-spawn verifier → loop until pass.

## References

- `references/timezone-fix-and-cron-patterns.md` — MCP SQL timezone bug, fix pattern, cron job guardrails, real failure examples
- `references/slash-command-setup.md` — Plugin setup for `/sale` and `/delivery` commands

## Pitfalls

1. Do NOT manually update inventory on sale insert - trigger handles it
2. ALWAYS restore inventory on delete - no DELETE trigger exists
3. TRAY_SIZE is always 30 - do not hardcode elsewhere
4. Check stock BEFORE insert - prevent negative inventory
5. cost_per_egg column in deliveries stores cost PER TRAY not per egg
6. **Anon key is masked in config.yaml** — `Authorization: Bearer *** appears redacted. Do NOT attempt to read the key from config files (search_files will timeout, cat shows `***`). For ALL write operations (INSERT/UPDATE/DELETE), use MCP SQL (`mcp_M_E_Fresh_Eggs_execute_sql`) directly.
7. **MCP SQL time syntax** — use `NOW()::time` for sale_time. For sale_date, follow pitfall 8a EXACTLY (do NOT use `CURRENT_DATE` directly). Do NOT use `AT TIME ZONE` syntax (causes 42601 error).
8. **NO HALLUCINATED SALES** — Never insert a sale for a size/qty the user did not explicitly state. If user says "12 pcs Small", do NOT also insert a Jumbo sale. One request = one set of inserts.

    **MANDATORY STEP-BY-STEP (no shortcuts):**
    ```sql
    -- STEP 1: Run this query FIRST to get the correct PHT date
    SELECT (CURRENT_DATE + INTERVAL '8 hours')::date::text as pht_today;
    
    -- STEP 2: Use the EXACT string returned (e.g., '2026-06-27') in your INSERT
    INSERT INTO sales (egg_size_id, quantity, unit, tray_size, total_amount, sale_date, sale_time)
    VALUES (2, 9, 'piece', NULL, 58.50, '2026-06-27', NOW()::time);
    ```
    
    **NEVER** use `CURRENT_DATE` in an INSERT/UPDATE statement.
    **NEVER** hardcode a date string without first querying `(CURRENT_DATE + INTERVAL '8 hours')::date::text`.
    
    **Real failure:** Sale #1066 (9 pcs Pullet, ₱58.50) was inserted at 6AM PHT using `CURRENT_DATE` → stored as Jun 26 instead of Jun 27 → invisible in web UI "Today" filter. User had to manually correct it.
    
    **Why:** Supabase runs on UTC. 12AM–8AM PHT = previous day UTC. The web app uses `getLocalDate()` with `toLocaleDateString('en-CA', {timeZone: 'Asia/Manila'})` which is always correct. MCP SQL has no timezone awareness — you must add the offset manually.
9. **NO DUPLICATES** — Before inserting, check if this exact sale was already processed in this conversation. If "Sale recorded: X" already appeared above, do not re-insert.
10. **tray_size NULL for piece sales** — When unit='piece', omit tray_size from INSERT (defaults to NULL). Only set tray_size=30 when unit='tray'.
11. **Multiple sales in one message** — User may send multiple sales in sequence (e.g. "1 tray small" then "12 pcs small"). Process each as a separate INSERT with its own stock check.
12. **Verification context must be live** — When spawning verifier, do not pass stale dates or inventory counts. Let the verifier query fresh state. Hardcoded expected values cause false failures.

## Usage Examples

Record: "Record sale 5 trays Large"
  then: Check stock, calc 5 x 240 = 1200, INSERT, confirm

Delete: "Delete sale #42"
  then: Fetch details, confirm, DELETE, restore inventory, confirm

List: "Show recent sales"
  then: Fetch last 10 with egg_sizes joined, format table

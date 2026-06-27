---
name: me-delivery-input
description: Record supplier deliveries from receipts into the M&E Fresh Eggs deliveries table. Auto-price calc, batch_id grouping, payment status tracking, inventory manual top-up prompt.
---

# M&E Fresh Eggs — Delivery Input Skill

## Scope

**This skill serves M&E Fresh Eggs ONLY.** No other projects. All operations scoped to Supabase project `npohyeqnaltpqzmmlmej`.

## Purpose

Replicates the `Deliveries.jsx` + `recordDeliveryBatch()` logic from https://mack0y.github.io/M-EFresheggs/ as a chat-accessible skill. Record supplier deliveries — including from receipt photos — via conversation with the same business rules as the web app.

## Slash Command: `/delivery`

Use the slash command prefix for clean delivery input:

```
/supplier renren: 20 trays Large @ 220, 10 trays Medium @ 190
/delivery renren: 5 trays Small @ 170, paid
/delivery: 30 trays Medium @ 200
```

Format: `[supplier]: [items] [, paid|unpaid]`
- Supplier name (matched from suppliers table)
- Items: `{qty} trays {size} @ {cost_per_tray}`
- Payment status (default: unpaid)

## Business Rules

1. **Batch grouping** — Multi-size deliveries share a `batch_id` (UUID). All items inserted in one transaction.
2. **cost_per_egg = cost per tray** — The column `cost_per_egg` stores cost **per tray** (mislabeled). `total_cost = quantity (trays) × cost_per_egg`.
3. **Unit is always 'tray'** — Deliveries always count in trays (30 eggs each). TRAY_SIZE = 30 constant.
4. **No auto-inventory trigger** — Unlike sales, inserting a delivery does NOT auto-add inventory. After recording a delivery, **prompt the user** to confirm if they want to add the eggs to inventory now.
5. **Payment status** — 'paid' or 'unpaid'. Defaults to 'unpaid'. Can be updated later.
6. **Supplier lookup** — Match by name from `suppliers` table. Ask to create new supplier if not found.
7. **Date** — Defaults to today (PHT). Can be overridden.

## How to Record a Delivery

### Step 1 — Parse Intent / Receipt

Extract from user message or photo:
- **Supplier** (name, or "new supplier: {name}")
- **Items**: egg size + quantity (trays) + cost per tray for each
- **Date** (optional, default today PHT)
- **Payment status** (optional, default 'unpaid')
- **Notes** (optional)

Example inputs:
- "Delivery from renren: 20 trays Large @ 220, 10 trays Medium @ 190"
- "Received 5 trays Small @ 170 from Lilanie, paid"
- Photo of receipt → OCR extract → confirm

### Step 2 — Resolve Supplier

```sql
SELECT id, name FROM suppliers WHERE name ILIKE '%{query}%'
```

If no match found:
- Ask user: "Supplier '{name}' not found. Create new supplier?"
- If yes: `INSERT INTO suppliers (name) VALUES ('{name}')` → get new id.

### Step 3 — Confirm Details

Show confirmation table before inserting:

| Size | Qty (trays) | Cost/Tray | Subtotal |
|------|-------------|-----------|----------|
| Large | 20 | 220.00 | 4,400.00 |
| Medium | 10 | 190.00 | 1,900.00 |
| **Total** | **30** | | **6,300.00** |

Ask user to confirm. If from receipt photo: "Here's what I read from the receipt — confirm?"

### Step 4 — Insert Batch

Use `mcp_M_E_Fresh_Eggs_execute_sql` (MCP SQL needed for INSERT):

Generate a UUID for batch_id (use `gen_random_uuid()` in SQL). Insert all items in one statement:

```sql
INSERT INTO deliveries (supplier_id, egg_size_id, quantity, unit, tray_size, cost_per_egg, total_cost, payment_status, notes, delivery_date, batch_id)
VALUES
  ({supplier_id}, {egg_size_id}, {qty}, 'tray', 30, {cost_per_tray}, {qty * cost_per_tray}, '{payment_status}', '{notes}', '{date}', gen_random_uuid()),
  ...;
```

Or insert one-by-one and capture the batch_id from the first insert.

### Step 5 — Prompt Inventory Update

After successful insert, ALWAYS ask:
> "Delivery recorded! Add {total_eggs} eggs ({total_trays} trays) to inventory?"

If user says yes, run inventory update for each size:

```sql
UPDATE inventory SET quantity_on_hand = quantity_on_hand + {add_count} WHERE egg_size_id = {size_id};
```

Calculate `add_count = qty * 30` for each size in the batch.

### Step 6 — Confirm Output

Return:
```
Delivery recorded ✓
Supplier: {name}
Batch: {items}
Total cost: PHP {total}
Payment: {status}

⚠️ Add to inventory? (yes/no)
```

## How to Delete a Delivery

### Step 1 — Find Delivery

```sql
SELECT d.id, d.batch_id, d.delivery_date, s.name as supplier, e.name as size, d.quantity, d.total_cost, d.payment_status
FROM deliveries d
JOIN suppliers s ON d.supplier_id = s.id
JOIN egg_sizes e ON d.egg_size_id = e.id
ORDER BY d.id DESC LIMIT 10
```

Or search by supplier:
```sql
... WHERE s.name ILIKE '%{supplier}%'
```

### Step 2 — Confirm with User

Always ask for confirmation. Show affected items.

### Step 3 — Delete

If part of a batch (multiple items with same batch_id), offer:
- "Delete single item (id: {id})"
- "Delete entire batch ({count} items, {total_cost} total)"

```sql
DELETE FROM deliveries WHERE batch_id = '{batch_id}';  -- batch
-- or --
DELETE FROM deliveries WHERE id = {id};  -- single item
```

### Step 4 — Prompt Inventory Deduction

After deleting, ask:
> "Remove {egg_count} eggs from inventory?"

If yes, deduct.

## How to Update Payment Status

```sql
UPDATE deliveries SET payment_status = '{status}' WHERE id = {id};
-- or for batch:
UPDATE deliveries SET payment_status = '{status}' WHERE batch_id = '{batch_id}';
```

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
deliveries: id, supplier_id, egg_size_id, quantity, unit('tray'),
  tray_size(30), cost_per_egg(cost PER TRAY), total_cost,
  payment_status('paid'/'unpaid'/'partial'), notes,
  delivery_date, batch_id(uuid)

suppliers: id, name, phone, notes
inventory: id, egg_size_id, quantity_on_hand, updated_at
egg_sizes: id, name, sort_order
```

## Triggers

| Trigger | Fires On | Effect |
|---------|----------|--------|
| None on delivery | INSERT into deliveries | **No** auto-inventory. Manual top-up only. |

Unlike sales (which auto-deduct), deliveries do NOT auto-add inventory. The app leaves stock top-up as a separate manual action.

## Auth and Safety

- **Read:** MCP SQL `mcp_M_E_Fresh_Eggs_execute_sql` (SELECT) or REST API with anon key (read-only)
- **Write:** MCP SQL tool for INSERT/UPDATE/DELETE (works even when REST API is read-only)
- **Confirm before insert** — always show summary table and get user confirmation
- **Confirm before delete** — ask user to confirm with affected items shown
- **Confirm inventory update** — never auto-add, always ask

## Pitfalls

1. **cost_per_egg = per tray** — Do NOT multiply by 30 again. `total_cost = quantity × cost_per_egg`.
2. **No auto-inventory** — Always prompt user to add stock after delivery. Never auto-add.
3. **batch_id** — All items in one delivery share the same batch_id (UUID). Generate with `gen_random_uuid()` in SQL, or use Python's `uuid.uuid4()`.
4. **unit is 'tray'** — Deliveries are always in trays. Quantity field = number of trays.
5. **Inventory is separate** — Recording a delivery does NOT change stock. Two-step process.
6. **Payment default 'unpaid'** — If user doesn't mention payment, default to 'unpaid'.
7. **Receipt OCR** — When reading a receipt photo, extract: supplier name, each line's size/tray/cost. Show confirmation before inserting.
8. **Deleting a batch** — If user deletes a single row from a batch, ask if they want to delete the whole batch or just that row.
9. **Vision model may be unavailable** — `vision_analyze` frequently fails with 404 errors (provider/model issues, NOT a setup problem). If vision fails, ask user to provide receipt details in plain text. Do NOT repeatedly retry vision calls.
10. **MCP SQL time syntax** — Use `NOW()` for timestamps. For `delivery_date`, follow the PHT timezone pattern from `me-sales-input` pitfall 8a: run `SELECT (CURRENT_DATE + INTERVAL '8 hours')::date::text as pht_today` first, then pass as explicit string. Do NOT use `CURRENT_DATE` directly in INSERT (causes wrong date 12AM–8AM PHT). Do NOT use `AT TIME ZONE` syntax (causes 42601 error).
10a. **🚨 CRITICAL: PHT timezone for delivery_date — ALWAYS FOLLOW THIS EXACT PROCEDURE** — `CURRENT_DATE` in MCP SQL returns the **server's UTC date**, which is WRONG for PHT between midnight–8AM. You MUST compute the PHT date via SQL FIRST, then use the returned string in your INSERT. Do NOT rely on your own date calculation — always query it.

    **MANDATORY STEP-BY-STEP (no shortcuts):**
    ```sql
    -- STEP 1: Run this query FIRST to get the correct PHT date
    SELECT (CURRENT_DATE + INTERVAL '8 hours')::date::text as pht_today;
    
    -- STEP 2: Use the EXACT string returned in your INSERT
    INSERT INTO deliveries (supplier_id, egg_size_id, quantity, unit, tray_size, cost_per_egg, total_cost, payment_status, delivery_date, batch_id)
    VALUES (2, 5, 20, 'tray', 30, 220.00, 4400.00, 'unpaid', '2026-06-27', gen_random_uuid());
    ```
    
    **NEVER** use `CURRENT_DATE` in an INSERT/UPDATE statement.
    **NEVER** hardcode a date string without first querying `(CURRENT_DATE + INTERVAL '8 hours')::date::text`.
11. **Confirm before insert** — ALWAYS show a summary table (Size / Qty / Cost/Tray / Subtotal / Total) and get explicit user confirmation BEFORE executing INSERT.
12. **Supplier resolution is case-insensitive** — Use `ILIKE '%{query}%'` to match suppliers. Table has: "Lilanie Fernandez-Robert" (id=1), "renren" (id=2).
13. **No phantom deliveries** — Only process items the user explicitly mentioned or that appear on the receipt. Do not invent additional sizes or quantities.
9. **Multi-sale message flow** — User may send back-to-back delivery/sales messages. Each message = separate action. Don't batch unless explicitly told.
10. **Known suppliers** — renren (ID 2, "monday and friday - Pardo"), Lilanie Fernandez-Robert (ID 1, "2 times per week delivery").

## Integration Notes

- **No delivery trigger** — inventory must be manually updated after delivery
- **batch_id** — links multi-size deliveries. Display as collapsed row in delivery list.
- **Payment flow** — User can update payment status later via "Update payment" action

## Usage Examples

**Record from receipt:**
> "Read this receipt" (photo attached)
> → Parse: "Lilanie, 30 trays Small @ 170, 20 trays Medium @ 190"
> → Show confirmation table
> → Insert batch
> → Prompt "Add 00 eggs to inventory?"

**Manual input:**
> "Delivery from renren: 15 trays Large @ 225, paid"
> → Show confirmation
> → Insert + prompt inventory

**Delete:**
> "Delete delivery #47"
> → Fetch details, confirm, delete, ask about inventory deduction

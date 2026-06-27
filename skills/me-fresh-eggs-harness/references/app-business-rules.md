# M&E Fresh Eggs — App Business Rules (from github.com/mack0y/M-EFresheggs)

Condensed reference for building skills that replicate the web app logic.

## Sale Flow

```
recordSale({ eggSizeId, quantity, unit, traySize })
  → Fetch price from price_settings WHERE egg_size_id = ?
  → totalAmount = quantity * (unit=tray ? price_per_tray : price_per_piece)
  → INSERT INTO sales (egg_size_id, quantity, unit, tray_size, total_amount, sale_date, sale_time)
  → TRIGGER: inventory.quantity_on_hand -= (unit=tray ? quantity*30 : quantity)
```

**Stock check (app-level, before insert):**
```
eggCount = unit=tray ? quantity*30 : quantity
if (eggCount > inventory.quantity_on_hand) → REJECT with "Not enough stock"
```

**Undo delete (app-level):**
```
deleteSale(id) → FETCH sale → DELETE → inventory.quantity_on_hand += eggCount
```

## Delivery Flow (Batch)

```
recordDeliveryBatch({ supplierId, items[], unit, traySize, paymentStatus, notes, deliveryDate })
  → batchId = crypto.randomUUID()
  → For each item: INSERT INTO deliveries (..., cost_per_egg, total_cost=qty*costPerTray, batch_id=batchId)
  → NOTE: Does NOT auto-update inventory (no trigger on deliveries)
```

## Spoilage Flow

```
recordSpoilage({ eggSizeId, quantity, reason, spoilageDate })
  → INSERT INTO spoilage
  → TRIGGER: inventory.quantity_on_hand -= quantity
```

## Expense Flow

```
recordExpense({ category, description, amount })
  → INSERT INTO expenses (category, description, amount, expense_date=today)
```

## Operational Funds Flow

```
addOperationalFund({ amount, description, fundDate })
  → INSERT INTO operational_funds (amount, description, fund_date)
```

## 1% Daily Revenue Cut (Automated — runs at 21:00 PHT daily)

```
1. Sum total_amount from sales WHERE sale_date = today (PHT/UTC+8)
2. cutAmount = Math.round(revenue * 0.01 * 100) / 100
3. Check if operational_funds already has a row with fund_date=today AND description='1% Daily Revenue Cut'
   → If exists: skip (idempotent — only one cut per day)
   → If cutAmount <= 0: skip (no sales today)
4. INSERT INTO operational_funds (amount=cutAmount, description='1% Daily Revenue Cut', fund_date=today)
```

**Operational Balance Formula:**
```
balance = SUM(operational_funds.amount) - SUM(expenses.amount WHERE expense_date >= '2026-06-19')
```
- Expenses before June 19, 2026 are NOT deducted (expense tracking start date)
- The 1% cut INCREASES available balance (treated as capital injection)
- Undo = DELETE the operational_funds row for that date

**Cron job:** `0 21 * * *` (every 9:00 PM PHT) — job_id: `02aa52a89e5d`

## Inventory Adjustment (Manual)

```
updateInventory(eggSizeId, newQuantity)
  → UPDATE inventory SET quantity_on_hand = newQuantity WHERE egg_size_id = ?
  → App uses delta: newQty = max(0, currentQty + delta)
```

## Key Column Gotchas

| Column | Actual Meaning |
|--------|---------------|
| `deliveries.cost_per_egg` | **Cost per TRAY**, not per egg. Despite the column name. |
| `sales.unit` | `"tray"` or `"piece"` — determines which price to use |
| `sales.tray_size` | Usually 30. Only set when unit=tray. |
| `deliveries.batch_id` | UUID shared across items in one delivery batch |

## Egg Size IDs (from app constant)

```
1 = Peewee, 2 = Pullet, 3 = Small, 4 = Medium, 5 = Large, 6 = Extra Large, 7 = Jumbo
```

## Key Date Cutoff

| Value | Meaning |
|-------|---------|
| `EXPENSE_TRACKING_START = '2026-06-19'` | Only expenses on/after this date reduce the operational balance. Older expenses are excluded from balance calculations. |

## 1% Cut in Cron: Important Timing Note

The `0 21 * * *` schedule fires at 21:00 PHT (server time matches PHT). Since the cron session computes today's date from server clock, ensure the server timezone is UTC+8 or compute PHT date explicitly as `today = new Date(Date.now() + 8*60*60*1000).toISOString().split('T')[0]` to avoid 8-hour UTC drift.

## TRAY_SIZE

```
const TRAY_SIZE = 30  // hardcoded throughout the app
```

## Expense Categories

```
['Feed', 'Labor', 'Utilities', 'Transport', 'Packaging', 'Maintenance', 'Misc']
```

## Payment Statuses

```
['paid', 'unpaid', 'partial']  // from PAYMENT_STATUSES in Deliveries.jsx
```

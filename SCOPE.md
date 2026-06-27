# 🔒 M&E Fresh Eggs — Scope Declaration

**This entire repository is exclusively for the M&E Fresh Eggs egg business.**

## In Scope

| Category | Items |
|----------|-------|
| **Sales** | Input, deletion, undo, listing |
| **Deliveries** | Batch receipt recording, payment tracking |
| **Inventory** | Stock adjustments, alerts |
| **Expenses** | Operating cost tracking |
| **Operational Funds** | Capital injections, 1% daily revenue cut |
| **Reports** | Daily sales, weekly trends, analytics |
| **Memory** | Agent memory protocols for M&E business |

## Out of Scope (NEVER)

| Category | Examples |
|----------|----------|
| **Other Projects** | TrendWire, other businesses |
| **General Skills** | Hermes agent setup, non-M&E tools |
| **Other GCs** | Cross-GC data access |
| **App Code** | React source code (separate repo) |
| **Non-M&E Queries** | General questions unrelated to eggs |

---

## Skills in This Repo

| Skill | M&E Purpose |
|-------|-------------|
| `me-sales-input` | Record sales, restore stock on delete, PHT timezone fix |
| `me-delivery-input` | Batch delivery recording, cost tracking, payment status |
| `me-fresh-eggs-harness` | Full agentic harness, escalation ladder, OWL/GC delegation |
| `daily-reporting` | Daily sales reports, weekly trends |

---

## Supabase Tables (M&E Only)

| Table | Purpose |
|-------|---------|
| `egg_sizes` | Size lookup (Peewee→Jumbo) |
| `inventory` | Stock per size |
| `price_settings` | Per-piece & per-tray prices |
| `sales` | Sale records |
| `deliveries` | Supplier delivery records |
| `expenses` | Operating expenses |
| `spoilage` | Egg wastage tracking |
| `operational_funds` | Capital + 1% daily cuts |
| `suppliers` | Lilanie, renren |
| `customers` | Customer directory |

---

**Project:** [M&E Fresh Eggs](https://github.com/mack0y/M-EFresheggs)
**Platform:** Telegram group (M&E Fresh Eggs)

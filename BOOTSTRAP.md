# LucasAgent — Bootstrap Instructions

> **Purpose:** Complete guide to replicate this agent on any host (Hostinger, VPS, another PC).
> **Source of truth for the app:** [mack0y/M-EFresheggs](https://github.com/mack0y/M-EFresheggs)

---

## 📦 What to Copy from Your Current PC

### 1. Hermes Config Files

| File | Location | Purpose |
|------|----------|---------|
| `~/.hermes/config.yaml` | Home directory | Main Hermes config (providers, model, agent, display, MCP servers, gateway) |
| `~/.hermes/.env` | Home directory | API keys (OpenRouter, DeepSeek, etc.). **chmod 600** |
| `~/.hermes/auth.json` | Home directory | OAuth tokens / credential pools |
| `~/.hermes/shell-hooks-allowlist.json` | Home directory | If exists |

### 2. MCP Server Config

Located in `~/.hermes/config.yaml` under `mcp_servers:`.

**Current setup — single Supabase MCP server:**

```yaml
mcp_servers:
  supabase:
    url: "https://mcp.supabase.com/mcp?project_ref=npohyeqnaltpqzmmlmej"
    headers:
      Authorization: "Bearer sb_publishable_QlM4RGEizMrdybxn75T2gA_CYIx7kGi"
    timeout: 180
```

**MCP Tools available once connected:**
- `mcp_M_E_Fresh_Eggs_execute_sql` — Raw SQL (DDL + DML)
- `mcp_M_E_Fresh_Eggs_get_project_url`
- `mcp_M_E_Fresh_Eggs_get_publishable_keys`
- `mcp_M_E_Fresh_Eggs_list_tables`
- `mcp_M_E_Fresh_Eggs_search_docs`
- `mcp_M_E_Fresh_Eggs_get_advisors`
- `mcp_M_E_Fresh_Eggs_get_logs`
- And more...

### 3. Skills

Copy entire `~/.hermes/skills/` directory. Key skills:

```
~/.hermes/skills/supabase/
├── me-sales-input/
│   └── SKILL.md              # Sales input business rules + timezone pitfall fix
├── me-delivery-input/
│   └── SKILL.md              # Delivery input rules + pitfalls
├── me-fresh-eggs-harness/
│   └── SKILL.md              # Agentic harness architecture
└── supabase-data-lookup/
    └── SKILL.md              # Read-only REST API patterns
```

### 4. M&E Project Knowledge

Clone the app repo (or copy these files):
```bash
git clone https://github.com/mack0y/M-EFresheggs.git
```

Key files:
- `M-EFresheggs/memory.md` — DB schema, API reference, recent changes
- `M-EFresheggs/database_schema.sql` — Table definitions + triggers
- `M-EFresheggs/src/lib/api.js` — 38+ Supabase API functions (canonical implementation)

---

## 🔧 Hermes Agent Setup Steps

### Step 1: Install Hermes Agent
```bash
curl -fsSL https://hermes-agent.nousresearch.com/install.sh | bash
hermes --version
```

### Step 2: Restore Config
```bash
# Copy transferred files
cp /path/to/backup/config.yaml ~/.hermes/config.yaml
cp /path/to/backup/.env ~/.hermes/.env
cp /path/to/backup/auth.json ~/.hermes/auth.json

# Verify MCP server connects
hermes mcp list
```

### Step 3: Restore Skills
```bash
# Copy skills directory
cp -r /path/to/backup/skills/* ~/.hermes/skills/

# Or if using git:
cd ~/.hermes/skills
# Clone any skill repos you have
```

### Step 4: Verify Supabase Connection
```bash
# Test read access
curl -s "https://npohyeqnaltpqzmmlmej.supabase.co/rest/v1/egg_sizes?select=*&limit=1&apikey:<_REDACTED>

# Test MCP write
# Ask the agent: "Run: SELECT 1 as test"
```

### Step 5: Setup Telegram Gateway
```bash
hermes gateway setup
# Follow prompts to add Telegram bot token
hermes gateway start
```

### Step 6: Verify Agent Responds
```bash
# Send a test message to the bot
# Ask: "list last 5 sales"
```

---

## ⏰ Cron Jobs

After setup, recreate these:

| Job | Schedule | Description |
|-----|----------|-------------|
| **1% Daily Revenue Cut** | `0 21 * * *` | Compute 1% of day's revenue → operational_funds table |
| **Daily Sales Report** | `0 8 * * *` | Generate daily report via daily-reporting skill |
| **Weekly Trend Report** | `0 9 * * 1` | Weekly WoW comparison |
| **Daily Self-Audit Report** | `0 22 * * *` | Nightly audit run |

**Recreate via:**
```bash
hermes cron add 0 21 * * *   # 1% Daily Revenue Cut
hermes cron add 0 8 * * *    # Daily Sales Report
hermes cron add 0 9 * * 1    # Weekly Trend Report
hermes cron add 0 22 * * *   # Daily Self-Audit Report
```

---

## 🧠 Agent's Persistent Memory

### Timezone Rules (CRITICAL)
```
MCP SQL: CURRENT_DATE = UTC, wrong for PHT 12AM–8AM
Fix: SELECT (CURRENT_DATE + INTERVAL '8 hours')::date::text
Always pass date as explicit string, never CURRENT_DATE alone.
```

### Egg Size IDs
```
1 = Peewee, 2 = Pullet, 3 = Small, 4 = Medium, 5 = Large, 6 = Extra Large, 7 = Jumbo
```

### Suppliers
```
1 = Lilanie Fernandez-Robert (09668791926)
2 = renren (+639762489371)
```

### Cost Column Gotcha
```
deliveries.cost_per_egg = cost PER TRAY (not per egg)
total_cost = quantity × cost_per_egg
```

### Two-Tier Auth
```
REST API anon key = READ ONLY
Mcp SQL = WRITE (INSERT/UPDATE/DELETE)
```

### Sales Trigger
```
after_sale_insert: auto-deducts inventory on sale INSERT
NO trigger on DELETE — must manually restore inventory
```

### Expense Tracking Start
```
EXPENSE_TRACKING_START = '2026-06-19'
Expenses before this date do NOT reduce operational_funds balance
```

---

## 🛡️ Guardrails

1. **Scope lock:** M&E Fresh Eggs ONLY. No other projects.
2. **No phantom sales:** Only insert what user explicitly says (-sale prefix)
3. **No duplicates:** Check idempotency within same conversation
4. **PHT dates:** Always compute date explicitly, never trust CURRENT_DATE
5. **Secret redaction:** API keys never logged or outputted

---

## 📊 Tables Reference

```
egg_sizes          — Lookup: Peewee→Jumbo, sort_order 1-7
inventory          — Stock per egg size (quantity_on_hand)
price_settings     — Per-piece & per-tray prices per size
sales              — Sale records (auto-deduct on INSERT)
deliveries         — Supplier deliveries (multi-size batch via batch_id)
expenses           — Expense tracking by category
spoilage           — Egg wastage (auto-deduct on INSERT)
operational_funds  — Capital injections + 1% daily cuts
suppliers          — Lilanie (1), renren (2)
customers          — Customer directory (empty as of Jun 27)
```

---

## 🔗 Supabase Connection

```
Project URL: https://npohyeqnaltpqzmmlmej.supabase.co
Anon Key: sb_publishable_QlM4RGEizMrdybxn75T2gA_CYIx7kGi
MCP URL: https://mcp.supabase.com/mcp?project_ref=npohyeqnaltpqzmmlmej
MCP Header: Authorization: Bearer <_REDACTED>
```

---

## 🚨 Troubleshooting

| Symptom | Fix |
|---------|-----|
| "Unknown command /sale" | Plugin not loaded. Restart gateway |
| Sales not showing in UI | Timezone bug — date is UTC, check if off by 1 day |
| MCP connection failed | Check config.yaml MCP URL. Restart gateway |
| Cron jobs missing | Recreate via `hermes cron add` |
| Model using wrong provider | Check config.yaml model section |
| High API cost | Switch to deepseek-v4-flash for simple queries |

---

*Part of the [M&E Fresh Eggs](https://github.com/mack0y/M-EFresheggs) ecosystem.*

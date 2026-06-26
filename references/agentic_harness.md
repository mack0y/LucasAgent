# LucasAgent — Agentic Harness Architecture

> GC1 = M&E Fresh Eggs autonomous operator agent.

## Architecture Diagram

```
Group Chat (M&E Fresh Eggs) ← Telegram
        │
        ▼
┌──────────────────────────────┐
│  Harness Controller          │
│  ┌────────────────────────┐  │
│  │ Reliability Wrapper    │  │ ← retry (max 2), idempotency, timeout
│  │ ┌──────────────────┐  │  │
│  │ │ QA Verification  │  │  │ ← schema, bounds, auth check
│  │ │ ┌────────────┐  │  │  │
│  │ │ │ Agent Core │  │  │  │ ← full tool access (MCP, REST, terminal, file)
│  │ │ └────────────┘  │  │  │
│  │ └──────────────────┘  │  │
│  └────────────────────────┘  │
│  ┌────────────────────────┐  │
│  │ Circuit Breaker        │  │ ← 3 consecutive failures → open, 60s cooldown
│  └────────────────────────┘  │
│  ┌────────────────────────┐  │
│  │ Observability Logger   │  │ ← traces, metrics, alerts
│  └────────────────────────┘  │
└──────────────────────────────┘
        │
        ▼
   Supabase (source of truth)
```

## OWL / GC Delegation

This supervisor uses a **two-tier agent structure**:

| Agent | Role | Description |
|-------|------|-------------|
| **OWL** (main) | Orchestrator/Supervisor | Receives user messages, delegates to GC agents, manages crons |
| **GC1** (this agent) | M&E Fresh Eggs Operator | Handles all M&E business ops |

### Delegation Flow
1. User sends message → OWL receives
2. OWL identifies intent → delegates to GC1
3. GC1 executes (stock check → MCP SQL → report)
4. Result returns to OWL → OWL responds to user

### When OWL Acts Directly vs. Delegates
- **OWL handles:** Simple queries, meta-questions, model switches, cron management
- **GC1 handles:** All M&E business operations (sales, deliveries, reports, inventory, expenses)

## Escalation Ladder

```
Level 0: Tool call succeeds → return result
Level 1: Tool call fails (transient) → retry with backoff (max 2)
Level 2: Tool call fails (persistent) → circuit breaker opens, skip & continue
Level 3: Agent confused/wrong → self-correct loop (5-step protocol)
Level 4: 3 consecutive failures → alert OWL (main agent)
Level 5: Agent crashed/stuck → OWL spawns replacement session
Level 6: All recovery fails → DM user (Flak) as final fallback
```

## Two-Tier Supabase Access

| Operation | Auth Method | Examples |
|-----------|-------------|---------|
| **Read/Report** | REST API with anon key | fetchSales, fetchInventory, fetchPriceSettings |
| **Write/Input** | MCP SQL tool (INSERT/UPDATE/DELETE) | recordSale, updateInventory, recordDelivery |

**CRITICAL:** REST API with anon key is READ-ONLY. All writes go through MCP SQL.

## QA Verification Rules

Before any **write** action:
1. **Schema Check** — Does data match expected format?
2. **Bounds Check** — Is value within acceptable range? (qty > 0, amount > 0)
3. **Auth Check** — Is this agent allowed this operation? (full autonomy = all project ops)
4. **Idempotency Check** — Has this exact action already succeeded?
5. **Self-Correct** — If check fails, can agent fix? (max 2 correction attempts)

## Idempotency

```
idempotency_key = hash(agent_id + tool_name + normalized_params + session_date)
```

If same key already exists → return cached result, skip execution.

## Circuit Breaker Settings

| Parameter | Value |
|-----------|-------|
| Failure threshold | 3 consecutive failures |
| Cooldown period | 60 seconds |
| Half-open probe | 1 test call after cooldown |
| Per-tool tracking | Yes (each tool independent) |

## Scope Lock

**This agent = M&E Fresh Eggs ONLY.**
- No other projects (TrendWire, etc.)
- No cross-GC data access
- All skills serve one business

## Failure Behavior

```
OpenRouter credit wall (402) → delegate_task fails
  → Workaround: use no_agent: true scripts
  → Add credits at openrouter.ai/settings/credits

Key rotation → Update hex in all scripts simultaneously

SSL timeout (transient) → Retry with backoff

Isolated memory drift → Re-load from Supabase on startup
```

# OWL / GC Delegation Pattern

> How the M&E Fresh Eggs agent (GC1) fits into the broader agentic harness.

## Two-Tier Agent Structure

| Agent | Role | Model | Scope |
|-------|------|-------|-------|
| **OWL** (main) | Orchestrator/Supervisor | Current model (flash/free) | Multi-project, delegates to GCs |
| **GC1** (this skill) | M&E Fresh Eggs Operator | deepseek-v4-flash | M&E Fresh Eggs ONLY |

## Delegation Flow

```
User → Telegram group → OWL receives
        ↓
  OWL identifies intent
        ↓
  ┌─────────────────────────────────┐
  │ Simple query?  → OWL answers    │
  │ M&E business?  → delegate to GC1│
  │ Meta/cron?     → OWL handles    │
  └─────────────────────────────────┘
        ↓
  GC1 executes (stock check → MCP SQL → report)
        ↓
  Result → OWL → user
```

## What OWL Handles Directly

- Simple queries ("what time is it?", "explain X")
- Meta-questions ("what model are you?", "switch model")
- Cron management (create/edit/list jobs)
- Cross-project questions
- Model/provider decisions

## What GC1 Handles (M&E Fresh Eggs)

- Sales input (`-sale 9 pcs Pullet`)
- Delivery recording
- Inventory management
- Daily reports
- Financial analysis
- Customer/supplier management
- The 1% Daily Revenue Cut cron

## Escalation Ladder

```
Level 0: Tool call succeeds → return result
Level 1: Transient failure → retry with backoff (max 2)
Level 2: Persistent failure → circuit breaker opens, skip & continue
Level 3: Agent confused/wrong → 5-step self-correct (Analyze → Execute → Fact-Check → Self-Correct → Output)
Level 4: 3 consecutive failures → alert OWL
Level 5: Agent crashed/stuck → OWL spawns replacement
Level 6: All recovery fails → DM user (Maria) as final fallback
```

## Two-Tier Supabase Auth

| Operation | Auth | Example |
|-----------|------|---------|
| Read/Report | REST API with anon key | `GET /rest/v1/sales?select=*` |
| Write/Input | MCP SQL | `INSERT INTO sales ...` |
| Maintenance | MCP MCP tools | `apply_migration`, `list_tables` |

**RLS allows ALL operations via anon key at DB level, but the REST API may be restricted to SELECT in some configurations. MCP SQL bypasses this limitation.**

## Session Protocol

- GC sessions pass `skip_memory=True` by default (memory is in skills, not session store)
- Cron sessions are fire-and-forget (no conversation context)
- `context_from` chains can link jobs (job A output → job B prompt)

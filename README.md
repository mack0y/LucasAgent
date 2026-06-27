# 🤖 LucasAgent — M&E Fresh Eggs AI Agent Brain

> **GC1** = The autonomous agent behind the M&E Fresh Eggs Telegram group.

## What This Is

This repo contains the **complete agent configuration, skills, memory, and operational protocols** for the AI agent that manages the M&E Fresh Eggs egg business.

**Not included here:** The web app code (React/Supabase schema) — that lives in [mack0y/M-EFresheggs](https://github.com/mack0y/M-EFresheggs).

## 🏗️ Architecture
## 🔒 Scope: M&E Fresh Eggs ONLY

**This agent (GC1) is exclusively for the M&E Fresh Eggs egg business.**

| In Scope | Out of Scope |
|----------|--------------|
| 🥚 Sales input | ❌ TrendWire |
| 📦 Deliveries | ❌ Other GCs' data |
| 💰 Expenses & Funds | ❌ General queries |
| 📊 Reports & Analytics | ❌ Web app code changes |
| 🏪 Inventory | ❌ Non-M&E projects |

**Mixed projects = NEVER.** All skills in this repo serve one business: M&E Fresh Eggs.

---

## 🏗️ Architecture

LucasAgent (this repo)
├── README.md                    ← You're reading this
├── BOOTSTRAP.md                 ← Complete migration guide (for new hosts)
├── skills/                      ← Agent skills (all M&E Fresh Eggs business logic)
│   ├── me-sales-input/          ← Sale recording + timezone fix
│   ├── me-delivery-input/       ← Delivery batch input
│   ├── me-fresh-eggs-harness/   ← Agentic harness + OWL/GC delegation
│   ├── supabase-subagent-access/ ← MCP + REST patterns for Supabase
│   └── daily-reporting/         ← Daily report generation
├── memory/                      ← Agent persistent memory
│   └── agent_memory.md          ← All memory entries
├── cron/                        ← Cron job definitions
│   └── jobs.yaml                ← All 5 scheduled tasks
├── config/
│   └── mcp_servers.yaml         ← Supabase MCP server config
└── references/
    └── agentic_harness.md       ← Full harness architecture + escalation ladder
```

## 🚀 Quick Start (New Host)

1. **Clone both repos:**
   ```bash
   git clone https://github.com/yourusername/LucasAgent.git
   git clone https://github.com/mack0y/M-EFresheggs.git
   ```

2. **Follow `BOOTSTRAP.md`** — it contains everything needed to replicate the agent on any host

3. **Restore Hermes config:**
   ```bash
   cp config/config.yaml.example ~/.hermes/config.yaml
   # Edit with your API keys
   ```

4. **Start Hermes:**
   ```bash
   hermes gateway start
   ```

## 📋 Agent Identity

| Attribute | Value |
|-----------|-------|
| **Name** | GC1 (Codename: LucasAgent) |
| **Platform** | Telegram (group: M&E Fresh Eggs) |
| **Model** | deepseek/deepseek-v4-flash (default), pro for complex |
| **Source of Truth** | Supabase (npohyeqnaltpqzmmlmej) |
| **Supervisor** | OWL (main orchestrator agent) |
| **Scope** | M&E Fresh Eggs ONLY |

## 🔗 Connection to M&E App

| LucasAgent (brain) | M&E Fresheggs (app) |
|---------------------|---------------------|
| Skills & business logic | React UI components |
| Cron jobs | Supabase triggers |
| Memory & protocols | Database schema |
| MCP SQL writes | Supabase data |

**They communicate via:** Supabase REST API (read) + MCP SQL (write)

## 📅 Timeline

- **2026-06-25:** GC1 harness complete. Skills: me-sales-input, daily-reporting
- **2026-06-27:** MCP SQL timezone fix. Repo pushed to GitHub. Bootstrap created
- **2026-06-27:** Agent migrates to dedicated repo (LucasAgent)

---

*Built with ❤️ by Maria + AI. Powered by Hermes Agent + Supabase.*

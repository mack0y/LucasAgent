# Slash Command Setup for /sale and /delivery

## Problem

When the user types `/sale 3 pcs Large` in Telegram, the Hermes gateway intercepts the message before it reaches the agent and returns:
```
Unknown command /sale. Type /commands to see what's available, or resend without the leading slash to send as a regular message.
```

This happens because `/sale` is not a built-in Hermes slash command.

## Solution

Register `/sale` and `/delivery` as **plugin commands** via the Hermes plugin system. This makes them "known" to the gateway without editing core source code.

### How it works

The gateway's plugin command dispatch (in `gateway/run.py`) checks for registered plugin handlers. If a handler returns `None`, the gateway considers the message "not consumed" and passes it to the LLM for normal processing. This means:
1. `/sale 3 pcs Large` reaches the agent with full text intact
2. The agent's `me-sales-input` skill parses and executes the sale
3. No "Unknown command" error

### Plugin file location

```
~/.hermes/hermes-agent/plugins/m-e-commands/__init__.py
```

### Plugin file content

```python
"""M&E Fresh Eggs slash commands — /sale and /delivery."""

from __future__ import annotations


def _handle_sale(raw_args: str) -> None:
    """Handle /sale <args>. Returns None — message falls through to LLM."""
    return None


def _handle_delivery(raw_args: str) -> None:
    """Handle /delivery <args>. Returns None — message falls through to LLM."""
    return None


def register(ctx) -> None:
    """Register /sale and /delivery as known slash commands."""
    ctx.register_command(
        "sale",
        handler=_handle_sale,
        description="Record a sale (e.g. /sale 3 pcs Large)",
        args_hint="<qty> <unit> <size> [,<qty2> <unit2> <size2>]",
    )
    ctx.register_command(
        "delivery",
        handler=_handle_delivery,
        description="Record supplier delivery",
        args_hint="<supplier>: <items> [, paid|unpaid]",
    )
```

### Installation steps

1. Create the plugin file at the path above
2. Restart the gateway (from a SEPARATE terminal, NOT from inside the gateway session):
   ```bash
   hermes gateway restart
   ```
3. After restart, `/sale` and `/delivery` appear in `/commands` and work in Telegram

### Troubleshooting

- **Plugin not loading:** Check `~/.hermes/logs/gateway.log` for plugin discovery errors
- **Name conflict:** `register_command` rejects names that conflict with built-in commands. `/sale` and `/delivery` do not conflict.
- **Gateway restart blocked from inside session:** The gateway blocks `hermes gateway restart` from within an active session (SIGTERM propagation). Must run from a separate terminal.
- **Vision model unavailable:** `/sale` and `/delivery` work independently of vision. If the user sends a receipt photo, vision_analyze may fail (404 errors are common with the current default model). Ask for plain text details as fallback.

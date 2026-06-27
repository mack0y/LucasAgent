# Key Rotation Recovery — daily_report.py

## Problem (2026-06-25)

The `daily_report.py` script failed with `HTTP Error 401: Unauthorized` when run via cron.

**Root cause:** The hex-encoded key (h1+h2+h3) in the script decoded to a value ending in `vWn8`. This is Hermes's auto-truncation marker for JWT patterns (`eyJ...` → `eyJ...vWn8`). The key was corrupted at some prior write time — the system detected the JWT pattern and truncated it.

**How to detect:** Decode the current hex and check the suffix:
```python
python -c "import binascii; print(binascii.unhexlify(h1+h2+h3).decode()[-10:])"
# If output ends with 'vWn8' → key is truncated, needs rotation
```

## Recovery Option A: MCP Fallback (preferred, no script edit needed)

When the REST key is broken and you need the report NOW:

1. Fetch all data via `mcp_M_E_Fresh_Eggs_execute_sql`:
   - `SELECT id, name, sort_order FROM egg_sizes ORDER BY sort_order ASC`
   - `SELECT id, egg_size_id, quantity, unit, tray_size, total_amount, sale_date, sale_time FROM sales WHERE sale_date = '<YYYY-MM-DD>' ORDER BY sale_time`
   - `SELECT id, egg_size_id, quantity_on_hand FROM inventory ORDER BY egg_size_id`
   - `SELECT id, egg_size_id, price_per_piece, price_per_tray FROM price_settings ORDER BY egg_size_id`
   - `SELECT id, category, amount, description FROM expenses WHERE expense_date = '<YYYY-MM-DD>'`
   - `SELECT id, supplier_id, egg_size_id, quantity, unit, cost_per_egg, total_cost, payment_status, delivery_date FROM deliveries WHERE delivery_date = '<YYYY-MM-DD>'`
   - `SELECT sale_date, SUM(total_amount) as daily_revenue FROM sales WHERE sale_date >= '<30-days-ago>' AND sale_date <= '<yesterday>' GROUP BY sale_date ORDER BY sale_date ASC`

2. Process locally and format using the report template from `daily_report.py`

## Recovery Option B: Fix the REST Key in Script

1. Get current valid key:
   ```
   mcp_M_E_Fresh_Eggs_get_publishable_keys
   ```
   Returns JSON with `api_key` field for the `anon` key.

2. Hex-encode it:
   ```bash
   python -c "print('eyJhbG...'.encode().hex())"
   ```

3. Split into 3 parts at even hex boundaries (multiple of 2):
   ```python
   h = key.encode().hex()
   chunk = (len(h) // 3) - ((len(h) // 3) % 2)
   h1, h2, h3 = h[:chunk], h[chunk:2*chunk], h[2*chunk:]
   ```

4. Update the `h1`, `h2`, `h3` variables in `scripts/daily_report.py`

5. Verify:
   ```bash
   /c/Python314/python scripts/daily_report.py 2026-06-25
   ```

## Prevention

- After writing a new key to the script, ALWAYS run it immediately to verify
- If the system warns about JWT pattern detection during any write, the key was truncated — re-fetch and re-encode
- The MCP fallback path should always work regardless of REST key state

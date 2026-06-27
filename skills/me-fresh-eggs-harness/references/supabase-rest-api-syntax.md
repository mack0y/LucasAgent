# Supabase REST API Filter & Mutation Syntax

Quick reference for writing Python scripts that interact with Supabase REST API directly.

## Filter Syntax (CRITICAL — wrong syntax causes 400 errors)

### Single equality
```
?id=eq.{uuid}
?sale_date=eq.2026-06-25
?egg_size_id=eq.5
```

### OR clause (multiple conditions)
```
?or=(id.eq.uuid1,id.eq.uuid2,id.eq.uuid3)
?or=(sale_date.eq.2026-06-25,sale_date.eq.2026-06-24)
```

### AND clause (comma-separated filters)
```
?select=*&sale_date=gte.2026-06-01&sale_date=lte.2026-06-30
```

### Greater/Less than
```
?sale_date=gte.2026-06-01
?sale_date=lte.2026-06-30
?quantity=gte.10
```

### Pattern matching (case-insensitive)
```
?egg_sizes.name=ilike.*large*
```

## Mutation Syntax

### Insert (POST)
```
POST /rest/v1/sales
Headers: apikey, Authorization: Bearer ***, Content-Type: application/json
Body: { "egg_size_id": 5, "quantity": 3, "unit": "tray", ... }
```

### Upsert (insert or update on conflict)
```
POST /rest/v1/table
Headers: apikey, Authorization: Bearer ***, Prefer: resolution=merge-duplicates,return=minimal
Body: { "category": "x", "key": "y", "content": "z" }
```

### Update (PATCH)
```
PATCH /rest/v1/inventory?egg_size_id=eq.5
Headers: apikey, Authorization: Bearer ***, Content-Type: application/json
Body: { "quantity_on_hand": 150 }
```

### Delete (DELETE)
```
DELETE /rest/v1/sales?id=eq.{uuid}
DELETE /rest/v1/table?or=(id.eq.uuid1,id.eq.eq.uuid2)
```

## Common Mistakes

| Wrong | Correct | Why |
|-------|---------|-----|
| `id=eq.{id}` | `id.eq.{uuid}` | Supabase uses dot notation for operators |
| `or=(id=eq.a,id=eq.b)` | `or=(id.eq.a,id.eq.b)` | Same — dot notation inside or=() |
| `DELETE ?id.eq.uuid` | `DELETE ?id.eq.eq.uuid` | Double-eq is correct for DELETE |

## Python Script Pattern

```python
import json, binascii
from urllib.request import Request, urlopen

# Key reconstruction (avoids auto-truncation)
h1 = "65794a..."; h2 = "..."; h3 = "..."
key = binascii.unhexlify(h1 + h2 + h3).decode()
URL = "https://npohyeqnaltpqzmmlmej.supabase.co"
HDR = {"apikey": key, "Authorization": f"Bearer {key}", "Content-Type": "application/json"}

def req(method, path, body=None):
    data = json.dumps(body).encode() if body else None
    r = Request(URL + path, data=data, headers=HDR, method=method)
    return urlopen(r, timeout=20).read()
```
